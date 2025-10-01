import React, { useState, useEffect } from 'react';
import { Check, Mail, Lock, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import type { FormErrors } from '../../types/auth';

const LoginPage = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });

  const [errors, setErrors] = useState<Partial<FormErrors>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [focusedField, setFocusedField] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

  useEffect(() => {
    document.title = "All IN ONE";
  }, []);

  const navigate = useNavigate();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({
        ...prev,
        [name]: undefined
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<FormErrors> = {};

    if (!formData.username.trim()) {
      newErrors.username = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.username)) {
      newErrors.username = 'Please enter a valid email';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      const res = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          username: formData.username,
          password: formData.password
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Login failed");
      }

      const data = await res.json();

      // 🔑 Store token depending on "Remember Me"
      if (rememberMe) {
        localStorage.setItem("access_token", data.access_token);
      } else {
        sessionStorage.setItem("access_token", data.access_token);
      }

      navigate('/taskmanager', { replace: true });
    } catch (err: any) {
      setErrors({ general: err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100 flex items-center justify-center p-4 relative">
      {/* Background */}
      <div className="absolute inset-0 overflow-hidden opacity-30">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-slate-200 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-gray-200 rounded-full blur-3xl"></div>
      </div>

      {/* Login Card */}
      <div className="relative w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden backdrop-blur-sm transition-all duration-300 hover:shadow-2xl">
          {/* Header */}
          <div className="px-8 pt-10 pb-8 text-center border-b border-gray-100">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-slate-900 rounded-xl shadow-lg mb-4">
              <Check className="w-7 h-7 text-white" strokeWidth={2.5} />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mb-1 tracking-tight">ALL-IN-ONE</h1>
            <p className="text-slate-500 text-sm">Sign in to your account</p>
          </div>

          {/* Form */}
          <div className="px-8 py-8">
            {errors.general && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3 animate-shake">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-700">{errors.general}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Email</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <Mail className={`w-5 h-5 ${focusedField === 'username' ? 'text-slate-700' : 'text-slate-400'}`} />
                  </div>
                  <input
                    type="email"
                    name="username"
                    placeholder="you@example.com"
                    value={formData.username}
                    onChange={handleInputChange}
                    onFocus={() => setFocusedField('username')}
                    onBlur={() => setFocusedField('')}
                    className={`w-full pl-11 pr-4 py-3 rounded-lg border text-slate-900 placeholder-slate-400 focus:ring-2 ${
                      errors.username
                        ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                        : 'border-gray-300 focus:border-slate-400 focus:ring-slate-200'
                    }`}
                  />
                </div>
                {errors.username && (
                  <p className="mt-2 text-sm text-red-600 flex items-center space-x-1">
                    <AlertCircle className="w-4 h-4" />
                    <span>{errors.username}</span>
                  </p>
                )}
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Password</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <Lock className={`w-5 h-5 ${focusedField === 'password' ? 'text-slate-700' : 'text-slate-400'}`} />
                  </div>
                  <input
                    type="password"
                    name="password"
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handleInputChange}
                    onFocus={() => setFocusedField('password')}
                    onBlur={() => setFocusedField('')}
                    className={`w-full pl-11 pr-4 py-3 rounded-lg border text-slate-900 placeholder-slate-400 focus:ring-2 ${
                      errors.password
                        ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                        : 'border-gray-300 focus:border-slate-400 focus:ring-slate-200'
                    }`}
                  />
                </div>
                {errors.password && (
                  <p className="mt-2 text-sm text-red-600 flex items-center space-x-1">
                    <AlertCircle className="w-4 h-4" />
                    <span>{errors.password}</span>
                  </p>
                )}
              </div>

              {/* Remember Me */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="remember"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-slate-900 focus:ring-slate-500"
                />
                <label htmlFor="remember" className="ml-2 text-sm text-slate-600 cursor-pointer">
                  Remember me for 30 days
                </label>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-slate-900 text-white font-medium py-3 rounded-lg shadow-sm hover:bg-slate-800 transition-all duration-200 disabled:opacity-60"
              >
                {isSubmitting ? 'Signing in…' : 'Sign in'}
              </button>
            </form>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-slate-400 text-xs">© 2025 ALL-IN-ONE. Secure authentication.</p>
        </div>
      </div>

      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-8px); }
          75% { transform: translateX(8px); }
        }
        .animate-shake {
          animation: shake 0.4s ease-in-out;
        }
      `}</style>
    </div>
  );
};

export default LoginPage;
