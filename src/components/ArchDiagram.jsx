export default function ArchDiagram() {
  return (
    <div className="arch-diagram-wrapper">
      <svg viewBox="0 0 900 700" className="arch-svg" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="grad-client" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#1e3a5f" stopOpacity="0.9"/>
            <stop offset="100%" stopColor="#2a4f7a" stopOpacity="0.9"/>
          </linearGradient>
          <linearGradient id="grad-cdn" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#1a3a2a" stopOpacity="0.9"/>
            <stop offset="100%" stopColor="#2a5a3a" stopOpacity="0.9"/>
          </linearGradient>
          <linearGradient id="grad-api" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3a1a1a" stopOpacity="0.9"/>
            <stop offset="100%" stopColor="#5a2a2a" stopOpacity="0.9"/>
          </linearGradient>
          <linearGradient id="grad-ai" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#2a1a3a" stopOpacity="0.9"/>
            <stop offset="100%" stopColor="#4a2a5a" stopOpacity="0.9"/>
          </linearGradient>
          <linearGradient id="grad-data" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#1a2a1a" stopOpacity="0.9"/>
            <stop offset="100%" stopColor="#2a4a2a" stopOpacity="0.9"/>
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto" fill="#6b7280">
            <polygon points="0 0, 10 3.5, 0 7"/>
          </marker>
        </defs>

        {/* Title */}
        <text x="450" y="35" textAnchor="middle" fill="#f5f5f5" fontSize="20" fontFamily="Playfair Display" fontWeight="700">
          VeritasAI — System Architecture
        </text>

        {/* Layer 1: Client */}
        <rect x="30" y="55" width="840" height="100" rx="12" fill="url(#grad-client)" stroke="#3b82f6" strokeWidth="1.5"/>
        <text x="50" y="80" fill="#93c5fd" fontSize="13" fontWeight="600" fontFamily="IBM Plex Mono">CLIENT LAYER</text>
        <rect x="60" y="90" width="170" height="50" rx="8" fill="#0f172a" stroke="#3b82f6" strokeWidth="1"/>
        <text x="145" y="120" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">React 18 SPA</text>
        <rect x="250" y="90" width="170" height="50" rx="8" fill="#0f172a" stroke="#3b82f6" strokeWidth="1"/>
        <text x="335" y="120" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Chart.js Dashboard</text>
        <rect x="440" y="90" width="170" height="50" rx="8" fill="#0f172a" stroke="#3b82f6" strokeWidth="1"/>
        <text x="525" y="120" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Auth Module</text>
        <rect x="630" y="90" width="210" height="50" rx="8" fill="#0f172a" stroke="#3b82f6" strokeWidth="1"/>
        <text x="735" y="120" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Realtime Feed (WS)</text>

        {/* Arrow 1→2 */}
        <line x1="450" y1="155" x2="450" y2="180" stroke="#6b7280" strokeWidth="2" markerEnd="url(#arrowhead)"/>

        {/* Layer 2: CDN */}
        <rect x="30" y="185" width="840" height="90" rx="12" fill="url(#grad-cdn)" stroke="#22c55e" strokeWidth="1.5"/>
        <text x="50" y="210" fill="#86efac" fontSize="13" fontWeight="600" fontFamily="IBM Plex Mono">CDN / DEPLOY LAYER</text>
        <rect x="120" y="220" width="200" height="40" rx="8" fill="#052e16" stroke="#22c55e" strokeWidth="1"/>
        <text x="220" y="245" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Netlify CDN</text>
        <rect x="350" y="220" width="200" height="40" rx="8" fill="#052e16" stroke="#22c55e" strokeWidth="1"/>
        <text x="450" y="245" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Static Assets (Vite)</text>
        <rect x="580" y="220" width="200" height="40" rx="8" fill="#052e16" stroke="#22c55e" strokeWidth="1"/>
        <text x="680" y="245" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Edge Cache</text>

        {/* Arrow 2→3 */}
        <line x1="450" y1="275" x2="450" y2="300" stroke="#6b7280" strokeWidth="2" markerEnd="url(#arrowhead)"/>

        {/* Layer 3: API */}
        <rect x="30" y="305" width="840" height="100" rx="12" fill="url(#grad-api)" stroke="#ef4444" strokeWidth="1.5"/>
        <text x="50" y="330" fill="#fca5a5" fontSize="13" fontWeight="600" fontFamily="IBM Plex Mono">API LAYER</text>
        <rect x="60" y="340" width="185" height="50" rx="8" fill="#1c0a0a" stroke="#ef4444" strokeWidth="1"/>
        <text x="152" y="370" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Heuristic API</text>
        <rect x="260" y="340" width="155" height="50" rx="8" fill="#1c0a0a" stroke="#ef4444" strokeWidth="1"/>
        <text x="337" y="370" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Rate Limiter</text>
        <rect x="430" y="340" width="185" height="50" rx="8" fill="#1c0a0a" stroke="#ef4444" strokeWidth="1"/>
        <text x="522" y="370" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Input Validation</text>
        <rect x="630" y="340" width="210" height="50" rx="8" fill="#1c0a0a" stroke="#ef4444" strokeWidth="1"/>
        <text x="735" y="370" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">CORS Middleware</text>

        {/* Arrow 3→4 */}
        <line x1="450" y1="405" x2="450" y2="430" stroke="#6b7280" strokeWidth="2" markerEnd="url(#arrowhead)"/>

        {/* Layer 4: AI Engine */}
        <rect x="30" y="435" width="840" height="100" rx="12" fill="url(#grad-ai)" stroke="#a855f7" strokeWidth="1.5"/>
        <text x="50" y="460" fill="#d8b4fe" fontSize="13" fontWeight="600" fontFamily="IBM Plex Mono">AI ENGINE LAYER</text>
        <rect x="60" y="470" width="195" height="50" rx="8" fill="#1a0a2e" stroke="#a855f7" strokeWidth="1"/>
        <text x="157" y="500" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">NLP Pattern Engine</text>
        <rect x="270" y="470" width="165" height="50" rx="8" fill="#1a0a2e" stroke="#a855f7" strokeWidth="1"/>
        <text x="352" y="500" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Heuristic Scorer</text>
        <rect x="450" y="470" width="180" height="50" rx="8" fill="#1a0a2e" stroke="#a855f7" strokeWidth="1"/>
        <text x="540" y="500" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Ensemble Merger</text>
        <rect x="645" y="470" width="195" height="50" rx="8" fill="#1a0a2e" stroke="#a855f7" strokeWidth="1"/>
        <text x="742" y="500" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Category Classifier</text>

        {/* Arrow 4→5 */}
        <line x1="450" y1="535" x2="450" y2="560" stroke="#6b7280" strokeWidth="2" markerEnd="url(#arrowhead)"/>

        {/* Layer 5: Data */}
        <rect x="30" y="565" width="840" height="100" rx="12" fill="url(#grad-data)" stroke="#22c55e" strokeWidth="1.5"/>
        <text x="50" y="590" fill="#86efac" fontSize="13" fontWeight="600" fontFamily="IBM Plex Mono">DATA LAYER</text>
        <rect x="60" y="600" width="195" height="50" rx="8" fill="#052e16" stroke="#22c55e" strokeWidth="1"/>
        <text x="157" y="623" textAnchor="middle" fill="#e2e8f0" fontSize="11" fontFamily="Inter">Supabase PostgreSQL</text>
        <rect x="270" y="600" width="165" height="50" rx="8" fill="#052e16" stroke="#22c55e" strokeWidth="1"/>
        <text x="352" y="623" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Supabase Auth</text>
        <rect x="450" y="600" width="180" height="50" rx="8" fill="#052e16" stroke="#22c55e" strokeWidth="1"/>
        <text x="540" y="623" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Supabase Realtime</text>
        <rect x="645" y="600" width="195" height="50" rx="8" fill="#052e16" stroke="#22c55e" strokeWidth="1"/>
        <text x="742" y="623" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="Inter">Row-Level Security</text>

        {/* Bidirectional arrows on sides */}
        <line x1="20" y1="155" x2="20" y2="565" stroke="#3b4f6a" strokeWidth="1" strokeDasharray="4"/>
        <text x="12" y="360" fill="#6b7280" fontSize="10" fontFamily="IBM Plex Mono" transform="rotate(-90, 12, 360)">DATA FLOW</text>
      </svg>
    </div>
  );
}
