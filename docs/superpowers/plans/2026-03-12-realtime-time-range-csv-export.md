# Realtime Time Range Selector + CSV Export — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a time range selector toolbar and CSV export to the realtime page, allowing users to select a capture window (up to 2h) and download traffic data as CSV.

**Architecture:** New backend GET endpoint queries TrafficData by time range and streams CSV. New frontend toolbar component with preset/custom range selection and export dropdown with confirmation dialog. Backend and frontend are fully independent tasks.

**Tech Stack:** FastAPI, SQLAlchemy, Python csv/io modules, React, shadcn/ui (Button, DropdownMenu, AlertDialog), next-intl

**Spec:** `docs/superpowers/specs/2026-03-12-realtime-time-range-csv-export-design.md`

---

## Chunk 1: Backend Export Endpoint

### Task 1: Create export route

**Files:**
- Create: `backend/app/api/routes/export.py`

- [ ] **Step 1: Create the export route file**

```python
"""
Export API endpoints.
Allows exporting realtime traffic data as CSV.
"""
import csv
import io
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.database import TrafficData, ThreatPrediction, AttackPrediction
from app.models.model_loaders import (
    ATTACK_CLASSIFICATION_FEATURES,
    THREAT_DETECTION_FEATURES,
)

router = APIRouter()

MAX_RANGE = timedelta(hours=2)


def _parse_dt(value: str) -> datetime:
    """Parse ISO datetime string, ensuring timezone-aware UTC."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("/export/realtime")
async def export_realtime(
    start: str = Query(..., description="ISO 8601 start time"),
    end: str = Query(..., description="ISO 8601 end time"),
    format: str = Query("features_only", regex="^(features_only|with_predictions)$"),
    count_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Export realtime traffic data as CSV or return count for preview."""
    try:
        start_dt = _parse_dt(start)
        end_dt = _parse_dt(end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO 8601.")

    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="end must be after start")

    if (end_dt - start_dt) > MAX_RANGE:
        raise HTTPException(status_code=400, detail="Time range exceeds 2-hour maximum")

    query = db.query(TrafficData).filter(
        TrafficData.created_at >= start_dt,
        TrafficData.created_at <= end_dt,
        TrafficData.source == "realtime",
    ).order_by(TrafficData.created_at.asc())

    if count_only:
        count = query.count()
        result = {
            "count": count,
            "time_range": {"start": start, "end": end},
        }
        if count > 10000:
            result["warning"] = "Large export"
        if count == 0:
            raise HTTPException(status_code=404, detail="No data found in this time range")
        return result

    records = query.all()
    if not records:
        raise HTTPException(status_code=404, detail="No data found in this time range")

    # Determine feature set from first record
    features = records[0].features or {}
    feature_count = len(features)
    if feature_count >= 35:
        feature_names = ATTACK_CLASSIFICATION_FEATURES
    else:
        feature_names = THREAT_DETECTION_FEATURES

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)

    headers = list(feature_names)
    if format == "with_predictions":
        headers += ["is_attack", "prediction_score", "attack_type_name", "confidence"]
    writer.writerow(headers)

    # Batch-load predictions if needed
    record_ids = [r.id for r in records]
    threat_map = {}
    attack_map = {}
    if format == "with_predictions":
        threats = db.query(ThreatPrediction).filter(
            ThreatPrediction.traffic_data_id.in_(record_ids)
        ).all()
        threat_map = {t.traffic_data_id: t for t in threats}

        attacks = db.query(AttackPrediction).filter(
            AttackPrediction.traffic_data_id.in_(record_ids)
        ).all()
        attack_map = {a.traffic_data_id: a for a in attacks}

    for record in records:
        row = [record.features.get(f, "") for f in feature_names]
        if format == "with_predictions":
            tp = threat_map.get(record.id)
            ap = attack_map.get(record.id)
            row += [
                tp.is_attack if tp else "",
                tp.prediction_score if tp else "",
                ap.attack_type_name if ap else "",
                ap.confidence if ap else "",
            ]
        writer.writerow(row)

    output.seek(0)
    filename = f"realtime-export-{start_dt.strftime('%Y%m%dT%H%M%S')}-{end_dt.strftime('%Y%m%dT%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/api/routes/export.py
git commit -m "feat: add realtime CSV export endpoint"
```

### Task 2: Register export router in main.py

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add import and include_router**

Add to the router imports (near line 12):
```python
from app.api.routes import upload, predictions, websocket, config, models, health, export
```

Add after the test_producer router include (near line 68):
```python
app.include_router(export.router, prefix=settings.API_V1_PREFIX, tags=["export"])
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: register export router"
```

---

## Chunk 2: Frontend — API Functions + Translations

### Task 3: Add export API functions

**Files:**
- Modify: `frontend/lib/api.ts`

- [ ] **Step 1: Add two new functions after `stopTestStream`**

