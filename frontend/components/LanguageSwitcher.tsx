'use client';

import { useLocale } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Languages } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useTranslations } from 'next-intl';

const languages = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'vi', name: 'Tiếng Việt', flag: '🇻🇳' },
];

interface LanguageSwitcherProps {
  /**
   * Compact variant for header placement
   * Uses smaller size and minimal styling
   */
  compact?: boolean;

  /**
   * Show tooltip on hover (useful for collapsed sidebar)
   */
  showTooltip?: boolean;

  /**
   * Custom CSS class name
   */
  className?: string;
}

export function LanguageSwitcher({
  compact = false,
  showTooltip = false,
  className = '',
}: LanguageSwitcherProps) {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const t = useTranslations('languageSwitcher');

  const handleLanguageChange = (newLocale: string) => {
    // Remove the current locale from pathname if it exists
    const pathnameWithoutLocale = pathname.replace(`/${locale}`, '') || '/';

    // Navigate to the new locale
    router.push(`/${newLocale}${pathnameWithoutLocale}`);
  };

  const currentLanguage = languages.find((lang) => lang.code === locale);
  const tooltipText = `${t('switch')}: ${languages
    .filter((l) => l.code !== locale)
    .map((l) => l.name)
    .join(' / ')}`;

  const button = (
    <Button
      variant="ghost"
      size={compact ? 'icon' : 'sm'}
      className={`${
        compact
          ? 'h-8 w-8 hover:bg-primary/10'
          : 'gap-2 hover:bg-primary/10'
      } ${className}`}
      aria-label={t('changeLanguage')}
    >
      <Languages className="h-4 w-4" aria-hidden="true" />
      {!compact && (
        <>
          <span className="text-lg" aria-hidden="true">
            {currentLanguage?.flag}
          </span>
          <span className="hidden sm:inline">{currentLanguage?.name}</span>
        </>
      )}
      {compact && (
        <span className="text-sm" aria-hidden="true">
          {currentLanguage?.flag}
        </span>
      )}
    </Button>
  );

  const content = (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        {showTooltip ? (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>{button}</TooltipTrigger>
              <TooltipContent side="right">
                <p>{tooltipText}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        ) : (
          button
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align={compact ? 'end' : 'end'}
        className="w-40"
        aria-label={t('selectLanguage')}
      >
        {languages.map((language) => (
          <DropdownMenuItem
            key={language.code}
            onClick={() => handleLanguageChange(language.code)}
            className={
              locale === language.code
                ? 'bg-primary/10 text-primary font-semibold'
                : ''
            }
            aria-selected={locale === language.code}
          >
            <span className="mr-2 text-lg" aria-hidden="true">
              {language.flag}
            </span>
            <span>{language.name}</span>
            {locale === language.code && (
              <span className="ml-auto text-xs">({t('current')})</span>
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );

  return content;
}
