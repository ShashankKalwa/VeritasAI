import ArchDiagram from '../components/ArchDiagram';

export default function AboutPage() {
  return (
    <div className="page-container about-page">
      <div className="page-header">
        <h1 className="page-title">System Architecture</h1>
        <p className="page-subtitle">VeritasAI — Full system architecture and technology stack</p>
      </div>

      <ArchDiagram />

      <div className="tech-stack-section">
        <h2 className="section-title">Technology Stack</h2>
        
        <div className="tech-grid">
          <div className="tech-card">
            <div className="tech-icon">⚛️</div>
            <h3>Frontend</h3>
            <ul>
              <li>React 18 (Vite)</li>
              <li>React Router DOM v6</li>
              <li>Chart.js 4 + react-chartjs-2</li>
              <li>Vanilla CSS (Custom Design System)</li>
            </ul>
          </div>

          <div className="tech-card">
            <div className="tech-icon">🧠</div>
            <h3>AI Engine</h3>
            <ul>
              <li>Custom NLP Heuristic Engine</li>
              <li>60+ Pattern Rules</li>
              <li>Multi-signal Ensemble Scoring</li>
              <li>6-Category Auto-Classifier</li>
            </ul>
          </div>

          <div className="tech-card">
            <div className="tech-icon">🗄️</div>
            <h3>Backend & Data</h3>
            <ul>
              <li>Supabase PostgreSQL</li>
              <li>Supabase Auth (JWT)</li>
              <li>Supabase Realtime (WebSockets)</li>
              <li>Row-Level Security (RLS)</li>
            </ul>
          </div>

          <div className="tech-card">
            <div className="tech-icon">🚀</div>
            <h3>Deployment</h3>
            <ul>
              <li>Netlify (Frontend CDN)</li>
              <li>Supabase Cloud (Database)</li>
              <li>Edge Caching</li>
              <li>CI/CD Pipeline</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="features-section">
        <h2 className="section-title">Key Features</h2>
        
        <div className="features-grid">
          <div className="feature-item">
            <span className="feature-badge">🔍</span>
            <h3>Real-Time Detection</h3>
            <p>Instant fake news analysis using our custom NLP engine with 60+ heuristic pattern rules covering linguistic, rhetorical, and source credibility signals.</p>
          </div>

          <div className="feature-item">
            <span className="feature-badge">📊</span>
            <h3>Analytics Dashboard</h3>
            <p>Comprehensive data visualization with category breakdowns, confidence distributions, and trend analytics powered by Chart.js.</p>
          </div>

          <div className="feature-item">
            <span className="feature-badge">🔴</span>
            <h3>Live Community Feed</h3>
            <p>Real-time detection feed powered by Supabase WebSocket subscriptions, showing community analyses as they happen.</p>
          </div>

          <div className="feature-item">
            <span className="feature-badge">📰</span>
            <h3>500-Row Dataset</h3>
            <p>Curated labeled dataset with hand-crafted and generated headlines across 6 categories for browsing and research.</p>
          </div>

          <div className="feature-item">
            <span className="feature-badge">🔐</span>
            <h3>Secure Authentication</h3>
            <p>Supabase Auth with email/password authentication, session management, and Row-Level Security on all database tables.</p>
          </div>

          <div className="feature-item">
            <span className="feature-badge">💡</span>
            <h3>Explainable AI</h3>
            <p>Every detection comes with detailed analysis, confidence scores, and specific indicator pills explaining why the verdict was reached.</p>
          </div>
        </div>
      </div>

      <div className="about-footer">
        <p>Built for <strong>AITHON 2025</strong> — Problem Statement #2: Fake News Detection</p>
        <p className="about-tagline">VeritasAI — See Through the Noise</p>
      </div>
    </div>
  );
}
