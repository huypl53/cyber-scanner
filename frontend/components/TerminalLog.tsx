'use client';

import { useTranslations, useLocale } from 'next-intl';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Terminal, AlertTriangle, Shield, Zap } from 'lucide-react';
import { useEffect, useRef } from 'react';

interface LogEntry {
  timestamp: string;
  type: 'attack' | 'normal' | 'action' | 'system';
  message: string;
  metadata?: {
    score?: number;
    attackType?: string;
    confidence?: number;
  };
}

interface TerminalLogProps {
  entries: LogEntry[];
  maxHeight?: string;
}

export function TerminalLog({ entries, maxHeight = '600px' }: TerminalLogProps) {
  const t = useTranslations('realtime.feed');
  const locale = useLocale();
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [entries]);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'attack':
        return <AlertTriangle className="h-3 w-3" />;
      case 'normal':
        return <Shield className="h-3 w-3" />;
      case 'action':
        return <Zap className="h-3 w-3" />;
      default:
        return <Terminal className="h-3 w-3" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'attack':
        return 'text-destructive';
      case 'normal':
        return 'text-status-safe';
      case 'action':
        return 'text-status-warning';
      default:
        return 'text-primary';
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'attack':
        return t('badge.threat');
      case 'normal':
        return t('badge.normal');
      case 'action':
        return t('badge.action');
      default:
        return t('badge.system');
    }
  };

  return (
    <Card className="shadow-glow bg-terminal-bg">
      <CardHeader className="border-b border-border bg-card/50">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <Terminal className="h-5 w-5 text-primary animate-pulse-glow" />
            <span className="font-mono">{t('title')}</span>
          </CardTitle>
          <Badge variant="outline" className="animate-pulse">
            <div className="h-2 w-2 rounded-full bg-status-safe mr-2 animate-pulse-glow" />
            {t('streaming')}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div
          className="overflow-y-auto font-mono text-xs terminal-text bg-terminal-bg"
          style={{ maxHeight }}
        >
          {entries.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <Terminal className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="font-mono">{t('waitingForData')}</p>
              <p className="text-[10px] mt-2 opacity-70">
                {t('startStreamHint')}
              </p>
            </div>
          ) : (
            <div className="p-4 space-y-1">
              {entries.map((entry, index) => (
                <div
                  key={index}
                  className={cn(
                    'py-1 px-2 rounded transition-all duration-200 hover:bg-muted/30 animate-slide-in-right',
                    entry.type === 'attack' && 'bg-destructive/10'
                  )}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-muted-foreground opacity-70">
                      [{new Date(entry.timestamp).toLocaleTimeString(locale, {
                        hour12: false,
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        fractionalSecondDigits: 3,
                      })}]
                    </span>
                    <div className={cn('flex items-center gap-1', getTypeColor(entry.type))}>
                      {getTypeIcon(entry.type)}
                      <Badge
                        variant={entry.type === 'attack' ? 'destructive' : 'outline'}
                        className="text-[9px] px-1 py-0 h-4"
                      >
                        {getTypeBadge(entry.type)}
                      </Badge>
                    </div>
                    <span className="flex-1">{entry.message}</span>
                  </div>
                  {entry.metadata && (
                    <div className="mt-1 ml-32 text-[10px] text-muted-foreground space-y-0.5">
                      {entry.metadata.score !== undefined && (
                        <div>
                          <span className="text-primary">{t('metadata.score')}:</span>{' '}
                          <span className="text-terminal-accent">
                            {entry.metadata.score.toFixed(4)}
                          </span>
                        </div>
                      )}
                      {entry.metadata.attackType && (
                        <div>
                          <span className="text-primary">{t('metadata.type')}:</span>{' '}
                          <span className="text-terminal-error">
                            {entry.metadata.attackType}
                          </span>
                        </div>
                      )}
                      {entry.metadata.confidence !== undefined && (
                        <div>
                          <span className="text-primary">{t('metadata.confidence')}:</span>{' '}
                          <span className="text-terminal-success">
                            {(entry.metadata.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
