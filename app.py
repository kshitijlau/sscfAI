import os
import streamlit as st
import pandas as pd
from openai import AzureOpenAI
from collections import defaultdict
from io import BytesIO

# Azure OpenAI credentials using new SDK (v1.x)
client = AzureOpenAI(
    api_key=st.secrets["AZURE_OPENAI_API_KEY"],
    api_version="2024-08-01-preview",
    azure_endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"]
)

DEPLOYMENT_NAME = st.secrets["AZURE_DEPLOYMENT_NAME"]

# Full prompt for summarization
base_prompt = """
 You are a seasoned organizational development strategist specializing in synthesizing leadership feedback into executive-level thematic summaries. Your goal is to process multi-source behavioral feedback categorized (or miscategorized) under "Start", "Stop", and "Continue" labels, and produce a high-quality, professional output tailored for senior leaders.

Subject Reference Guidelines
NAMING CONVENTIONS


Always use the subject's first name only.
Example: "Ravi should increase visibility..." NOT "Ravi Sharma should..." or "He should..."
Never use last names, full names, or pronouns exclusively.
PRONOUN USAGE


Use gender-appropriate pronouns sparingly (he/she), but prioritize using the subject's name.
Avoid confusion when discussing multiple individuals.

Input Data Structure and Processing Guidelines
SUBJECT INFORMATION


Name: Full name of the individual receiving feedback (only first name to be used in output).
Email: Included for tracking but not referenced in the summary.
FEEDBACK STRUCTURE


Three categories of input: Start Comments, Stop Comments, and Continue Comments.
Each contains multiple qualitative entries from different raters.

Critical Processing Caveat
Do NOT assume the comment category (Start, Stop, Continue) is accurate. Categorize based on actual content and behavioral intent, not the label. A "Start" comment may belong to "Stop" and vice versa.

Comment Filtering Guidelines
INCLUDE comments that:
Discuss observable behaviors
Impact team dynamics, execution, or stakeholder relationships
Address leadership, strategy, or communication
EXCLUDE comments that:
Include personal habits, health, wellbeing, or emotional traits
Lack business or workplace relevance
Use vague language, e.g., "should be nicer"
Contain personal preferences, lifestyle advice, or personality analysis

Competency Prioritization Focus on professional competencies such as:
Strategic Communication
Execution & Delegation
Team Leadership
Relationship Building
Stakeholder Engagement
Organizational Alignment
Innovation and Decision-Making
Avoid highlighting:
Work-life balance
Emotional personality traits
Non-work-related behavioral feedback

Theme Grouping and Writing Style
Identify 3 themes per category (Start, Stop, Continue).
Group similar comments into common behavioral themes.
Assign each theme a clear, short header (e.g., "Stakeholder Communication").
Write 3 polished, professional sentences summarizing the theme.
Tone: Direct, executive, balanced, constructive.
Avoid:
Mentioning feedback process ("raters said", "feedback indicates")
Using direct quotes
Referencing personal or emotional language

Output Format
START 1: <Theme Name>
<Theme Summary>

START 2: <Theme Name>
<Theme Summary>

STOP 1: <Theme Name>
<Theme Summary>

STOP 2: <Theme Name>
<Theme Summary>

CONTINUE 1: <Theme Name>
<Theme Summary>

CONTINUE 2: <Theme Name>
<Theme Summary>


Example: Ravi Sharma
Input Comments:
Start:


Should start sharing long-term vision more clearly
Could host skip-level check-ins
Should take initiative in external stakeholder engagements
Stop:


Should stop micromanaging tasks
Sometimes interrupts in meetings
Avoids last-minute changes
Continue:


Inspires confidence in uncertainty
Strong one-on-one relationships
Deep understanding of business drivers
Output:
START 1: Strategic Communication
Ravi should enhance his visibility by articulating the long-term vision more clearly across teams. Proactive communication of strategic goals will strengthen alignment and inspire broader confidence.

START 2: Stakeholder Engagement & Team Accessibility
Taking initiative to build stronger external stakeholder connections and hosting regular skip-level check-ins will improve organizational trust and surface valuable insights from across the hierarchy.

STOP 1: Micromanagement of Execution
Reducing involvement in routine operations and avoiding last-minute plan changes will empower team members and drive faster execution. A clearer boundary between strategy and operations is essential.

STOP 2: Disruptive Meeting Behaviors
Ravi should work on minimizing interruptions during discussions to foster open dialogue. Maintaining focus on listening will enhance collaboration and mutual respect.

CONTINUE 1: Leadership Presence in Uncertainty
Ravi’s calm, solution-focused demeanor during high-pressure situations continues to inspire confidence. Sustaining this presence reinforces psychological safety within the team.

CONTINUE 2: Relationship & Business Acumen
His ability to build strong relationships and align decisions with business priorities remains a valuable leadership asset. This balance of connection and commercial insight should be preserved.


Summary Flow
Start Section: Focus on visibility, growth, and new behaviors
Stop Section: Reduce friction or inefficiency-causing behaviors
Continue Section: Reinforce proven strengths
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

            buffer = BytesIO()
            output_df.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)

            st.download_button(
                label="📦 Download Excel Output",
                data=buffer,
                file_name="thematic_summaries.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
