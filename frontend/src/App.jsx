import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, UploadCloud, Loader2, User, Info, BookOpen, Building, Briefcase, Trash2, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './index.css';

const API_URL = import.meta.env.DEV ? 'http://localhost:8000' : 'https://campusgpt-tqd6.onrender.com';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_URL}/documents`);
      setUploadedDocs(response.data.documents || []);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e, customMessage = null) => {
    if (e) e.preventDefault();
    const textToSend = customMessage || input;
    
    if (!textToSend.trim() || isLoading) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: textToSend }]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        message: textToSend,
        chat_history: messages
      });
      
      setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please ensure the FastAPI backend is running.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setUploadStatus({ type: 'error', text: 'Invalid file format. Please upload official documents in PDF format only.' });
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadStatus({ type: 'error', text: 'File is too large. Please upload a PDF smaller than 10MB.' });
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setIsUploading(true);
    setUploadStatus(null);

    try {
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadStatus({ type: 'success', text: response.data.message });
      fetchDocuments(); // Refresh the document list
      setTimeout(() => setUploadStatus(null), 5000);
    } catch (error) {
      setUploadStatus({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to upload document.' 
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const exampleQuestions = [
    "What are the eligibility criteria for B.Tech admissions?",
    "How many credits are required for graduation?",
    "What are the hostel regulations and timings?",
    "Which companies visit IIT Indore for placements?"
  ];

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <img src="/logo.png" alt="CampusGPT Logo" className="app-logo" />
          <h1>IITI CampusGPT</h1>
        </div>

        <div className="sidebar-content">
          <h2 className="section-title">Knowledge Base</h2>
          
          <div 
            className={`upload-box ${isUploading ? 'drag-active' : ''}`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              style={{ display: 'none' }} 
              accept=".pdf" 
              onChange={handleFileUpload}
            />
            {isUploading ? (
              <Loader2 className="upload-icon animate-spin" size={32} />
            ) : (
              <UploadCloud className="upload-icon" size={32} />
            )}
            <p className="upload-text">
              {isUploading ? 'Processing document...' : 'Upload Official PDF'}
            </p>
          </div>

          {uploadStatus && (
            <div style={{ 
              fontSize: '0.85rem', 
              padding: '0.75rem', 
              borderRadius: '8px',
              backgroundColor: uploadStatus.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              color: uploadStatus.type === 'success' ? '#10b981' : '#ef4444',
              marginBottom: '1.5rem',
              border: `1px solid ${uploadStatus.type === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
            }}>
              {uploadStatus.text}
            </div>
          )}

          <div style={{ marginTop: '2rem' }}>
            <h2 className="section-title">Upload Guidelines</h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
              Enhance the system by uploading:
              <br/>• Academic Handbooks
              <br/>• Placement Reports
              <br/>• Hostel Rules
              <br/>• Admission Brochures
            </p>
          </div>

          <div style={{ marginTop: '2rem', flexGrow: 1, overflowY: 'auto' }}>
            <h2 className="section-title">Current Documents</h2>
            {uploadedDocs.length === 0 ? (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No documents available.</p>
            ) : (
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {uploadedDocs.map((doc, idx) => (
                  <li key={idx} style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '0.5rem', 
                    fontSize: '0.8rem',
                    color: 'var(--text-muted)',
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    padding: '0.5rem',
                    borderRadius: '6px',
                    wordBreak: 'break-all'
                  }}>
                    <FileText size={14} style={{ flexShrink: 0, color: 'var(--primary)' }} />
                    <span>{doc}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="status-badge">
            <div className="status-dot"></div>
            System Online
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="main-chat">
        {messages.length > 0 && (
          <button 
            className="clear-chat-btn"
            onClick={() => setMessages([])}
            title="Clear Chat"
          >
            <Trash2 size={18} />
          </button>
        )}
        <div className="chat-history">
          {messages.length === 0 ? (
            <div className="welcome-container">
              <img src="/logo.png" alt="CampusGPT Logo" className="welcome-logo" />
              <h1 className="welcome-title">IIT Indore CampusGPT</h1>
              <p className="welcome-subtitle">
                An intelligent RAG assistant designed to provide accurate, official information directly from IIT Indore's knowledge base.
              </p>
              
              <div className="welcome-grid">
                <div className="welcome-card">
                  <h3><Info size={18} /> How It Works</h3>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                    CampusGPT uses Retrieval-Augmented Generation to search our document database and generate context-aware answers grounded only in official uploads.
                  </p>
                </div>
                
                <div className="welcome-card">
                  <h3><BookOpen size={18} /> Academics & Admissions</h3>
                  <ul>
                    <li><button className="suggested-btn" onClick={() => handleSend(null, "What is the fee structure for undergraduate programs?")}>Fee Structure</button></li>
                    <li><button className="suggested-btn" onClick={() => handleSend(null, "What are the branch change rules?")}>Branch Change Policy</button></li>
                    <li><button className="suggested-btn" onClick={() => handleSend(null, "How does JoSAA counselling work?")}>JoSAA Counselling</button></li>
                  </ul>
                </div>

                <div className="welcome-card">
                  <h3><Building size={18} /> Campus Life</h3>
                  <ul>
                    <li><button className="suggested-btn" onClick={() => handleSend(null, "What are the hostel regulations?")}>Hostel Rules</button></li>
                    <li><button className="suggested-btn" onClick={() => handleSend(null, "What facilities are available in the central library?")}>Library Facilities</button></li>
                    <li><button className="suggested-btn" onClick={() => handleSend(null, "How does the mess system operate?")}>Mess System</button></li>
                  </ul>
                </div>

                <div className="welcome-card">
                  <h3><Briefcase size={18} /> Placements & Careers</h3>
                  <ul>
                    <li><button className="suggested-btn" onClick={() => handleSend(null, "What are the latest placement statistics?")}>Placement Stats</button></li>
                    <li><button className="suggested-btn" onClick={() => handleSend(null, "Which top companies visit IIT Indore?")}>Top Recruiters</button></li>
                    <li><button className="suggested-btn" onClick={() => handleSend(null, "What internship opportunities are available?")}>Internships</button></li>
                  </ul>
                </div>
              </div>
              
              <p style={{ marginTop: '2rem', fontSize: '0.75rem', color: 'rgba(255,255,255,0.3)', textAlign: 'center' }}>
                Disclaimer: Responses are generated based on uploaded documents. Verify details through official IIT Indore notifications.
              </p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`message-wrapper ${msg.role}`}>
                <div className={`avatar ${msg.role === 'user' ? 'user-avatar' : 'bot-avatar'}`}>
                  {msg.role === 'user' ? <User size={20} /> : <img src="/logo.png" alt="Bot" />}
                </div>
                <div className="message-content markdown-body">
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="message-wrapper bot">
              <div className="avatar bot-avatar">
                <img src="/logo.png" alt="Bot" />
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <form onSubmit={handleSend} className="input-box">
            <input
              type="text"
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything about IIT Indore..."
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className="send-button"
              disabled={!input.trim() || isLoading}
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

export default App;
