import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { User, Mail, Building2, Lock, ArrowRight } from 'lucide-react';

export const SignupPage: React.FC = () => {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [officialEmail, setOfficialEmail] = useState('');
  const [organization, setOrganization] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setError(null);
    setIsLoading(true);
    setTimeout(() => {
      localStorage.setItem('paimana_auth_token', 'demo_mock_token_sih26103');
      navigate('/dashboard');
    }, 400);
  };

  return (
    <div>
      <div className="text-center mb-6">
        <h2 className="text-xl font-bold text-slate-900">Request Official Account Access</h2>
        <p className="text-xs text-slate-500 mt-1">
          Ministry, Line Department, or Executing CPSE Officer Registration
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3.5">
        {error && (
          <div className="p-2.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded-md">
            {error}
          </div>
        )}

        <Input
          label="Full Name & Title"
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="e.g. Dr. Rajesh Sharma"
          leftIcon={<User className="w-4 h-4" />}
          required
        />

        <Input
          label="Official Email Address"
          type="email"
          value={officialEmail}
          onChange={(e) => setOfficialEmail(e.target.value)}
          placeholder="e.g. r.sharma@railnet.gov.in"
          leftIcon={<Mail className="w-4 h-4" />}
          required
        />

        <Input
          label="Organization / Executing Agency"
          type="text"
          value={organization}
          onChange={(e) => setOrganization(e.target.value)}
          placeholder="e.g. West Central Railway / NHAI / NTPC"
          leftIcon={<Building2 className="w-4 h-4" />}
          required
        />

        <Input
          label="Create Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Minimum 8 characters"
          leftIcon={<Lock className="w-4 h-4" />}
          required
        />

        <Input
          label="Confirm Password"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Re-enter password"
          leftIcon={<Lock className="w-4 h-4" />}
          required
        />

        <div className="pt-3">
          <Button
            type="submit"
            className="w-full justify-center"
            size="md"
            isLoading={isLoading}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Submit Access Request
          </Button>
        </div>
      </form>

      <div className="mt-6 pt-5 border-t border-slate-100 text-center text-xs text-slate-500">
        Already registered with MoSPI surveillance?{' '}
        <Link to="/login" className="text-blue-700 hover:text-blue-800 font-semibold hover:underline">
          Sign In
        </Link>
      </div>
    </div>
  );
};

