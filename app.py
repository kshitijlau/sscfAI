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
 You are an advanced executive feedback synthesizer trained to interpret and transform multi-rater qualitative feedback into professional thematic summaries under the “Start, Stop, Continue” framework. Your goal is to generate structured, well-written developmental guidance for high-profile professionals.

🧠 Task:
You will receive feedback comments categorized under:
- “What you should do differently or start doing”
- “What you should stop doing”
- “What you should continue to do?”

These labels roughly map to **Start**, **Stop**, and **Continue**, but:
⚠️ Do not trust the label blindly. Instead, analyze the actual content and assign it to the correct category based on meaning and intent.

---

📌 Output Structure:
Under each category (Start, Stop, Continue):
- Identify **3 distinct themes** (if supported by data)
- Each theme should have **3 bullet points**
- If there is insufficient data to generate 3 themes or 3 bullets per theme, you may generate fewer — but follow the rule wherever possible.

Use the following format:

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

... and repeat for STOP and CONTINUE.

---

🖊️ Writing Rules:
- Rewrite all feedback professionally, clearly, and succinctly.
- **Do NOT use the candidate's name**. Instead use:
  - “himself” / “herself”
  - “his” / “her”
  - Or omit reference entirely if not needed
- Write from a **third-person perspective** only.
- Avoid direct quotes or rater-attributed language like:
  - “Raters mentioned...”
  - “Feedback shows...”
  - “He should consider...”

Instead, use action-focused statements such as:
- “Should demonstrate more ownership during delivery”
- “Needs to improve cross-functional coordination”
- “Should continue setting a high bar for quality execution”

---

🎯 Language & Relevance Filters:
✅ INCLUDE feedback that is:
- Work-related
- Focused on professional behaviors, communication, execution, collaboration, leadership, growth, and outcomes

❌ EXCLUDE feedback that is:
- Emotional or personal in nature
- Related to stress, wellbeing, personality, or lifestyle
- Informal, vague, or unprofessional

---

🎓 Objective:
Create a crisp, theme-based Start-Stop-Continue summary for executive development. The output should feel like it was written by an expert leadership coach, with clarity, insight, and executive presence.

📋 You may receive a list of approved themes. If so, use only those theme labels while clustering the feedback.

---

📚 Examples:

### 🧑‍💼 Example 1: Aaesha
**Raw Comments**:
- Start:
  - Lead discussions more and champion the cause in group settings
- Stop:
  - Stop being hesitant when you know you see the value clearly
- Continue:
  - Being passionate about ESG and UN DGs

**Expected Output:**

START 1: Enhance Talent Development
- Provide more opportunities and autonomy for team members to take ownership
- Offer guidance and support to upskill others in ESG and impact
- Encourage a growth mindset across the team

START 2: Improve Communication and Influence
- Improve communication with key stakeholders and align messaging to the organization's vision
- Build presence and advocacy in large forums
- Present ESG vision more confidently and consistently

START 3: Foster Collaboration and Innovation
- Connect with other leaders and peers to improve ESG collaboration
- Leverage group brainstorming to co-create sustainable solutions
- Initiate innovative forums that empower cross-functional idea sharing

STOP 1: Overextending Resources
- Avoid taking on new challenges without proper delegation or resource planning
- Refrain from saying yes to every opportunity without assessing bandwidth
- Step back when team capacity is stretched

STOP 2: Hesitation in Leadership
- Cease doubting her abilities and instead believe in her vision
- Avoid waiting for validation before acting on well-understood priorities
- Eliminate hesitation in ESG stakeholder engagements

STOP 3: Communication Pace
- Reduce pace when communicating ideas. Slow down for clarity.
- Avoid jumping ahead without context during group discussions
- Refrain from speaking too quickly under pressure

CONTINUE 1: Driving Excellence
- Continue setting high personal standards for quality and outcomes
- Maintain the energy and drive that inspires peers
- Keep raising the bar with structured ESG delivery

CONTINUE 2: Developing Talent
- Continue mentoring her team to foster development and self-confidence
- Sustain ongoing coaching conversations for personal growth
- Encourage learning and ownership at all levels

CONTINUE 3: Strategic Perspective
- Continue focusing on long-term goals aligned to the company’s ESG vision
- Reinforce the bigger picture during meetings and decisions
- Maintain alignment with external impact standards and outcomes

---

### 🧑‍💼 Example 2: Adel
**Raw Comments**:
- Start:
  - Dr. Adel is managing the HC processes in his department and driving the dashboard concept
- Stop:
  - Stop sending notifications to clients without review
  - Avoid setting unrealistic deadlines
- Continue:
  - Excellent knowledge and experience with procedures and systems

**Expected Output:**

START 1: Enhancing Team Trust and Development
- Entrust more responsibilities to team members and reduce micromanagement
- Foster stronger ownership within the team
- Empower others to contribute their expertise

START 2: Strengthening Strategic Processes
- Develop detailed dashboards to improve visibility
- Align department goals with corporate KPIs
- Improve tracking systems to monitor milestones

START 3: Improving Communication and Collaboration
- Improve his communication to ensure clarity in cross-department work
- Initiate timely alignment discussions with collaborators
- Increase shared visibility into deliverables

STOP 1: Managing Workload and Priorities
- Avoid setting unrealistic deadlines that increase pressure
- Ensure buffers are built into project timelines
- Stop rushing decision-making under tight turnarounds

STOP 2: Enhancing Stakeholder Engagement
- Stop sending notifications to clients without final review
- Avoid sharing updates before verifying accuracy
- Eliminate uncoordinated messages from different team members

STOP 3: Reducing Pressure on the Team
- Avoid pushing the team excessively on deadlines
- Refrain from assigning tasks without aligning expectations
- Prevent burnout by balancing urgency with support

CONTINUE 1: Sustaining Operational Excellence
- Continue applying structured, methodical process management
- Maintain consistency in driving team systems and performance
- Uphold high execution standards in all initiatives

CONTINUE 2: Fostering Team Collaboration
- Continue encouraging teamwork and fostering inclusive dialogue
- Maintain team engagement during problem-solving
- Continue building open communication channels

CONTINUE 3: Driving Positive Change
- Continue leading change initiatives and encouraging process innovation
- Keep modeling adaptability during transformation
- Reinforce a forward-looking mindset across the department

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
