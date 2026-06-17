# Reload trigger
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

@app.get("/")
async def root():
    return {"status": "ok", "message": "CampusGPT API is running"}

class MessageRequest(BaseModel):
    message: str
    chat_history: list = []

DEFAULT_SYSTEM_PROMPT = """You are a **specialized AI assistant** for **IIT Indore**. Your responses must be **accurate, concise, and helpful**.

Your goals:
1. Provide **clear, concise, helpful answers** directly addressing the user's query.
2. If the 'Context' contains relevant information (e.g., from uploaded PDFs), prioritize using it to formulate your answer.
3. If the user asks general questions about IIT Indore that are not in the context, you may use your internal knowledge about IIT Indore to answer them.
4. Suggest **relevant IIT Indore services** only when appropriate and helpful.
5. Maintain a **warm, professional, and empathetic tone**, occasionally using 1-2 relevant emojis.

---
### **CONTEXT & CONFLICT RESOLUTION RULES**
1. The 'Context' section below contains text from uploaded documents, along with their 'Source' filenames.
2. **CONFLICT RESOLUTION:** If multiple sources provide contradictory information, you **MUST prioritize the information from user-uploaded PDFs** over the default `IIT_Indore_Handbook.pdf` or any default rules. 
3. **CITATIONS ARE MANDATORY:** If you use information from the Context to answer the question, you **MUST** include inline citations using the exact source filename and page number (e.g., "Based on [Source: rules.pdf, Page: 5]...").
4. If you use your internal knowledge instead of the Context, do not include any citations.
5. Always use bullet points for readability when listing items or summarizing.
6. Do NOT ask unnecessary follow-up questions unless absolutely needed.
"""

DEFAULT_NEGATIVE_PROMPT = """
- Do **NOT** provide any information that is **not supported by verified IIT Indore data** or your internal knowledge of IIT Indore.
- Do **NOT** imply you are an **employee, representative, agent, or official spokesperson** of IIT Indore.
- Do **NOT** fabricate or invent IIT Indore **services, features, pricing, policies, internal processes, or proprietary details**.
- Do **NOT** offer **legal, financial, medical, or other unrelated professional advice** outside IIT Indore's domain.
- Do **NOT** respond to topics **completely outside IIT Indore's scope**; instead, politely state that you are specialized in IIT Indore and can only assist with related topics.
- Do **NOT** guess or assume **confidential, internal, or sensitive business information** about IIT Indore.
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
    
    # Check if DB exists and has outdated metadata
    if os.path.exists(persist_directory) and os.listdir(persist_directory):
        try:
            temp_vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
            sample = temp_vectorstore.get(limit=1)
            if sample and sample.get("metadatas") and len(sample["metadatas"]) > 0:
                meta = sample["metadatas"][0]
                if meta and "page" not in meta:
                    print("Outdated vector database detected (missing 'page' metadata). Rebuilding...")
                    import shutil
                    shutil.rmtree(persist_directory)
        except Exception as e:
            print(f"Error checking vector db: {e}")

    # Check if vector DB is missing or empty, and initialize from default_data and data if so
    if not os.path.exists(persist_directory) or not os.listdir(persist_directory):
        print("Vector DB is empty or outdated. Initializing with PDFs...")
        dirs_to_load = [os.path.join(working_dir, "default_data"), os.path.join(working_dir, "data")]
        for target_dir in dirs_to_load:
            if os.path.exists(target_dir):
                for filename in os.listdir(target_dir):
                    if filename.lower().endswith(".pdf"):
                        try:
                            file_path = os.path.join(target_dir, filename)
                            print(f"Loading document: {filename}")
                            from vectorize_documents import load_and_vectorize_pdf
                            load_and_vectorize_pdf(file_path)
                        except Exception as e:
                            print(f"Failed to process document {filename}: {e}")

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
    
    doc_prompt = PromptTemplate(
        template="Source: {source}, Page: {page}\nContent: {page_content}",
        input_variables=["page_content", "source", "page"]
    )
    
    chain = ConversationalRetrievalChain.from_llm(
        llm = llm,
        retriever = retriever,
        chain_type = "stuff",
        memory = memory,
        verbose = True,
        return_source_documents = True,
        combine_docs_chain_kwargs={
            "prompt": prompt,
            "document_prompt": doc_prompt
        }
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
        result = conversational_chain({"question": message})
        response = result["answer"]
        
        # Extract unique source document names and pages
        source_docs = result.get("source_documents", [])
        
        # Group pages by source
        source_pages = {}
        for doc in source_docs:
            meta = doc.metadata or {}
            src = meta.get("source")
            page = meta.get("page")
            if src:
                if src not in source_pages:
                    source_pages[src] = set()
                if page:
                    source_pages[src].add(str(page))
        
        # Append references if sources were retrieved and cited
        if source_pages and "[Source:" in response:
            response += "\n\n**References:**\n"
            for source, pages in source_pages.items():
                if pages:
                    pages_str = ", ".join(sorted(list(pages)))
                    response += f"- {source} (Pages: {pages_str})\n"
                else:
                    response += f"- {source}\n"
                
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

@app.get("/documents")
async def get_documents():
    documents = set()
    data_dir = f"{working_dir}/data"
    default_dir = f"{working_dir}/default_data"
    
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.lower().endswith(".pdf"):
                documents.add(f)
                
    if os.path.exists(default_dir):
        for f in os.listdir(default_dir):
            if f.lower().endswith(".pdf"):
                documents.add(f)
                
    return {"documents": sorted(list(documents))}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
