import React, { useState } from 'react';
import { 
  Plus, 
  Paperclip, 
  Mic, 
  Send, 
  CheckCircle2, 
  ShieldCheck, 
  Sparkles, 
  X, 
  Database, 
  Bot, 
  Search, 
  Zap, 
  UserCheck, 
  FileText,
  Mail,
  User,
  Lock,
  ArrowRight
} from 'lucide-react';

export default function App() {
  // Navigation & Modal state
  const [activeModal, setActiveModal] = useState(null); // 'about', 'features', 'contact', 'signup', 'demo'
  const [authTab, setAuthTab] = useState('signup'); // 'signup' | 'signin'

  // Chatbot state
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: 'Hi 👋 How can I help you today?',
      citation: null,
      confidence: null
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // Pre-configured RAG Knowledge Base Answers from ResolvAI Case Study
  const ragKnowledgeBase = [
    {
      keywords: ['track', 'order', 'package', 'status', 'delivery'],
      response: 'To track your order, please provide your 6-digit Order ID. ResolvAI routes this query using intent classification (Order Tracking) and queries real-time shipping records.',
      citation: 'E-commerce_Logistics_API_v4.pdf',
      confidence: '0.98'
    },
    {
      keywords: ['refund', 'return', 'cancel', 'policy', 'money'],
      response: 'According to our return policy, items can be returned within 30 days of delivery for a full refund if they are in original condition. Refunds are processed within 3-5 business days upon item inspection.',
      citation: 'Returns_and_Refunds_Policy_2026.pdf',
      confidence: '0.96'
    },
    {
      keywords: ['hallucination', 'hallucinate', 'accurate', 'rag', 'knows'],
      response: 'ResolvAI uses an "Open Book" RAG architecture. Instead of generating answers from raw memory, it retrieves grounded policy chunks using hybrid search (BM25 + Dense Sentence-BERT) and includes verifiable source citations. If retrieval confidence falls below threshold, it abstains and escalates to a human operator.',
      citation: 'ResolvAI_Architecture_Paper.pdf (Section 2.3)',
      confidence: '0.99'
    },
    {
      keywords: ['team', 'author', 'project', 'who', 'members', 'nlp'],
      response: 'ResolvAI is developed by:\n• Parthivsurya K B (CB.SC.U4CSE24535)\n• Awaaz Muhammed (CB.SC.U4CSE24562)\n• Rajendra G (CB.SC.U4CSE24511)\nSlogan: "Support that knows, not guesses."',
      citation: 'NLP_Case_Study_ResolvAI.pdf',
      confidence: '1.00'
    }
  ];

  const handleSendMessage = (e) => {
    e?.preventDefault();
    if (!inputText.trim()) return;

    const userQuery = inputText.trim();
    const newUserMsg = {
      id: Date.now(),
      sender: 'user',
      text: userQuery
    };

    setMessages((prev) => [...prev, newUserMsg]);
    setInputText('');
    setIsTyping(true);

    // Simulate RAG Pipeline Query Processing
    setTimeout(() => {
      const lowerQuery = userQuery.toLowerCase();
      const match = ragKnowledgeBase.find(kb => 
        kb.keywords.some(kw => lowerQuery.includes(kw))
      );

      let botReply;
      if (match) {
        botReply = {
          id: Date.now() + 1,
          sender: 'bot',
          text: match.response,
          citation: match.citation,
          confidence: match.confidence
        };
      } else {
        botReply = {
          id: Date.now() + 1,
          sender: 'bot',
          text: 'I searched the internal knowledge base, but the retrieval confidence score is below threshold. Escalating this query with full conversation history to a human support agent.',
          citation: 'Confidence-Aware Fallback System',
          confidence: '0.42 (Escalated)'
        };
      }

      setMessages((prev) => [...prev, botReply]);
      setIsTyping(false);
    }, 900);
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

        {/* Hero Section */}
        <section className="hero-section">
          <h1 className="hero-title">
            AI Customer Support<br />
            That Never Sleeps
          </h1>
          <p className="hero-subtitle">
            Automate your customer support with an AI-powered chatbot that answers instantly reduces support costs
          </p>
          <button 
            className="btn-demo"
            onClick={() => setActiveModal('demo')}
          >
            Book a Demo
          </button>
        </section>

        {/* Interactive Chatbot Box Widget */}
        <section className="chat-preview-card">
          <div className="chat-inner-container">
            {/* Header inside chatbot box */}
            <div className="chat-header">
              <div className="chat-header-left">
                <span className="status-dot"></span>
                <span>AI Customer Support / Chatbot.</span>
              </div>
              <span style={{ fontSize: '0.75rem', opacity: 0.6 }}>RAG Engine v1.2</span>
            </div>

            {/* Chat Body */}
            <div className="chat-body">
              {messages.map((msg) => (
                <div 
                  key={msg.id} 
                  className={`chat-message-row ${msg.sender}`}
                >
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
              ))}

              {isTyping && (
                <div className="chat-message-row bot" style={{ opacity: 0.7 }}>
                  <div className="message-content" style={{ fontStyle: 'italic' }}>
                    ResolvAI is searching vector database & formulating grounded answer...
                  </div>
                </div>
              )}
            </div>

            {/* Quick Sample Prompts */}
            <div style={{ padding: '0 20px 8px' }}>
              <div className="prompt-chips">
                <button 
                  className="prompt-chip"
                  onClick={() => handlePromptClick('How do I request a refund?')}
                >
                  💳 Refund Policy
                </button>
                <button 
                  className="prompt-chip"
                  onClick={() => handlePromptClick('Track my order status')}
                >
                  📦 Track Order
                </button>
                <button 
                  className="prompt-chip"
                  onClick={() => handlePromptClick('How does ResolvAI prevent hallucinations?')}
                >
                  🧠 RAG Architecture
                </button>
                <button 
                  className="prompt-chip"
                  onClick={() => handlePromptClick('Who created ResolvAI?')}
                >
                  🎓 Case Study Team
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

        {/* Logos Bar at Bottom */}
        <footer className="logos-bar">
          <div className="logo-item">
            <div className="logo-icon" style={{ background: '#7c3aed', color: '#fff' }}>G</div>
            <span>LGPSM</span>
            <span className="logo-badge">RAG</span>
          </div>

          <div className="logo-item">
            <div className="logo-icon" style={{ background: '#ef4444', color: '#fff' }}>L</div>
            <span>Logoipsum</span>
          </div>

          <div className="logo-item">
            <div className="logo-icon" style={{ background: '#0284c7', color: '#fff' }}>⚡</div>
            <span>Logoipsum</span>
          </div>

          <div className="logo-item">
            <div className="logo-icon" style={{ background: '#f97316', color: '#fff' }}>▲</div>
            <span>LOGOIPSUM</span>
          </div>

          <div className="logo-item">
            <div className="logo-icon" style={{ background: '#2563eb', color: '#fff' }}>✦</div>
            <span>Logoipsum</span>
          </div>
        </footer>
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
              An intelligent, retrieval-augmented customer support chatbot for the e-commerce domain.
              <br />
              <strong>Slogan:</strong> <em>"Support that knows, not guesses."</em>
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
                ResolvAI operates like an open-book exam: it opens the exact pages in your company's internal documentation, reads those pages, and responds with direct citations.
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
              Built on Retrieval-Augmented Generation (RAG) to eliminate hallucinations and lower support costs.
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
                  Fine-tuned DistilBERT classifier routes queries into exact intent categories (order tracking, refund, etc.).
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
              Have questions about integrating ResolvAI into your e-commerce platform? Reach out to us.
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
                <textarea className="form-input" rows="4" placeholder="Tell us about your support ticket volume and knowledge base..." required></textarea>
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
                  <label className="form-label">Work Email</label>
                  <input type="email" className="form-input" placeholder="john@company.com" required />
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
                  <label className="form-label">Work Email</label>
                  <input type="email" className="form-input" placeholder="john@company.com" required />
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
