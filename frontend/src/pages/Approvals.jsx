import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  Mail, 
  User, 
  Calendar,
  RefreshCw,
  Eye,
  AlertCircle
} from 'lucide-react';
import { supabase } from '../lib/supabase';

function Approvals() {
  const [pendingEmails, setPendingEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [processingId, setProcessingId] = useState(null);

  useEffect(() => {
    loadPendingEmails();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadPendingEmails, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadPendingEmails = async () => {
    try {
      setLoading(true);
      
      // Get current user
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        console.log('No user logged in');
        return;
      }

      // Get user's vault
      const { data: vaults } = await supabase
        .from('vaults')
        .select('id')
        .eq('user_id', user.id)
        .limit(1);

      if (!vaults || vaults.length === 0) {
        console.log('No vault found');
        setLoading(false);
        return;
      }

      // Load pending emails (emails that need approval)
      const { data, error } = await supabase
        .from('emails')
        .select('*')
        .eq('vault_id', vaults[0].id)
        .eq('requires_approval', true)
        .eq('status', 'pending_approval')
        .order('received_at', { ascending: false });

      if (error) throw error;

      setPendingEmails(data || []);
      
    } catch (error) {
      console.error('Error loading pending emails:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (emailId) => {
    try {
      setProcessingId(emailId);
      
      // Update email status to approved
      const { error } = await supabase
        .from('emails')
        .update({ 
          status: 'approved',
          approved_at: new Date().toISOString()
        })
        .eq('id', emailId);

      if (error) throw error;

      // Remove from list
      setPendingEmails(prev => prev.filter(e => e.id !== emailId));
      
      alert('✅ Email approved! It will be sent within 30 seconds.');
      
    } catch (error) {
      console.error('Error approving email:', error);
      alert('❌ Failed to approve email: ' + error.message);
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (emailId) => {
    try {
      setProcessingId(emailId);
      
      // Update email status to rejected
      const { error } = await supabase
        .from('emails')
        .update({ 
          status: 'rejected',
          rejected_at: new Date().toISOString()
        })
        .eq('id', emailId);

      if (error) throw error;

      // Remove from list
      setPendingEmails(prev => prev.filter(e => e.id !== emailId));
      
      alert('✅ Email rejected.');
      
    } catch (error) {
      console.error('Error rejecting email:', error);
      alert('❌ Failed to reject email: ' + error.message);
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-primary-900/20">
      {/* Header */}
      <header className="sticky top-0 z-30 glass border-b border-dark-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Pending Approvals</h1>
            <p className="text-dark-300 text-sm">Review and approve AI-drafted responses</p>
          </div>
          <button
            onClick={loadPendingEmails}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-primary-500/10 border border-primary-500/20 hover:bg-primary-500/20 transition-all"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <StatCard
            icon={<Clock className="w-5 h-5" />}
            label="Pending Approval"
            value={pendingEmails.length}
            color="yellow"
          />
          <StatCard
            icon={<CheckCircle className="w-5 h-5" />}
            label="Approved Today"
            value="0"
            color="green"
          />
          <StatCard
            icon={<Mail className="w-5 h-5" />}
            label="Total Processed"
            value={pendingEmails.length}
            color="primary"
          />
        </div>

        {/* Pending Emails List */}
        <div className="glass rounded-xl border border-dark-700 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-dark-300">Loading pending approvals...</p>
            </div>
          ) : pendingEmails.length === 0 ? (
            <div className="p-8 text-center">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">All Caught Up!</h3>
              <p className="text-dark-300">No pending approvals at the moment.</p>
              <p className="text-dark-500 text-sm mt-2">
                New emails requiring approval will appear here.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-dark-700">
              {pendingEmails.map((email) => (
                <EmailApprovalItem
                  key={email.id}
                  email={email}
                  onApprove={() => handleApprove(email.id)}
                  onReject={() => handleReject(email.id)}
                  isProcessing={processingId === email.id}
                  onView={() => setSelectedEmail(email)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Email Detail Modal */}
        {selectedEmail && (
          <EmailDetailModal
            email={selectedEmail}
            onClose={() => setSelectedEmail(null)}
            onApprove={() => {
              handleApprove(selectedEmail.id);
              setSelectedEmail(null);
            }}
            onReject={() => {
              handleReject(selectedEmail.id);
              setSelectedEmail(null);
            }}
            isProcessing={processingId === selectedEmail.id}
          />
        )}
      </main>
    </div>
  );
}

function StatCard({ icon, label, value, color }) {
  const colors = {
    primary: 'from-primary-500 to-primary-400',
    yellow: 'from-yellow-500 to-yellow-400',
    green: 'from-green-500 to-green-400',
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

function EmailApprovalItem({ email, onApprove, onReject, isProcessing, onView }) {
  const subject = email.subject || 'No Subject';
  const fromAddress = email.from_address || 'Unknown';
  const aiAnalysis = email.ai_analysis || 'No AI analysis available';
  const draftResponse = email.ai_draft_response;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-6 hover:bg-dark-800/50 transition-all"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-4 flex-1">
          <div className="w-12 h-12 rounded-full bg-yellow-500/10 flex items-center justify-center flex-shrink-0">
            <Clock className="w-6 h-6 text-yellow-400" />
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-2">
              <h3 className="text-lg font-bold text-white truncate">{subject}</h3>
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
                Pending Approval
              </span>
            </div>
            
            <div className="flex items-center space-x-4 text-sm text-dark-400 mb-3">
              <div className="flex items-center space-x-1">
                <User className="w-4 h-4" />
                <span>{fromAddress}</span>
              </div>
              <div className="flex items-center space-x-1">
                <Calendar className="w-4 h-4" />
                <span>{new Date(email.received_at).toLocaleString()}</span>
              </div>
            </div>
            
            {/* AI Analysis Preview */}
            <div className="glass p-3 rounded-lg mb-3 border border-primary-500/20">
              <div className="flex items-center space-x-2 mb-2">
                <AlertCircle className="w-4 h-4 text-primary-400" />
                <span className="text-sm font-medium text-primary-400">AI Analysis</span>
              </div>
              <p className="text-sm text-dark-300 line-clamp-2">
                {aiAnalysis}
              </p>
            </div>
            
            {/* Draft Response Preview */}
            {draftResponse && (
              <div className="glass p-3 rounded-lg border border-green-500/20">
                <div className="flex items-center space-x-2 mb-2">
                  <Mail className="w-4 h-4 text-green-400" />
                  <span className="text-sm font-medium text-green-400">Draft Response</span>
                </div>
                <p className="text-sm text-dark-300 line-clamp-2">
                  {draftResponse}
                </p>
              </div>
            )}
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex flex-col space-y-2 ml-4">
          <button
            onClick={onView}
            disabled={isProcessing}
            className="px-4 py-2 rounded-lg border border-dark-300 hover:bg-dark-700 transition-all text-sm flex items-center space-x-2"
          >
            <Eye className="w-4 h-4" />
            <span>View</span>
          </button>
          
          <button
            onClick={onApprove}
            disabled={isProcessing}
            className="px-4 py-2 rounded-lg bg-green-500 hover:bg-green-600 transition-all text-sm flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <CheckCircle className="w-4 h-4" />
            <span>Approve</span>
          </button>
          
          <button
            onClick={onReject}
            disabled={isProcessing}
            className="px-4 py-2 rounded-lg border border-red-500 text-red-400 hover:bg-red-500/10 transition-all text-sm flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <XCircle className="w-4 h-4" />
            <span>Reject</span>
          </button>
        </div>
      </div>
    </motion.div>
  );
}

function EmailDetailModal({ email, onClose, onApprove, onReject, isProcessing }) {
  const subject = email.subject || 'No Subject';
  const fromAddress = email.from_address || 'Unknown';
  const aiAnalysis = email.ai_analysis || 'No AI analysis available';
  const draftResponse = email.ai_draft_response || 'No draft response generated';

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass rounded-2xl border border-dark-700 max-w-4xl w-full max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="sticky top-0 bg-dark-900/90 backdrop-blur border-b border-dark-700 p-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Approval Required</h2>
            <p className="text-dark-300 text-sm">Review AI-drafted response</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-dark-800 transition-all"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Email Info */}
          <div className="space-y-3">
            <div>
              <label className="text-sm text-dark-400">From</label>
              <p className="text-white">{fromAddress}</p>
            </div>
            <div>
              <label className="text-sm text-dark-400">Subject</label>
              <p className="text-white">{subject}</p>
            </div>
            <div>
              <label className="text-sm text-dark-400">Received</label>
              <p className="text-white">{new Date(email.received_at).toLocaleString()}</p>
            </div>
          </div>

          {/* AI Analysis */}
          <div className="glass p-4 rounded-lg border border-primary-500/20">
            <h3 className="text-sm font-medium text-primary-400 mb-2 flex items-center">
              <AlertCircle className="w-4 h-4 mr-2" />
              AI Analysis
            </h3>
            <p className="text-dark-300 text-sm whitespace-pre-wrap">{aiAnalysis}</p>
          </div>

          {/* Draft Response */}
          <div className="glass p-4 rounded-lg border border-green-500/20">
            <h3 className="text-sm font-medium text-green-400 mb-2 flex items-center">
              <Mail className="w-4 h-4 mr-2" />
              Draft Response (Ready to Send)
            </h3>
            <div className="text-dark-300 text-sm whitespace-pre-wrap bg-dark-800/50 p-3 rounded">
              {draftResponse}
            </div>
          </div>

          {/* Warning */}
          <div className="bg-yellow-500/10 border border-yellow-500/20 p-4 rounded-lg">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-yellow-400 font-medium">Important</p>
                <p className="text-sm text-dark-300 mt-1">
                  Approving this email will send the draft response to <strong>{fromAddress}</strong>. 
                  The email will be sent within 30 seconds of approval.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-dark-700 flex space-x-3">
          <button
            onClick={onApprove}
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
            onClick={onReject}
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
      </motion.div>
    </div>
  );
}

export default Approvals;
