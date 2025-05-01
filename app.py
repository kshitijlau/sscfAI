import streamlit as st
import pandas as pd
import openai
from io import BytesIO
import time
from datetime import timedelta

# Streamlit config
st.set_page_config(page_title="German Translator", layout="wide")
st.title("🇩🇪 AI-Powered English to German Translator for Psychometric Simulations")

# Azure OpenAI credentials via Streamlit secrets
openai.api_type = "azure"
openai.api_key = st.secrets["AZURE_OPENAI_API_KEY"]
openai.api_base = st.secrets["AZURE_OPENAI_ENDPOINT"]
openai.api_version = "2024-08-01-preview"

DEPLOYMENT_NAME = st.secrets["AZURE_DEPLOYMENT_NAME"]

# Upload JSON file
uploaded_file = st.file_uploader("Upload a JSON file with English strings", type=["json"])

if uploaded_file:
    try:
        data = pd.read_json(uploaded_file, typ='series')
    except Exception as e:
        st.error(f"Failed to read JSON file: {e}")
        st.stop()

    st.subheader("📄 Preview of English Strings")
    st.dataframe(data.head(10))

    if st.button("⚙️ Translate to German"):
        total_tasks = len(data)
        progress_bar = st.progress(0)
        status_text = st.empty()
        start_time = time.time()

        translated = {}

        for i, (key, value) in enumerate(data.items()):
            prompt = f"""
You are a native-level German translator and psychometric content expert. Your task is to translate immersive simulation and assessment content from English to German while preserving **psychometric meaning**, **functional usability**, and **instructional clarity**.

The source includes:
- Behavioral simulation narratives and dialogues
- Role-based instructions and stakeholder briefings
- UI buttons, menus, tooltips, and alerts
- Dynamic instructions with embedded placeholders
- Economic, environmental, and demographic data

---

🔐 ABSOLUTE RULES

1. ✅ DO NOT TRANSLATE NAMES  
   - Do not alter personal names or organizational entities. These must remain untouched:  
     `Ayaan`, `Zara`, `Liam`, `Mei`, `Carlos`, `Amira`, `Noah`, `Priya`, `Elena`, `Tariq`  
     `Lighthouse`, `Mercer Talent Enterprise`, `Sienna`, `River Faro`, `Control Room`, `Crowdsource Reporting App`

2. ✅ DO NOT TRANSLATE PLACEHOLDERS OR VARIABLES  
   - Leave all placeholders and code tokens unchanged:  
     `{{user_name}}`, `{{count}}`, `{{duration}}`, `<tag>`, `[value]`, `%score%`  
   - Example:  
     - “Duration: {{duration}}” → “Dauer: {{duration}}” ✅  
     - Not “Dauer: [Dauer]” ❌

3. ✅ RETAIN FORMAT & STRUCTURE  
   - Preserve bullet points, HTML tags (e.g., `<b>`, `<i>`), line breaks, bolding, and punctuation  
   - Translate line-by-line where applicable; DO NOT merge or split sentences unless absolutely necessary

---

🧩 CATEGORY-SPECIFIC INSTRUCTIONS

1. **Terminology Precision**  
   Translate these terms precisely and never interchange them:

   | English Term          | German Equivalent       | Notes                                    |
   |-----------------------|--------------------------|------------------------------------------|
   | Task                  | Aufgabe                  | One-step action                          |
   | Quest                 | Mission                  | Multi-step or narrative section          |
   | Trial Activity        | Testaktivität / Proberunde | Practice section of simulation         |
   | Control Room          | Kontrollraum             | System dashboard                         |
   | Alert                 | Benachrichtigung         | Never use “Warnung” unless critical      |
   | Essential / Important / Non-essential | Unverzichtbar / Wichtig / Weniger wichtig | Preserve tone of urgency |
   | Submit (button)       | Absenden                 | UI button                                |
   | Play (media)          | Abspielen                | Use only if it refers to media action    |
   | Collapse              | Einklappen               | UI toggle                                |
   | Expand                | Ausklappen / Details     | Depends on context                       |

2. **Content Type Awareness**  
   - **UI Labels**: Use short, direct commands  
     - “Continue” → “Weiter”  
     - “Back” → “Zurück”  
   - **Instructions**: Formal, clear  
     - “Rank the team members from 1 to {{count}}” → “Ordne die Teammitglieder von 1 bis {{count}} ein”  
   - **Narratives**: Use neutral, professional tone  
     - “Emma oversees the development...” → “Emma leitet die Entwicklung...”  

3. **Contextual Accuracy in Simulation**  
   - Distinguish between technical vs emotional content:
     - Technical (e.g., “Environmental Impact”, “GDP Growth Rate”) → translate formally
     - Behavioral (e.g., “Team of first responders assessing contamination”) → translate expressively but professionally

4. **Preserve Economic & Demographic Contexts**  
   - Terms like “€1,000 per metric ton” → “1.000 € pro Tonne”  
   - Use German conventions for decimals (comma = decimal, dot = thousand separator)  
   - Translate only the **units**, not the values or numbers unless instructed

---

📌 EXAMPLES

**Correct:**
- “City of Sienna in chaos after the chemical leak in River Faro”  
  → “Die Stadt Sienna ist nach dem Chemieunfall im Fluss Faro im Chaos”

- “Select up to 3 digital tools”  
  → “Wähle bis zu 3 digitale Tools aus”

- “VP, Disaster Mitigation Unit”  
  → “VP, Abteilung für Katastrophenminderung”  
  *(Keep 'VP' if organizational styling prefers it)*

- “The local government oversees urban planning and infrastructure...”  
  → “Die lokale Regierung überwacht die Stadtplanung und Infrastruktur...”

---

✅ FINAL CHECK BEFORE SUBMISSION:
- [ ] All names and brands are untouched  
- [ ] Placeholders (`{{...}}`) are preserved  
- [ ] All UI buttons are in command form  
- [ ] Terminology is translated per glossary  
- [ ] Structural formatting is intact (bullets, bold, spacing)  
- [ ] Decimals, currency, and units follow German conventions  
- [ ] Sentences are fluent, formal, and match the content type  

---

💬 Return only the final German translation.  
Do not return the original English, any notes, or explanations.
"{value}"
"""
            try:
                response = openai.chat.completions.create(
                    model=DEPLOYMENT_NAME,
                    messages=[
                        {"role": "system", "content": "You are a professional German translator for psychometric simulations and assessment content."},
                        {"role": "user", "content": prompt.strip()}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                translated[key] = response.choices[0].message.content.strip()
            except Exception as e:
                translated[key] = f"[ERROR] {e}"

            elapsed = time.time() - start_time
            rate = elapsed / (i + 1)
            remaining = total_tasks - (i + 1)
            eta = timedelta(seconds=int(rate * remaining))
            progress_bar.progress((i + 1) / total_tasks)
            status_text.text(f"Translated {i + 1}/{total_tasks} | ETA: {eta}")

        st.success("✅ Translation completed!")

        # Show preview
        st.dataframe(pd.Series(translated).head(10))

        # Download
        buffer = BytesIO()
        pd.Series(translated).to_json(buffer, force_ascii=False, indent=2)
        buffer.seek(0)

        st.download_button(
            label="📥 Download Translated JSON",
            data=buffer,
            file_name="translated_de.json",
            mime="application/json"
        )
