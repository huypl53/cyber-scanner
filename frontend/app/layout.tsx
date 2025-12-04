import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "AI Shield - Threat Detection System",
  description: "Real-time network threat detection and self-healing AI system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans antialiased">
        <div className="flex h-screen overflow-hidden bg-background">
          {/* Sidebar Navigation */}
          <Sidebar />

          {/* Main Content Area */}
          <main className="flex-1 overflow-y-auto">
            <div className="container mx-auto p-6 lg:p-8">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
