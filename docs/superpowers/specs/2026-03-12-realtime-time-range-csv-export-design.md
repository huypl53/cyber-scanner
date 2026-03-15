# Realtime Page: Time Range Selector + CSV Export

## Overview

Add a time range selector and CSV export to the `/realtime` page so users can select a capture window (up to 2 hours) and download traffic data as CSV — either raw features only (re-uploadable) or with prediction results appended.

## Constraints

- Max time range: **2 hours**, enforced server-side
- CSV "features only" format must match the upload CSV format exactly (round-trippable)
- Export is a backend query against the database, not a frontend data dump (frontend only holds ~100 predictions in memory)

## Backend

### New file: `backend/app/api/routes/export.py`

Single endpoint with dual mode:

```
GET /api/v1/export/realtime
  ?start=<ISO datetime>
  &end=<ISO datetime>
  &format=features_only | with_predictions
  &count_only=true | false
```

**Parameters:**
- `start`, `end` — ISO 8601 timestamps defining the range
- `format` — `features_only` returns only the feature columns (matches upload CSV); `with_predictions` appends `is_attack`, `prediction_score`, `attack_type_name`, `confidence`
- `count_only` — when `true`, returns JSON `{ count, time_range: { start, end } }` for the preview step; when `false`, returns a `text/csv` file download

**Validation:**
- `end - start` must be <= 2 hours; return 400 otherwise
- `start` must be before `end`
- Return 404 if no records found in range

**Query:**
- Query `TrafficData` filtered by `created_at BETWEEN start AND end` where `source = 'realtime'`
- For `with_predictions`: LEFT JOIN `ThreatPrediction` and `AttackPrediction` on `traffic_data_id`
- Order by `created_at ASC`

**CSV generation:**
- Use Python's `csv` module writing to `io.StringIO`
- For `features_only`: column headers match the feature names from the model (42 attack classification features or 10 threat detection features, based on what's in the `features` JSON column)
- For `with_predictions`: append columns `is_attack`, `prediction_score`, `attack_type_name`, `confidence`
- Return as `StreamingResponse` with `Content-Disposition: attachment; filename=realtime-export-{start}-{end}.csv`

**Router registration:**
- Register in `backend/app/main.py` alongside existing routers

### Row limit safety

If count exceeds 10,000 rows, the count_only response includes a `warning: "Large export"` field. The frontend can display this in the confirmation dialog. The download endpoint still works — no hard row cap beyond the 2-hour time limit.

## Frontend

### New component: `frontend/components/TimeRangeToolbar.tsx`

A horizontal toolbar row placed above the `<TerminalLog>` on the realtime page.

**Layout:**
```
[ 1m ] [ 5m ] [ 15m ] [ 30m ] [ 1h ] [ 2h ] [ Custom ▾ ]    [ Export ▾ ]
                                         ┌──────────────┐
                                         │ From: [____] │  (shown when Custom active)
                                         │ To:   [____] │
                                         └──────────────┘
```

**Preset buttons:**
- Each sets `start = now - duration`, `end = now`
- Active preset gets primary styling; clicking again deselects
- Selecting a preset hides the custom range inputs

**Custom range:**
- Clicking "Custom" toggles visibility of two `datetime-local` inputs
- Inputs pre-filled with current preset range (or last hour if no preset active)
- Validates: end > start, range <= 2 hours, shows inline error if violated

**Export dropdown:**
- Two options: "Features Only (CSV)" and "With Predictions (CSV)"
- Disabled when no time range is selected
- On click: calls `getExportCount(start, end, format)` → shows AlertDialog: "Found {count} records from {start} to {end}. Export?" → on confirm, triggers `downloadExport(start, end, format)` which opens the CSV download URL

### New API functions: `frontend/lib/api.ts`

```typescript
getExportCount(start: string, end: string, format: string): Promise<{ count: number; warning?: string }>
getExportUrl(start: string, end: string, format: string): string  // returns URL for direct download
```

### Realtime page changes: `frontend/app/[locale]/realtime/page.tsx`

- Import and render `<TimeRangeToolbar />` between `<ThroughputGraph>` and `<TerminalLog>`
- Toolbar is stateless from the page's perspective — it manages its own range state and export flow internally

### Confirmation dialog

Reuse shadcn `AlertDialog` inside the toolbar component. Shows:
- Record count
- Time range
- Warning if count > 10,000
- Cancel / Export buttons

## Translation keys

Add to both `en.json` and `vi.json` under a new `realtime.export` namespace:

- `preset1m`, `preset5m`, `preset15m`, `preset30m`, `preset1h`, `preset2h`
- `custom`, `from`, `to`
- `exportBtn`, `featuresOnly`, `withPredictions`
- `confirmTitle`, `confirmMessage`, `confirmLargeWarning`
- `cancel`, `export`
- `noRange`, `invalidRange`, `rangeTooLarge`
- `noData`

## Files to create/modify

| Action | File |
|--------|------|
| Create | `backend/app/api/routes/export.py` |
| Modify | `backend/app/main.py` (register export router) |
| Create | `frontend/components/TimeRangeToolbar.tsx` |
| Modify | `frontend/lib/api.ts` (add export API functions) |
| Modify | `frontend/app/[locale]/realtime/page.tsx` (add toolbar) |
| Modify | `frontend/messages/en.json` (add export translations) |
| Modify | `frontend/messages/vi.json` (add export translations) |

## Verification

1. Start Docker, open `/en/realtime`, run test stream for ~2 minutes
2. Click "1m" preset → Export "Features Only" → confirm dialog shows count → CSV downloads with correct feature columns matching upload format
3. Re-upload that CSV via Upload & Analyze page → should process without errors
4. Export "With Predictions" → CSV has extra prediction columns
5. Click "Custom" → set range > 2h → error shown
6. Select range with no data → "No data found" message
