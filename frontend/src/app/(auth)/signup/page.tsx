import AuthShell from '@/components/auth/auth-shell';
import SignupForm from '@/components/auth/signup-form';

export const metadata = {
  title: 'Signup | Tender Watch',
};

export default function SignupPage() {
  return (
    <AuthShell>
      <SignupForm />
    </AuthShell>
  );
}
