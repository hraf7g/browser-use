import { NextRequest, NextResponse } from 'next/server';

type OperatorSessionResponse = {
  authenticated: boolean;
  user: {
    id: string;
    email: string;
    is_active: boolean;
    is_operator: boolean;
  } | null;
};

function getBackendBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (!configured) {
    throw new Error('NEXT_PUBLIC_API_URL must be configured for operator proxy routes');
  }
  return configured.replace(/\/$/, '');
}

function getOperatorApiKey(): string {
  const configured = process.env.UTW_OPERATOR_API_KEY?.trim();
  if (!configured) {
    throw new Error('UTW_OPERATOR_API_KEY must be configured for operator proxy routes');
  }
  return configured;
}

async function requireOperatorSession(request: NextRequest): Promise<NextResponse | null> {
  const cookieHeader = request.headers.get('cookie') ?? '';
  const response = await fetch(`${getBackendBaseUrl()}/auth/session`, {
    headers: cookieHeader ? { cookie: cookieHeader } : {},
    cache: 'no-store',
  });

  if (!response.ok) {
    return NextResponse.json(
      { detail: 'Unable to verify current session' },
      { status: 502 },
    );
  }

  const session = (await response.json()) as OperatorSessionResponse;
  if (!session.authenticated || session.user === null) {
    return NextResponse.json({ detail: 'authentication required' }, { status: 401 });
  }

  if (!session.user.is_operator) {
    return NextResponse.json({ detail: 'operator access required' }, { status: 403 });
  }

  return null;
}

async function proxyOperatorRequest(
  request: NextRequest,
  method: 'GET' | 'PUT',
): Promise<NextResponse> {
  try {
    const authError = await requireOperatorSession(request);
    if (authError) {
      return authError;
    }

    const headers = new Headers({
      'X-Operator-Key': getOperatorApiKey(),
    });
    let body: string | undefined;
    if (method === 'PUT') {
      headers.set('Content-Type', 'application/json');
      body = await request.text();
    }

    const upstream = await fetch(`${getBackendBaseUrl()}/operator/ai-control`, {
      method,
      headers,
      body,
      cache: 'no-store',
    });

    const payload = await upstream.text();
    return new NextResponse(payload, {
      status: upstream.status,
      headers: {
        'content-type': upstream.headers.get('content-type') ?? 'application/json',
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        detail:
          error instanceof Error ? error.message : 'Unexpected operator proxy failure',
      },
      { status: 500 },
    );
  }
}

export async function GET(request: NextRequest) {
  return proxyOperatorRequest(request, 'GET');
}

export async function PUT(request: NextRequest) {
  return proxyOperatorRequest(request, 'PUT');
}
