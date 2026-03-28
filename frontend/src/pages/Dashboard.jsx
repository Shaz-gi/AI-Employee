import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Mail,
  Linkedin,
  Calendar,
  Settings,
  LogOut,
  Menu,
  X,
  Sparkles,
  TrendingUp,
  MailOpen,
  CheckCircle,
  Clock,
  ArrowUpRight,
  User
} from 'lucide-react';
import { supabase } from '../lib/supabase';

function Dashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState({
    emailsProcessed: 0,
    emailsPending: 0,
    postsScheduled: 0,
    approvalsPending: 0
  });

  useEffect(() => {
    getUser();
    loadStats();
  }, []);

  const getUser = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    setUser(user);
  };

  const loadStats = async () => {
    // Simulated stats - replace with real API calls
    setStats({
      emailsProcessed: 47,
      emailsPending: 12,
      postsScheduled: 8,
      approvalsPending: 3
    });
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/inbox', icon: Mail, label: 'Inbox' },
    { path: '/linkedin', icon: Linkedin, label: 'LinkedIn' },
    { path: '/scheduler', icon: Calendar, label: 'Scheduler' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-primary-900/20">
      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={{ x: -300 }}
        animate={{ x: sidebarOpen ? 0 : -300 }}
        className={`fixed top-0 left-0 h-full w-64 glass border-r border-dark-700 z-50 lg:translate-x-0 lg:static transition-transform duration-300`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-dark-700">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <Sparkles className="w-8 h-8 text-primary-400" />
              <span className="text-xl font-bold gradient-text">AI Employee</span>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-primary-500/20 border border-primary-500 text-white'
                      : 'text-dark-300 hover:bg-dark-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* User Profile */}
          <div className="p-4 border-t border-dark-700">
            <div className="flex items-center space-x-3 px-4 py-3 rounded-lg bg-dark-800 mb-3">
              <div className="w-10 h-10 rounded-full bg-primary-500 flex items-center justify-center">
                <User className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-white truncate">
                  {user?.email?.split('@')[0] || 'User'}
                </div>
                <div className="text-xs text-dark-400 truncate">
                  {user?.email || 'user@example.com'}
                </div>
              </div>
            </div>
            <button
              onClick={handleSignOut}
              className="w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg border border-dark-700 hover:border-red-500 hover:bg-red-500/10 transition-all text-dark-300 hover:text-red-400"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </motion.aside>

      {/* Main Content */}
      <div className="lg:ml-64">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 glass border-b border-dark-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-lg hover:bg-dark-800 transition-all"
              >
                {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
              <h1 className="text-2xl font-bold text-white">Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="hidden md:flex items-center space-x-2 px-4 py-2 rounded-lg bg-primary-500/10 border border-primary-500/20">
                <span className="text-sm text-dark-300">Free Plan</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6">
          {/* Welcome Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-2xl p-8 mb-8 border border-dark-700"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-3xl font-bold text-white mb-2">
                  Welcome back! 👋
                </h2>
                <p className="text-dark-300">
                  Here's what's happening with your AI Employee today.
                </p>
              </div>
              <Sparkles className="w-12 h-12 text-primary-400 hidden md:block" />
            </div>
          </motion.div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              icon={MailOpen}
              label="Emails Processed"
              value={stats.emailsProcessed}
              trend="+12%"
              color="primary"
            />
            <StatCard
              icon={Clock}
              label="Pending Review"
              value={stats.emailsPending}
              trend="+3"
              color="yellow"
            />
            <StatCard
              icon={Linkedin}
              label="Posts Scheduled"
              value={stats.postsScheduled}
              trend="+5"
              color="purple"
            />
            <StatCard
              icon={CheckCircle}
              label="Approvals Needed"
              value={stats.approvalsPending}
              trend="Action Required"
              color="green"
            />
          </div>

          {/* Recent Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass rounded-2xl p-6 border border-dark-700"
            >
              <h3 className="text-xl font-bold text-white mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <Link
                  to="/inbox"
                  className="flex items-center justify-between p-4 rounded-lg bg-dark-800 hover:bg-dark-700 transition-all group"
                >
                  <div className="flex items-center space-x-3">
                    <Mail className="w-5 h-5 text-primary-400" />
                    <span className="text-dark-300 group-hover:text-white">Inbox</span>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-dark-500 group-hover:text-primary-400" />
                </Link>
                <Link
                  to="/linkedin"
                  className="flex items-center justify-between p-4 rounded-lg bg-dark-800 hover:bg-dark-700 transition-all group"
                >
                  <div className="flex items-center space-x-3">
                    <Calendar className="w-5 h-5 text-purple-400" />
                    <span className="text-dark-300 group-hover:text-white">Schedule Post</span>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-dark-500 group-hover:text-purple-400" />
                </Link>
              </div>
            </motion.div>

            {/* Usage Stats */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass rounded-2xl p-6 border border-dark-700"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-white">Monthly Usage</h3>
                <TrendingUp className="w-5 h-5 text-primary-400" />
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-dark-300">Emails</span>
                    <span className="text-white">47 / 100</span>
                  </div>
                  <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: '47%' }}
                      className="h-full bg-gradient-to-r from-primary-500 to-primary-400"
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-dark-300">LinkedIn Posts</span>
                    <span className="text-white">8 / 10</span>
                  </div>
                  <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: '80%' }}
                      className="h-full bg-gradient-to-r from-purple-500 to-purple-400"
                    />
                  </div>
                </div>
              </div>
              <div className="mt-6 p-4 rounded-lg bg-primary-500/10 border border-primary-500/20">
                <p className="text-sm text-dark-300">
                  <span className="text-primary-400 font-medium">Pro Tip:</span> Upgrade to Pro for 1,000 emails/month
                </p>
              </div>
            </motion.div>
          </div>
        </main>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, trend, color }) {
  const colors = {
    primary: 'from-primary-500 to-primary-400',
    yellow: 'from-yellow-500 to-yellow-400',
    purple: 'from-purple-500 to-purple-400',
    green: 'from-green-500 to-green-400',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      className="glass rounded-2xl p-6 border border-dark-700 card-hover"
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colors[color]} flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="text-xs text-green-400 font-medium bg-green-500/10 px-2 py-1 rounded">
          {trend}
        </div>
      </div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-dark-300">{label}</div>
    </motion.div>
  );
}

export default Dashboard;
