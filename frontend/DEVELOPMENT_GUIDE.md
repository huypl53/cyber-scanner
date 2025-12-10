# AI Shield - Threat Detection System Development Guide

## Project Overview

AI Shield is a real-time network threat detection and self-healing AI system built with Next.js 14, React, TypeScript, and Tailwind CSS. The system provides an intuitive dashboard for monitoring network traffic, detecting threats, and managing security responses.

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom animations
- **UI Components**: Radix UI primitives
- **Charts & Visualizations**: Recharts, D3.js, VISX
- **Internationalization**: next-intl (English & Vietnamese)
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Backend API**: FastAPI (running on localhost:8000)

## Project Structure

```
ui/frontend/
├── app/
│   ├── [locale]/           # Locale-based routing (en, vi)
│   │   ├── layout.tsx      # Root layout with i18n provider
│   │   ├── page.tsx        # Home page
│   │   ├── dashboard/      # Dashboard page
│   │   ├── models/         # Model management
│   │   ├── realtime/       # Real-time monitoring
│   │   └── settings/       # Settings page
│   ├── globals.css         # Global styles and animations
│   └── layout.tsx          # App root layout
├── components/
│   ├── ui/                 # Reusable UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── dropdown-menu.tsx
│   │   └── ...
│   ├── Sidebar.tsx         # Main navigation sidebar
│   ├── LanguageSwitcher.tsx # Language switcher component
│   ├── CSVUploaderEnhanced.tsx
│   ├── StatCard.tsx
│   ├── ThreatTable.tsx
│   ├── AttackHeatmap.tsx
│   ├── ThreatDetectionChart.tsx
│   └── AttackDistributionChart.tsx
├── i18n/
│   ├── request.ts          # i18n configuration
│   └── locales.ts          # Locale definitions
├── messages/               # Translation files
│   ├── en.json            # English translations
│   └── vi.json            # Vietnamese translations
├── lib/
│   ├── api.ts             # API client configuration
│   └── utils.ts           # Utility functions
├── middleware.ts           # i18n middleware
├── next.config.js          # Next.js configuration
└── package.json
```

## Internationalization (i18n)

The application supports multiple languages using next-intl. Currently supports English and Vietnamese.

### Configuration Files

1. **`i18n/request.ts`**: Main i18n configuration
   ```typescript
   export default getRequestConfig(async ({ requestLocale }) => {
     let locale = await requestLocale;
     if (!locale || !['en', 'vi'].includes(locale)) {
       locale = 'en';
     }
     return {
       locale,
       messages: (await import(`../messages/${locale}.json`)).default
     };
   });
   ```

2. **`middleware.ts`**: Handles locale routing
   ```typescript
   export default createMiddleware({
     locales: ['en', 'vi'],
     defaultLocale: 'en'
   });
   ```

3. **`messages/en.json` & `messages/vi.json`**: Translation files with nested structure

### Adding Translations

1. **Translation Keys Structure**:
   - `app.*`: Application metadata
   - `sidebar.*`: Navigation elements
   - `home.*`: Home page content
   - `dashboard.*`: Dashboard content
   - `common.*`: Shared text elements

2. **Using Translations in Components**:
   ```typescript
   import { useTranslations } from 'next-intl';

   function Component() {
     const t = useTranslations('namespace');
     return <h1>{t('key')}</h1>;
   }
   ```

3. **Adding a New Language**:
   - Add locale to `i18n/request.ts`
   - Create new translation file in `messages/`
   - Update `i18n/locales.ts` if needed

## API Integration

The frontend communicates with a FastAPI backend running on `localhost:8000`.

### API Configuration

1. **API Rewrites** in `next.config.js`:
   ```javascript
   async rewrites() {
     return [{
       source: '/api/:path*',
       destination: 'http://localhost:8000/api/:path*',
     }];
   }
   ```

2. **API Client** in `lib/api.ts`:
   ```typescript
   import axios from 'axios';

   export const api = axios.create({
     baseURL: '/api/v1',
     timeout: 30000,
   });
   ```

### Common API Endpoints

- `GET /api/v1/predictions/stats` - Get prediction statistics
- `POST /api/v1/predictions` - Submit new prediction
- `GET /api/v1/predictions/history` - Get prediction history

## Styling System

### Tailwind CSS Configuration

- Custom color palette for threat levels
- Animation classes for UI effects
- Responsive design utilities

### CSS Custom Properties

Defined in `globals.css`:
```css
:root {
  --color-status-safe: #22c55e;
  --color-status-warning: #f59e0b;
  --color-status-danger: #ef4444;
  --color-primary: #06b6d4;
}
```

