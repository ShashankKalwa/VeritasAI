export default function MetricCard({ title, value, subtitle, icon, color }) {
  return (
    <div className="metric-card" style={{ borderTopColor: color || '#dc2626' }}>
      <div className="metric-icon" style={{ color: color || '#dc2626' }}>
        {icon}
      </div>
      <div className="metric-info">
        <span className="metric-value">{value}</span>
        <span className="metric-title">{title}</span>
        {subtitle && <span className="metric-subtitle">{subtitle}</span>}
      </div>
    </div>
  );
}
