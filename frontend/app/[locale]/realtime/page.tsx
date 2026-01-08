'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { useWebSocket } from '@/hooks/useWebSocket';
import { startTestStream } from '@/lib/api';
import { StatCard } from '@/components/StatCard';
import { TerminalLog } from '@/components/TerminalLog';
import { ThroughputGraph } from '@/components/ThroughputGraph';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  Activity,
  Shield,
  AlertTriangle,
  Zap,
  Play,
  Pause,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface RealtimePrediction {
  timestamp: string;
  traffic_data_id: number;
  threat_prediction: {
    prediction_score: number;
    is_attack: boolean;
    threshold: number;
  } | null;
  attack_prediction?: {
    attack_type_name: string;
    confidence: number;
  };
  self_healing_action?: {
    action_type: string;
    action_description: string;
  };
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export default function RealtimePage() {
  const t = useTranslations('realtime');
  const [predictions, setPredictions] = useState<RealtimePrediction[]>([]);
  const [streamActive, setStreamActive] = useState(false);
  const [throughputData, setThroughputData] = useState<Array<{
    timestamp: string;
    total: number;
    threats: number;
    normal: number;
  }>>([]);

  const handleMessage = useCallback((message: any) => {
    if (message.type === 'prediction') {
      setPredictions((prev) => [message.data, ...prev].slice(0, 100));
    }
  }, []);

  const { isConnected } = useWebSocket({
    url: `${WS_URL}/ws/realtime`,
    onMessage: handleMessage,
  });

  // Update throughput data every second
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date().toISOString();
      const lastSecondPredictions = predictions.filter(
        (p) => new Date(p.timestamp).getTime() > Date.now() - 1000
      );
      const threats = lastSecondPredictions.filter(
        (p) => p.threat_prediction?.is_attack
      ).length;
      const normal = lastSecondPredictions.length - threats;

      setThroughputData((prev) => [
        ...prev.slice(-29),
        {
          timestamp: now,
          total: lastSecondPredictions.length,
          threats,
          normal,
        },
      ]);
    }, 1000);

    return () => clearInterval(interval);
  }, [predictions]);

  const handleStartStream = async () => {
    try {
      setStreamActive(true);
      await startTestStream({
        count: 100,
        interval: 1.0,
        model_type: 'attack_classification',
      });
    } catch (error) {
      console.error('Failed to start stream:', error);
    } finally {
      setTimeout(() => setStreamActive(false), 5000);
    }
  };

  const stats = useMemo(() => {
    const total = predictions.length;
    const attacks = predictions.filter((p) => p.threat_prediction?.is_attack).length;
    const normal = total - attacks;
    const avgThreatScore = predictions.length > 0
      ? predictions.reduce((sum, p) => sum + (p.threat_prediction?.prediction_score || 0), 0) / predictions.length
      : 0;

    return { total, attacks, normal, avgThreatScore };
  }, [predictions]);

  // Convert predictions to terminal log entries
  const logEntries = useMemo(() => {
    return predictions.slice(0, 50).map((pred) => {
      const isAttack = pred.threat_prediction?.is_attack || pred.attack_prediction;
      const hasAction = !!pred.self_healing_action;

      if (hasAction) {
        return {
          timestamp: pred.timestamp,
          type: 'action' as const,
          message: pred.self_healing_action!.action_description,
          metadata: {
            score: pred.threat_prediction?.prediction_score,
          },
        };
      }

      return {
        timestamp: pred.timestamp,
        type: isAttack ? ('attack' as const) : ('normal' as const),
        message: isAttack
          ? `Attack detected from traffic_id ${pred.traffic_data_id}`
          : `Normal traffic analyzed - traffic_id ${pred.traffic_data_id}`,
        metadata: {
          score: pred.threat_prediction?.prediction_score,
          attackType: pred.attack_prediction?.attack_type_name,
          confidence: pred.attack_prediction?.confidence,
        },
      };
    });
  }, [predictions]);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header with Connection Status */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gradient-cyan">
            {t('title')}
          </h1>
          <p className="text-muted-foreground mt-1 flex items-center gap-2">
            {t('subtitle')}
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* Connection Status Badge */}
          <Card className={cn(
            'transition-all duration-300',
            isConnected ? 'shadow-glow-green' : 'shadow-glow-red'
          )}>
            <CardContent className="px-4 py-2 flex items-center gap-2">
              {isConnected ? (
                <>
                  <div className="h-3 w-3 rounded-full bg-status-safe animate-pulse-glow" />
                  <Wifi className="h-4 w-4 text-status-safe" />
                  <span className="text-sm font-medium text-status-safe">
                    {t('connected')}
                  </span>
                </>
              ) : (
                <>
                  <div className="h-3 w-3 rounded-full bg-destructive animate-pulse" />
                  <WifiOff className="h-4 w-4 text-destructive" />
                  <span className="text-sm font-medium text-destructive">
                    {t('disconnected')}
                  </span>
                </>
              )}
            </CardContent>
          </Card>

          {/* Start/Stop Stream Button */}
          <Button
            onClick={handleStartStream}
            disabled={streamActive || !isConnected}
            className={cn(
              'shadow-glow',
              streamActive && 'animate-pulse-glow'
            )}
          >
            {streamActive ? (
              <>
                <Pause className="h-4 w-4 mr-2 animate-pulse" />
                {t('streamActive')}
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                {t('startTestStream')}
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Live Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title={t('stats.eventsReceived')}
          value={stats.total.toLocaleString()}
          icon={Activity}
          variant="default"
          badge="LIVE"
        />
        <StatCard
          title={t('stats.threatsDetected')}
          value={stats.attacks.toLocaleString()}
          icon={AlertTriangle}
          variant="threat"
        />
        <StatCard
          title={t('stats.normalTraffic')}
          value={stats.normal.toLocaleString()}
          icon={Shield}
          variant="success"
        />
        <StatCard
          title={t('stats.avgThreatScore')}
          value={stats.avgThreatScore.toFixed(3)}
          icon={Zap}
          variant="warning"
        />
      </div>

      {/* Throughput Graph */}
      <ThroughputGraph data={throughputData} />

      {/* Terminal Log */}
      <TerminalLog entries={logEntries} maxHeight="500px" />
    </div>
  );
}