### Custom Animations

- `animate-fade-in`: Smooth fade in effect
- `animate-pulse-glow`: Pulsing glow effect
- `animate-shimmer`: Loading shimmer effect

## Components

### UI Components (components/ui/)

Built on Radix UI primitives with Tailwind styling:

1. **Button**: Supports multiple variants (default, destructive, outline, etc.)
2. **Card**: Container with shadow effects
3. **Badge**: Status indicators
4. **Dropdown Menu**: Language switcher and actions

### Custom Components

1. **Sidebar.tsx**: Main navigation with collapsible feature
2. **StatCard.tsx**: Statistics display with trend indicators
3. **ThreatTable.tsx**: Threats data table
4. **CSVUploaderEnhanced.tsx**: File upload component

## Chart Components

### Threat Detection Chart
- Line chart showing threat scores over time
- Real-time updates via WebSocket

### Attack Distribution Chart
- Bar/Pie chart showing attack type distribution
- Interactive tooltips

### Attack Heatmap
- 7x24 grid showing attack frequency
- Color-coded intensity

## Development Setup

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm run test

# Run E2E tests
npm run test:e2e

# Build for production
npm run build
```

### Environment Variables

Create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Code Conventions

### TypeScript

- Strict typing enabled
- Interface definitions for API responses
- Component props with TypeScript

### Component Structure

1. Imports: External libraries first, then internal
2. Type definitions (if needed)
3. Component implementation
4. Export default

```typescript
'use client';

import { useState } from 'react';
import { ComponentProps } from '@/types';

interface Props extends ComponentProps {
  // Component-specific props
}

export default function Component({ ...props }: Props) {
  // Implementation
}
```

### File Naming

- Components: PascalCase (`ComponentName.tsx`)
- Utilities: camelCase (`utilityFunction.ts`)
- Constants: UPPER_SNAKE_CASE (`CONSTANT_VALUE`)

## Adding New Features

### 1. Adding a New Page

1. Create folder: `app/[locale]/new-page/`
2. Add `page.tsx` with default export
3. Update Sidebar navigation if needed
4. Add translations

### 2. Adding a New Component

1. Create in appropriate directory (`components/` or `components/ui/`)
2. Follow TypeScript conventions
3. Add documentation
4. Include responsive design

### 3. Adding a New API Endpoint

1. Update API client in `lib/api.ts`
2. Add TypeScript interfaces
3. Handle loading and error states
4. Add to API documentation

### 4. Adding a New Translation

1. Update both `messages/en.json` and `messages/vi.json`
2. Maintain consistent key structure
3. Use namespace organization

## Testing

### Unit Tests

- Jest configuration in `jest.setup.js`
- Test files: `__tests__/**/*.test.tsx`
- Component testing with React Testing Library

### E2E Tests

- Playwright configuration
- Test files: `e2e/*.spec.ts`
- Critical user flows

## WebSocket Integration

Real-time updates are handled via WebSocket connections:

```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

const { data, isConnected } = useWebSocket('/ws/realtime');
```

## Performance Considerations

### Code Splitting

- Dynamic imports for large components
- Route-based code splitting with Next.js

### Image Optimization

- Next.js Image component
- Lazy loading for charts
- Optimized SVG icons

### Bundle Size

- Tree shaking enabled
- Only import needed components
- Minimize third-party dependencies

## Security

### API Security

- CORS configuration
- Rate limiting
- Input validation

### Client Security

- XSS protection
- HTTPS enforcement
- Secure cookie handling

## Deployment

### Production Build

```bash
# Build with standalone output
npm run build

# The build outputs to .next/standalone
```

### Docker

- Dockerfile configured for production
- Multi-stage build for optimization
- Environment-based configuration

## Troubleshooting

### Common Issues

1. **i18n not working**:
   - Check middleware configuration
   - Verify translation file structure
   - Ensure locale routing is correct

2. **API not connecting**:
   - Verify backend is running on port 8000
   - Check API rewrites in next.config.js
   - Review CORS settings

3. **Charts not rendering**:
   - Check data structure
   - Verify D3.js imports
   - Check responsive breakpoints

### Debug Mode

Enable debug mode:
```bash
DEBUG=* npm run dev
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request
5. Update documentation

## Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [next-intl Documentation](https://next-intl.dev/docs)
- [Radix UI Documentation](https://www.radix-ui.com/primitives)
- [Recharts Documentation](https://recharts.org/en-US)