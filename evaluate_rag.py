import os
import json
import requests
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage

# Ensure API Key is loaded
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
            os.environ["GROQ_API_KEY"] = config.get("GROQ_API_KEY", "")

# The FastAPI endpoint where the RAG chatbot is running
CHATBOT_URL = "http://localhost:8000/chat"

# --- TEST DATASET ---
# Load from JSON file
test_cases_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_cases.json")
try:
    with open(test_cases_path, "r", encoding="utf-8") as f:
        TEST_CASES = json.load(f)
except Exception as e:
    print(f"Error loading test cases from {test_cases_path}: {e}")
    TEST_CASES = []

def get_chatbot_answer(question, chat_history=None):
    """Hits the local FastAPI backend to get the RAG generated answer."""
    if chat_history is None:
        chat_history = []
    try:
        response = requests.post(CHATBOT_URL, json={"message": question, "chat_history": chat_history})
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"Error calling chatbot API for question '{question}': {e}")
        return "ERROR"

def evaluate_answer(question, expected_answer, generated_answer):
    """Uses Groq LLM as a judge to evaluate the accuracy of the generated answer."""
    if generated_answer == "ERROR":
        return 0, "Failed to get an answer from the chatbot."
        
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    prompt = f"""You are an impartial evaluator assessing the accuracy of an AI chatbot.
    
Question Asked: {question}

Expected Correct Answer/Facts: {expected_answer}

Chatbot's Generated Answer: {generated_answer}

Task:
Evaluate how well the Chatbot's Generated Answer aligns with the Expected Correct Answer. 
Did it capture the necessary facts? Did it hallucinate?

Provide your evaluation in the following strict format:
SCORE: <A number from 0 to 10, where 10 is perfectly accurate and complete, and 0 is completely wrong or refused to answer when it shouldn't have>
REASON: <A brief 1-2 sentence explanation for your score>
"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        
        # Parse score and reason
        score_line = [line for line in content.split('\n') if 'SCORE:' in line]
        reason_line = [line for line in content.split('\n') if 'REASON:' in line]
        
        score = 0
        if score_line:
            try:
                score_str = score_line[0].split('SCORE:')[1].strip()
                score = float(score_str)
            except ValueError:
                score = 0
                
        reason = reason_line[0].split('REASON:')[1].strip() if reason_line else "No reason provided."
        
        return score, reason
    except Exception as e:
        print(f"Error during LLM evaluation: {e}")
        return 0, "Evaluation failed due to LLM error."

def main():
    print("Starting Automated RAG Evaluation...")
    print(f"Total Test Cases: {len(TEST_CASES)}\n")
    
    total_score = 0
    results = []
    
    for i, test_case in enumerate(TEST_CASES, 1):
        question = test_case["question"]
        expected = test_case["expected_answer"]
        chat_history = test_case.get("chat_history", [])
        
        print(f"Test {i}: {question}")
        print("-> Fetching answer from chatbot...")
        generated = get_chatbot_answer(question, chat_history)
        
        print("-> Evaluating response...")
        score, reason = evaluate_answer(question, expected, generated)
        
        total_score += score
        
        results.append({
            "question": question,
            "generated": generated,
            "score": score,
            "reason": reason
        })
        
        print(f"-> Score: {score}/10")
        print(f"-> Reason: {reason}\n")
        print("-" * 50 + "\n")
        
    avg_score = total_score / len(TEST_CASES) if TEST_CASES else 0
    print("=== FINAL RESULTS ===")
    print(f"Average Accuracy Score: {avg_score:.2f} / 10.0")
    
    with open("evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "average_score": avg_score,
            "results": results
        }, f, indent=2)
    print("Detailed results saved to evaluation_results.json")

if __name__ == "__main__":
    main()
