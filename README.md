# CampusGPT – IIT Indore RAG Chatbot

**Live Demo:** [CampusGPT](https://campus-gpt-wajl.vercel.app)

An enterprise-grade, highly robust Retrieval-Augmented Generation (RAG) chatbot designed exclusively for IIT Indore. The system enables students and faculty to query institutional documents using natural language and receive strictly factual, context-aware responses backed solely by official college documentation, rather than general internet knowledge.

The application combines semantic search, vector embeddings, and Large Language Models (LLMs) to provide accurate answers from academic handbooks, hostel policies, placement reports, admission brochures, and other official institute documents.
---

## Features

### Document-Based Question Answering

* Upload PDF documents and query them using natural language.
* Responses are generated using retrieved document context rather than pretrained model knowledge.
* Supports multi-turn conversational interactions.

### Semantic Search Pipeline

* PDF text extraction and preprocessing.
* Recursive text chunking using LangChain.
* Vector embedding generation using HuggingFace embeddings.
* Semantic retrieval using ChromaDB.

### Guardrails & Validation

* Strict citation-based responses referencing specific uploaded documents.
* PDF-only file validation.
* File size restrictions to prevent resource abuse.
* Out-of-scope query detection.
* Reduced hallucinations through retrieval-constrained generation.

### Modern Web Interface

* Responsive React frontend built with Vite.
* Real-time conversational chat interface.
* Drag-and-drop PDF upload support.
* Clean and intuitive user experience.



## Tech Stack

### Frontend

* React
* Vite
* JavaScript
* CSS

### Backend

* FastAPI
* Python

### AI & Retrieval

* LangChain
* ChromaDB
* HuggingFace Embeddings (all-MiniLM-L6-v2)
* Groq API (Llama 3.3 70B)

### Document Processing

* PyPDF2
* RecursiveCharacterTextSplitter

---

## Installation

### Clone Repository

```bash
git clone https://github.com/Nitya-sigadapu/CampusGPT.git
cd CampusGPT
```

### Backend Setup

```bash
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

Create a `config.json` file:

```json
{
  "GROQ_API_KEY": "your_groq_api_key"
}
```

### Frontend Setup

```bash
cd frontend
npm install
```

---

## Running the Application

### Backend

```bash
python main.py
```

### Frontend

```bash
npm run dev
```

Or use:

```bash
run.bat
```

to start both services simultaneously.

---

## Security & Privacy

* Uploaded documents are stored locally.
* Vector embeddings remain within the local vector database.
* API keys are excluded through `.gitignore`.
* File validation is performed on both frontend and backend.

---

## Future Improvements

* PostgreSQL + pgvector integration
* OCR support for scanned PDFs
* Role-Based Access Control (RBAC)
* Conversation analytics dashboard
* Batch document ingestion
* Cloud vector database support

---

## License

This project is licensed under the MIT License.
