import React from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { Calendar, Settings, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Layout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-24 md:pb-0">
      <nav className="bg-white shadow-sm border-b hidden md:block">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Calendar className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">SmartMeet AI</span>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">Welcome, {user?.name}</span>

              <Link
                to="/settings"
                aria-label="Settings"
                title="Settings"
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
              >
                <Settings className="h-5 w-5" />
              </Link>

              <button
                type="button"
                onClick={handleLogout}
                aria-label="Log out"
                title="Log out"
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Mobile Bottom Nav */}
      <nav aria-label="Mobile navigation" className="md:hidden fixed inset-x-0 bottom-0 bg-white border-t shadow-lg">
        <div className="flex justify-around py-2">
          <Link
            to="/"
            aria-label="Meetings dashboard"
            className={`flex flex-col items-center text-xs p-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded-lg ${
              location.pathname === '/' ? 'text-primary-600 font-medium' : 'text-gray-500'
            }`}
          >
            <Calendar className="h-6 w-6" />
            <span>Meetings</span>
          </Link>
          <Link
            to="/settings"
            aria-label="Settings"
            className={`flex flex-col items-center text-xs p-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded-lg ${
              location.pathname.includes('settings') ? 'text-primary-600 font-medium' : 'text-gray-500'
            }`}
          >
            <Settings className="h-6 w-6" />
            <span>Settings</span>
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            aria-label="Log out"
            className="flex flex-col items-center text-xs text-gray-500 p-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded-lg hover:text-gray-900"
          >
            <LogOut className="h-6 w-6" />
            <span>Logout</span>
          </button>
        </div>
      </nav>
    </div>
  );
};

export default Layout;
