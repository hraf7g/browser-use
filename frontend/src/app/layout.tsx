import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './globals.css';

export const metadata: Metadata = {
  title: 'Tender Watch — AI Tender Intelligence',
  description:
    'Monitor live tender sources, qualify opportunities faster, and turn procurement signals into action with AI-powered tender intelligence.',
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
