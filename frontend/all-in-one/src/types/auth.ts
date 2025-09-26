// Authentication related types
export interface FormData {
    username: string;

    password: string;
    confirmPassword: string;
  }
  
  export interface FormErrors {
    username?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    general?: string;
  }
  
  export interface AuthResponse {
    success: boolean;
    message: string;
    user?: {
      id: string;
      username: string;
      email: string;
    };
    token?: string;
  }
  
  export interface ValidationRules {
    minPasswordLength: number;
    requireSpecialChar: boolean;
    requireNumber: boolean;
    requireUppercase: boolean;
  }
  
  export type AuthMode = 'signin' | 'signup';
  
  export interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    signin: (credentials: LoginCredentials) => Promise<void>;
    signup: (userData: SignupData) => Promise<void>;
    signout: () => void;
  }
  
  export interface User {
    id: string;
    username: string;
    email: string;
    createdAt: string;
  }
  
  export interface LoginCredentials {
    email: string;
    password: string;
  }
  
  export interface SignupData {
    username: string;
    email: string;
    password: string;
  }