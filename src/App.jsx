import React, { useState, useRef, useEffect } from 'react';
import {
  Plus,
  Paperclip,
  Mic,
  Send,
  ShieldCheck,
  Sparkles,
  X,
  Search,
  Zap,
  UserCheck,
  FileText
} from 'lucide-react';

// ResolvAI backend (FastAPI). Override at build time with VITE_API_URL if needed.
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  // Navigation & Modal state
  const [activeModal, setActiveModal] = useState(null); // 'about', 'features', 'contact', 'signup', 'demo'
  const [authTab, setAuthTab] = useState('signup'); // 'signup' | 'signin'

  // Chatbot state
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: 'Hi 👋 I\'m ResolvAI, your placement prep assistant. Ask me about company PYQs, aptitude, coding rounds, HR interviews, eligibility, or the placement process.',
      citation: null,
      confidence: null,
      intent: 'Greeting',
      retrievedChunks: 0,
      processingTime: '0ms'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // Stable session id so the backend can rewrite multi-turn follow-ups.
  const [sessionId] = useState(() => 'web-' + Math.random().toString(36).slice(2));

  // Auto-scroll the chat body to the most recent message.
  const chatBodyRef = useRef(null);
  useEffect(() => {
    const el = chatBodyRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSendMessage = async (e) => {
    e?.preventDefault();
    const userQuery = inputText.trim();
    if (!userQuery) return;

    const newUserMsg = { id: Date.now(), sender: 'user', text: userQuery };
    setMessages((prev) => [...prev, newUserMsg]);
    setInputText('');
    setIsTyping(true);
    const startedAt = Date.now();

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userQuery, session_id: sessionId })
      });
      if (!res.ok) throw new Error(`Backend responded ${res.status}`);
      const data = await res.json();

      // Map backend citations (array) -> a concise source line for the badge.
      const sources = [...new Set((data.citations || []).map((c) => c.source))];
      const citation = sources.length
        ? sources.join(', ')
        : (data.escalated ? 'Escalated to a placement officer' : null);
      const confidence = data.confidence != null
        ? `${Math.round(data.confidence * 100)}%${data.escalated ? ' • Escalated' : ''}`
        : null;
      const processingTime = `${Date.now() - startedAt}ms`;

      setMessages((prev) => [...prev, {
        id: Date.now() + 1,
        sender: 'bot',
        text: data.answer,
        citation,
        confidence,
        intent: data.intent,
        retrievedChunks: (data.citations || []).length,
        processingTime
      }]);
    } catch {
      setMessages((prev) => [...prev, {
        id: Date.now() + 1,
        sender: 'bot',
        text: `I couldn't reach the ResolvAI backend at ${API_URL}. Make sure it's running (uvicorn backend.app:app --reload).`,
        citation: null,
        confidence: null,
        intent: 'Error',
        retrievedChunks: 0,
        processingTime: '—'
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handlePromptClick = (promptText) => {
    setInputText(promptText);
  };

  return (
    <div className="app-viewport">
      {/* Background Lighting Beam Effect */}
      <div className="curtain-overlay"></div>
      <div className="ambient-glow"></div>

      <div className="main-container">
        {/* Navigation Bar */}
        <header className="navbar">
          <div className="brand-logo" onClick={() => setActiveModal(null)}>
            ResolvAI
            <span className="brand-dot"></span>
          </div>

          <nav>
            <ul className="nav-links">
              <li>
                <button 
                  className={`nav-link ${activeModal === null ? 'active' : ''}`}
                  onClick={() => setActiveModal(null)}
                >
                  Home
                </button>
              </li>
              <li>
                <button 
                  className={`nav-link ${activeModal === 'about' ? 'active' : ''}`}
                  onClick={() => setActiveModal('about')}
                >
                  About
                </button>
              </li>
              <li>
                <button 
                  className={`nav-link ${activeModal === 'features' ? 'active' : ''}`}
                  onClick={() => setActiveModal('features')}
                >
                  Feature
                </button>
              </li>
              <li>
                <button 
                  className={`nav-link ${activeModal === 'contact' ? 'active' : ''}`}
                  onClick={() => setActiveModal('contact')}
                >
                  Contact
                </button>
              </li>
            </ul>
          </nav>

          <button 
            className="btn-signup-pill"
            onClick={() => setActiveModal('signup')}
          >
            Sign Up
          </button>
        </header>

        <div className="chat-stage">
        {/* Hero lead-in */}
        <div className="hero-lead">
          <span className="hero-badge">
            <Sparkles size={13} />
            RAG-grounded • source-cited
          </span>
          <h1 className="hero-lead-title">
            Crack your placements with answers that <span className="grad-text">cite their source</span>
          </h1>
          <p className="hero-lead-sub">
            Ask about company PYQs, aptitude, coding rounds, HR interviews & eligibility —
            ResolvAI reads real placement material before it answers.
          </p>
        </div>

        {/* Interactive Chatbot Box Widget */}
        <section className="chat-preview-card">
          <div className="chat-inner-container">
            {/* Header inside chatbot box */}
            <div className="chat-header">
              <div className="chat-header-left">
                <span className="status-dot"></span>
                <span>ResolvAI · Placement Assistant</span>
              </div>
              <span style={{ fontSize: '0.75rem', opacity: 0.6 }}>RAG Engine v1.2</span>
            </div>

            {/* Chat Body */}
            <div className="chat-body" ref={chatBodyRef}>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`chat-message-row ${msg.sender}`}
                >
                  {msg.sender === 'bot' && <div className="msg-avatar">AI</div>}
                  <div className="msg-stack">
                    <div className="message-content">{msg.text}</div>
                    {msg.citation && (
                      <div className="citation-badge">
                        <FileText size={13} />
                        <span>Source: {msg.citation}</span>
                        {msg.confidence && (
                          <span className="confidence-score">
                            [{msg.confidence}]
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="chat-message-row bot">
                  <div className="msg-avatar">AI</div>
                  <div className="msg-stack">
                    <div className="message-content typing-indicator">
                      <span></span><span></span><span></span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Quick Sample Prompts */}
            <div style={{ padding: '0 20px 8px' }}>
              <div className="prompt-chips">
                <button
                  className="prompt-chip"
                  onClick={() => handlePromptClick('What TCS PYQ coding questions are asked?')}
                >
                  📝 TCS PYQs
                </button>
                <button
                  className="prompt-chip"
                  onClick={() => handlePromptClick('How do I prepare for the aptitude round?')}
                >
                  🧮 Aptitude Prep
                </button>
                <button
                  className="prompt-chip"
                  onClick={() => handlePromptClick('What are common HR interview questions?')}
                >
                  💼 HR Round
                </button>
                <button
                  className="prompt-chip"
                  onClick={() => handlePromptClick('What is the eligibility criteria for placements?')}
                >
                  ✅ Eligibility
                </button>
              </div>
            </div>

            {/* Chat Input Bar */}
            <form onSubmit={handleSendMessage} className="chat-input-wrapper">
              <button type="button" className="chat-icon-btn" title="Add item">
                <Plus size={18} />
              </button>

              <span style={{ color: '#334155', margin: '0 2px' }}>|</span>

              <button type="button" className="chat-icon-btn" title="Attach file">
                <Paperclip size={18} />
              </button>

              <input
                type="text"
                className="chat-input-field"
                placeholder="Ask ResolvAI a question..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
              />

              {inputText.trim() ? (
                <button type="submit" className="send-btn">
                  <span>Send</span>
                  <Send size={14} />
                </button>
              ) : (
                <button type="button" className="chat-icon-btn mic-btn" title="Voice Search">
                  <Mic size={16} />
                </button>
              )}
            </form>
          </div>
        </section>
        </div>

      </div>

      {/* MODAL: ABOUT RESOLVAI */}
      {activeModal === 'about' && (
        <div className="modal-overlay" onClick={() => setActiveModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setActiveModal(null)}>
              <X size={18} />
            </button>
            
            <h2 className="modal-title">About ResolvAI</h2>
            <p className="modal-subtitle">
              An intelligent, retrieval-augmented placement &amp; interview-prep assistant for students.
              <br />
              <strong>Slogan:</strong> <em>"Answers that know, not guess."</em>
            </p>

            <div className="team-list">
              <h4 style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8', fontSize: '0.9rem' }}>
                NLP Project Team Members:
              </h4>
              <div className="team-member">
                <span className="member-name">Parthivsurya K B</span>
                <span className="member-id">CB.SC.U4CSE24535</span>
              </div>
              <div className="team-member">
                <span className="member-name">Awaaz Muhammed</span>
                <span className="member-id">CB.SC.U4CSE24562</span>
              </div>
              <div className="team-member">
                <span className="member-name">Rajendra G</span>
                <span className="member-id">CB.SC.U4CSE24511</span>
              </div>
            </div>

            <div style={{ marginTop: '20px', fontSize: '0.9rem', color: '#94a3b8', lineHeight: 1.6 }}>
              <h4 style={{ color: '#ffffff', marginBottom: '8px', fontFamily: 'var(--font-mono)' }}>
                The "Open Book Examination" Analogy:
              </h4>
              <p>
                Standard AI chatbots answer questions from memory like a closed-book exam—when they don't know the answer, they risk hallucinating.
                ResolvAI operates like an open-book exam: it opens the exact pages in the placement knowledge base and company PYQ archives, reads those pages, and responds with direct citations.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: FEATURES */}
      {activeModal === 'features' && (
        <div className="modal-overlay" onClick={() => setActiveModal(null)}>
          <div className="modal-card" style={{ maxWidth: '800px' }} onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setActiveModal(null)}>
              <X size={18} />
            </button>
            
            <h2 className="modal-title">ResolvAI Key Innovations</h2>
            <p className="modal-subtitle">
              Built on Retrieval-Augmented Generation (RAG) to eliminate hallucinations and give students grounded, source-cited placement guidance.
            </p>

            <div className="features-grid">
              <div className="feature-card-item">
                <div className="feature-icon-title">
                  <Search size={18} />
                  <span>Hybrid Retrieval</span>
                </div>
                <div className="feature-desc">
                  Fuses dense semantic vector embeddings (Sentence-BERT) with sparse BM25 keyword search for maximum precision.
                </div>
              </div>

              <div className="feature-card-item">
                <div className="feature-icon-title">
                  <ShieldCheck size={18} />
                  <span>Confidence Abstention</span>
                </div>
                <div className="feature-desc">
                  Computes retrieval confidence scores; gracefully escalates to human agents when confidence is low.
                </div>
              </div>

              <div className="feature-card-item">
                <div className="feature-icon-title">
                  <FileText size={18} />
                  <span>Source-Cited Answers</span>
                </div>
                <div className="feature-desc">
                  Every response includes exact passage citations for verifiable enterprise transparency.
                </div>
              </div>

              <div className="feature-card-item">
                <div className="feature-icon-title">
                  <Zap size={18} />
                  <span>Intent Routing</span>
                </div>
                <div className="feature-desc">
                  Fine-tuned DistilBERT classifier routes queries into exact intent categories (PYQs, aptitude, coding round, HR, eligibility, etc.).
                </div>
              </div>

              <div className="feature-card-item">
                <div className="feature-icon-title">
                  <UserCheck size={18} />
                  <span>PII Anonymization</span>
                </div>
                <div className="feature-desc">
                  Automatic NER and regex filters mask sensitive personal information before indexing.
                </div>
              </div>

              <div className="feature-card-item">
                <div className="feature-icon-title">
                  <Sparkles size={18} />
                  <span>SDG Alignment</span>
                </div>
                <div className="feature-desc">
                  Mapped to UN SDG 9 (Industry & Innovation) and SDG 8 (Decent Work & Economic Growth).
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: CONTACT */}
      {activeModal === 'contact' && (
        <div className="modal-overlay" onClick={() => setActiveModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setActiveModal(null)}>
              <X size={18} />
            </button>
            
            <h2 className="modal-title">Contact ResolvAI Team</h2>
            <p className="modal-subtitle">
              Have questions about ResolvAI or want to add your college's placement material? Reach out to us.
            </p>

            <form className="auth-form" onSubmit={(e) => { e.preventDefault(); alert('Thank you for contacting ResolvAI! We will get back to you shortly.'); setActiveModal(null); }}>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input type="text" className="form-input" placeholder="Awaaz Muhammed" required />
              </div>

              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input type="email" className="form-input" placeholder="name@company.com" required />
              </div>

              <div className="form-group">
                <label className="form-label">Message</label>
                <textarea className="form-input" rows="4" placeholder="Tell us which companies or rounds you'd like covered..." required></textarea>
              </div>

              <button type="submit" className="btn-submit">
                Send Message
              </button>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: SIGN UP / SIGN IN */}
      {activeModal === 'signup' && (
        <div className="modal-overlay" onClick={() => setActiveModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setActiveModal(null)}>
              <X size={18} />
            </button>
            
            <div className="auth-tabs">
              <button 
                className={`auth-tab ${authTab === 'signup' ? 'active' : ''}`}
                onClick={() => setAuthTab('signup')}
              >
                Sign Up
              </button>
              <button 
                className={`auth-tab ${authTab === 'signin' ? 'active' : ''}`}
                onClick={() => setAuthTab('signin')}
              >
                Sign In
              </button>
            </div>

            {authTab === 'signup' ? (
              <form className="auth-form" onSubmit={(e) => { e.preventDefault(); alert('Account created successfully!'); setActiveModal(null); }}>
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input type="text" className="form-input" placeholder="John Doe" required />
                </div>
                <div className="form-group">
                  <label className="form-label">College Email</label>
                  <input type="email" className="form-input" placeholder="name@college.edu" required />
                </div>
                <div className="form-group">
                  <label className="form-label">Password</label>
                  <input type="password" className="form-input" placeholder="••••••••" required />
                </div>
                <button type="submit" className="btn-submit">
                  Create ResolvAI Account
                </button>
              </form>
            ) : (
              <form className="auth-form" onSubmit={(e) => { e.preventDefault(); alert('Signed in successfully!'); setActiveModal(null); }}>
                <div className="form-group">
                  <label className="form-label">College Email</label>
                  <input type="email" className="form-input" placeholder="name@college.edu" required />
                </div>
                <div className="form-group">
                  <label className="form-label">Password</label>
                  <input type="password" className="form-input" placeholder="••••••••" required />
                </div>
                <button type="submit" className="btn-submit">
                  Sign In to Dashboard
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* MODAL: BOOK A DEMO */}
      {activeModal === 'demo' && (
        <div className="modal-overlay" onClick={() => setActiveModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setActiveModal(null)}>
              <X size={18} />
            </button>
            
            <h2 className="modal-title">Book a ResolvAI Demo</h2>
            <p className="modal-subtitle">
              See how our RAG-powered chatbot reduces tier-1 customer support tickets by up to 80%.
            </p>

            <form className="auth-form" onSubmit={(e) => { e.preventDefault(); alert('Demo request submitted! Our team will send a calendar invite.'); setActiveModal(null); }}>
              <div className="form-group">
                <label className="form-label">Work Email</label>
                <input type="email" className="form-input" placeholder="alex@ecommerce.com" required />
              </div>

              <div className="form-group">
                <label className="form-label">Company / Product Domain</label>
                <input type="text" className="form-input" placeholder="E-commerce / Retail" required />
              </div>

              <div className="form-group">
                <label className="form-label">Monthly Support Ticket Volume</label>
                <select className="form-input" style={{ background: '#0f172a' }}>
                  <option>1,000 - 5,000 tickets/mo</option>
                  <option>5,000 - 25,000 tickets/mo</option>
                  <option>25,000+ tickets/mo</option>
                </select>
              </div>

              <button type="submit" className="btn-submit">
                Schedule Live Demo
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
