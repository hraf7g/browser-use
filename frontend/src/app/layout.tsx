import type { Metadata } from "next";
import { IBM_Plex_Sans_Arabic } from "next/font/google";
import { ThemeProvider } from "@/context/theme-context";
import { LanguageProvider } from "@/context/language-context";
import "./globals.css";

const ibmPlexArabic = IBM_Plex_Sans_Arabic({
  subsets: ["arabic"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-ibm-plex-arabic",
});

export const metadata: Metadata = {
  title: "تيندر ووتش | منصة رصد المناقصات في الشرق الأوسط",
  description:
    "نظام ذكاء اصطناعي لمراقبة المناقصات، يكتشف العقود الجديدة، ويحلل المحتوى، ويرسل تنبيهات فورية.",
  keywords: ["مناقصات", "الشرق الأوسط", "ذكاء اصطناعي", "المشتريات الحكومية", "Tender Watch", "MENA Procurement"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl" suppressHydrationWarning className={ibmPlexArabic.variable}>
      <body className="antialiased min-h-screen selection:bg-primary/20">
        <ThemeProvider>
          <LanguageProvider>
            {children}
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
