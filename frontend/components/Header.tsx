'use client';

import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { useTranslations, useLocale } from 'next-intl';
import { usePathname } from 'next/navigation';

interface HeaderProps {
  /**
   * Custom title for the header
   * If not provided, will use the page title based on the current route
   */
  title?: string;

  /**
   * Custom CSS class name
   */
  className?: string;
}

export function Header({ title, className = '' }: HeaderProps) {
  const t = useTranslations('header');
  const locale = useLocale();
  const pathname = usePathname();

  // Get the page title based on the current route
  const getPageTitle = () => {
    if (title) return title;

    // Remove the locale from the pathname
    const pathWithoutLocale = pathname.replace(`/${locale}`, '') || '/';

    // Map routes to page titles
    const routeTitles: Record<string, string> = {
      '/': t('home'),
      '/dashboard': t('dashboard'),
      '/realtime': t('realtime'),
      '/models': t('models'),
      '/settings': t('settings'),
    };

    return routeTitles[pathWithoutLocale] || t('default');
  };

  return (
    <header
      className={`flex items-center justify-between border-b border-border bg-card px-6 py-4 ${className}`}
    >
      {/* Page Title */}
      <div className="flex items-center space-x-4">
        <h1 className="text-xl font-semibold text-foreground">
          {getPageTitle()}
        </h1>
      </div>

      {/* Right Side - Language Switcher */}
      <div className="flex items-center space-x-4">
        <LanguageSwitcher compact={false} />
      </div>
    </header>
  );
}
