import os
import streamlit as st
import pandas as pd
from openai import AzureOpenAI
from collections import defaultdict

# Azure OpenAI credentials using new SDK (v1.x)
client = AzureOpenAI(
    api_key=st.secrets["AZURE_OPENAI_API_KEY"],
    api_version="2024-08-01-preview",
    azure_endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"]
)

DEPLOYMENT_NAME = st.secrets["AZURE_DEPLOYMENT_NAME"]

# Full prompt for summarization
base_prompt = """
You are a seasoned organizational development strategist, skilled in synthesizing multi-source behavioral feedback into clear, theme-based insights tailored for senior leaders. Your task is to analyze multiple "Start, Stop, Continue" comments received about an individual and transform them into a professionally-written thematic summary that highlights key behavior patterns.

Generate a structured and polished thematic summary using the Start–Stop–Continue framework. Identify up to 3 unique themes under each category and rewrite the comments into concise, professional language that reflects a strategic tone, appropriate for high-profile leadership.

Each theme should be given a short, professional heading followed by up to 3 bullet points. If there is insufficient data, leave blanks.

⚠️ Important:
Do NOT assume the comment category (Start, Stop, Continue) is accurate. Categorize based on actual content.

📋 Output Format:
START 1: <Theme Name>
- Bullet
- Bullet
- Bullet

START 2: <Theme Name>
- Bullet
- Bullet
- Bullet

START 3: <Theme Name>
- Bullet
- Bullet
- Bullet

STOP 1: <Theme Name>
- Bullet
- Bullet
- Bullet

STOP 2: <Theme Name>
- Bullet
- Bullet
- Bullet

STOP 3: <Theme Name>
- Bullet
- Bullet
- Bullet

CONTINUE 1: <Theme Name>
- Bullet
- Bullet
- Bullet

CONTINUE 2: <Theme Name>
- Bullet
- Bullet
- Bullet

CONTINUE 3: <Theme Name>
- Bullet
- Bullet
- Bullet

🖋️ Use professional tone. No quote formatting or references to "raters said".
"""

# Generate summary for each person
def generate_summary(name, starts, stops, continues):
    user_input = f"Person: {name}\nStart Comments: {starts}\nStop Comments: {stops}\nContinue Comments: {continues}"
    full_prompt = base_prompt + "\n\n" + user_input

    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "You are a professional leadership feedback analyst."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    return response.choices[0].message.content

# Streamlit UI
st.set_page_config(page_title="Feedback Theming Tool", layout="wide")
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
