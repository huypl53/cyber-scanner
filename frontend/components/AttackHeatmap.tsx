'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useMemo } from 'react';
import { Flame } from 'lucide-react';

interface AttackHeatmapProps {
  data: {
    hour: number;
    day: string;
    count: number;
  }[];
}

export function AttackHeatmap({ data }: AttackHeatmapProps) {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const hours = Array.from({ length: 24 }, (_, i) => i);

  const maxCount = useMemo(() => {
    return Math.max(...data.map((d) => d.count), 1);
  }, [data]);

  const getHeatColor = (count: number) => {
    const intensity = count / maxCount;
    if (intensity === 0) return 'bg-muted/30';
    if (intensity < 0.2) return 'bg-blue-900/50';
    if (intensity < 0.4) return 'bg-cyan-800/60';
    if (intensity < 0.6) return 'bg-orange-700/70';
    if (intensity < 0.8) return 'bg-red-700/80';
    return 'bg-red-600/90 shadow-glow-red';
  };

  const getCellData = (day: string, hour: number) => {
    return data.find((d) => d.day === day && d.hour === hour)?.count || 0;
  };

  return (
    <Card className="shadow-glow">
      <CardHeader className="border-b border-border">
        <CardTitle className="text-xl font-bold flex items-center gap-2">
          <Flame className="h-5 w-5 text-primary" />
          Attack Patterns <span className="text-muted-foreground text-sm font-normal">(by time)</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="space-y-2">
          {/* Hour Labels */}
          <div className="flex">
            <div className="w-12" />
            <div className="flex-1 grid grid-cols-24 gap-1">
              {hours.map((hour) => (
                <div
                  key={hour}
                  className="text-[10px] text-center text-muted-foreground font-mono"
                >
                  {hour % 6 === 0 ? hour : ''}
                </div>
              ))}
            </div>
          </div>

          {/* Heatmap Grid */}
          {days.map((day) => (
            <div key={day} className="flex items-center">
              <div className="w-12 text-xs font-medium text-muted-foreground">
                {day}
              </div>
              <div className="flex-1 grid grid-cols-24 gap-1">
                {hours.map((hour) => {
                  const count = getCellData(day, hour);
                  return (
                    <div
                      key={`${day}-${hour}`}
                      className={`h-6 rounded-sm transition-all duration-200 hover:scale-110 hover:z-10 relative group ${getHeatColor(
                        count
                      )}`}
                      title={`${day} ${hour}:00 - ${count} attacks`}
                    >
                      {/* Tooltip on hover */}
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
                        {count} attacks
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="mt-6 flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Less activity</span>
          <div className="flex gap-1">
            {[0, 0.2, 0.4, 0.6, 0.8, 1].map((intensity, i) => (
              <div
                key={i}
                className={`w-4 h-4 rounded-sm ${getHeatColor(intensity * maxCount)}`}
              />
            ))}
          </div>
          <span className="text-muted-foreground">More activity</span>
        </div>
      </CardContent>
    </Card>
  );
}
