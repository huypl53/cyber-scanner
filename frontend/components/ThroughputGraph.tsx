'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Area, AreaChart, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Activity } from 'lucide-react';

interface DataPoint {
  timestamp: string;
  total: number;
  threats: number;
  normal: number;
}

interface ThroughputGraphProps {
  data: DataPoint[];
  maxDataPoints?: number;
}

export function ThroughputGraph({ data, maxDataPoints = 30 }: ThroughputGraphProps) {
  // Keep only the last N data points
  const chartData = data.slice(-maxDataPoints);

  return (
    <Card className="shadow-glow">
      <CardHeader className="border-b border-border">
        <CardTitle className="text-lg font-bold flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary animate-pulse-glow" />
          Traffic Throughput
          <span className="text-xs font-normal text-muted-foreground ml-2">
            (events/sec)
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        {chartData.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Waiting for traffic data...</p>
            </div>
          </div>
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.1} />
                  </linearGradient>
                  <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
                  </linearGradient>
                  <linearGradient id="colorNormal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                <XAxis
                  dataKey="timestamp"
                  stroke="#94a3b8"
                  fontSize={10}
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return date.toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: false,
                    });
                  }}
                />
                <YAxis stroke="#94a3b8" fontSize={10} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '0.5rem',
                    color: 'hsl(var(--popover-foreground))',
                  }}
                  labelFormatter={(value) => {
                    return new Date(value).toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: false,
                    });
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="threats"
                  stroke="#ef4444"
                  fillOpacity={1}
                  fill="url(#colorThreats)"
                  name="Threats"
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey="normal"
                  stroke="#10b981"
                  fillOpacity={1}
                  fill="url(#colorNormal)"
                  name="Normal"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 mt-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-destructive shadow-glow-red" />
            <span className="text-muted-foreground">Threat Traffic</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-status-safe shadow-glow-green" />
            <span className="text-muted-foreground">Normal Traffic</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
