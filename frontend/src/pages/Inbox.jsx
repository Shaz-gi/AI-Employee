import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Mail,
  Search,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Inbox as InboxIcon,
  Send,
  RefreshCw,
  Eye,
  Database,
  User,
  Folder,
  ChevronDown,
  ChevronUp,
  Edit2,
  Archive
} from 'lucide-react';
import { supabase } from '../lib/supabase';

// Helper functions
function getStatusColor(status) {
  switch (status) {
    case 'pending_approval': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
    case 'approved': return 'text-green-400 bg-green-500/10 border-green-500/20';
    case 'sent': return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
    case 'rejected': return 'text-red-400 bg-red-500/10 border-red-500/20';
    case 'failed': return 'text-red-400 bg-red-500/10 border-red-500/20';
    default: return 'text-dark-400 bg-dark-800 border-dark-700';
  }
}

function getStatusIcon(status) {
  switch (status) {
    case 'pending_approval': return <Clock className="w-4 h-4" />;
    case 'approved': return <CheckCircle className="w-4 h-4" />;
    case 'sent': return <Send className="w-4 h-4" />;
    case 'rejected': return <XCircle className="w-4 h-4" />;
    case 'failed': return <AlertCircle className="w-4 h-4" />;
    default: return <InboxIcon className="w-4 h-4" />;
  }
}

