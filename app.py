import streamlit as st
import pandas as pd
import openai
from collections import defaultdict

# Set your OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]  # Store it safely in Streamlit secrets

# Prompt Template
base_prompt = """
You are a seasoned organizational development strategist, skilled in synthesizing multi-source behavioral feedback into clear, theme-based insights tailored for senior leaders. Your task is to analyze multiple "Start, Stop, Continue" comments received about an individual and transform them into a professionally-written thematic summary that highlights key behavior patterns.

⚠️ Important:
Do NOT assume the comment category (Start, Stop, Continue) is accurate. Categorize based on actual content and behavioral intent, not the label.

Output Format:
START 1: <Theme Name>
<Summary>

START 2: <Theme Name>
<Summary>

STOP 1: <Theme Name>
<Summary>

STOP 2: <Theme Name>
<Summary>

CONTINUE 1: <Theme Name>
<Summary>

CONTINUE 2: <Theme Name>
<Summary>
"""

def generate_summary(name, starts, stops, continues):
    user_input = f"Person: {name}\nStart Comments: {starts}\nStop Comments: {stops}\nContinue Comments: {continues}"
    full_prompt = base_prompt + "\n\n" + user_input

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional leadership feedback analyst."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message["content"]

# Streamlit App
st.set_page_config(page_title="Start-Stop-Continue Theme Generator", layout="wide")
st.title("📄 Start-Stop-Continue Feedback Theming Tool")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Validate expected columns
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

        if st.button("\u2699\ufe0f Generate Summaries"):
            output_data = []
            progress = st.progress(0)
            total = len(grouped_data)

            for i, (name, comments) in enumerate(grouped_data.items()):
                summary = generate_summary(name, comments["Start"], comments["Stop"], comments["Continue"])
                output_data.append({"Name": name, "Summary": summary})
                progress.progress((i + 1) / total)

            # Create output DataFrame
            output_df = pd.DataFrame(output_data)
            st.success("\ud83c\udf89 Thematic summaries generated!")
            st.dataframe(output_df)

            # Download button
            st.download_button(
                label="\ud83d\udce6 Download Excel Output",
                data=output_df.to_excel(index=False, engine="openpyxl"),
                file_name="thematic_summaries.xlsx"
            )
