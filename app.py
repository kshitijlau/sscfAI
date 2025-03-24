import streamlit as st
import pandas as pd
import openai
from collections import defaultdict

# Set your OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

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
"""

def generate_summary(name, starts, stops, continues):
    user_input = f"Person: {name}\nStart Comments: {starts}\nStop Comments: {stops}\nContinue Comments: {continues}"
    full_prompt = base_prompt + "\n\n" + user_input

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional leadership feedback analyst."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    return response.choices[0].message.content

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


