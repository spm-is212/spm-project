import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Bell, X, Check, AlertCircle, Clock, User, CheckCircle, Mail } from 'lucide-react';
import { apiFetch } from '../../utils/api';

interface Notification {
  id: number;
  sender_id: string;
  receiver_id: string;
  task_id?: number;
  action: string;
  message: string;
  timestamp: string;
  read?: boolean;
}

const NotificationBell: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await apiFetch('notifications/');
      setNotifications(data.notifications || []);
    } catch (err) {
      setError('Failed to load notifications');
      console.error('Notification fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const unreadCount = notifications.filter(n => !n.read).length;

  const getNotificationIcon = (action: string) => {
    switch (action.toLowerCase()) {
      case 'created':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'updated':
        return <AlertCircle className="w-5 h-5 text-blue-600" />;
      case 'completed':
        return <Check className="w-5 h-5 text-green-600" />;
      case 'reminder':
        return <Clock className="w-5 h-5 text-orange-600" />;
      case 'assigned':
        return <User className="w-5 h-5 text-purple-600" />;
      case 'mentioned':
        return <Mail className="w-5 h-5 text-blue-600" />;
      default:
        return <Bell className="w-5 h-5 text-gray-600" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const clearAll = () => {
    setNotifications([]);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
        aria-label="Notifications"
      >
        <Bell className="w-6 h-6 text-gray-700" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="fixed top-16 right-4 w-96 bg-white rounded-lg shadow-2xl border border-gray-200 z-50 max-h-[600px] flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <Bell className="w-5 h-5 text-gray-700" />
              <h3 className="text-lg font-semibold text-gray-900">Notifications</h3>
              {unreadCount > 0 && (
                <span className="bg-red-100 text-red-600 text-xs font-medium px-2 py-1 rounded-full">
                  {unreadCount} new
                </span>
              )}
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <div className="overflow-y-auto flex-1">
            {loading && (
              <div className="flex items-center justify-center p-8">
                <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              </div>
            )}

            {error && (
              <div className="p-4 text-center text-red-600 text-sm">
                <AlertCircle className="w-6 h-6 mx-auto mb-2" />
                {error}
              </div>
            )}

            {!loading && !error && notifications.length === 0 && (
              <div className="p-8 text-center text-gray-500">
                <Bell className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm font-medium">No notifications yet</p>
                <p className="text-xs mt-1">You'll see updates about your tasks here</p>
              </div>
            )}

            {!loading && !error && notifications.length > 0 && (
              <div className="divide-y divide-gray-100">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`p-4 hover:bg-gray-50 transition-colors cursor-pointer ${
                      !notification.read ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 mt-1">
                        {getNotificationIcon(notification.action)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900 font-medium">
                          {notification.message}
                        </p>
                        <div className="flex items-center mt-1 space-x-2">
                          <span className="text-xs text-gray-500">
                            {formatTimestamp(notification.timestamp)}
                          </span>
                          {notification.action && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                              {notification.action}
                            </span>
                          )}
                        </div>
                      </div>
                      {!notification.read && (
                        <div className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0 mt-2"></div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {notifications.length > 0 && (
            <div className="p-3 border-t border-gray-200 bg-gray-50 flex justify-between items-center">
              <button
                onClick={clearAll}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                Clear all
              </button>
              <button
                onClick={fetchNotifications}
                className="text-sm text-gray-600 hover:text-gray-700 font-medium transition-colors"
              >
                Refresh
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationBell;