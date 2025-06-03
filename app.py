import streamlit as st
import yaml
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Psychometric Assessment Portal", layout="wide")

st.title("🧠 Psychometric Assessment Portal")
st.markdown("Please answer the following questions honestly.")

# Load question bank
@st.cache_data
def load_question_bank():
    with open("question_bank.json", "r") as f:
        return json.load(f)

question_bank = load_question_bank()

# Load career rules
def load_career_rules():
    with open("career_rules.yaml", "r") as f:
        return yaml.safe_load(f)

career_rules = load_career_rules()

# Connect to Google Sheets
def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open("PsychometricResponses").worksheet("Responses")

# Collect user input
st.subheader("Questions")
user_response = {}
for q in question_bank:
    user_response[q["id"]] = st.selectbox(
        q["text"],
        options=["1 - Strongly Disagree", "2 - Disagree", "3 - Neutral", "4 - Agree", "5 - Strongly Agree"],
        index=2,
        key=q["id"]
    )

# Submit button
if st.button("Submit"):
    # Convert response to numeric scale
    numeric_responses = {qid: int(ans[0]) for qid, ans in user_response.items()}

    # Calculate scores per domain
    domain_scores = {}
    for q in question_bank:
        qid = q["id"]
        score = numeric_responses[qid] * q.get("weight", 1)
        for domain in q["domains"]:
            name = domain["name"]
            weight = domain.get("weight", 1)
            domain_scores[name] = domain_scores.get(name, 0) + score * weight

    # Normalize scores (optional)
    max_score_per_domain = 5 * sum(
        q.get("weight", 1) * d.get("weight", 1)
        for q in question_bank
        for d in q["domains"] if d["name"] == q["domains"][0]["name"]
    )
    normalized_scores = {k: round(v / max_score_per_domain * 100, 2) for k, v in domain_scores.items()}

    # Match career clusters
    matched_clusters = []
    for cluster, rule in career_rules.items():
        min_score = rule.get("min_score", 0)
        domains = rule.get("domains", [])
        avg = sum([normalized_scores.get(d, 0) for d in domains]) / len(domains)
        if avg >= min_score:
            matched_clusters.append((cluster, avg))

    matched_clusters.sort(key=lambda x: x[1], reverse=True)

    # Show results
    st.subheader("Your Scores")
    st.json(normalized_scores)

    st.subheader("Recommended Career Clusters")
    if matched_clusters:
        for cluster, score in matched_clusters:
            st.markdown(f"**{cluster}**: {score:.2f}% match")
    else:
        st.warning("No matching career cluster found. Try retaking with different answers.")

    # Log to Google Sheets
    try:
        sheet = connect_to_sheet()
        row = [datetime.now().isoformat()] + [numeric_responses[q["id"]] for q in question_bank]
        sheet.append_row(row)
        st.success("Response logged to Google Sheets successfully!")
    except Exception as e:
        st.error(f"Logging failed: {e}")
