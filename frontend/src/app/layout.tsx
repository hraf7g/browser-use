import type { Metadata } from "next";
import { LanguageProvider } from "@/context/language-context";
import { ThemeProvider } from "@/context/theme-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "UAE Tender Watch | Official MENA Tender Intelligence",
  description:
    "Tender Watch monitors official procurement sources across MENA and helps businesses move faster on relevant tenders.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased min-h-screen bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-50">
        <ThemeProvider>
          <LanguageProvider>
            {children}
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
