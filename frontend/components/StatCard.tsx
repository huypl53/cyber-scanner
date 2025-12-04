'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus, LucideIcon } from 'lucide-react';
import { Line, LineChart, ResponsiveContainer } from 'recharts';

interface StatCardProps {
  title: string;
  value: string | number;
  trend?: number; // Percentage change
  sparklineData?: number[];
  icon?: LucideIcon;
  variant?: 'default' | 'threat' | 'success' | 'warning';
  badge?: string;
}

const variantStyles = {
  default: {
    text: 'text-primary',
    glow: 'shadow-glow',
    bg: 'from-primary/20 to-primary/5',
    sparkline: '#06b6d4',
  },
  threat: {
    text: 'text-destructive',
    glow: 'shadow-glow-red',
    bg: 'from-destructive/20 to-destructive/5',
    sparkline: '#ef4444',
  },
  success: {
    text: 'text-status-safe',
    glow: 'shadow-glow-green',
    bg: 'from-green-500/20 to-green-500/5',
    sparkline: '#10b981',
  },
  warning: {
    text: 'text-status-warning',
    glow: 'shadow-[0_0_8px_rgba(245,158,11,0.5)]',
    bg: 'from-amber-500/20 to-amber-500/5',
    sparkline: '#f59e0b',
  },
};

export function StatCard({
  title,
  value,
  trend,
  sparklineData,
  icon: Icon,
  variant = 'default',
  badge,
}: StatCardProps) {
  const styles = variantStyles[variant];

  const getTrendIcon = () => {
    if (trend === undefined) return null;
    if (trend > 0) return <TrendingUp className="h-4 w-4" />;
    if (trend < 0) return <TrendingDown className="h-4 w-4" />;
    return <Minus className="h-4 w-4" />;
  };

  const getTrendColor = () => {
    if (trend === undefined) return '';
    if (trend > 0) return 'text-green-500';
    if (trend < 0) return 'text-red-500';
    return 'text-muted-foreground';
  };

  const chartData = sparklineData?.map((value, index) => ({
    value,
    index,
  })) || [];

  return (
    <Card className={cn('relative overflow-hidden transition-all duration-300 hover:scale-105', styles.glow)}>
      <div className={cn('absolute inset-0 bg-gradient-to-br opacity-50', styles.bg)} />

      <CardContent className="relative p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <div className="flex items-center gap-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                {title}
              </p>
              {badge && (
                <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                  {badge}
                </Badge>
              )}
            </div>
            <div className="flex items-baseline gap-2">
              <h3 className={cn('text-3xl font-bold tabular-nums', styles.text)}>
                {value}
              </h3>
              {trend !== undefined && (
                <div className={cn('flex items-center gap-1 text-xs font-medium', getTrendColor())}>
                  {getTrendIcon()}
                  <span>{Math.abs(trend)}%</span>
                </div>
              )}
            </div>
          </div>
          {Icon && (
            <div className={cn('rounded-lg p-2 bg-card/50', styles.glow)}>
              <Icon className={cn('h-5 w-5', styles.text)} />
            </div>
          )}
        </div>

        {sparklineData && sparklineData.length > 0 && (
          <div className="mt-4 h-12">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={styles.sparkline}
                  strokeWidth={2}
                  dot={false}
                  animationDuration={300}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
