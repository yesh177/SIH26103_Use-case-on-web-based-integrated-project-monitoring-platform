import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Mail, Lock, Eye, EyeOff, ArrowRight } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [emailOrUser, setEmailOrUser] = useState('surveillance.lead@mospi.gov.in');
  const [password, setPassword] = useState('••••••••••••');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Simulate instantaneous frontend credential check for prototype demo
    setTimeout(() => {
      localStorage.setItem('paimana_auth_token', 'demo_mock_token_sih26103');
      navigate('/dashboard');
    }, 400);
  };

  return (
    <div>
      <div className="text-center mb-6">
        <h2 className="text-xl font-bold text-slate-900">Sign in to PAIMANA</h2>
        <p className="text-xs text-slate-500 mt-1">
          Access the Central Infrastructure Risk Surveillance Platform
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Official Email or Username"
          type="text"
          value={emailOrUser}
          onChange={(e) => setEmailOrUser(e.target.value)}
          placeholder="e.g. name@mospi.gov.in"
          leftIcon={<Mail className="w-4 h-4" />}
          required
        />

        <div className="space-y-1">
          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            leftIcon={<Lock className="w-4 h-4" />}
            rightIcon={
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="hover:text-slate-700 focus:outline-none"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            }
            required
          />
        </div>

        <div className="flex items-center justify-between text-xs pt-1">
          <label className="flex items-center gap-2 cursor-pointer text-slate-600 select-none">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
            />
            <span>Remember credentials</span>
          </label>

          <a
            href="#forgot-password"
            onClick={(e) => {
              e.preventDefault();
              alert('Password reset requests should be submitted to your CPSE or MoSPI IT administrator.');
            }}
            className="text-blue-700 hover:text-blue-800 font-medium hover:underline"
          >
            Forgot password?
          </a>
        </div>

        <div className="pt-2">
          <Button
            type="submit"
            className="w-full justify-center"
            size="md"
            isLoading={isLoading}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Sign In to Platform
          </Button>
        </div>
      </form>

      <div className="mt-6 pt-5 border-t border-slate-100 text-center text-xs text-slate-500">
        Need official surveillance portal access?{' '}
        <Link to="/signup" className="text-blue-700 hover:text-blue-800 font-semibold hover:underline">
          Request an Account
        </Link>
      </div>
    </div>
  );
};
