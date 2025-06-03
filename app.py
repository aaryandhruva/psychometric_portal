
import streamlit as st
import json
import yaml

# === Load Data ===
@st.cache_data
def load_question_bank():
    with open("question_bank.json", "r") as f:
        return json.load(f)

@st.cache_data
def load_rules():
    with open("career_rules.yaml", "r") as f:
        return yaml.safe_load(f)

# === Core Functions ===
def calculate_scores(question_bank, user_response):
    domain_scores = {}
    domain_counts = {}

    for q in question_bank:
        qid = q['id']
        if qid not in user_response:
            continue

        response = user_response[qid]
        for domain in q['domains']:
            dname = domain['name']
            weight = domain.get('weight', 1)
            domain_scores[dname] = domain_scores.get(dname, 0) + response * weight
            domain_counts[dname] = domain_counts.get(dname, 0) + (5 * weight)

    normalized_scores = {}
    for domain in domain_scores:
        raw = domain_scores[domain]
        max_score = domain_counts[domain]
        min_score = (max_score / 5)
        normalized = ((raw - min_score) / (max_score - min_score)) * 100
        normalized_scores[domain] = round(normalized, 2)

    return normalized_scores

def match_clusters(scores, rules):
    matches = []

    for cluster, conditions in rules.items():
        total = len(conditions)
        hits = 0

        for domain, threshold in conditions.items():
            if scores.get(domain, 0) >= threshold:
                hits += 1

        fit_score = (hits / total) * 100
        if fit_score > 0:
            matches.append((cluster, round(fit_score, 2)))

    matches.sort(key=lambda x: x[1], reverse=True)
    return matches

# === Streamlit UI ===
st.set_page_config(page_title="Psychometric Career Guidance", layout="centered")
st.title("🧠 Psychometric Assessment Portal")

question_bank = load_question_bank()
rules = load_rules()

st.markdown("### Please respond to the following items:")
user_response = {}

for q in question_bank[:]:  # Limit to 20 for demo
    qid = q['id']
    qtext = q['text']
    response = st.selectbox(
        f"{qid}: {qtext}",
        options=[1, 2, 3, 4, 5],
        format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x - 1],
        key=qid
    )
    user_response[qid] = response

if st.button("Submit Assessment"):
    scores = calculate_scores(question_bank, user_response)
    matches = match_clusters(scores, rules)

    st.subheader("Your Normalized Trait Scores")
    st.json(scores)

    st.subheader("Top Career Cluster Matches")
    for cluster, score in matches:
        st.markdown(f"**{cluster}** — {score}% match")

