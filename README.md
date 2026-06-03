# CampusGPT - IIT Indore RAG Chatbot

An enterprise-grade, highly robust Retrieval-Augmented Generation (RAG) chatbot designed exclusively for IIT Indore. This system uses advanced vector embeddings and large language models (LLMs) to provide strictly factual, context-aware answers to student and faculty queries, backed solely by official college documentation.

---

## Key Features

- **Strict Factual Guardrails:** The chatbot is engineered to refuse subjective opinions, hallucinated facts, and out-of-scope questions (e.g., "Who won the IPL?"). It only answers based on the uploaded official documents.
- **Automated Relevance Filtering (Pre-indexing):** Uses an LLM check during document upload to instantly reject non-academic or irrelevant PDFs before they pollute the vector database.
- **Robust File Handling:** Enforces a strict 10MB file size limit and strict PDF-only checks on both the React frontend and FastAPI backend to prevent server crashes.
- **Modern React Frontend:** A sleek, responsive UI built with Vite and React, featuring a professional matte aesthetic tailored for IIT Indore.
- **Emoji Support:** The backend and frontend fully support UTF-8 encoding, allowing students to use emojis in their queries seamlessly.

---

## Evaluation & Accuracy Framework

CampusGPT comes with a state-of-the-art testing suite designed to catch the edge cases that break standard RAG applications. The system consistently scores highly (9.0+/10) on factual accuracy tests evaluated by an automated LLM Judge.

### 1. Prompt & Context Edge Cases
The framework tests 30 advanced FAANG-level scenarios, including:
- **Pronoun Resolution:** Retaining context across multi-turn conversations.
- **Jailbreak Attempts:** Refusing malicious prompt overrides.
- **Synonyms & Case Sensitivity:** Handling varied inputs correctly.
- **Multilingual Support:** Successfully parsing and retrieving context from non-English queries (e.g., Hindi).

To run these tests:
```bash
venv\Scripts\python.exe evaluate_rag.py
```
Results are automatically saved to `evaluation_results.json`.

### 2. Document State Edge Cases
The automated testing script generates PDFs on the fly using `fpdf2` to test the system's architectural limits:
- **Prompt Injection PDFs:** Verifies the system ignores malicious instructions hidden inside uploaded PDFs.
- **Contradictory Information:** Evaluates how the bot handles uploading two rulebooks with conflicting facts.
- **Chunk Boundary Failures:** Tests the text-splitter's ability to retain context across large whitespace gaps.
- **Table Extraction:** Ensures tabular data is not mangled during the vectorization process.

To run these tests:
```bash
venv\Scripts\python.exe evaluate_document_state.py
```
Results are automatically saved to `document_test_results.json`.

---

## Tech Stack

- **Frontend:** React (Vite), JavaScript, Vanilla CSS
- **Backend:** FastAPI, Python
- **LLM Inference:** Groq (`llama-3.3-70b-versatile`)
- **Vector Database:** ChromaDB
- **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`)
- **Document Processing:** PyPDF2, LangChain `RecursiveCharacterTextSplitter`

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Nitya-sigadapu/CampusGPT.git
cd CampusGPT
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Create a `config.json` file in the root directory for your API keys:
```json
{
  "GROQ_API_KEY": "gsk_your_groq_api_key_here"
}
```

### 3. Frontend Setup
Open a new terminal window:
```bash
cd frontend
npm install
```

---

## Running the Application

For development, you can start both the frontend and backend simultaneously using the provided batch script (Windows):

```bash
run.bat
```
(This will start FastAPI on port 8000 and the React dev server on port 5173).

---

## Security & Privacy

- All document embeddings are stored locally in the `vector_db_dir/`.
- Uploaded PDFs are stored locally in the `data/` folder.
- Both folders, along with your `config.json`, are explicitly ignored in `.gitignore` to prevent data leaks.

---

## Contributing

Contributions to improve response latency, expand OCR capabilities for scanned PDFs, and implement batch-uploading are welcome.

**License:** MIT
