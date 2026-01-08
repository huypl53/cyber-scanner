'use client';

import { useTranslations, useLocale } from 'next-intl';
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
  const t = useTranslations('dashboard.threats');
  const locale = useLocale();

  const getSeverityBadge = (score: number) => {
    if (score >= 0.9) return { label: t('severity.critical'), variant: 'destructive' as const, icon: AlertTriangle };
    if (score >= 0.7) return { label: t('severity.high'), variant: 'destructive' as const, icon: AlertTriangle };
    if (score >= 0.5) return { label: t('severity.medium'), variant: 'outline' as const, icon: Shield };
    return { label: t('severity.low'), variant: 'secondary' as const, icon: Shield };
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active':
        return t('status.active');
      case 'mitigated':
        return t('status.mitigated');
      case 'investigating':
        return t('status.investigating');
      default:
        return status;
    }
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
            {t('title')}
          </CardTitle>
          <Badge variant="destructive" className="animate-pulse">
            {threats.length} {t('active')}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">
                  {t('table.severity')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">
                  {t('table.timestamp')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">
                  {t('table.sourceIp')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">
                  {t('table.attackType')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">
                  {t('table.confidence')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">
                  {t('table.status')}
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground uppercase">
                  {t('table.actions')}
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
                        {new Date(threat.timestamp).toLocaleString(locale, {
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
                        {getStatusLabel(threat.status)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8 w-8 p-0"
                          title={t('actions.investigate')}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8 w-8 p-0"
                          title={t('actions.blockIp')}
                        >
                          <Ban className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8 w-8 p-0"
                          title={t('actions.viewDetails')}
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
