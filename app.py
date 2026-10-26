"""Echo for Investors: illustrative synthetic pitch testing."""
import json
from pathlib import Path
import streamlit as st
from analysis import frame, metrics, segment_chart, sentiment_chart, summary_markdown
from llm import run_focus_group
from personas import load_personas, filter_personas

st.set_page_config(page_title="Echo for Investors", page_icon="◉", layout="wide")
st.markdown("<style>.block-container{max-width:1250px;padding-top:2rem}h1,h2,h3{color:#15354d}div[data-testid='stMetric']{background:#f1f6f8;padding:1rem;border-radius:12px}</style>", unsafe_allow_html=True)

SCENARIOS = {
    "Robo-advisor fee change": {"company":"Harbor Bank Guided Investing","product_type":"robo-advisor","context":"The annual advisory fee drops from 0.35% to 0.25%, while a new $3 monthly account fee applies to every account. Investments retain market risk; the account fee is charged regardless of balance.","A":"Get professional investing for just 0.25% a year, down from 0.35%, plus a simple $3 monthly account fee. Build your future with automated portfolios and easy monitoring.","B":"Our advisory fee falls to 0.25% annually, and a $3 monthly account fee is added. At a $10,000 balance, that is about $61 per year in combined fees versus $35 before. Review the total cost for your balance before deciding."},
    "Crypto trading launch": {"company":"Northstar Brokerage","product_type":"crypto feature","context":"A brokerage app is adding crypto trading. Crypto is volatile and may not suit every investor. The company has not specified trading spreads in this hypothetical concept.","A":"Buy and sell crypto alongside your stocks in one sleek app. Explore a new asset class in seconds and take your portfolio further.","B":"Crypto trading is coming to Northstar. Start with educational risk information, set a personal spending limit, and review the full trading cost before each order. Crypto can lose substantial value."},
    "Overdraft protection plan": {"company":"Cedar Bank Checking","product_type":"fee change","context":"The bank removes per-incident overdraft fees and offers an optional $5 per month overdraft protection plan. Customers who do not opt in do not pay the plan fee; transactions may be declined under the standard account terms.","A":"Say goodbye to surprise overdraft fees. For just $5 a month, get the peace of mind of overdraft protection whenever you need it.","B":"Per-incident overdraft fees are ending. You can opt into a $5 monthly protection plan, or pay no plan fee and have transactions declined when funds are insufficient. See coverage limits and examples before choosing."},
}

@st.cache_data(show_spinner=False)
def cached_run(api_key, model, persona_ids, scenario_json, _progress_callback=None):
    selected = [p for p in load_personas() if p["id"] in persona_ids]
    return run_focus_group(api_key, model, selected, json.loads(scenario_json), progress_callback=_progress_callback)

def demo_results():
    return json.loads((Path(__file__).parent / "data" / "demo_results.json").read_text(encoding="utf-8"))

def secret_key():
    try:
        return st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        return ""

st.title("Echo for Investors")
st.write("Test two financial product pitches with 30 **synthetic, illustrative** retail investor personas. Explore who responds, what they question, and how to improve your message.")
all_personas = load_personas()
with st.sidebar:
    st.header("Research setup")
    typed_key = st.text_input("OpenAI API key", type="password", help="Used for this session only; a configured Streamlit secret is the fallback.")
    api_key = typed_key.strip() or secret_key()
    model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"], index=0)
    demo = st.toggle("Demo mode", value=not bool(api_key), help="Demo uses the pre-generated robo-advisor scenario.")
    st.caption("Live mode makes two model calls per selected persona, plus one synthesis call. API charges may apply.")
    ages = st.multiselect("Age band", ["18-29","30-44","45-59","60+"], default=["18-29","30-44","45-59","60+"])
    incomes = st.multiselect("Income band", ["low","middle","upper-middle","high"], default=["low","middle","upper-middle","high"])
    risks = st.multiselect("Risk tolerance", ["conservative","moderate","aggressive"], default=["conservative","moderate","aggressive"])
    selected_people = filter_personas(all_personas, ages, incomes, risks)
    st.info(f"{len(selected_people)} of 30 personas selected")

choice = st.selectbox("Load a sample scenario", ["Custom"] + list(SCENARIOS), index=1)
if choice != st.session_state.get("loaded_choice"):
    sample = SCENARIOS.get(choice, {"company":"","product_type":"brokerage feature","context":"","A":"","B":""})
    for key, value in sample.items():
        st.session_state[f"input_{key}"] = value
    st.session_state.loaded_choice = choice
