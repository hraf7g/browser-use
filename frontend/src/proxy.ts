import { NextResponse } from 'next/server';

export function proxy() {
  // Auth is resolved client-side through /auth/session against the API origin.
  // Do not gate protected routes here because the backend cookie lives on a
  // different origin and is not readable from the frontend request.
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/dashboard',
    '/dashboard/:path*',
    '/profile',
    '/profile/:path*',
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
