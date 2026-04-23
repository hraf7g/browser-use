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
    return NextResponse.json({ detail: 'Unable to verify current session' }, { status: 502 });
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

export async function GET(request: NextRequest) {
  try {
    const authError = await requireOperatorSession(request);
    if (authError) {
      return authError;
    }

    const upstream = await fetch(`${getBackendBaseUrl()}/operator/status`, {
      headers: {
        'X-Operator-Key': getOperatorApiKey(),
      },
      cache: 'no-store',
    });

    const payload = await upstream.json();
    if (!upstream.ok) {
      return NextResponse.json(payload, { status: upstream.status });
    }

    return NextResponse.json(payload.browser_agent_runtime, { status: upstream.status });
  } catch (error) {
    return NextResponse.json(
      {
        detail: error instanceof Error ? error.message : 'Unexpected operator proxy failure',
      },
      { status: 500 },
    );
  }
}
