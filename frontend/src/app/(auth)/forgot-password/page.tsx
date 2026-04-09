import AuthShell from '@/components/auth/auth-shell';
import ForgotPasswordForm from '@/components/auth/forgot-password-form';

export const metadata = {
  title: 'Forgot Password | Tender Watch',
};

export default function ForgotPasswordPage() {
  return (
    <AuthShell>
      <ForgotPasswordForm />
    </AuthShell>
  );
}
