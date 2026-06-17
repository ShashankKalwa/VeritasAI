import { useState, useEffect } from 'react';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  ArcElement, PointElement, LineElement,
  Title, Tooltip, Legend, Filler
} from 'chart.js';
import MetricCard from '../components/MetricCard';
import { getStats } from '../lib/api';

ChartJS.register(
  CategoryScale, LinearScale, BarElement,
  ArcElement, PointElement, LineElement,
  Title, Tooltip, Legend, Filler
);

// v2 verdict taxonomy colors
const VERDICT_COLORS = {
  'Credible': '#22c55e',
  'Likely True': '#86efac',
  'Mixed / Misleading': '#eab308',
  'Likely False': '#f97316',
  'False': '#ef4444',
  'Insufficient Evidence': '#94a3b8',
  'Opinion': '#6366f1',
};

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (err) {
      console.error('Stats error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">
          <div className="spinner large"></div>
          <p>Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  const categoryBarData = {
    labels: stats.byCategory.map(c => c.category),
    datasets: [
      {
        label: 'False / Likely False',
        data: stats.byCategory.map(c => c.false),
        backgroundColor: 'rgba(239, 68, 68, 0.8)',
        borderColor: '#ef4444',
        borderWidth: 1,
        borderRadius: 4,
      },
      {
        label: 'Mixed / Misleading',
        data: stats.byCategory.map(c => c.mixed || 0),
        backgroundColor: 'rgba(234, 179, 8, 0.8)',
        borderColor: '#eab308',
        borderWidth: 1,
        borderRadius: 4,
      },
      {
        label: 'Credible / Likely True',
        data: stats.byCategory.map(c => c.credible),
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        borderColor: '#22c55e',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  // v2 verdict distribution doughnut
  const verdictDist = stats.verdictDistribution || {};
  const doughnutData = {
    labels: Object.keys(verdictDist).length > 0
      ? Object.keys(verdictDist)
      : ['False', 'Mixed / Misleading', 'Credible'],
    datasets: [{
      data: Object.keys(verdictDist).length > 0
        ? Object.values(verdictDist)
        : [stats.falseCount, stats.mixedCount || 0, stats.credibleCount],
      backgroundColor: Object.keys(verdictDist).length > 0
        ? Object.keys(verdictDist).map(k => (VERDICT_COLORS[k] || '#94a3b8') + 'cc')
        : ['rgba(239, 68, 68, 0.8)', 'rgba(234, 179, 8, 0.8)', 'rgba(34, 197, 94, 0.8)'],
      borderColor: Object.keys(verdictDist).length > 0
        ? Object.keys(verdictDist).map(k => VERDICT_COLORS[k] || '#94a3b8')
        : ['#ef4444', '#eab308', '#22c55e'],
      borderWidth: 2,
      hoverOffset: 8,
    }],
  };

  const confidenceData = {
    labels: Object.keys(stats.confidenceBuckets),
    datasets: [{
      label: 'Analyses',
      data: Object.values(stats.confidenceBuckets),
      borderColor: '#a855f7',
      backgroundColor: 'rgba(168, 85, 247, 0.2)',
      fill: true,
      tension: 0.4,
      pointBackgroundColor: '#a855f7',
      pointBorderColor: '#a855f7',
      pointRadius: 5,
    }],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#9ca3af', font: { family: 'IBM Plex Mono', size: 11 } }
      },
    },
    scales: {
      x: {
        ticks: { color: '#6b7280', font: { family: 'IBM Plex Mono', size: 10 } },
        grid: { color: 'rgba(107, 114, 128, 0.1)' }
      },
      y: {
        ticks: { color: '#6b7280', font: { family: 'IBM Plex Mono', size: 10 } },
        grid: { color: 'rgba(107, 114, 128, 0.1)' }
      },
    },
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: '#9ca3af', font: { family: 'IBM Plex Mono', size: 11 }, padding: 15 }
      },
    },
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Analytics Dashboard</h1>
        <p className="page-subtitle">Real-time insights from VeritasAI verification engine</p>
      </div>

      <div className="metrics-row">
        <MetricCard
          title="Total Analyses"
          value={stats.total}
          icon="📊"
          color="#3b82f6"
        />
        <MetricCard
          title="False / Likely False"
          value={stats.falseCount}
          subtitle={`${stats.total > 0 ? Math.round(stats.falseCount / stats.total * 100) : 0}% of total`}
          icon="⚠️"
          color="#ef4444"
        />
        <MetricCard
          title="Credible / Likely True"
          value={stats.credibleCount}
          subtitle={`${stats.total > 0 ? Math.round(stats.credibleCount / stats.total * 100) : 0}% of total`}
          icon="✅"
          color="#22c55e"
        />
        <MetricCard
          title="Avg Confidence"
          value={`${stats.avgConfidence}%`}
          icon="🎯"
          color="#a855f7"
        />
      </div>

      <div className="charts-grid">
        <div className="chart-card chart-wide">
          <h3 className="chart-title">Verification by Category</h3>
          <div className="chart-container">
            <Bar data={categoryBarData} options={chartOptions} />
          </div>
        </div>

        <div className="chart-card">
          <h3 className="chart-title">Verdict Distribution</h3>
          <div className="chart-container doughnut-container">
            <Doughnut data={doughnutData} options={doughnutOptions} />
          </div>
        </div>

        <div className="chart-card">
          <h3 className="chart-title">Confidence Distribution</h3>
          <div className="chart-container">
            <Line data={confidenceData} options={chartOptions} />
          </div>
        </div>
      </div>
    </div>
  );
}
