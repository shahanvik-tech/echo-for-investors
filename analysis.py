"""Aggregate interview results and build charts."""
import pandas as pd
import plotly.express as px


def frame(results):
    return pd.DataFrame(results["responses"])


def metrics(df):
    output = {}
    for version in ("A", "B"):
        part = df[df.version == version]
        output[version] = {"intent": float(part.purchase_intent.mean()) if len(part) else 0.0, "yes_pct": float(part.would_switch_or_sign_up.eq("yes").mean() * 100) if len(part) else 0.0}
    output["winner"] = "A" if output["A"]["intent"] > output["B"]["intent"] else "B" if output["B"]["intent"] > output["A"]["intent"] else "Tie"
    return output


def segment_chart(df, segment):
    grouped = df.groupby([segment, "version"], as_index=False).purchase_intent.mean()
    fig = px.bar(grouped, x=segment, y="purchase_intent", color="version", barmode="group", color_discrete_map={"A": "#245A81", "B": "#16A6A1"}, labels={"purchase_intent": "Average intent (1–10)", segment: segment.replace("_", " ").title()})
    fig.update_layout(yaxis_range=[0, 10], legend_title_text="Pitch", margin=dict(l=10, r=10, t=20, b=10))
    return fig


def sentiment_chart(df):
    counts = df.groupby(["version", "sentiment"]).size().reset_index(name="responses")
    fig = px.bar(counts, x="version", y="responses", color="sentiment", barmode="stack", category_orders={"sentiment": ["positive", "neutral", "negative"]}, color_discrete_map={"positive": "#16A6A1", "neutral": "#9BA7B3", "negative": "#D47760"}, labels={"version": "Pitch", "responses": "Responses"})
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10))
    return fig


def summary_markdown(summary, stats, scenario):
    lines = [f"# Echo for Investors — {scenario['company']}", "", f"Product type: {scenario['product_type']}", f"Winner by average intent: {stats['winner']}", f"A: {stats['A']['intent']:.1f}/10 intent; {stats['A']['yes_pct']:.0f}% yes", f"B: {stats['B']['intent']:.1f}/10 intent; {stats['B']['yes_pct']:.0f}% yes", "", "## Executive summary", summary.get("executive_summary", ""), "", "## Biggest objection", summary.get("biggest_objection", ""), "", "## Segment insights"]
    lines += [f"- {item}" for item in summary.get("segment_insights", [])]
    lines += ["", "## Concern themes"]
    lines += [f"- **{item.get('theme', 'Theme')}**: {item.get('explanation', '')}" for item in summary.get("concern_themes", [])]
    lines += ["", "## Recommendations"]
    lines += [f"{i}. {item}" for i, item in enumerate(summary.get("recommendations", []), 1)]
    lines += ["", "Synthetic personas; not real customer research or financial advice."]
    return "\n".join(lines)
