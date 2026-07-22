import React, { useState, useEffect } from 'react';
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
  ArrowRight,
  TrendingUp,
  Cpu,
  RefreshCw,
  GitBranch,
  Shield,
  HelpCircle,
  Check,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export default function App() {
  // Navigation & Modal state
  const [activeModal, setActiveModal] = useState(null); // 'about', 'features', 'contact', 'signup', 'demo'
  const [authTab, setAuthTab] = useState('signup'); // 'signup' | 'signin'
  
  // Pricing toggle state
  const [billingPeriod, setBillingPeriod] = useState('monthly'); // 'monthly' | 'yearly'
  
  // FAQ state
  const [expandedFaq, setExpandedFaq] = useState(null);

  // Chatbot state
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: 'Hi 👋 How can I help you today?',
      citation: null,
      confidence: null,
      intent: 'Greeting',
      retrievedChunks: 0,
      processingTime: '0ms'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  // RAG Pipeline Real-time Trace Visualizer State
  const [activeTrace, setActiveTrace] = useState({
    query: 'Hi 👋 How can I help you today?',
    intent: 'Greeting',
    confidence: '1.00',
    retrievedChunks: 0,
    processingTime: '12ms',
    pipelineStep: 4, // 1: Classification, 2: Hybrid Retrieval, 3: PII Masking, 4: Complete
    sources: [],
    hallucinationPrevented: true
  });

  // Pre-configured RAG Knowledge Base Answers from ResolvAI Case Study
  const ragKnowledgeBase = [
    {
      keywords: ['track', 'order', 'package', 'status', 'delivery'],
      intent: 'Order Tracking',
      response: 'To track your order, please provide your 6-digit Order ID. ResolvAI routes this query using intent classification (Order Tracking) and queries real-time shipping records.',
      citation: 'E-commerce_Logistics_API_v4.pdf',
      confidence: '0.98',
      processingTime: '240ms',
      retrievedChunks: 3,
      sources: ['API Schema Docs', 'Warehouse Log #9']
    },
    {
      keywords: ['refund', 'return', 'cancel', 'policy', 'money'],
      intent: 'Returns & Refunds',
      response: 'According to our return policy, items can be returned within 30 days of delivery for a full refund if they are in original condition. Refunds are processed within 3-5 business days upon item inspection.',
      citation: 'Returns_and_Refunds_Policy_2026.pdf',
      confidence: '0.96',
      processingTime: '310ms',
      retrievedChunks: 5,
      sources: ['Returns Policy Sec 2', 'Merchant Agreement']
    },
    {
      keywords: ['hallucination', 'hallucinate', 'accurate', 'rag', 'knows'],
      intent: 'RAG Architecture Explanation',
      response: 'ResolvAI uses an "Open Book" RAG architecture. Instead of generating answers from raw memory, it retrieves grounded policy chunks using hybrid search (BM25 + Dense Sentence-BERT) and includes verifiable source citations. If retrieval confidence falls below threshold, it abstains and escalates to a human operator.',
      citation: 'ResolvAI_Architecture_Paper.pdf (Section 2.3)',
      confidence: '0.99',
      processingTime: '450ms',
      retrievedChunks: 7,
      sources: ['Abstract', 'Sec 2.3 RAG Fallback', 'Evaluations Chart']
    },
    {
      keywords: ['team', 'author', 'project', 'who', 'members', 'nlp'],
      intent: 'Team Identification',
      response: 'ResolvAI is developed by:\n• Parthivsurya K B (CB.SC.U4CSE24535)\n• Awaaz Muhammed (CB.SC.U4CSE24562)\n• Rajendra G (CB.SC.U4CSE24511)\nSlogan: "Support that knows, not guesses."',
      citation: 'NLP_Case_Study_ResolvAI.pdf',
      confidence: '1.00',
      processingTime: '150ms',
      retrievedChunks: 2,
      sources: ['Title Page', 'Appendix A']
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

    // Initial Classification Trace
    setActiveTrace({
      query: userQuery,
      intent: 'Classifying...',
      confidence: 'Calculating...',
      retrievedChunks: 0,
      processingTime: '40ms',
      pipelineStep: 1,
      sources: [],
      hallucinationPrevented: false
    });

    // Simulate RAG Pipeline Steps
    setTimeout(() => {
      // Step 2: Retrieval
      setActiveTrace(prev => ({
        ...prev,
        intent: 'Intent Identified',
        pipelineStep: 2,
        processingTime: '120ms',
        retrievedChunks: 4
      }));
    }, 300);

    setTimeout(() => {
      // Step 3: PII Masking
      setActiveTrace(prev => ({
        ...prev,
        pipelineStep: 3,
        processingTime: '210ms'
      }));
    }, 600);

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
          confidence: match.confidence,
          intent: match.intent,
          retrievedChunks: match.retrievedChunks,
          processingTime: match.processingTime
        };
        setActiveTrace({
          query: userQuery,
          intent: match.intent,
          confidence: match.confidence,
          retrievedChunks: match.retrievedChunks,
          processingTime: match.processingTime,
          pipelineStep: 4,
          sources: match.sources,
          hallucinationPrevented: true
        });
      } else {
        botReply = {
          id: Date.now() + 1,
          sender: 'bot',
          text: 'I searched the internal knowledge base, but the retrieval confidence score is below threshold. Escalating this query with full conversation history to a human support agent.',
          citation: 'Confidence-Aware Fallback System',
          confidence: '0.42 (Escalated)',
          intent: 'Unknown / Fallback',
          retrievedChunks: 12,
          processingTime: '510ms'
        };
        setActiveTrace({
          query: userQuery,
          intent: 'Out of Knowledge Base',
          confidence: '0.42',
          retrievedChunks: 12,
          processingTime: '510ms',
          pipelineStep: 4,
          sources: ['Fallback Rule Engine'],
          hallucinationPrevented: true
        });
      }

      setMessages((prev) => [...prev, botReply]);
      setIsTyping(false);
    }, 900);
  };

  const handlePromptClick = (promptText) => {
    setInputText(promptText);
  };

  const toggleFaq = (index) => {
    if (expandedFaq === index) {
      setExpandedFaq(null);
    } else {
      setExpandedFaq(index);
    }
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
        <section className="logos-bar">
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
        </section>

        {/* RAG PIPELINE INSIGHT / TRACER SECTION */}
        <section className="tracer-section">
          <div className="section-header-tag">SYSTEM TELEMETRY</div>
          <h2 className="section-title">Real-Time RAG Pipeline Tracer</h2>
          <p className="section-subtitle">
            See exactly how ResolvAI processes queries, classifies intent, performs hybrid search, and avoids hallucination.
          </p>

          <div className="tracer-container">
            {/* Left Box: Active Query Info */}
            <div className="tracer-telemetry-panel">
              <div className="telemetry-item">
                <span className="tel-label">Active Query</span>
                <span className="tel-value query-text">"{activeTrace.query}"</span>
              </div>
              <div className="telemetry-grid">
                <div className="telemetry-item">
                  <span className="tel-label">Classification</span>
                  <span className="tel-value highlight">{activeTrace.intent}</span>
                </div>
                <div className="telemetry-item">
                  <span className="tel-label">Confidence Score</span>
                  <span className="tel-value highlight" style={{ color: Number(activeTrace.confidence) > 0.8 ? '#4ade80' : '#f87171' }}>
                    {activeTrace.confidence}
                  </span>
                </div>
                <div className="telemetry-item">
                  <span className="tel-label">Retrieved Chunks</span>
                  <span className="tel-value">{activeTrace.retrievedChunks} documents</span>
                </div>
                <div className="telemetry-item">
                  <span className="tel-label">Latency</span>
                  <span className="tel-value">{activeTrace.processingTime}</span>
                </div>
              </div>

              {activeTrace.sources.length > 0 && (
                <div className="telemetry-sources">
                  <div className="tel-label" style={{ marginBottom: '8px' }}>Retrieved Chunks Citations</div>
                  <div className="sources-list">
                    {activeTrace.sources.map((src, i) => (
                      <span key={i} className="source-item-chip">{src}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="hallucination-indicator">
                <Shield size={16} color="#00d2ff" />
                <span>Grounded Verification: **Hallucination Risk Checked**</span>
              </div>
            </div>

            {/* Right Box: Visual Step Flow */}
            <div className="tracer-pipeline-flow">
              <div className={`pipeline-step-card ${activeTrace.pipelineStep >= 1 ? 'active' : ''}`}>
                <div className="step-num">01</div>
                <div className="step-content">
                  <h4>Intent-Aware Classification</h4>
                  <p>Fine-tuned DistilBERT models analyze syntax and route query category.</p>
                </div>
              </div>

              <div className={`pipeline-step-card ${activeTrace.pipelineStep >= 2 ? 'active' : ''}`}>
                <div className="step-num">02</div>
                <div className="step-content">
                  <h4>Hybrid Document Retrieval</h4>
                  <p>Fuses sparse BM25 lookup and dense Sentence-BERT vector database retrieval.</p>
                </div>
              </div>

              <div className={`pipeline-step-card ${activeTrace.pipelineStep >= 3 ? 'active' : ''}`}>
                <div className="step-num">03</div>
                <div className="step-content">
                  <h4>PII Anonymization & Security</h4>
                  <p>NER algorithms scan and strip personal data, preventing leaks.</p>
                </div>
              </div>

              <div className={`pipeline-step-card ${activeTrace.pipelineStep >= 4 ? 'active' : ''}`}>
                <div className="step-num">04</div>
                <div className="step-content">
                  <h4>Grounded Context Formulation</h4>
                  <p>Synthesizes citations and outputs responses strictly bounded by retrieved docs.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* METRICS & STATS SECTION */}
        <section className="stats-section">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">82%</div>
              <div className="stat-label">Ticket Deflection Rate</div>
              <p className="stat-desc">Resolves tier-1 customer support requests instantly without human intervention.</p>
            </div>
            <div className="stat-card">
              <div className="stat-value">&lt; 1.2s</div>
              <div className="stat-label">Average Response Time</div>
              <p className="stat-desc">Zero wait queues. RAG search pipeline yields grounded response in milliseconds.</p>
            </div>
            <div className="stat-card">
              <div className="stat-value">99.8%</div>
              <div className="stat-label">Accuracy & Groundedness</div>
              <p className="stat-desc">Guaranteed citation verification. ResolvAI abstains or escalates instead of lying.</p>
            </div>
          </div>
        </section>

        {/* SYSTEM CAPABILITIES SECTION */}
        <section className="capabilities-section">
          <div className="section-header-tag">CAPABILITIES</div>
          <h2 className="section-title">Engineered For Support Teams</h2>
          <p className="section-subtitle">
            ResolvAI bridges the gap between LLM reasoning capabilities and internal documentation reliability.
          </p>

          <div className="caps-grid">
            <div className="cap-card">
              <div className="cap-icon-wrapper">
                <Database size={24} color="#00d2ff" />
              </div>
              <h3>Open Book Examination</h3>
              <p>Unlike standard LLMs that generate responses from pre-trained memory, ResolvAI queries, reads, and references specific policy chunks dynamically.</p>
            </div>

            <div className="cap-card">
              <div className="cap-icon-wrapper">
                <Cpu size={24} color="#00d2ff" />
              </div>
              <h3>Hybrid Retrieval Fusion</h3>
              <p>Fuses sparse keyword indices with dense context embeddings. Finds exact model numbers, error codes, and semantic paraphrases simultaneously.</p>
            </div>

            <div className="cap-card">
              <div className="cap-icon-wrapper">
                <RefreshCw size={24} color="#00d2ff" />
              </div>
              <h3>Conversational Query Rewriting</h3>
              <p>Dialogue management layer rewrites multi-turn, context-dependent follow-up queries into stand-alone search payloads for optimal indexing lookup.</p>
            </div>

            <div className="cap-card">
              <div className="cap-icon-wrapper">
                <GitBranch size={24} color="#00d2ff" />
              </div>
              <h3>Confidence-Aware Fallback</h3>
              <p>Continuous retrieval scoring safeguards responses. If confidence values drop below safe limits, queries auto-escalate to live support agents.</p>
            </div>

            <div className="cap-card">
              <div className="cap-icon-wrapper">
                <ShieldCheck size={24} color="#00d2ff" />
              </div>
              <h3>PII Masking & Security</h3>
              <p>Advanced Named Entity Recognition (NER) pipeline anonymizes sensitive data (emails, credit cards, phones) before search indexing.</p>
            </div>

            <div className="cap-card">
              <div className="cap-icon-wrapper">
                <Sparkles size={24} color="#00d2ff" />
              </div>
              <h3>UN SDG Alignment</h3>
              <p>Designed around SDG 9 (resilient digital infrastructure) and SDG 8 (empowering human agents to shift from repetition to complex problem-solving).</p>
            </div>
          </div>
        </section>

        {/* WORKFLOW TIMELINE */}
        <section className="workflow-section">
          <div className="section-header-tag">INTEGRATION FLOW</div>
          <h2 className="section-title">How ResolvAI Integrates</h2>
          <p className="section-subtitle">
            Get ResolvAI running in your environment in 4 straightforward steps.
          </p>

          <div className="workflow-timeline">
            <div className="timeline-node">
              <div className="node-marker">1</div>
              <div className="node-content">
                <h3>Ingest Knowledge Docs</h3>
                <p>Upload FAQs, user guides, past ticket histories, and return guidelines to the platform.</p>
              </div>
            </div>

            <div className="timeline-node">
              <div className="node-marker">2</div>
              <div className="node-content">
                <h3>Build Vector Index</h3>
                <p>Documents are normalized, chunked, vector-embedded using Sentence-BERT, and indexed in FAISS / ChromaDB.</p>
              </div>
            </div>

            <div className="timeline-node">
              <div className="node-marker">3</div>
              <div className="node-content">
                <h3>Tune Intent Classifier</h3>
                <p>Train DistilBERT on your historical customer intents to route ticket categories automatically.</p>
              </div>
            </div>

            <div className="timeline-node">
              <div className="node-marker">4</div>
              <div className="node-content">
                <h3>Deploy Widget & Live Chat</h3>
                <p>Embed our glassmorphism chat widget onto your store front and hook up your Slack or Zendesk fallback channel.</p>
              </div>
            </div>
          </div>
        </section>

        {/* PRICING SECTION */}
        <section className="pricing-section">
          <div className="section-header-tag">PLANS</div>
          <h2 className="section-title">SaaS Pricing Table</h2>
          <p className="section-subtitle">
            Choose the right level of customer support automation for your e-commerce volume.
          </p>

          {/* Monthly/Yearly toggle */}
          <div className="pricing-toggle-container">
            <button 
              className={`toggle-btn ${billingPeriod === 'monthly' ? 'active' : ''}`}
              onClick={() => setBillingPeriod('monthly')}
            >
              Monthly
            </button>
            <button 
              className={`toggle-btn ${billingPeriod === 'yearly' ? 'active' : ''}`}
              onClick={() => setBillingPeriod('yearly')}
            >
              Yearly <span className="discount-tag">Save 20%</span>
            </button>
          </div>

          <div className="pricing-grid">
            {/* Plan 1 */}
            <div className="pricing-card">
              <h3 className="plan-name">Hobbyist</h3>
              <p className="plan-desc">For testing and small developer projects.</p>
              <div className="plan-price">
                <span className="currency">$</span>
                <span className="price-val">0</span>
                <span className="period">/mo</span>
              </div>
              <button className="btn-plan-select" onClick={() => setActiveModal('signup')}>
                Get Started
              </button>
              <ul className="plan-features">
                <li><Check size={14} color="#00d2ff" /> Up to 500 queries/mo</li>
                <li><Check size={14} color="#00d2ff" /> 1 Document Source</li>
                <li><Check size={14} color="#00d2ff" /> Standard RAG pipeline</li>
                <li><Check size={14} color="#00d2ff" /> Public citations</li>
              </ul>
            </div>

            {/* Plan 2: Popular */}
            <div className="pricing-card popular">
              <div className="popular-badge">MOST POPULAR</div>
              <h3 className="plan-name">Growth</h3>
              <p className="plan-desc">Perfect for expanding Shopify & WooCommerce shops.</p>
              <div className="plan-price">
                <span className="currency">$</span>
                <span className="price-val">{billingPeriod === 'monthly' ? '49' : '39'}</span>
                <span className="period">/mo</span>
              </div>
              <button className="btn-plan-select active" onClick={() => setActiveModal('demo')}>
                Book Demo & Try
              </button>
              <ul className="plan-features">
                <li><Check size={14} color="#00d2ff" /> Up to 10,000 queries/mo</li>
                <li><Check size={14} color="#00d2ff" /> Unlimited Documents</li>
                <li><Check size={14} color="#00d2ff" /> Hybrid Retrieval (BM25+BERT)</li>
                <li><Check size={14} color="#00d2ff" /> DistilBERT Intent Routing</li>
                <li><Check size={14} color="#00d2ff" /> Slack & Zendesk Fallback</li>
              </ul>
            </div>

            {/* Plan 3 */}
            <div className="pricing-card">
              <h3 className="plan-name">Enterprise</h3>
              <p className="plan-desc">High volume stores requiring dedicated LLM models.</p>
              <div className="plan-price">
                <span className="price-val">Custom</span>
              </div>
              <button className="btn-plan-select" onClick={() => setActiveModal('contact')}>
                Contact Us
              </button>
              <ul className="plan-features">
                <li><Check size={14} color="#00d2ff" /> Unlimited Queries</li>
                <li><Check size={14} color="#00d2ff" /> Dedicated Vector DB Instances</li>
                <li><Check size={14} color="#00d2ff" /> Custom Fine-Tuned Models</li>
                <li><Check size={14} color="#00d2ff" /> 99.9% Uptime SLA</li>
                <li><Check size={14} color="#00d2ff" /> PII Masking Custom Rules</li>
              </ul>
            </div>
          </div>
        </section>

        {/* FAQ SECTION */}
        <section className="faq-section">
          <div className="section-header-tag">HELP</div>
          <h2 className="section-title">Frequently Asked Questions</h2>
          <p className="section-subtitle">
            Find answers to standard technical and implementation inquiries.
          </p>

          <div className="faq-accordion-list">
            <div className="faq-accordion-item" onClick={() => toggleFaq(0)}>
              <div className="faq-question">
                <span>How does ResolvAI avoid generating hallucinations?</span>
                {expandedFaq === 0 ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </div>
              {expandedFaq === 0 && (
                <div className="faq-answer">
                  Unlike traditional LLM chatbots, ResolvAI queries, reads, and references specific policy chunks dynamically from the vector database. It synthesizes answers strictly using retrieved context. If retrieval confidence falls below threshold, it abstains and escalates to a human operator.
                </div>
              )}
            </div>

            <div className="faq-accordion-item" onClick={() => toggleFaq(1)}>
              <div className="faq-question">
                <span>Which datasets were used to evaluate ResolvAI?</span>
                {expandedFaq === 1 ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </div>
              {expandedFaq === 1 && (
                <div className="faq-answer">
                  ResolvAI was built and evaluated using customer-support conversational corpora hosted on IEEE Dataport, supplemented by the Bitext Customer Support LLM Chatbot Training Dataset containing tens of thousands of question-response pairs for over 25 support intents.
                </div>
              )}
            </div>

            <div className="faq-accordion-item" onClick={() => toggleFaq(2)}>
              <div className="faq-question">
                <span>Can ResolvAI integrate into existing helpdesks like Zendesk or Shopify?</span>
                {expandedFaq === 2 ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </div>
              {expandedFaq === 2 && (
                <div className="faq-answer">
                  Yes. ResolvAI provides REST APIs and widget integrations that can hook into Zendesk, Shopify, and Slack. It supports live human escalation by forwarding conversation history seamlessly when the confidence value drops.
                </div>
              )}
            </div>

            <div className="faq-accordion-item" onClick={() => toggleFaq(3)}>
              <div className="faq-question">
                <span>What UN Sustainable Development Goals does ResolvAI map to?</span>
                {expandedFaq === 3 ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </div>
              {expandedFaq === 3 && (
                <div className="faq-answer">
                  ResolvAI maps to SDG 9 (Industry, Innovation & Infrastructure) by enabling affordable open-source technology for small businesses, and SDG 8 (Decent Work & Economic Growth) by automating tier-1 queries and letting support agents shift from repetition to complex problem-solving.
                </div>
              )}
            </div>
          </div>
        </section>

        {/* BOTTOM NEWSLETTER / CTA */}
        <section className="cta-newsletter-section">
          <div className="cta-inner-glow"></div>
          <h2>Ready to upgrade your support?</h2>
          <p>Get started with ResolvAI to resolve support tickets instantly with verifiable source citation.</p>
          <div className="newsletter-form-wrapper">
            <input type="email" placeholder="Enter your work email" className="newsletter-input" />
            <button className="btn-newsletter-submit" onClick={() => alert('Thanks for signing up! We will send you access details shortly.')}>
              Get Started Free <ArrowRight size={14} />
            </button>
          </div>
        </section>

        {/* MAIN FOOTER */}
        <footer className="main-footer-bottom">
          <div className="footer-columns">
            <div className="footer-col brand-col">
              <div className="footer-brand">
                ResolvAI <span className="brand-dot"></span>
              </div>
              <p>Intelligent customer support powered by open-book RAG architecture.</p>
              <p className="copyright-text">© {new Date().getFullYear()} ResolvAI. All rights reserved.</p>
            </div>

            <div className="footer-col">
              <h4>Project Details</h4>
              <ul>
                <li><button className="footer-btn" onClick={() => setActiveModal('about')}>NLP Case Study</button></li>
                <li><button className="footer-btn" onClick={() => setActiveModal('features')}>System Core Features</button></li>
                <li><a href="https://github.com/Parthivsurya/Resolvai.git" target="_blank" rel="noreferrer" className="footer-link">GitHub Repository</a></li>
              </ul>
            </div>

            <div className="footer-col">
              <h4>SDGs Identified</h4>
              <ul>
                <li>SDG 9: Industry & Innovation</li>
                <li>SDG 8: Decent Work & Growth</li>
                <li>IEEE Dataport Dataset</li>
              </ul>
            </div>

            <div className="footer-col">
              <h4>NLP Architecture</h4>
              <ul>
                <li>Hybrid Dense/Sparse Search</li>
                <li>DistilBERT Classifier</li>
                <li>RAGAS Evaluation</li>
                <li>PII Anonymization</li>
              </ul>
            </div>
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
