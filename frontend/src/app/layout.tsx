import type { Metadata } from 'next';
import { IBM_Plex_Sans_Arabic } from 'next/font/google';
import type { ReactNode } from 'react';
import './globals.css';

const ibmPlexArabic = IBM_Plex_Sans_Arabic({
  subsets: ['arabic', 'latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-ibm-plex-arabic',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'تيندر ووتش | مراقبة المناقصات بالذكاء الاصطناعي',
  description:
    'منصة عربية أولاً لمراقبة المناقصات في منطقة الشرق الأوسط وشمال أفريقيا عبر وكيل متصفح يحلل المحتوى بالعربية والإنجليزية ويرسل تنبيهات فورية وملخصات يومية.',
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="ar" dir="rtl" suppressHydrationWarning>
      <body className={ibmPlexArabic.variable}>{children}</body>
    </html>
  );
}
