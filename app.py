import streamlit as st
import json
import yaml
import os
from datetime import datetime

# Load data
@st.cache_data
def load_question_bank():
    with open("question_bank.json", "r") as f:
        return json.load(f)

@st.cache_data
def load_rules():
    with open("career_rules.yaml", "r") as f:
        return yaml.safe_load(f)

from scoring import calculate_scores
from mapping import match_clusters

question_bank = load_question_bank()
rules = load_rules()

st.title("🧠 Psychometric Assessment")

st.markdown("### Please answer all questions:")

user_response = {}

for q in question_bank:
    qid = q["id"]
    qtext = q["text"]
    rtype = q["responseType"]

    if rtype == "likert-5":
        response = st.selectbox(
            f"{qid}: {qtext}",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x - 1],
            key=qid
        )
        user_response[qid] = response

    elif rtype == "mcq":
        response = st.text_input(f"{qid} (MCQ): {qtext}", key=qid)
        user_response[qid] = response  # You can convert these to 1/0 if needed

# Button
if st.button("Submit"):
    # Save user input to file
    response_record = {
        "timestamp": datetime.now().isoformat(),
        "responses": user_response
    }

    if os.path.exists("user_responses.json"):
        with open("user_responses.json", "r") as f:
            existing = json.load(f)
    else:
        existing = []

    existing.append(response_record)

    with open("user_responses.json", "w") as f:
        json.dump(existing, f, indent=2)

    # Score + Match
    scores = calculate_scores(question_bank, user_response)
    matches = match_clusters(scores, rules)

    # Output
    st.subheader("Normalized Scores:")
    st.json(scores)

    st.subheader("Career Cluster Matches:")
    for cluster, score in matches:
        st.markdown(f"**{cluster}** → {score}%")
