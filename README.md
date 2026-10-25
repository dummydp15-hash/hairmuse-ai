# HairMuse AI — Hairstyle Recommendation App

A beginner-friendly Streamlit app that:
- Accepts a front photo and optional side-profile photo.
- Asks a vision model to analyze visible facial proportions and hair.
- Compares multiple distinct hairstyle candidates and recommends one.
- Generates hairstyle previews by editing the uploaded reference photo.
- Provides barber instructions and downloadable preview images.

## 1. Install Python
Use Python 3.10 or newer.

## 2. Install dependencies
Open a terminal in this folder and run:

```bash
pip install -r requirements.txt
```

## 3. Add your API key
Option A: Create a `.env` file based on `.env.example`, then export the key in your terminal.
This starter app reads environment variables; it does not automatically load `.env`.

Windows PowerShell:
```powershell
$env:OPENAI_API_KEY="your_api_key_here"
streamlit run app.py
```

macOS/Linux:
```bash
export OPENAI_API_KEY="your_api_key_here"
streamlit run app.py
```

Alternatively, enter your API key in the app's sidebar. Do not put real API keys into public source code or GitHub.

## 4. Start the app
```bash
streamlit run app.py
```
The browser will open the app locally.

## 5. Deploy online
A straightforward option is Streamlit Community Cloud:
1. Put `app.py`, `requirements.txt`, and `README.md` in a private or public GitHub repository.
2. Create a Streamlit app and select `app.py` as the entry point.
3. Add `OPENAI_API_KEY` under the deployment's Secrets settings.
4. Deploy.

Do not commit your API key. For a public app, use authentication, rate limits, usage caps, and abuse protection before sharing widely.

## Configuration
The app defaults to:
- Vision model: `gpt-4.1`
- Image edit model: `gpt-image-1`

You can change model names in the sidebar or through environment variables:
- `OPENAI_VISION_MODEL`
- `OPENAI_IMAGE_MODEL`

Model availability, API access, image dimensions, and prices may vary by account and provider. If a model is unavailable to your account, choose one supported by your API project.

## Important limitations
- Face-shape estimates from photos are approximate; camera angle and lens distortion affect them.
- Candidate scores are AI estimates, not validated scientific measurements.
- Image generation can subtly alter identity despite strict instructions. Always inspect previews.
- This is a starter project, not a production-grade medical or biometric system.
- Uploaded photos are sent to the configured AI provider when analysis/editing is requested. This app does not intentionally save them to its own database.
