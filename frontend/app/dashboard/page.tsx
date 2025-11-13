'use client';

import { useEffect, useState } from 'react';
import { getPredictionStats, PredictionStats } from '@/lib/api';
import ThreatDetectionChart from '@/components/ThreatDetectionChart';
import AttackDistributionChart from '@/components/AttackDistributionChart';
import SelfHealingActionsTable from '@/components/SelfHealingActionsTable';
import PredictionHistoryTable from '@/components/PredictionHistoryTable';

export default function DashboardPage() {
  const [stats, setStats] = useState<PredictionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await getPredictionStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError('Failed to load statistics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-xl text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
        <button
          onClick={loadStats}
          className="mt-2 text-red-600 hover:text-red-800 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center text-gray-600">
        No data available. Upload some network traffic data to get started.
      </div>
    );
  }

  const threatData = stats.recent_predictions.map((pred) => ({
    timestamp: pred.threat_prediction.created_at,
    score: pred.threat_prediction.prediction_score,
    isAttack: pred.threat_prediction.is_attack,
  }));

  const actions = stats.recent_predictions
    .filter((pred) => pred.self_healing_action)
    .map((pred) => pred.self_healing_action!);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Overview of threat detection and attack classification</p>
        </div>
        <button
          onClick={loadStats}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-sm text-gray-600 mb-1">Total Predictions</p>
          <p className="text-3xl font-bold text-blue-600">{stats.total_predictions}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-sm text-gray-600 mb-1">Attacks Detected</p>
          <p className="text-3xl font-bold text-red-600">{stats.total_attacks}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-sm text-gray-600 mb-1">Normal Traffic</p>
          <p className="text-3xl font-bold text-green-600">{stats.total_normal}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-sm text-gray-600 mb-1">Attack Rate</p>
          <p className="text-3xl font-bold text-orange-600">{stats.attack_rate.toFixed(1)}%</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {threatData.length > 0 && <ThreatDetectionChart data={threatData} />}
        {Object.keys(stats.attack_type_distribution).length > 0 && (
          <AttackDistributionChart distribution={stats.attack_type_distribution} />
        )}
      </div>

      {/* Tables */}
      <div className="space-y-6">
        <PredictionHistoryTable predictions={stats.recent_predictions.slice(0, 20)} />
        {actions.length > 0 && <SelfHealingActionsTable actions={actions.slice(0, 20)} />}
      </div>
    </div>
  );
}
