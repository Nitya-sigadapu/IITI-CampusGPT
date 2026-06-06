import os
import json
import pytesseract
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage

import sys

if sys.platform.startswith('win'):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def check_relevance_with_llm(text):
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    os.environ["GROQ_API_KEY"] = config.get("GROQ_API_KEY", "")
        
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        sample = text[:4000]
        prompt = f"You are a document classifier. Determine if the following text is related to IIT Indore, an academic institution, university, college, campus life, educational curriculum, or academic administration. Reply with exactly the word 'YES' if it is related, or 'NO' if it is completely unrelated (e.g., a random story, unrelated manual, cookbook). \n\nText to analyze:\n{sample}"
        
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip().upper()
        
        if "NO" in content and "YES" not in content:
            return False
        return True
    except Exception as e:
        print(f"Relevance check failed: {e}")
        return True

def load_and_vectorize_pdf(file_path):
    print(f"Processing {file_path}...")
    
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
            
    if not text.strip():
        raise ValueError("Could not extract any readable text from this PDF. It may be a scanned document or an image.")
        
    if not check_relevance_with_llm(text):
        raise ValueError("The uploaded document does not appear to be related to IIT Indore or an academic context.")
    
    doc = Document(
        page_content=text,
        metadata={"source": os.path.basename(file_path)}
    )
    
    embeddings = FastEmbedEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=500,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    text_chunks = text_splitter.split_documents([doc])
        
    print(f"Split document into {len(text_chunks)} chunks")
    
    persist_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "vector_db_dir")
    os.makedirs(persist_dir, exist_ok=True)
    
    vectordb = Chroma.from_documents(
        documents=text_chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    
    print(f"Successfully vectorized and stored {os.path.basename(file_path)}")

def load_pdf_documents(directory):
    documents = []
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    
    for pdf_file in pdf_files:
        try:
            print(f"Processing {pdf_file}...")
            file_path = os.path.join(directory, pdf_file)
            
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            
            if not text.strip():
                print(f"Skipping {pdf_file}: No readable text found.")
                continue
                
            if not check_relevance_with_llm(text):
                print(f"Skipping {pdf_file}: Not related to IIT Indore or academic context.")
                continue

            doc = Document(
                page_content=text,
                metadata={"source": pdf_file}
            )
            documents.append(doc)
            print(f"Successfully processed {pdf_file}")
            
        except Exception as e:
            print(f"Error processing {pdf_file}: {str(e)}")
            continue
    
    return documents

def main():
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Created 'data' directory. Please add your PDF files here.")
        return

    if not os.path.exists("vector_db_dir"):
        os.makedirs("vector_db_dir")
        print("Created 'vector_db_dir' directory for storing vectorized documents.")

    try:
        print("Loading embedding model...")
        embeddings = FastEmbedEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        print("Loading and processing PDF documents...")
        documents = load_pdf_documents("data")
        
        if not documents:
            print("No documents were successfully processed. Please check your PDF files.")
            return
            
        print(f"Successfully loaded {len(documents)} documents")

        print("Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=500,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        text_chunks = text_splitter.split_documents(documents)
        print(f"Split documents into {len(text_chunks)} chunks")

        print("Creating vector database...")
        vectordb = Chroma.from_documents(
            documents=text_chunks,
            embedding=embeddings,
            persist_directory="vector_db_dir"
        )
        
        print("Successfully vectorized and stored documents in 'vector_db_dir'")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
