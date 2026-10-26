"""OpenAI persona interviews and synthesis."""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

SENTIMENTS = {"positive", "neutral", "negative"}
DECISIONS = {"yes", "maybe", "no"}


def validate_response(value):
    if not isinstance(value, dict):
        raise ValueError("Response must be a JSON object")
    required = {"purchase_intent", "sentiment", "would_switch_or_sign_up", "top_reason", "top_concern", "what_would_change_my_mind", "quote"}
    if not required.issubset(value):
        raise ValueError("Missing response fields")
    if type(value["purchase_intent"]) is not int or not 1 <= value["purchase_intent"] <= 10:
        raise ValueError("purchase_intent must be an integer 1-10")
    if value["sentiment"] not in SENTIMENTS or value["would_switch_or_sign_up"] not in DECISIONS:
        raise ValueError("Invalid sentiment or decision")
    if any(not isinstance(value[key], str) or not value[key].strip() for key in required - {"purchase_intent"}):
        raise ValueError("Text fields must be nonempty strings")
    return {key: value[key] for key in required}


def _json_call(client, model, messages):
    response = client.chat.completions.create(model=model, messages=messages, response_format={"type": "json_object"}, temperature=0.3, timeout=45)
    return json.loads(response.choices[0].message.content)


def interview_one(client, model, persona, version, scenario):
    system = ("You are a synthetic research respondent. Answer in character as the supplied persona, honestly and skeptically. "
              "Use their finances, goals, and pain points. Do not claim to be a real customer. Return only a JSON object with: "
              "purchase_intent (integer 1-10), sentiment (positive/neutral/negative), would_switch_or_sign_up (yes/maybe/no), "
              "top_reason, top_concern, what_would_change_my_mind, quote (1-2 sentences in the persona's voice).")
    prompt = json.dumps({"persona": persona, "company": scenario["company"], "product_type": scenario["product_type"], "context": scenario["context"], "pitch_version": version, "pitch": scenario[version]}, ensure_ascii=False)
    error = None
    for attempt in range(3):
        try:
            value = _json_call(client, model, [{"role": "system", "content": system}, {"role": "user", "content": prompt}])
            return validate_response(value)
        except Exception as exc:
            error = exc
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"Persona {persona['id']} version {version}: {error}")


def summarize(client, model, rows):
    prompt = {"task": "Cluster all top_concern values into 3-5 themes. Write a concise executive summary that names the overall winner, segment preferences, biggest objection, and exactly 3 concrete pitch recommendations. Ground claims in the provided responses. Return JSON only with keys executive_summary (string), winner (A, B, or Tie), biggest_objection (string), segment_insights (list of strings), recommendations (list of exactly 3 strings), concern_themes (list of 3-5 objects with theme and explanation).", "responses": rows}
    messages = [{"role": "system", "content": "You are a careful research analyst. These are synthetic responses, not representative survey data. Return only a JSON object."}, {"role": "user", "content": json.dumps(prompt)}]
    error = None
    for attempt in range(3):
        try:
            result = _json_call(client, model, messages)
            if not isinstance(result, dict) or not isinstance(result.get("executive_summary"), str) or not isinstance(result.get("concern_themes"), list) or not 3 <= len(result["concern_themes"]) <= 5 or not isinstance(result.get("recommendations"), list) or len(result["recommendations"]) != 3:
                raise ValueError("Invalid summary JSON")
            return result
        except Exception as exc:
            error = exc
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Summary failed after 3 attempts: {error}")


def run_focus_group(api_key, model, personas, scenario, progress_callback=None):
    client = OpenAI(api_key=api_key)
    rows = []
    futures = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for persona in personas:
            for version in ("A", "B"):
                future = pool.submit(interview_one, client, model, persona, version, scenario)
                futures[future] = (persona, version)
        for count, future in enumerate(as_completed(futures), 1):
            persona, version = futures[future]
            response = future.result()
            rows.append({"persona_id": persona["id"], "persona_name": persona["name"], "age_band": persona["age_band"], "income_band": persona["income_band"], "risk_tolerance": persona["risk_tolerance"], "version": version, **response})
            if progress_callback:
                progress_callback(count / len(futures))
    rows.sort(key=lambda r: (r["persona_id"], r["version"]))
    summary = summarize(client, model, rows)
    return {"responses": rows, "summary": summary}
