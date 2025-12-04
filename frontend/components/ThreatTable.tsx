'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  Shield,
  AlertTriangle,
  Eye,
  Ban,
  FileText,
  ChevronRight,
} from 'lucide-react';

interface Threat {
  id: string;
  timestamp: string;
  source_ip?: string;
  attack_type?: string;
  confidence: number;
  threat_score: number;
  status: 'active' | 'mitigated' | 'investigating';
}

interface ThreatTableProps {
  threats: Threat[];
}

export function ThreatTable({ threats }: ThreatTableProps) {
  const getSeverityBadge = (score: number) => {
    if (score >= 0.9) return { label: 'CRITICAL', variant: 'destructive' as const, icon: AlertTriangle };
    if (score >= 0.7) return { label: 'HIGH', variant: 'destructive' as const, icon: AlertTriangle };
    if (score >= 0.5) return { label: 'MEDIUM', variant: 'outline' as const, icon: Shield };
    return { label: 'LOW', variant: 'secondary' as const, icon: Shield };
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-destructive animate-pulse-glow';
      case 'mitigated':
        return 'text-status-safe';
      case 'investigating':
        return 'text-status-warning';
      default:
        return 'text-muted-foreground';
    }
  };

  return (
    <Card className="shadow-glow">
      <CardHeader className="border-b border-border">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-bold text-gradient-cyan flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Recent Threats
          </CardTitle>
          <Badge variant="destructive" className="animate-pulse">
            {threats.length} Active
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">
                  Severity
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">
                  Timestamp
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">
                  Source IP
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">
                  Attack Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">
                  Confidence
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {threats.map((threat, index) => {
                const severity = getSeverityBadge(threat.threat_score);
                const SeverityIcon = severity.icon;

                return (
                  <tr
                    key={threat.id || index}
                    className="hover:bg-muted/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Badge variant={severity.variant} className="flex items-center gap-1 w-fit">
                        <SeverityIcon className="h-3 w-3" />
                        {severity.label}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-mono">
                        {new Date(threat.timestamp).toLocaleString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                        })}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-mono text-primary">
                        {threat.source_ip || 'N/A'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm">
                        {threat.attack_type || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className={cn(
                              'h-full transition-all',
                              threat.confidence >= 0.8
                                ? 'bg-status-safe'
                                : threat.confidence >= 0.6
                                ? 'bg-status-warning'
                                : 'bg-destructive'
                            )}
                            style={{ width: `${threat.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono">
                          {(threat.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={cn(
                          'text-xs font-semibold uppercase',
                          getStatusColor(threat.status)
                        )}
                      >
                        {threat.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8 w-8 p-0"
                          title="Investigate"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8 w-8 p-0"
                          title="Block IP"
                        >
                          <Ban className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8 w-8 p-0"
                          title="View Details"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