```typescript
// Get export record count for preview
export const getExportCount = async (
  start: string,
  end: string,
  format: string
): Promise<{ count: number; warning?: string; time_range: { start: string; end: string } }> => {
  const response = await api.get('/api/v1/export/realtime', {
    params: { start, end, format, count_only: true },
  });
  return response.data;
};

// Build export download URL
export const getExportUrl = (start: string, end: string, format: string): string => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const params = new URLSearchParams({ start, end, format, count_only: 'false' });
  return `${baseUrl}/api/v1/export/realtime?${params.toString()}`;
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/lib/api.ts
git commit -m "feat: add export count and URL API functions"
```

### Task 4: Add translation keys

**Files:**
- Modify: `frontend/messages/en.json`
- Modify: `frontend/messages/vi.json`

- [ ] **Step 1: Add `realtime.export` section to en.json**

Add after the `realtime.feed` section:

```json
"export": {
  "preset1m": "1m",
  "preset5m": "5m",
  "preset15m": "15m",
  "preset30m": "30m",
  "preset1h": "1h",
  "preset2h": "2h",
  "custom": "Custom",
  "from": "From",
  "to": "To",
  "apply": "Apply",
  "exportBtn": "Export",
  "featuresOnly": "Features Only (CSV)",
  "withPredictions": "With Predictions (CSV)",
  "confirmTitle": "Export Data",
  "confirmMessage": "Found {count} records from {start} to {end}.",
  "confirmLargeWarning": "This is a large export and may take a moment.",
  "cancel": "Cancel",
  "export": "Export",
  "selectRange": "Select a time range first",
  "invalidRange": "End must be after start",
  "rangeTooLarge": "Range cannot exceed 2 hours",
  "noData": "No data found in this time range"
}
```

- [ ] **Step 2: Add `realtime.export` section to vi.json**

```json
"export": {
  "preset1m": "1p",
  "preset5m": "5p",
  "preset15m": "15p",
  "preset30m": "30p",
  "preset1h": "1g",
  "preset2h": "2g",
  "custom": "Tùy chỉnh",
  "from": "Từ",
  "to": "Đến",
  "apply": "Áp dụng",
  "exportBtn": "Xuất",
  "featuresOnly": "Chỉ Đặc trưng (CSV)",
  "withPredictions": "Kèm Dự đoán (CSV)",
  "confirmTitle": "Xuất Dữ liệu",
  "confirmMessage": "Tìm thấy {count} bản ghi từ {start} đến {end}.",
  "confirmLargeWarning": "Đây là bản xuất lớn, có thể mất một lúc.",
  "cancel": "Hủy",
  "export": "Xuất",
  "selectRange": "Chọn khoảng thời gian trước",
  "invalidRange": "Thời gian kết thúc phải sau thời gian bắt đầu",
  "rangeTooLarge": "Khoảng thời gian không được vượt quá 2 giờ",
  "noData": "Không tìm thấy dữ liệu trong khoảng thời gian này"
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/messages/en.json frontend/messages/vi.json
git commit -m "feat: add export translation keys (en + vi)"
```

---

## Chunk 3: Frontend — TimeRangeToolbar Component + Page Integration

### Task 5: Create TimeRangeToolbar component

**Files:**
- Create: `frontend/components/TimeRangeToolbar.tsx`

- [ ] **Step 1: Create the component**

```tsx
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
    // Pre-fill with last hour
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

function toLocalDatetimeString(date: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/TimeRangeToolbar.tsx
git commit -m "feat: add TimeRangeToolbar component with presets, custom range, and export"
```

### Task 6: Integrate toolbar into realtime page

**Files:**
- Modify: `frontend/app/[locale]/realtime/page.tsx`

- [ ] **Step 1: Add import**

Add with other component imports:
```typescript
import { TimeRangeToolbar } from '@/components/TimeRangeToolbar';
```

- [ ] **Step 2: Add toolbar between ThroughputGraph and TerminalLog**

Replace:
```tsx
      {/* Throughput Graph */}
      <ThroughputGraph data={throughputData} />

      {/* Terminal Log */}
```

With:
```tsx
      {/* Throughput Graph */}
      <ThroughputGraph data={throughputData} />

      {/* Time Range & Export Toolbar */}
      <TimeRangeToolbar />

      {/* Terminal Log */}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app/\[locale\]/realtime/page.tsx
git commit -m "feat: add TimeRangeToolbar to realtime page"
```

---

## Chunk 4: Build & Verify

### Task 7: Docker build and manual verification

- [ ] **Step 1: Rebuild and start containers**

```bash
docker-compose -f docker-compose.full.yml up -d --build
```

- [ ] **Step 2: Check for build errors in logs**

```bash
docker-compose -f docker-compose.full.yml logs --tail=30 backend
docker-compose -f docker-compose.full.yml logs --tail=30 frontend
```

- [ ] **Step 3: Verify export endpoint responds**

```bash
curl -s "http://localhost:8000/api/v1/export/realtime?start=2026-01-01T00:00:00Z&end=2026-01-01T01:00:00Z&format=features_only&count_only=true" | python3 -m json.tool
```

Expected: 404 "No data found" (no realtime data yet) or a count response.

- [ ] **Step 4: Final commit if any fixes needed**
