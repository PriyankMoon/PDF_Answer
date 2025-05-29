import streamlit as st
from PyPDF2 import PdfReader
from google.generativeai import genai
import time
api_key = st.secrets["api_keys"]["gemini_key"]
# Initialize client with your API key
client = genai.Client(api_key)

SYSTEM_PROMPT_PDF = """
You are a helpful assistant.
Answer from the text provided between the <PDF> tags.
If the answer is not present in the PDF, use your own knowledge.
You are an expert computer science professor. Provide detailed explanations with examples. Always elaborate concepts clearly.
and don't mention that gemini is answering .
"""

SYSTEM_PROMPT_NO_PDF = """
just answer what is being asked okay .
"""

st.title("📄 Ask-your-PDF (Gemini edition)")

pdf_file = st.file_uploader("Upload a PDF (≤ 15 pages, text-based)", type="pdf")

pdf_text = ""
if pdf_file:
    reader = PdfReader(pdf_file)
    pdf_text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    st.success(f"Loaded {len(reader.pages)} pages.")
    st.session_state["pdf_text"] = pdf_text[:80_000]  # truncate if >80k chars
else:
    st.info("No PDF uploaded. Ask questions based on general knowledge.")

question = st.text_input("Ask your question:")

if question:
    with st.spinner("Streamlit is thinking…"):
        if pdf_file:
            # First try to answer from PDF content
            prompt_pdf = f"{SYSTEM_PROMPT_PDF}\n<PDF>\n{st.session_state['pdf_text']}\n</PDF>\n\nUser: {question}"

            response_pdf = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[{"text": prompt_pdf}]
            )
            answer_pdf = response_pdf.text.strip()

            if "NOT_IN_PDF" in answer_pdf:
                # If not found in PDF, fallback to general knowledge
                prompt_general = f"{SYSTEM_PROMPT_NO_PDF}\nUser: {question}"
                response_general = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[{"text": prompt_general}]
                )
                final_answer = response_general.text.strip()
            else:
                final_answer = answer_pdf.replace("NOT_IN_PDF", "").strip()

        else:
            # No PDF uploaded, answer from general knowledge directly
            prompt_general = f"{SYSTEM_PROMPT_NO_PDF}\nUser: {question}"
            response_general = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[{"text": prompt_general}]
            )
            final_answer = response_general.text.strip()

    st.markdown("**Answer:**")

    # Streaming simulation
    placeholder = st.empty()
    displayed_text = ""
    for char in final_answer:
        displayed_text += char
        placeholder.markdown(displayed_text + "▌")  # typing cursor effect
        time.sleep(0.003)  # adjust speed for readability

    placeholder.markdown(displayed_text)  # final output without cursor
