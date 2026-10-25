import base64
import io
import json
import os
from typing import Any

import streamlit as st
from PIL import Image
from openai import OpenAI

st.set_page_config(
    page_title="HairMuse AI — Hairstyle Studio",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Visual style ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0b0d12; color: #f4f5f7; }
.block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem; }
.hero { padding: 1.5rem 0 1rem 0; }
.eyebrow { color: #c6a8ff; font-size: .78rem; letter-spacing: .18em; font-weight: 700; text-transform: uppercase; }
.hero h1 { font-family: 'Manrope', sans-serif; font-size: clamp(2.2rem, 5vw, 4rem); line-height: 1.05; margin: .5rem 0; color: #fff; }
.hero p { color: #aeb3c2; max-width: 700px; font-size: 1.05rem; }
.panel { background: #141720; border: 1px solid #282c39; border-radius: 20px; padding: 1.15rem; }
.small-muted { color: #aeb3c2; font-size: .9rem; }
.tag { display:inline-block; background:#252033; color:#d9c7ff; padding:.3rem .65rem; border-radius:99px; font-size:.8rem; margin:.15rem .2rem .15rem 0; }
div[data-testid="stMetric"] { background: #141720; border: 1px solid #282c39; padding: 1rem; border-radius: 14px; }
.stButton > button[kind="primary"] { background: linear-gradient(90deg,#9b78ff,#c08cff); color:#0c0d12; border:0; border-radius:12px; font-weight:800; min-height:3rem; }
.stButton > button { border-radius:12px; }
hr { border-color:#282c39; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">PERSONAL GROOMING • AI STUDIO</div>
  <h1>Find your <span style="color:#bd9cff">best hair.</span></h1>
  <p>Upload a photo. HairMuse studies your visible face proportions and hair, compares different cuts, then creates realistic hairstyle previews and a barber-ready recommendation.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Settings")
    api_key_input = st.text_input("OpenAI API key (optional if set in environment)", type="password")
    analysis_model = st.text_input("Vision model", value=os.getenv("OPENAI_VISION_MODEL", "gpt-4.1"))
    image_model = st.text_input("Image edit model", value=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"))
    st.caption("Your API key is used only for requests from this app session. Never publish a key in shared code.")

api_key = api_key_input.strip() or os.getenv("OPENAI_API_KEY", "")
if not api_key:
    st.info("To enable AI analysis and image previews, add an OpenAI API key in the sidebar or set OPENAI_API_KEY in your environment. The interface works without a key, but AI actions will remain disabled.")

left, right = st.columns([1.05, 1], gap="large")
with left:
    st.markdown("### 01 · Your photo")
    uploaded = st.file_uploader(
        "Upload a clear front-facing photo",
        type=["jpg", "jpeg", "png", "webp"],
        help="Use a well-lit photo with your full hairline, face, ears, and jaw visible.",
    )
    side_uploaded = st.file_uploader(
        "Side-profile photo (recommended)",
        type=["jpg", "jpeg", "png", "webp"],
        help="A side view improves head-shape and hairstyle analysis.",
    )
    if uploaded:
        try:
            image = Image.open(uploaded).convert("RGB")
            st.image(image, caption="Primary photo", use_container_width=True)
        except Exception:
            st.error("That image could not be opened. Try a JPG or PNG file.")

with right:
    st.markdown("### 02 · Your style preferences")
    hair_density = st.select_slider("Hair density", options=["Fine", "Medium", "Thick"], value="Thick")
    length_preference = st.selectbox(
        "Preferred hair length",
        ["Let AI decide", "Short", "Medium", "Medium to long", "Long"],
        index=0,
    )
    vibe = st.selectbox(
        "Desired look",
        ["Let AI decide", "Big and voluminous", "Clean and sharp", "Messy and textured",
         "Classic and mature", "Trendy / editorial", "Low-maintenance"],
        index=1,
    )
    maintenance = st.selectbox("Daily styling effort", ["Low", "Moderate", "High"], index=1)
    variants = st.slider("Hairstyle previews to generate", min_value=3, max_value=5, value=4)
    st.caption("Each preview uses image editing and may consume API credits. Generated styles are visual approximations, not a guarantee of exact barber results.")

ANALYSIS_SYSTEM = """
You are an evidence-conscious men's hairstylist and facial-proportion analyst.
Analyze only visible evidence. Do not claim exact anatomical measurements from an ordinary photo.
Do not infer hidden body size or unseen features. Treat user-provided hair density as given, but distinguish density from strand thickness and texture.
Recommend genuinely distinct hairstyles, not five minor fade variations. Personalize to this specific person.
Preserve identity in every image-edit prompt: change hair only; never alter face, facial hair, skin, expression, age, body, clothes, background, framing, or lighting.
Return valid JSON only, no markdown.
"""

def image_data_url(pil_img: Image.Image) -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=92)
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"

def parse_json_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text)

def run_analysis(client: OpenAI, front: Image.Image, side: Image.Image | None,
                 density: str, length: str, vibe_choice: str, maintenance_choice: str,
                 count: int, model: str) -> dict[str, Any]:
    content = [
        {"type": "input_text", "text": f"""
Analyze the attached person's front photo{(' and side-profile photo' if side else '')}.
User-provided hair density: {density}.
Length preference: {length}.
Desired look: {vibe_choice}.
Daily styling effort: {maintenance_choice}.
Create exactly {count} distinct hairstyle candidates and select one winner.
The candidates should have different silhouettes (for example layered curtain flow, wolf cut, textured volume, side-swept layered volume, classic long layers, etc. only if suitable).
Avoid a generic default. The current hairstyle must not simply be copied.
Score each candidate 1-10 on: facial geometry (30%), forehead/cheek/jaw balance (20%), hair compatibility (20%), visible proportions (10%), style coherence (10%), maintenance (10%). Give weighted_total out of 100.
Return this exact JSON structure:
{{
 "face_analysis": {{
   "shape_estimate": "string",
   "observations": ["string", "string", "string"],
   "uncertainties": ["string"],
   "hair_observations": ["string", "string"]
 }},
 "candidates": [
   {{
    "name":"specific haircut name",
    "description":"what it looks like",
    "why_it_may_suit":"specific evidence-based reason",
    "watch_out":"main drawback",
    "scores": {{
      "facial_geometry": 1,
      "feature_balance": 1,
      "hair_compatibility": 1,
      "proportions": 1,
      "style_coherence": 1,
      "maintenance": 1
    }},
    "weighted_total": 0,
    "image_prompt":"Detailed image-edit prompt for this hairstyle only. Preserve the exact person and all non-hair details. Include hair silhouette, top length, sides, back, fringe/parting, texture and volume. Do not change hair color unless asked."
   }}
 ],
 "winner_name":"exact candidate name",
 "winner_reason":"why this candidate wins against the alternatives",
 "barber_instructions":["instruction 1","instruction 2","instruction 3"]
}}
Ensure scores are integers 1-10 and totals are consistent with the specified weights. Do not claim scores are scientifically objective.
"""}
    ]
    content.append({"type": "input_image", "image_url": image_data_url(front), "detail": "high"})
    if side:
        content.append({"type": "input_text", "text": "The next image is the same person's side profile. Use it only as a supporting geometry reference."})
        content.append({"type": "input_image", "image_url": image_data_url(side), "detail": "high"})
    response = client.responses.create(
        model=model,
        instructions=ANALYSIS_SYSTEM,
        input=[{"role": "user", "content": content}],
        max_output_tokens=5000,
    )
    return parse_json_response(response.output_text)

def generate_edit(client: OpenAI, source: Image.Image, prompt: str, model: str) -> bytes:
    buf = io.BytesIO()
    source.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "reference.png"
    result = client.images.edit(
        model=model,
        image=buf,
        prompt=(
            "Perform a precise photorealistic edit of the supplied reference photo. "
            "The same person must remain unmistakably identical. Change ONLY the hairstyle and necessary hair-edge details. "
            "Do not alter face shape, eyes, eyebrows, nose, lips, ears, moustache, beard, skin, expression, age, body, clothes, "
            "background, lighting, camera angle, or framing. Do not beautify or regenerate the face. "
            + prompt
        ),
        size="1024x1536",
    )
    return base64.b64decode(result.data[0].b64_json)

if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "previews" not in st.session_state:
    st.session_state.previews = {}

st.markdown("---")
analyze_clicked = st.button("✦ Analyze my face & design hairstyles", type="primary", use_container_width=True)

if analyze_clicked:
    if not uploaded:
        st.warning("Upload a front-facing photo first.")
    elif not api_key:
        st.error("Add an OpenAI API key in the sidebar or set OPENAI_API_KEY before running AI analysis.")
    else:
        try:
            client = OpenAI(api_key=api_key)
            front_img = Image.open(uploaded).convert("RGB")
            side_img = Image.open(side_uploaded).convert("RGB") if side_uploaded else None
            with st.spinner("Analyzing facial proportions and comparing distinct hairstyle designs…"):
                result = run_analysis(
                    client, front_img, side_img, hair_density, length_preference,
                    vibe, maintenance, variants, analysis_model
                )
            st.session_state.analysis = result
            st.session_state.previews = {}
            st.success("Analysis complete. Review the candidates below.")
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.caption("Check your API key, model access, internet connection, and current API billing.")

analysis = st.session_state.analysis
if analysis:
    st.markdown("---")
    st.markdown("## Your personalized analysis")
    face = analysis.get("face_analysis", {})
    a, b = st.columns([1, 1])
    with a:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Facial geometry")
        st.markdown(f"**Estimated shape:** {face.get('shape_estimate', 'Not determined')}")
        for item in face.get("observations", []):
            st.write("• " + item)
        st.markdown("### Hair observations")
        for item in face.get("hair_observations", []):
            st.write("• " + item)
        st.markdown("</div>", unsafe_allow_html=True)
    with b:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Important uncertainties")
        uncertainties = face.get("uncertainties", [])
        if uncertainties:
            for item in uncertainties:
                st.write("• " + item)
        else:
            st.write("The model did not flag major uncertainties.")
        st.markdown("### Final recommendation")
        st.markdown(f"**{analysis.get('winner_name', 'Selected style')}**")
        st.write(analysis.get("winner_reason", ""))
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("## Compare your hairstyle options")
    st.caption("Scores are AI-assisted estimates, not scientific measurements. Generated previews may vary slightly from the source photo.")
    candidates = analysis.get("candidates", [])
    cols = st.columns(min(3, len(candidates)) or 1)
    for idx, candidate in enumerate(candidates):
        with cols[idx % len(cols)]:
            is_winner = candidate.get("name") == analysis.get("winner_name")
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            if is_winner:
                st.markdown("⭐ **AI RECOMMENDED WINNER**")
            st.markdown(f"### {candidate.get('name', 'Hairstyle')}")
            st.write(candidate.get("description", ""))
            st.metric("Suitability score", f"{candidate.get('weighted_total', 0)}/100")
            st.write("**Why it may suit you:** " + candidate.get("why_it_may_suit", ""))
            st.write("**Trade-off:** " + candidate.get("watch_out", ""))
            if st.button("Generate this look", key=f"generate_{idx}", use_container_width=True):
                if not api_key:
                    st.error("Add an API key in the sidebar.")
                else:
                    try:
                        client = OpenAI(api_key=api_key)
                        original = Image.open(uploaded).convert("RGB")
                        with st.spinner(f"Creating {candidate.get('name', 'hairstyle')} preview…"):
                            image_bytes = generate_edit(
                                client, original, candidate.get("image_prompt", candidate.get("description", "")), image_model
                            )
                        st.session_state.previews[candidate.get("name", str(idx))] = image_bytes
                        st.rerun()
                    except Exception as e:
                        st.error(f"Image edit failed: {e}")
            preview = st.session_state.previews.get(candidate.get("name", str(idx)))
            if preview:
                st.image(preview, caption=candidate.get("name", "Hairstyle preview"), use_container_width=True)
                st.download_button(
                    "Download preview",
                    data=preview,
                    file_name=f"hairmuse_{idx+1}.png",
                    mime="image/png",
                    key=f"download_{idx}",
                    use_container_width=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## Take this to your barber")
    for instruction in analysis.get("barber_instructions", []):
        st.write("✂️ " + instruction)

st.markdown("---")
st.markdown(
    '<p class="small-muted">Privacy tip: use a photo you have permission to upload. Images are sent to the configured AI provider for analysis/editing when you use those features. This starter app does not save uploaded photos to its own database.</p>',
    unsafe_allow_html=True
)
