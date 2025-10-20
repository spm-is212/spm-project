import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { CheckSquare, Users, Menu, X, LogOut, CheckCircle, Calendar } from 'lucide-react';
import NotificationBell from '../Notifications';

export default function Sidebar() {
  const [isOpen, setIsOpen] = useState(true);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [showLogoutMessage, setShowLogoutMessage] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth <= 768) {
        setIsOpen(false);
      } else {
        setIsOpen(true);
      }
    };

    handleResize(); // set on initial load
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const navigation = [
    { name: 'Task Manager', href: '/taskmanager', icon: CheckSquare },
    { name: 'Projects', href: '/team', icon: Users },
    { name: 'Calendar View', href: '/calendarview', icon: Calendar },
  ];

  const handleLogout = async () => {
    if (!showConfirmDialog) {
      setShowConfirmDialog(true);
      return;
    }

    setIsLoggingOut(true);
    setShowConfirmDialog(false);

    try {
      localStorage.removeItem('access_token');
      setShowLogoutMessage(true);

      setTimeout(() => {
        navigate('/');
      }, 1500);

    } catch (error) {
      console.error('Error during logout:', error);
      navigate('/');
    } finally {
      setIsLoggingOut(false);
    }
  };

  const cancelLogout = () => {
    setShowConfirmDialog(false);
  };

  return (
    <>
      <div
        className={`${
          isOpen ? 'w-64' : 'w-20'
        } bg-gray-900 text-white transition-all duration-300 ease-in-out flex flex-col`}
      >
        {/* Header */}
<div
  className={`flex items-center ${
    isOpen ? 'justify-between p-4' : 'justify-center py-6'
  } border-b border-[#2C2C2E]`}
>
  {isOpen ? (
    <>
      <div className="flex items-center gap-2">
        <img src="/l1.svg" alt="Logo" className="h-8" />
        <span className="font-semibold text-lg tracking-tight text-gray-100">
          ALL-IN-ONE
        </span>
      </div>
      <div className="flex items-center gap-2">
        <NotificationBell />  {/* ← NEW: Notification Bell Component */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 rounded-lg hover:bg-[#2C2C2E] transition-colors"
        >
          <X size={20} />
        </button>
      </div>
    </>
  ) : (
    <button
      onClick={() => setIsOpen(!isOpen)}
      className="p-2 rounded-lg hover:bg-[#2C2C2E] transition-colors mx-auto"
    >
      <Menu size={20} />
    </button>
  )}
</div>
        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;

              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:bg-gray-800'
                    }`}
                  >
                    <Icon size={20} className="flex-shrink-0" />
                    {isOpen && <span className="font-medium">{item.name}</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Logout Button at Bottom */}
        <div className="p-4 border-t border-gray-700">
          <button
            onClick={handleLogout}
            disabled={isLoggingOut}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
              ${isLoggingOut
                ? 'bg-gray-700 cursor-not-allowed'
                : 'text-red-400 hover:bg-gray-800 hover:text-red-300'
              }`}
          >
            {isLoggingOut ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin flex-shrink-0"></div>
                {isOpen && <span className="font-medium">Logging out...</span>}
              </>
            ) : (
              <>
                <LogOut size={20} className="flex-shrink-0" />
                {isOpen && <span className="font-medium">Logout</span>}
              </>
            )}
          </button>
        </div>
      </div>

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
              Log out successful. Redirecting to login page...
            </p>
            <div className="mt-4">
              <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
