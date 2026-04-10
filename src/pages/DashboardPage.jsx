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
        label: 'Fake',
        data: stats.byCategory.map(c => c.fake),
        backgroundColor: 'rgba(220, 38, 38, 0.8)',
        borderColor: '#dc2626',
        borderWidth: 1,
        borderRadius: 4,
      },
      {
        label: 'Real',
        data: stats.byCategory.map(c => c.real),
        backgroundColor: 'rgba(22, 163, 74, 0.8)',
        borderColor: '#16a34a',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const doughnutData = {
    labels: ['Fake', 'Real'],
    datasets: [{
      data: [stats.fakeCount, stats.realCount],
      backgroundColor: ['rgba(220, 38, 38, 0.8)', 'rgba(22, 163, 74, 0.8)'],
      borderColor: ['#dc2626', '#16a34a'],
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
        labels: { color: '#9ca3af', font: { family: 'IBM Plex Mono', size: 12 }, padding: 20 }
      },
    },
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Analytics Dashboard</h1>
        <p className="page-subtitle">Real-time insights from VeritasAI detection engine</p>
      </div>

      <div className="metrics-row">
        <MetricCard
          title="Total Analyses"
          value={stats.total}
          icon="📊"
          color="#3b82f6"
        />
        <MetricCard
          title="Fake Detected"
          value={stats.fakeCount}
          subtitle={`${stats.total > 0 ? Math.round(stats.fakeCount / stats.total * 100) : 0}% of total`}
          icon="⚠️"
          color="#dc2626"
        />
        <MetricCard
          title="Real Verified"
          value={stats.realCount}
          subtitle={`${stats.total > 0 ? Math.round(stats.realCount / stats.total * 100) : 0}% of total`}
          icon="✅"
          color="#16a34a"
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
          <h3 className="chart-title">Detection by Category</h3>
          <div className="chart-container">
            <Bar data={categoryBarData} options={chartOptions} />
          </div>
        </div>

        <div className="chart-card">
          <h3 className="chart-title">Fake vs Real Distribution</h3>
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
