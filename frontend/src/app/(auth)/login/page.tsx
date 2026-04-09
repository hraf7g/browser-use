import AuthShell from '@/components/auth/auth-shell';
import LoginForm from '@/components/auth/login-form';

export const metadata = {
  title: 'Login | Tender Watch',
};

export default function LoginPage() {
  return (
    <AuthShell>
      <LoginForm />
    </AuthShell>
  );
}
