'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Download, ChevronDown, Clock, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getExportCount, getExportUrl } from '@/lib/api';

interface PresetOption {
  labelKey: string;
  minutes: number;
}

const PRESETS: PresetOption[] = [
  { labelKey: 'preset1m', minutes: 1 },
  { labelKey: 'preset5m', minutes: 5 },
  { labelKey: 'preset15m', minutes: 15 },
  { labelKey: 'preset30m', minutes: 30 },
  { labelKey: 'preset1h', minutes: 60 },
  { labelKey: 'preset2h', minutes: 120 },
];

function toLocalDatetimeString(date: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function TimeRangeToolbar() {
  const t = useTranslations('realtime.export');

  const [activePreset, setActivePreset] = useState<number | null>(null);
  const [showCustom, setShowCustom] = useState(false);
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [error, setError] = useState('');

  // Export confirmation state
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState('features_only');
  const [exportCount, setExportCount] = useState(0);
  const [exportWarning, setExportWarning] = useState('');
  const [exportLoading, setExportLoading] = useState(false);
  const [exportStart, setExportStart] = useState('');
  const [exportEnd, setExportEnd] = useState('');

  const getTimeRange = (): { start: string; end: string } | null => {
    if (showCustom && customStart && customEnd) {
      return {
        start: new Date(customStart).toISOString(),
        end: new Date(customEnd).toISOString(),
      };
    }
    if (activePreset !== null) {
      const end = new Date();
      const start = new Date(end.getTime() - activePreset * 60 * 1000);
      return { start: start.toISOString(), end: end.toISOString() };
    }
    return null;
  };

  const validateCustomRange = (): boolean => {
    setError('');
    if (!customStart || !customEnd) return false;
    const start = new Date(customStart);
    const end = new Date(customEnd);
    if (end <= start) {
      setError(t('invalidRange'));
      return false;
    }
    const diffMs = end.getTime() - start.getTime();
    if (diffMs > 2 * 60 * 60 * 1000) {
      setError(t('rangeTooLarge'));
      return false;
    }
    return true;
  };

  const handlePresetClick = (minutes: number) => {
    if (activePreset === minutes) {
      setActivePreset(null);
    } else {
      setActivePreset(minutes);
      setShowCustom(false);
      setError('');
    }
  };

  const handleCustomClick = () => {
    setShowCustom(!showCustom);
    setActivePreset(null);
    setError('');
    if (!customStart) {
      const now = new Date();
      const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
      setCustomEnd(toLocalDatetimeString(now));
      setCustomStart(toLocalDatetimeString(oneHourAgo));
    }
  };

  const handleExportClick = async (format: string) => {
    const range = getTimeRange();
    if (!range) {
      setError(t('selectRange'));
      return;
    }
    if (showCustom && !validateCustomRange()) return;

    setExportLoading(true);
    setExportFormat(format);
    try {
      const result = await getExportCount(range.start, range.end, format);
      setExportCount(result.count);
      setExportWarning(result.warning || '');
      setExportStart(range.start);
      setExportEnd(range.end);
      setConfirmOpen(true);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(detail || t('noData'));
    } finally {
      setExportLoading(false);
    }
  };

  const handleConfirmExport = () => {
    const url = getExportUrl(exportStart, exportEnd, exportFormat);
    window.open(url, '_blank');
    setConfirmOpen(false);
  };

  const hasRange = activePreset !== null || (showCustom && customStart && customEnd);

  const formatTime = (iso: string) => {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  return (
    <>
      <Card>
        <CardContent className="py-3 px-4">
          <div className="flex flex-wrap items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />

            {/* Preset buttons */}
            {PRESETS.map((preset) => (
              <Button
                key={preset.minutes}
                variant={activePreset === preset.minutes ? 'default' : 'outline'}
                size="sm"
                onClick={() => handlePresetClick(preset.minutes)}
                className="h-7 px-2 text-xs"
              >
                {t(preset.labelKey)}
              </Button>
            ))}

            {/* Custom button */}
            <Button
              variant={showCustom ? 'default' : 'outline'}
              size="sm"
              onClick={handleCustomClick}
              className="h-7 px-2 text-xs"
            >
              {t('custom')}
            </Button>

            <div className="flex-1" />

            {/* Export dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!hasRange || exportLoading}
                  className="h-7 gap-1 text-xs"
                >
                  <Download className="h-3 w-3" />
                  {t('exportBtn')}
                  <ChevronDown className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleExportClick('features_only')}>
                  {t('featuresOnly')}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExportClick('with_predictions')}>
                  {t('withPredictions')}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Custom range inputs */}
          {showCustom && (
            <div className="flex flex-wrap items-center gap-3 mt-3 pt-3 border-t border-border">
              <label className="text-xs text-muted-foreground">{t('from')}</label>
              <input
                type="datetime-local"
                value={customStart}
                onChange={(e) => { setCustomStart(e.target.value); setError(''); }}
                className="h-7 rounded border border-border bg-background px-2 text-xs"
              />
              <label className="text-xs text-muted-foreground">{t('to')}</label>
              <input
                type="datetime-local"
                value={customEnd}
                onChange={(e) => { setCustomEnd(e.target.value); setError(''); }}
                className="h-7 rounded border border-border bg-background px-2 text-xs"
              />
            </div>
          )}

          {/* Error message */}
          {error && (
            <p className="text-xs text-destructive mt-2">{error}</p>
          )}
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('confirmTitle')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('confirmMessage', {
                count: exportCount.toLocaleString(),
                start: formatTime(exportStart),
                end: formatTime(exportEnd),
              })}
              {exportWarning && (
                <span className="flex items-center gap-1 mt-2 text-status-warning">
                  <AlertTriangle className="h-3 w-3" />
                  {t('confirmLargeWarning')}
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('cancel')}</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmExport}>
              {t('export')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
