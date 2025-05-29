import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import time

# 1️⃣ Configure – DON'T assign the return value
genai.configure(api_key=st.secrets["api_keys"]["gemini_key"])

# 2️⃣ Create a model object once and reuse it
MODEL = genai.GenerativeModel("gemini-2.0-flash")

SYSTEM_PROMPT_PDF = """You are a helpful assistant…
(keep your prompt text)
"""
SYSTEM_PROMPT_NO_PDF = "just answer what is being asked okay ."

st.title("📄 Ask-your-PDF (Gemini edition)")

pdf_file = st.file_uploader("Upload a PDF (≤ 15 pages, text-based)", type="pdf")

# --- Load PDF --------------------------------------------------------------
pdf_text = ""
if pdf_file:
    reader = PdfReader(pdf_file)
    pdf_text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    st.session_state["pdf_text"] = pdf_text[:80_000]
    st.success(f"Loaded {len(reader.pages)} pages.")
else:
    st.info("No PDF uploaded. Ask questions based on general knowledge.")

question = st.text_input("Ask your question:")

# --- Answer ---------------------------------------------------------------
if question:
    with st.spinner("Thinking…"):
        if pdf_file:
            prompt_pdf = (
                f"{SYSTEM_PROMPT_PDF}\n<PDF>\n{st.session_state['pdf_text']}\n</PDF>\n\n"
                f"User: {question}"
            )
            response = MODEL.generate_content(prompt_pdf)
            answer = response.text.strip()

            # If your PDF-prompt template tells Gemini to return NOT_IN_PDF
            # when it can’t find an answer, handle that here:
            if "NOT_IN_PDF" in answer:
                prompt_general = f"{SYSTEM_PROMPT_NO_PDF}\nUser: {question}"
                answer = MODEL.generate_content(prompt_general).text.strip()
                answer = answer.replace("NOT_IN_PDF", "").strip()
        else:
            prompt_general = f"{SYSTEM_PROMPT_NO_PDF}\nUser: {question}"
            answer = MODEL.generate_content(prompt_general).text.strip()

    # --- Typewriter effect -------------------------------------------------
    placeholder = st.empty()
    shown = ""
    for ch in answer:
        shown += ch
        placeholder.markdown(shown + "▌")
        time.sleep(0.003)
    placeholder.markdown(shown)
