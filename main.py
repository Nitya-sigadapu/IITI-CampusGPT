import os
import json
import re
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from vectorize_documents import load_and_vectorize_pdf

def remove_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

working_dir = os.path.dirname(os.path.realpath(__file__))
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    try:
        config_path = os.path.join(working_dir, "config.json")
        with open(config_path, "r") as f:
            config_data = json.load(f)
            GROQ_API_KEY = config_data.get("GROQ_API_KEY")
            if GROQ_API_KEY:
                os.environ["GROQ_API_KEY"] = GROQ_API_KEY
    except FileNotFoundError:
        print("Warning: config.json not found and GROQ_API_KEY not set in environment.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    message: str
    chat_history: list = []

DEFAULT_SYSTEM_PROMPT = """You are a **specialized AI assistant** for **IIT Indore**. Your responses must be **accurate, concise, and strictly based on the provided context (which contains data from the user's uploaded PDFs and IIT Indore's knowledge base)**.

Your goals:
1. Provide **clear, concise, helpful answers** directly addressing the user's query using the provided context.
2. If the user asks about a PDF they uploaded, assume the 'Context' contains the contents of that PDF.
3. Suggest **relevant IIT Indore services** only when appropriate and helpful.
4. Maintain a **warm, professional, and empathetic tone**, occasionally using 1-2 relevant emojis.

---
### **CONTEXT & RESPONSE RULES**
1. The 'Context' section below contains the text from the documents/PDFs the user has uploaded. If the user asks to summarize or extract information from their PDF, use the Context to do so directly.
2. If the provided context contains relevant information, build your answer entirely on it.
3. If the context does not contain the answer, politely inform the user that you don't have that information in the provided documents.
4. Always use bullet points for readability when listing items or summarizing.
5. Do NOT ask unnecessary follow-up questions like "Are you a prospective student?" unless you absolutely need that information to answer their specific question.
"""

DEFAULT_NEGATIVE_PROMPT = """
- Do **NOT** provide any information that is **not supported by verified IIT Indore data** or the provided system context.
- Do **NOT** imply you are an **employee, representative, agent, or official spokesperson** of IIT Indore.
- Do **NOT** fabricate or invent IIT Indore **services, features, pricing, policies, internal processes, or proprietary details**.
- Do **NOT** offer **legal, financial, medical, or other unrelated professional advice** outside IIT Indore's domain.
- Do **NOT** respond to topics **outside IIT Indore's scope**; instead, politely state that the relevant data is not available.
- Do **NOT** guess or assume **confidential, internal, or sensitive business information** about IIT Indore.
- Do **NOT** generate speculative, generic, or hypothetical business advice that is **not grounded in IIT Indore's verified information**.
- Do **NOT** use, cite, or reference **external sources, external knowledge, or outside databases** beyond the authorized IIT Indore context.
- Do **NOT** insert personal opinions, assumptions, unfounded claims, or subjective judgments.
- Do **NOT** mislead the user with unsupported or speculative responses.
- Do **NOT** use an unprofessional, casual, or overly familiar tone; maintain professionalism at all times.
"""

def contains_sensitive_topics(question):
    sensitive_keywords = []
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in sensitive_keywords)

def setup_vectorstore():
    persist_directory = f"{working_dir}/vector_db_dir"
    embeddings = FastEmbedEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=persist_directory,
                         embedding_function=embeddings)
    return vectorstore

def chat_chain(vectorstore, system_prompt=DEFAULT_SYSTEM_PROMPT, negative_prompt=DEFAULT_NEGATIVE_PROMPT):
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0
    )
    
    prompt_template = f"""{system_prompt}

{negative_prompt}

Context (from database):
{{context}}

Chat History:
{{chat_history}}

Question: {{question}}

Answer:"""
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "chat_history", "question"]
    )
    
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 3}
    )
    memory = ConversationBufferMemory(
        llm = llm,
        output_key = "answer",
        memory_key = "chat_history",
        return_messages = True
    )
    
    chain = ConversationalRetrievalChain.from_llm(
        llm = llm,
        retriever = retriever,
        chain_type = "stuff",
        memory = memory,
        verbose = True,
        return_source_documents = True,
        combine_docs_chain_kwargs={"prompt": prompt}
    )
    return chain

# Initialize globally to avoid recreating on each request
vectorstore = setup_vectorstore()
conversational_chain = chat_chain(vectorstore)

@app.post("/chat")
async def chatbot(request: MessageRequest):
    message = request.message

    if contains_sensitive_topics(message):
        return {"response": "It seems you may be asking questions outside my context, please ask questions related to IIT Indore only."}
    
    try:
        response = conversational_chain({"question": message})["answer"]
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload official documents in PDF format only.")
        
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File is too large. Please upload a PDF smaller than 10MB.")
    
    os.makedirs(f"{working_dir}/data", exist_ok=True)
    file_path = f"{working_dir}/data/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(content)
    
    try:
        load_and_vectorize_pdf(file_path)
        
        global vectorstore, conversational_chain
        vectorstore = setup_vectorstore()
        conversational_chain = chat_chain(vectorstore)

        return {"message": f"Successfully uploaded and processed {file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
