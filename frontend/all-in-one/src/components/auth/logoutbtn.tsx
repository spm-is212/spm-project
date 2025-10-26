// components/auth/LogoutButton.tsx
import React, { useState, useEffect } from 'react';
import { LogOut, CheckCircle } from 'lucide-react';

interface LogoutButtonProps {
  onLogout?: () => void;
  className?: string;
  showConfirm?: boolean;
  redirectTo?: string;
}

const LogoutBtn: React.FC<LogoutButtonProps> = ({
  onLogout,
  className = '',
  showConfirm = false,
  redirectTo = '/'
}) => {
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [showLogoutMessage, setShowLogoutMessage] = useState(false);

  useEffect(() => {
    document.title = "All IN ONE";
  }, []);

  const handleLogout = async () => {
    if (showConfirm && !showConfirmDialog) {
      setShowConfirmDialog(true);
      return;
    }

    setIsLoggingOut(true);
    setShowConfirmDialog(false);

    try {
      localStorage.removeItem('access_token');

      if (onLogout) {
        await onLogout();
      }

      // Show logout message instead of alert
      setShowLogoutMessage(true);

      // Redirect after showing message
      setTimeout(() => {
        window.location.href = redirectTo;
      }, 1500);

    } catch (error) {
      console.error('Error during logout:', error);
      window.location.href = redirectTo;
    } finally {
      setIsLoggingOut(false);
    }
  };

  const cancelLogout = () => {
    setShowConfirmDialog(false);
  };

  return (
    <>
      <button
        onClick={handleLogout}
        disabled={isLoggingOut}
        className={`
          inline-flex items-center gap-2 px-4 py-2
          bg-blue-600 hover:bg-blue-700
          text-white font-medium rounded-lg
          transition-colors duration-200
          disabled:opacity-50 disabled:cursor-not-allowed
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          ${className}
        `}
        aria-label="Logout from account"
      >
        {isLoggingOut ? (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            Logging out...
          </div>
        ) : (
          <>
            <LogOut size={16} />
            Logout
          </>
        )}
      </button>

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Confirm Logout
            </h3>
            <p className="text-gray-600 mb-4">
              Are you sure you want to logout? You'll need to sign in again to access your account.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={cancelLogout}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Logout Success Message */}
      {showLogoutMessage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm mx-4 shadow-xl text-center">
            <div className="flex justify-center mb-4">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Logging You Out!
            </h3>
            <p className="text-gray-600">
              You have been successfully logged out. Redirecting to login page...
            </p>
            <div className="mt-4">
              <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default LogoutBtn;
