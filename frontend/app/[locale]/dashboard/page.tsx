'use client';

import { useEffect, useState, useMemo } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { getPredictionStats, PredictionStats } from '@/lib/api';
import { StatCard } from '@/components/StatCard';
import { ThreatTable } from '@/components/ThreatTable';
import { AttackHeatmap } from '@/components/AttackHeatmap';
import ThreatDetectionChart from '@/components/ThreatDetectionChart';
import AttackDistributionChart from '@/components/AttackDistributionChart';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  Activity,
  Shield,
  AlertTriangle,
  TrendingUp,
  RefreshCw,
  Loader2,
} from 'lucide-react';

export default function DashboardPage() {
  const t = useTranslations('dashboard');
  const [stats, setStats] = useState<PredictionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadStats = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      const data = await getPredictionStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError('Failed to load statistics');
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadStats();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => loadStats(true), 30000);
    return () => clearInterval(interval);
  }, []);

  // Generate sparkline data for cards (mock data - you can enhance with real historical data)
  const generateSparkline = (current: number, variance: number = 20) => {
    return Array.from({ length: 12 }, () =>
      Math.max(0, current + (Math.random() - 0.5) * variance)
    );
  };

  // Prepare heatmap data (mock - you can enhance with real data)
  const heatmapData = useMemo(() => {
    if (!stats) return [];
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days.flatMap((day) =>
      Array.from({ length: 24 }, (_, hour) => ({
        day,
        hour,
        count: Math.floor(Math.random() * stats.total_attacks * 0.1),
      }))
    );
  }, [stats]);

  // Prepare threat table data
  const threatsData = useMemo(() => {
    if (!stats) return [];
    return stats.recent_predictions
      .filter((pred) => pred.threat_prediction.is_attack)
      .slice(0, 10)
      .map((pred) => ({
        id: String(pred.threat_prediction.id),
        timestamp: pred.threat_prediction.created_at,
        source_ip: '192.168.1.' + Math.floor(Math.random() * 255),
        attack_type: pred.attack_prediction?.attack_type_name || 'Unknown',
        confidence: pred.attack_prediction?.confidence || pred.threat_prediction.prediction_score,
        threat_score: pred.threat_prediction.prediction_score,
        status: Math.random() > 0.7 ? 'active' : Math.random() > 0.5 ? 'investigating' : 'mitigated',
      })) as any;
  }, [stats]);

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-[60vh] space-y-4">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="text-lg text-muted-foreground">{t('loading')}</p>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="shadow-glow-red">
        <CardContent className="p-6">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-8 w-8 text-destructive" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-destructive">{t('error.title')}</h3>
              <p className="text-muted-foreground">{error}</p>
            </div>
            <Button onClick={() => loadStats()} variant="destructive">
              <RefreshCw className="h-4 w-4 mr-2" />
              {t('error.retry')}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!stats) {
    return (
      <Card className="shadow-glow">
        <CardContent className="p-12 text-center">
          <Shield className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-xl font-semibold mb-2">{t('noData.title')}</h3>
          <p className="text-muted-foreground mb-4">
            {t('noData.description')}
          </p>
          <Button variant="default">
            <TrendingUp className="h-4 w-4 mr-2" />
            {t('noData.uploadButton')}
          </Button>
        </CardContent>
      </Card>
    );
  }

  const threatData = stats.recent_predictions.map((pred) => ({
    timestamp: pred.threat_prediction.created_at,
    score: pred.threat_prediction.prediction_score,
    isAttack: pred.threat_prediction.is_attack,
  }));

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gradient-cyan">
            {t('title')}
          </h1>
          <p className="text-muted-foreground mt-1 flex items-center gap-2">
            {t('subtitle')}
            <Badge variant="outline" className="animate-pulse">
              {t('liveBadge')}
            </Badge>
          </p>
        </div>
        <Button
          onClick={() => loadStats(true)}
          disabled={refreshing}
          className="shadow-glow"
        >
          {refreshing ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          {refreshing ? t('refreshing') : t('refresh')}
        </Button>
      </div>

      {/* KPI Cards with Sparklines */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title={t('stats.totalPredictions')}
          value={stats.total_predictions.toLocaleString()}
          trend={5.2}
          sparklineData={generateSparkline(stats.total_predictions / 12, stats.total_predictions * 0.1)}
          icon={Activity}
          variant="default"
        />
        <StatCard
          title={t('stats.attacksDetected')}
          value={stats.total_attacks.toLocaleString()}
          trend={-2.3}
          sparklineData={generateSparkline(stats.total_attacks / 12, stats.total_attacks * 0.15)}
          icon={AlertTriangle}
          variant="threat"
          badge={t('stats.criticalBadge')}
        />
        <StatCard
          title={t('stats.normalTraffic')}
          value={stats.total_normal.toLocaleString()}
          trend={3.1}
          sparklineData={generateSparkline(stats.total_normal / 12, stats.total_normal * 0.1)}
          icon={Shield}
          variant="success"
        />
        <StatCard
          title={t('stats.attackRate')}
          value={`${stats.attack_rate.toFixed(1)}%`}
          trend={stats.attack_rate > 50 ? 12.5 : -8.2}
          sparklineData={generateSparkline(stats.attack_rate, 10)}
          icon={TrendingUp}
          variant="warning"
        />
      </div>

      {/* Threat Detection & Attack Distribution Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {threatData.length > 0 && <ThreatDetectionChart data={threatData} />}
        {Object.keys(stats.attack_type_distribution).length > 0 && (
          <AttackDistributionChart distribution={stats.attack_type_distribution} />
        )}
      </div>

      {/* Attack Heatmap */}
      {heatmapData.length > 0 && <AttackHeatmap data={heatmapData} />}

      {/* Recent Threats Table with Actions */}
      {threatsData.length > 0 && <ThreatTable threats={threatsData} />}
    </div>
  );
}
