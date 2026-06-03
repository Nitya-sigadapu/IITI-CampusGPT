# CampusGPT - IIT Indore RAG Chatbot

An enterprise-grade, highly robust **Retrieval-Augmented Generation (RAG) chatbot** designed exclusively for IIT Indore. This system uses advanced vector embeddings and large language models (LLMs) to provide strictly factual, context-aware answers to student and faculty queries, backed solely by official college documentation.

---

## 🌟 Key Features

- **Strict Factual Guardrails:** The chatbot is engineered to *refuse* subjective opinions, hallucinated facts, and out-of-scope questions (e.g., "Who won the IPL?"). It only answers based on the uploaded official documents.
- **Automated Relevance Filtering (Pre-indexing):** Uses an LLM check during document upload to instantly reject non-academic or irrelevant PDFs before they pollute the vector database.
- **Robust File Handling:** Enforces a strict 10MB file size limit and strict PDF-only checks on both the React frontend and FastAPI backend to prevent server crashes.
- **Enterprise-Grade Evaluation Suite:** Includes an automated LLM-as-a-Judge evaluation framework testing 30 advanced FAANG-level edge cases (Prompt Injection, Chunk Boundary Failures, Contradictory Information, Context Switching).
- **Modern React Frontend:** A sleek, responsive UI built with Vite and React, featuring a professional matte aesthetic tailored for IIT Indore.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | React (Vite), JavaScript, Vanilla CSS |
| **Backend** | FastAPI, Python |
| **LLM Inference** | Groq (`llama-3.3-70b-versatile`) |
| **Vector Database** | ChromaDB |
| **Embeddings** | HuggingFace (`all-MiniLM-L6-v2`) |
| **Document Processing** | PyPDF2, LangChain `RecursiveCharacterTextSplitter` |

---

## 🚀 Installation & Setup

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

## 🏃‍♂️ Running the Application

For development, you can start both the frontend and backend simultaneously using the provided batch script (Windows):

```bash
run.bat
```
*(This will start FastAPI on port 8000 and the React dev server on port 5173).*

---

## 🧪 Advanced Evaluation Framework

CampusGPT comes with a state-of-the-art testing suite designed to catch the edge cases that break 99% of tutorial-level RAG apps.

### 1. Run Text & Prompt Edge Cases
Tests context memory (pronoun resolution), jailbreak attempts, empty queries, multilingual queries, and more.
```bash
venv\Scripts\python.exe evaluate_rag.py
```
*Results are automatically saved to `evaluation_results.json`.*

### 2. Run Document State Edge Cases
Automatically generates conflicting PDFs, malicious prompt-injection PDFs, and chunk-breaking PDFs on the fly using `fpdf2` to test the system's architectural limits.
```bash
venv\Scripts\python.exe evaluate_document_state.py
```
*Results are automatically saved to `document_test_results.json`.*

---

## 🔒 Security & Privacy

- All document embeddings are stored **locally** in the `vector_db_dir/`.
- Uploaded PDFs are stored **locally** in the `data/` folder.
- Both folders, along with your `config.json`, are explicitly ignored in `.gitignore` to prevent data leaks.

---

## 🤝 Contributing

Contributions to improve response latency, expand OCR capabilities for scanned PDFs, and implement batch-uploading are welcome!

**License:** MIT