with st.form("pitch_form"):
    left, right = st.columns(2)
    with left:
        company = st.text_input("Company or product name", key="input_company")
    with right:
        product_type = st.selectbox("Product type", ["brokerage feature","fee change","savings or deposit product","credit product","robo-advisor","crypto feature","other"], key="input_product_type")
    context = st.text_area("Product context and factual terms", key="input_context", height=110)
    a_col, b_col = st.columns(2)
    with a_col:
        pitch_a = st.text_area("Version A pitch", key="input_A", height=175)
    with b_col:
        pitch_b = st.text_area("Version B pitch", key="input_B", height=175)
    submitted = st.form_submit_button("Run focus group", type="primary")

if submitted:
    scenario = {"company":company.strip(),"product_type":product_type,"context":context.strip(),"A":pitch_a.strip(),"B":pitch_b.strip()}
    if not selected_people:
        st.error("Select at least one persona in the sidebar.")
    elif not all(scenario[key] for key in ("company","context","A","B")):
        st.error("Complete the company, context, and both pitches.")
    elif demo or not api_key:
        if not api_key and not demo:
            st.info("No API key found, so the pre-generated demo is shown.")
        if choice != "Robo-advisor fee change" or scenario != SCENARIOS["Robo-advisor fee change"]:
            st.info("Demo results use the pre-generated robo-advisor scenario shown below. Switch off demo mode with an API key to test your own input.")
        progress = st.progress(0, text="Loading demo results")
        source = demo_results()
        ids = {p["id"] for p in selected_people}
        source["responses"] = [r for r in source["responses"] if r["persona_id"] in ids]
        st.session_state.results = source
        st.session_state.result_scenario = SCENARIOS["Robo-advisor fee change"]
        progress.progress(1.0, text="Demo ready")
    else:
        progress = st.progress(0, text="Interviewing synthetic personas")
        try:
            result = cached_run(api_key, model, tuple(p["id"] for p in selected_people), json.dumps(scenario, sort_keys=True), _progress_callback=lambda fraction: progress.progress(fraction, text=f"Interviewing synthetic personas · {fraction:.0%}"))
            st.session_state.results = result
            st.session_state.result_scenario = scenario
            progress.progress(1.0, text="Analysis ready")
        except Exception as exc:
            st.error(f"Live run failed: {exc}. You can turn on demo mode to explore the app.")

if "results" in st.session_state:
    results = st.session_state.results
    scenario_used = st.session_state.result_scenario
    df = frame(results)
    stats = metrics(df)
    st.divider()
    st.header("Results")
    st.caption(f"Scenario: {scenario_used['company']} · {df.persona_id.nunique()} synthetic personas · {len(df)} responses")
    cols = st.columns(5)
    cols[0].metric("A: average intent", f"{stats['A']['intent']:.1f}/10")
    cols[1].metric("B: average intent", f"{stats['B']['intent']:.1f}/10")
    cols[2].metric("A: yes", f"{stats['A']['yes_pct']:.0f}%")
    cols[3].metric("B: yes", f"{stats['B']['yes_pct']:.0f}%")
    cols[4].metric("Winner by intent", stats["winner"])
    st.caption("The winner is based on average purchase intent; these synthetic responses are directional only.")
    st.subheader("Intent by segment")
    tabs = st.tabs(["Age band", "Income band", "Risk tolerance"])
    for tab, field in zip(tabs, ["age_band","income_band","risk_tolerance"]):
        with tab:
            st.plotly_chart(segment_chart(df, field), use_container_width=True)
    st.subheader("Sentiment")
    st.plotly_chart(sentiment_chart(df), use_container_width=True)
    summary = results["summary"]
    st.subheader("Executive summary")
    st.write(summary.get("executive_summary", ""))
    st.markdown(f"**Biggest objection:** {summary.get('biggest_objection', '')}")
    for insight in summary.get("segment_insights", []):
        st.markdown(f"- {insight}")
    st.subheader("Concern themes")
    for theme in summary.get("concern_themes", []):
        st.markdown(f"**{theme.get('theme','Theme')}** — {theme.get('explanation','')}")
    st.subheader("Recommendations")
    for i, item in enumerate(summary.get("recommendations", []), 1):
        st.markdown(f"{i}. {item}")
    st.subheader("Persona responses")
    versions = st.multiselect("Filter pitch", ["A","B"], default=["A","B"])
    sentiments = st.multiselect("Filter sentiment", ["positive","neutral","negative"], default=["positive","neutral","negative"])
    shown = df[df.version.isin(versions) & df.sentiment.isin(sentiments)]
    st.dataframe(shown, use_container_width=True, hide_index=True)
    st.download_button("Download responses CSV", df.to_csv(index=False).encode("utf-8"), "echo_responses.csv", "text/csv")
    st.download_button("Download summary Markdown", summary_markdown(summary, stats, scenario_used), "echo_summary.md", "text/markdown")
else:
    st.info("Choose a sample, then run the focus group. Demo mode works without an API key.")
st.divider()
st.caption("Synthetic personas, not real customer research. Outputs may be inaccurate and are not financial advice. The profiles are illustrative and are not a representative sample of US households.")