function Inbox() {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedEmail, setExpandedEmail] = useState(null);
  const [processingId, setProcessingId] = useState(null);
  const [debugInfo, setDebugInfo] = useState({ user: null, vault: null, error: null });

  useEffect(() => {
    loadEmails();
    const interval = setInterval(loadEmails, 30000);
    return () => clearInterval(interval);
  }, [filter]);

  const loadEmails = async () => {
    setLoading(true);
    setDebugInfo({ user: null, vault: null, error: null });

    try {
      const { data: { user }, error: authError } = await supabase.auth.getUser();

      if (authError || !user) {
        setDebugInfo(prev => ({ ...prev, error: authError?.message || 'Not logged in' }));
        setLoading(false);
        return;
      }

      setDebugInfo(prev => ({ ...prev, user }));

      const { data: vaults, error: vaultError } = await supabase
        .from('vaults')
        .select('id')
        .eq('user_id', user.id)
        .limit(1);

      if (vaultError || !vaults || vaults.length === 0) {
        setDebugInfo(prev => ({ ...prev, error: 'No vault found. Please connect Gmail first.' }));
        setLoading(false);
        return;
      }

      setDebugInfo(prev => ({ ...prev, vault: vaults[0] }));

      let query = supabase
        .from('emails')
        .select('*')
        .eq('vault_id', vaults[0].id)
        .order('received_at', { ascending: false });

      if (filter !== 'all') {
        query = query.eq('status', filter);
      }

      const { data, error } = await query;

      if (error) {
        setDebugInfo(prev => ({ ...prev, error: `Email error: ${error.message}` }));
        setLoading(false);
        return;
      }

      setEmails(data || []);

    } catch (error) {
      setDebugInfo(prev => ({ ...prev, error: `Unexpected error: ${error.message}` }));
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (emailId) => {
    try {
      setProcessingId(emailId);

      const { error } = await supabase
        .from('emails')
        .update({
          status: 'approved',
          approved_at: new Date().toISOString()
        })
        .eq('id', emailId);

      if (error) throw error;

      setEmails(prev => prev.map(e => 
        e.id === emailId ? { ...e, status: 'approved', approved_at: new Date().toISOString() } : e
      ));
      
      if (expandedEmail?.id === emailId) {
        setExpandedEmail(null);
      }

      alert('✅ Email approved! It will be sent within 30 seconds.');

    } catch (error) {
      alert('❌ Failed to approve: ' + error.message);
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (emailId) => {
    try {
      setProcessingId(emailId);

      const { error } = await supabase
        .from('emails')
        .update({
          status: 'rejected',
          rejected_at: new Date().toISOString()
        })
        .eq('id', emailId);

      if (error) throw error;

      setEmails(prev => prev.map(e => 
        e.id === emailId ? { ...e, status: 'rejected', rejected_at: new Date().toISOString() } : e
      ));
      
      if (expandedEmail?.id === emailId) {
        setExpandedEmail(null);
      }

      alert('✅ Email rejected.');

    } catch (error) {
      alert('❌ Failed to reject: ' + error.message);
    } finally {
      setProcessingId(null);
    }
  };

  const filteredEmails = emails.filter(email =>
    email.subject?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    email.from_address?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const stats = {
    total: emails.length,
    pending: emails.filter(e => e.status === 'pending_approval').length,
    approved: emails.filter(e => e.status === 'approved').length,
    sent: emails.filter(e => e.status === 'sent').length
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-primary-900/20">
      {/* Header */}
      <header className="sticky top-0 z-30 glass border-b border-dark-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Inbox</h1>
            <p className="text-dark-300 text-sm">Manage, review & approve AI-drafted responses</p>
          </div>
          <button
            onClick={loadEmails}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-primary-500/10 border border-primary-500/20 hover:bg-primary-500/20 transition-all"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        {/* Debug Info */}
        {debugInfo.error && (
          <div className="mb-6 glass rounded-xl p-6 border border-red-500/20">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-lg font-bold text-red-400 mb-2">Issue Detected</h3>
                <p className="text-dark-300 text-sm mb-4">{debugInfo.error}</p>
                {!debugInfo.user && (
                  <div className="text-sm text-red-300">
                    <p className="font-medium mb-2">Solution:</p>
                    <ol className="list-decimal list-inside space-y-1">
                      <li>Go to <a href="/login" className="text-primary-400 underline">Login</a> page</li>
                      <li>Sign in with your account</li>
                      <li>Return to this page</li>
                    </ol>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <StatCard icon={<InboxIcon className="w-5 h-5" />} label="Total" value={stats.total} color="primary" />
          <StatCard icon={<Clock className="w-5 h-5" />} label="Pending" value={stats.pending} color="yellow" />
          <StatCard icon={<CheckCircle className="w-5 h-5" />} label="Approved" value={stats.approved} color="green" />
          <StatCard icon={<Send className="w-5 h-5" />} label="Sent" value={stats.sent} color="blue" />
        </div>

        {/* Filters and Search */}
        <div className="glass rounded-xl p-4 border border-dark-700 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex space-x-2 flex-wrap">
              <FilterButton active={filter === 'all'} onClick={() => setFilter('all')} label="All" count={stats.total} />
              <FilterButton active={filter === 'pending_approval'} onClick={() => setFilter('pending_approval')} label="Pending" count={stats.pending} />
              <FilterButton active={filter === 'approved'} onClick={() => setFilter('approved')} label="Approved" count={stats.approved} />
              <FilterButton active={filter === 'sent'} onClick={() => setFilter('sent')} label="Sent" count={stats.sent} />
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dark-400" />
              <input
                type="text"
                placeholder="Search emails..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full md:w-64 pl-10 pr-4 py-2 bg-dark-800 border border-dark-700 rounded-lg focus:outline-none focus:border-primary-500 text-white text-sm"
              />
            </div>
          </div>
        </div>

        {/* Email List */}
        <div className="glass rounded-xl border border-dark-700 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-dark-300">Loading emails...</p>
            </div>
          ) : filteredEmails.length === 0 ? (
            <div className="p-8 text-center">
              <InboxIcon className="w-12 h-12 text-dark-500 mx-auto mb-4" />
              <p className="text-dark-300">
                {debugInfo.error ? 'Fix the issues above to see emails' : 'No emails found'}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-dark-700">
              <AnimatePresence>
                {filteredEmails.map((email) => (
                  <EmailItem
                    key={email.id}
                    email={email}
                    isExpanded={expandedEmail?.id === email.id}
                    onToggle={() => setExpandedEmail(expandedEmail?.id === email.id ? null : email)}
                    onApprove={() => handleApprove(email.id)}
                    onReject={() => handleReject(email.id)}
                    isProcessing={processingId === email.id}
                  />
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function StatCard({ icon, label, value, color }) {
  const colors = {
    primary: 'from-primary-500 to-primary-400',
    yellow: 'from-yellow-500 to-yellow-400',
    green: 'from-green-500 to-green-400',
    blue: 'from-blue-500 to-blue-400',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass p-6 rounded-xl border border-dark-700"
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${colors[color]} flex items-center justify-center`}>
          <div className="text-white">{icon}</div>
        </div>
      </div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-dark-300">{label}</div>
    </motion.div>
  );
}

function FilterButton({ active, onClick, label, count }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
        active
          ? 'bg-primary-500 text-white'
          : 'bg-dark-800 text-dark-300 hover:bg-dark-700'
      }`}
    >
      {label}
      {count > 0 && (
        <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
          active ? 'bg-white/20' : 'bg-dark-700'
        }`}>
          {count}
        </span>
      )}
    </button>
  );
}

function EmailItem({ email, isExpanded, onToggle, onApprove, onReject, isProcessing }) {
  const statusColor = getStatusColor(email.status);
  const statusIcon = getStatusIcon(email.status);
  const needsApproval = email.status === 'pending_approval' && email.requires_approval;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="transition-all"
    >
      {/* Email Row */}
      <div
        className={`p-4 hover:bg-dark-800/50 transition-all cursor-pointer ${
          isExpanded ? 'bg-dark-800/50' : ''
        }`}
        onClick={onToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 flex-1 min-w-0">
            <div className="w-10 h-10 rounded-full bg-dark-700 flex items-center justify-center flex-shrink-0">
              <Mail className="w-5 h-5 text-dark-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <h3 className="text-white font-medium truncate">{email.subject}</h3>
                <span className={`flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs ${statusColor}`}>
                  {statusIcon}
                  <span className="capitalize">{email.status?.replace('_', ' ')}</span>
                </span>
                {needsApproval && (
                  <span className="px-2 py-0.5 rounded-full text-xs bg-red-500/10 text-red-400 border border-red-500/20 animate-pulse">
                    Action Required
                  </span>
                )}
              </div>
              <p className="text-dark-400 text-sm truncate">{email.from_address}</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-sm text-dark-300">
                {new Date(email.received_at).toLocaleDateString()}
              </div>
              <div className="text-xs text-dark-500">
                {new Date(email.received_at).toLocaleTimeString()}
              </div>
            </div>
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-dark-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-dark-400" />
            )}
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden border-t border-dark-700"
          >
            <div className="p-6 space-y-4 bg-dark-900/30">
              {/* Email Metadata */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-dark-400">From:</span>
                  <p className="text-white">{email.from_address}</p>
                </div>
                <div>
                  <span className="text-dark-400">Received:</span>
                  <p className="text-white">{new Date(email.received_at).toLocaleString()}</p>
                </div>
              </div>

              {/* AI Analysis */}
              {email.ai_analysis && (
                <div className="glass p-4 rounded-lg border border-primary-500/20">
                  <h4 className="text-sm font-medium text-primary-400 mb-2 flex items-center">
                    <AlertCircle className="w-4 h-4 mr-2" />
                    AI Analysis
                  </h4>
                  <p className="text-dark-300 text-sm">{email.ai_analysis}</p>
                </div>
              )}

              {/* AI Draft Response */}
              {email.ai_draft_response && (
                <div className="glass p-4 rounded-lg border border-green-500/20">
                  <h4 className="text-sm font-medium text-green-400 mb-2 flex items-center">
                    <Edit2 className="w-4 h-4 mr-2" />
                    AI Draft Response
                  </h4>
                  <div className="text-dark-300 text-sm whitespace-pre-wrap bg-dark-800/50 p-3 rounded">
                    {email.ai_draft_response}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              {needsApproval && (
                <div className="flex space-x-3 pt-4 border-t border-dark-700">
                  <button
                    onClick={(e) => { e.stopPropagation(); onApprove(); }}
                    disabled={isProcessing}
                    className="flex-1 btn-primary py-3 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isProcessing ? (
                      <div className="flex items-center justify-center space-x-2">
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Processing...</span>
                      </div>
                    ) : (
                      <>
                        <CheckCircle className="w-5 h-5" />
                        <span>Approve & Send</span>
                      </>
                    )}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); onReject(); }}
                    disabled={isProcessing}
                    className="px-6 py-3 rounded-lg border border-red-500 text-red-400 hover:bg-red-500/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isProcessing ? (
                      <div className="flex items-center justify-center space-x-2">
                        <div className="w-5 h-5 border-2 border-red-400 border-t-transparent rounded-full animate-spin"></div>
                        <span>Processing...</span>
                      </div>
                    ) : (
                      <>
                        <XCircle className="w-5 h-5" />
                        <span>Reject</span>
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* Info for non-pending emails */}
              {!needsApproval && (
                <div className="flex items-center space-x-2 text-sm text-dark-400 pt-4 border-t border-dark-700">
                  <Archive className="w-4 h-4" />
                  <span>
                    {email.status === 'sent' && 'This email has been sent'}
                    {email.status === 'rejected' && 'This email was rejected'}
                    {email.status === 'approved' && 'This email is approved and will be sent'}
                  </span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default Inbox;
