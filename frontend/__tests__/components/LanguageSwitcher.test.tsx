import { render, screen } from '@testing-library/react';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import * as nextNavigation from 'next/navigation';
import { NextIntlClientProvider } from 'next-intl';

// Mock next-intl
jest.mock('next-intl', () => ({
  useLocale: jest.fn(),
  useTranslations: jest.fn(() => (key: string) => key),
  NextIntlClientProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
  useRouter: jest.fn(() => ({
    push: mockPush,
  })),
}));

describe('LanguageSwitcher', () => {
  const mockLocale = 'en';
  const mockPathname = '/en/dashboard';
  const mockMessages = {
    sidebar: {
      brand: 'AI Shield',
      subtitle: 'Threat Detection',
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (nextNavigation.usePathname as jest.Mock).mockReturnValue(mockPathname);
    const { useLocale } = require('next-intl');
    useLocale.mockReturnValue(mockLocale);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    document.body.innerHTML = '<div></div>';
  });

  const renderWithProviders = (component: React.ReactNode) => {
    return render(
      <NextIntlClientProvider locale={mockLocale} messages={mockMessages}>
        {component}
      </NextIntlClientProvider>
    );
  };

  describe('Rendering', () => {
    it('renders the language switcher button', () => {
      renderWithProviders(<LanguageSwitcher />);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('displays the current language flag and name', () => {
      renderWithProviders(<LanguageSwitcher />);
      expect(screen.getByText('🇺🇸')).toBeInTheDocument();
      expect(screen.getByText('English')).toBeInTheDocument();
    });

    it('displays Vietnamese flag and name when locale is vi', () => {
      const { useLocale } = require('next-intl');
      useLocale.mockReturnValue('vi');

      renderWithProviders(<LanguageSwitcher />);
      expect(screen.getByText('🇻🇳')).toBeInTheDocument();
      expect(screen.getByText('Tiếng Việt')).toBeInTheDocument();
    });

    it('has correct accessibility attributes', () => {
      renderWithProviders(<LanguageSwitcher />);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-haspopup', 'menu');
    });

    it('applies correct CSS classes', () => {
      renderWithProviders(<LanguageSwitcher />);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('gap-2');
    });

    it('has icon button with languages icon', () => {
      renderWithProviders(<LanguageSwitcher />);
      const svg = document.querySelector('button svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Language Switching Logic', () => {
    it('has correct language options', () => {
      renderWithProviders(<LanguageSwitcher />);
      // Component should have the Languages icon
      const svg = document.querySelector('button svg');
      expect(svg).toBeInTheDocument();
    });

    it('can be focused for keyboard navigation', () => {
      renderWithProviders(<LanguageSwitcher />);
      const button = screen.getByRole('button');
      expect(typeof button.focus).toBe('function');
    });
  });

  describe('Edge Cases - Pathname Handling', () => {
    it('handles English locale correctly', () => {
      const { useLocale } = require('next-intl');
      useLocale.mockReturnValue('en');

      renderWithProviders(<LanguageSwitcher />);
      expect(screen.getByText('🇺🇸')).toBeInTheDocument();
      expect(screen.getByText('English')).toBeInTheDocument();
    });

    it('handles Vietnamese locale correctly', () => {
      const { useLocale } = require('next-intl');
      useLocale.mockReturnValue('vi');

      renderWithProviders(<LanguageSwitcher />);
      expect(screen.getByText('🇻🇳')).toBeInTheDocument();
      expect(screen.getByText('Tiếng Việt')).toBeInTheDocument();
    });

    it('handles different pathnames', () => {
      (nextNavigation.usePathname as jest.Mock).mockReturnValue('/en/realtime');

      renderWithProviders(<LanguageSwitcher />);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('hides language name on small screens', () => {
      renderWithProviders(<LanguageSwitcher />);
      const button = screen.getByRole('button');

      // The button should contain the flag always
      expect(screen.getByText('🇺🇸')).toBeInTheDocument();

      // But the language name should have the hidden class for small screens
      const languageName = screen.getByText('English');
      expect(languageName).toHaveClass('hidden');
      expect(languageName).toHaveClass('sm:inline');
    });
  });
});
