# Echo for Investors

A ready-to-run Streamlit app for **illustrative synthetic focus groups** in financial services. Compare two pitches with 30 fictional US retail investors, review segment differences, read individual objections, and export the results. The bundled robo-advisor demo works without an OpenAI API key.

The personas are synthetic and loosely inspired by broad variation in age, income, wealth, and investment ownership reported in the Federal Reserve's [2022 Survey of Consumer Finances](https://www.federalreserve.gov/econres/scfindex.htm). They are **not** sampled or weighted to match the survey, and their answers are not real customer evidence or financial advice.

## Screenshots

Screenshots can be captured after deployment from the input form and the results dashboard. The app itself includes three sample scenarios and a complete pre-generated robo-advisor result.

## Files

- `app.py` — Streamlit inputs, controls, and results
- `personas.py` — profile loading and filtering
- `llm.py` — parallel OpenAI interviews, validation, retries, synthesis
- `analysis.py` — metrics, Plotly charts, Markdown export
- `data/personas.json` — 30 labeled synthetic profiles
- `data/demo_results.json` — 60 pre-generated responses plus summary
- `requirements.txt` — pinned runtime dependencies
- `.streamlit/secrets.toml.example` — secret format; never commit the real secret

## Run locally

Use Python 3.11 or 3.12:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Demo mode is on when no key is configured. Select **Robo-advisor fee change** and click **Run focus group**. The app shows the bundled result, filtered by the sidebar selections. Other sample inputs are available, but their live analysis requires a key.

For live runs, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, replace the example value with your key, and restart Streamlit. Alternatively enter a key in the sidebar for the current browser session. Turn off demo mode to run a custom scenario. A full 30-persona run makes 61 model calls; charges and runtime vary by model and prompt size. Failed requests show an error and do not replace the last successful result.

## GitHub and Streamlit Community Cloud

1. Create an empty GitHub repository named `echo-for-investors`. Do not add a README, license, or `.gitignore` in GitHub; these are already included.
2. In this folder, run:

   ```bash
   git init
   git add app.py personas.py llm.py analysis.py data requirements.txt .streamlit/secrets.toml.example .gitignore README.md
   git commit -m "Build Echo for Investors"
   git branch -M main
   git remote add origin https://github.com/shahanvik-tech/echo-for-investors.git
   git push -u origin main
   ```

   The `.gitignore` excludes `.streamlit/secrets.toml`; check `git status` before pushing to ensure no key is staged.
3. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub, choose **Create app**, then **Yup, I have an app**. Select the repo, `main` branch, and `app.py` as the entrypoint.
4. To enable live runs, open **Advanced settings** during deployment and paste `OPENAI_API_KEY = "your-real-key"` into **Secrets**. You can also add it later in the app's **Settings → Secrets**. Save, then rerun the app with demo mode off.
5. Deploy. Without a secret, the app still works in demo mode. When you push changes to the repo, Community Cloud updates the app.

Deployment and secrets steps follow the [official Streamlit deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [secrets guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## Interpretation

The winner is whichever version has higher mean purchase intent across selected synthetic personas. The model generates qualitative reactions and can be inconsistent. Use real user research, compliance review, and product economics before making financial product decisions.
