import streamlit as st

st.write("🔐 Secrets Loaded:")
st.write("AZURE_OPENAI_KEY in secrets:", "AZURE_OPENAI_API_KEY" in st.secrets)
st.write("AZURE_OPENAI_ENDPOINT in secrets:", "AZURE_OPENAI_ENDPOINT" in st.secrets)
st.write("AZURE_DEPLOYMENT_NAME in secrets:", "AZURE_DEPLOYMENT_NAME" in st.secrets)


import pandas as pd
import openai
from collections import defaultdict

# Azure OpenAI setup
openai.api_type = "azure"
openai.api_key = st.secrets["AZURE_OPENAI_KEY"]
openai.api_base = st.secrets["AZURE_OPENAI_ENDPOINT"]
openai.api_version = "2024-08-01-preview"

# Full enriched base prompt with updated instructions for 3 themes and 3 bullet points per theme
base_prompt = """
You are a seasoned organizational development strategist, skilled in synthesizing multi-source behavioral feedback into clear, theme-based insights tailored for senior leaders. Your task is to analyze multiple "Start, Stop, Continue" comments received about an individual and transform them into a professionally-written thematic summary that highlights key behavior patterns.

Generate a structured and polished thematic summary using the Start–Stop–Continue framework. Identify up to 3 unique themes under each category and rewrite the comments into concise, professional language that reflects a strategic tone, appropriate for high-profile leadership.

Each theme should be given a short, professional heading (e.g., "Strategic Communication") followed by up to 3 bullet points that summarize feedback related to that theme. If there is insufficient data to generate 3 themes or 3 bullet points per theme, leave the missing themes or bullets blank.

⚠️ Important:
Do NOT assume the comment category (Start, Stop, Continue) is accurate. Some comments may be miscategorized by raters. Instead, analyze the actual content of the comment to determine its correct category. Assign each comment to the correct category based on intent and behavioral context, not the label.

📋 Output Format:
START 1: <Theme Name>
- Bullet 1
- Bullet 2
- Bullet 3

START 2: <Theme Name>
- Bullet 1
- Bullet 2
- Bullet 3

START 3: <Theme Name>
- Bullet 1
- Bullet 2
- Bullet 3

STOP 1: <Theme Name>
- Bullet 1
- Bullet 2
- Bullet 3

STOP 2: <Theme Name>
- Bullet 1
- Bullet 2
- Bullet 3

STOP 3: <Theme Name>
- Bullet 1
- Bullet 2
- Bullet 3

CONTINUE 1: <Theme Name>
- Bullet 1
- Bullet 2
- Bullet 3

CONTINUE 2: <Theme Name>
- Bullet 1
- Bullet 2
- Bullet 3

CONTINUE 3: <Theme Name>
- Bullet 1
- Bullet 2
- Bullet 3

🧠 Comment Filtering Guidelines:
INCLUDE comments that:
- Focus on professional behaviors with strategic or organizational impact
- Mention observable actions, leadership styles, communication, execution, or decision-making

EXCLUDE comments that:
- Are emotional, vague, or personal
- Reference wellbeing, personality traits, lifestyle, or stress
- Use unprofessional, irrelevant, or informal language

✍️ Language Rules:
- Rewrite feedback into professional, elegant, action-oriented language
- Use third-person perspective
- Avoid attribution language ("Raters said…", "Feedback shows…")
- Avoid direct quotes
- Use concise, high-impact bullet points

📌 Example:
Person: Ravi Sharma

Start Comments:
- Should start sharing long-term vision more clearly with the team
- Needs to be more vocal about strategic goals in cross-team meetings
- Should take initiative in external stakeholder engagements
- Could start hosting regular skip-level check-ins

Stop Comments:
- Should stop micromanaging tasks
- Needs to stop stepping into day-to-day operational decisions
- Sometimes interrupts in meetings; should stop doing that
- Should avoid last-minute changes to plans

Continue Comments:
- Great at inspiring confidence in the team during uncertain times
- Builds strong one-on-one relationships
- Always calm and solution-oriented in challenging situations
- Has a deep understanding of business drivers and priorities

Expected Output:
START 1: Strategic Communication
- Clarify long-term vision across teams
- Reinforce strategic messaging in cross-functional meetings
- Establish consistent communication cadence

START 2: Stakeholder Engagement
- Build stronger connections with external stakeholders
- Proactively represent the team in external forums
- Seek feedback to align interests

START 3: Team Visibility
- Host regular skip-level check-ins
- Improve upward and downward visibility
- Encourage open dialogue across levels

STOP 1: Micromanagement of Execution
- Avoid over-involvement in day-to-day tasks
- Trust team ownership and decision-making
- Step back from tactical control

STOP 2: Meeting Disruptions
- Refrain from interrupting others
- Allow space for open discussion
- Listen actively before responding

STOP 3: Last-Minute Changes
- Reduce unplanned adjustments to plans
- Provide early clarity on priorities
- Avoid reactive decision shifts

CONTINUE 1: Calm Leadership Presence
- Remain composed during uncertainty
- Instill confidence in the team
- Provide steady leadership

CONTINUE 2: Strong Relationships
- Maintain strong one-on-one connections
- Continue personalized team engagement
- Foster a culture of approachability

CONTINUE 3: Business Acumen
- Align decisions with business priorities
- Keep focus on strategic outcomes
- Demonstrate commercial awareness
"""

def generate_summary(name, starts, stops, continues):
    user_input = f"Person: {name}\nStart Comments: {starts}\nStop Comments: {stops}\nContinue Comments: {continues}"
    full_prompt = base_prompt + "\n\n" + user_input

    response = openai.ChatCompletion.create(
        engine=st.secrets["AZURE_DEPLOYMENT_NAME"],
        messages=[
            {"role": "system", "content": "You are a professional leadership feedback analyst."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    return response.choices[0].message["content"]

st.set_page_config(page_title="Start-Stop-Continue Feedback Theming Tool", layout="wide")
st.title("📄 Start-Stop-Continue Feedback Theming Tool")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    expected_columns = {"Name", "Comment Type", "Comment"}
    if not expected_columns.issubset(set(df.columns)):
        st.error("Excel must contain columns: Name, Comment Type, Comment")
    else:
        grouped_data = defaultdict(lambda: {"Start": [], "Stop": [], "Continue": []})

        for _, row in df.iterrows():
            name = row["Name"]
            ctype = row["Comment Type"].strip().capitalize()
            comment = row["Comment"]
            grouped_data[name][ctype].append(comment)

        if st.button("⚙️ Generate Summaries"):
            output_data = []
            progress = st.progress(0)
            total = len(grouped_data)

            for i, (name, comments) in enumerate(grouped_data.items()):
                summary = generate_summary(name, comments["Start"], comments["Stop"], comments["Continue"])
                output_data.append({"Name": name, "Summary": summary})
                progress.progress((i + 1) / total)

            output_df = pd.DataFrame(output_data)
            st.success("🎉 Thematic summaries generated!")
            st.dataframe(output_df)

            st.download_button(
                label="📦 Download Excel Output",
                data=output_df.to_excel(index=False, engine="openpyxl"),
                file_name="thematic_summaries.xlsx"
            )
