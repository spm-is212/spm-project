import React, { useState, useEffect} from 'react';
import { Check } from 'lucide-react';
import type { FormData, FormErrors } from '../../types/auth';
import { useNavigate } from 'react-router-dom';

const LoginPage: React.FC = () => {

  const navigate = useNavigate();
      useEffect(() => {
        document.title = "All IN ONE";
      }, []);
  const [formData, setFormData] = useState<FormData>({
    username: '',
    password: '',
    confirmPassword: ''
  });


  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

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
    const newErrors: FormErrors = {};



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
          username: formData.username,   // backend expects `username`
          password: formData.password
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Login failed");
      }

      const data = await res.json();
      localStorage.setItem("access_token", data.access_token); // save token
      navigate('/taskmanager', { replace: true });
    } catch (err: any) {
      setErrors({ general: err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Logo and Title */}
        <div className="logo-container">
          <div className="logo-icon">
            <Check className="logo-check" strokeWidth={3} />
          </div>
          <h1 className="heading-secondary">ALL-IN-ONE</h1>
          <h2 className="heading-primary">Sign In</h2>
        </div>

        {/* General Error */}
        {errors.general && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {errors.general}
          </div>
        )}

        {/* Form */}
        <div className="form-container">

          {/* Email Field */}
          <div className="form-field">
            <input
              type="email"
              name="username"
              placeholder="Email"
              value={formData.username}
              onChange={handleInputChange}
              className={`form-input ${errors.username ? 'form-input-error' : 'form-input-normal'}`}
              aria-invalid={errors.username ? 'true' : 'false'}
              aria-describedby={errors.username ? 'username-error' : undefined}
            />
            {errors.username && (
              <p id="username-error" className="error-text" role="alert">
                {errors.username}
              </p>
            )}
          </div>

          {/* Password Field */}
          <div className="form-field">
            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleInputChange}
              className={`form-input ${errors.password ? 'form-input-error' : 'form-input-normal'}`}
              aria-invalid={errors.password ? 'true' : 'false'}
              aria-describedby={errors.password ? 'password-error' : undefined}
            />
            {errors.password && (
              <p id="password-error" className="error-text" role="alert">
                {errors.password}
              </p>
            )}
          </div>

          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="btn-primary"
            aria-label="Sign in to account"
          >
            {isSubmitting ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                Signing In...
              </div>
            ) : (
              'Sign In'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;