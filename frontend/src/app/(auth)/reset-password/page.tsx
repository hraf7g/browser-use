import AuthShell from '@/components/auth/auth-shell';
import ResetPasswordForm from '@/components/auth/reset-password-form';

export const metadata = {
  title: 'Reset Password | Tender Watch',
};

export default function ResetPasswordPage() {
  return (
    <AuthShell>
      <ResetPasswordForm />
    </AuthShell>
  );
}
