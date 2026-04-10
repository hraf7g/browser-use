import { NextRequest, NextResponse } from 'next/server';
import { getPublicAuthCookieName } from '@/lib/runtime-env';

const PROTECTED_PATHS = [
  '/dashboard',
  '/tenders',
  '/notifications',
  '/activity',
  '/matches',
  '/alerts',
  '/sources',
  '/settings',
];

function isProtectedPath(pathname: string) {
  return PROTECTED_PATHS.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`)
  );
}

export function proxy(request: NextRequest) {
  if (!isProtectedPath(request.nextUrl.pathname)) {
    return NextResponse.next();
  }

  const sessionToken = request.cookies.get(getPublicAuthCookieName())?.value?.trim();
  if (sessionToken) {
    return NextResponse.next();
  }

  const loginUrl = request.nextUrl.clone();
  loginUrl.pathname = '/login';
  loginUrl.searchParams.set('next', `${request.nextUrl.pathname}${request.nextUrl.search}`);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    '/dashboard',
    '/dashboard/:path*',
    '/tenders',
    '/tenders/:path*',
    '/notifications',
    '/notifications/:path*',
    '/activity',
    '/activity/:path*',
    '/matches',
    '/matches/:path*',
    '/alerts',
    '/alerts/:path*',
    '/sources',
    '/sources/:path*',
    '/settings',
    '/settings/:path*',
  ],
};
