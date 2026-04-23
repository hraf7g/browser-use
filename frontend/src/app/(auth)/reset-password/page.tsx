import AuthShell from '@/components/auth/auth-shell';
import ResetPasswordForm from '@/components/auth/reset-password-form';

export const metadata = {
  title: 'Reset Password | Tender Watch',
};

export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const params = await searchParams;

  return (
    <AuthShell>
      <ResetPasswordForm token={params.token} />
    </AuthShell>
  );
}
