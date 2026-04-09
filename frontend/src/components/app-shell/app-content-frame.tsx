'use client';

export default function AppContentFrame({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto w-full max-w-7xl">{children}</div>;
}
