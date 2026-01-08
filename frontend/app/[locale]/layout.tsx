import { NextIntlClientProvider } from 'next-intl';
import { getMessages, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { locales } from '@/i18n';
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: { params: { locale: string } }) {
  const t = await getTranslations({ locale: params.locale, namespace: 'app' });

  return {
    title: t('title'),
    description: t('description'),
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  const { locale } = params;

  // Validate locale
  if (!locales.includes(locale as any)) {
    notFound();
  }

  const messages = await getMessages({ locale });

  return (
    <html lang={locale} className="dark">
      <body className="font-sans antialiased">
        <NextIntlClientProvider locale={locale} messages={messages}>
          <div className="flex h-screen overflow-hidden bg-background">
            {/* Sidebar Navigation */}
            <Sidebar />

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col overflow-hidden">
              {/* Header with Language Switcher */}
              <Header />

              {/* Page Content */}
              <div className="flex-1 overflow-y-auto">
                <div className="container mx-auto p-6 lg:p-8">
                  {children}
                </div>
              </div>
            </main>
          </div>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
