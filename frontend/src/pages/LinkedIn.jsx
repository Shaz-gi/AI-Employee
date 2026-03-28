import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Linkedin,
  Calendar,
  Plus,
  Clock,
  CheckCircle,
  TrendingUp,
  RefreshCw,
  ExternalLink,
  Trash2,
  Edit,
  Sparkles,
  XCircle,
  Eye,
  Zap,
  AlertCircle
} from 'lucide-react';
import { supabase } from '../lib/supabase';

function LinkedIn() {
  const [isConnected, setIsConnected] = useState(false);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [showAiGenerateModal, setShowAiGenerateModal] = useState(false);
  const [generatingPost, setGeneratingPost] = useState(false);
  const [newPost, setNewPost] = useState({
    content: '',
    scheduledFor: '',
    post_type: 'insight'
  });
  const [selectedPost, setSelectedPost] = useState(null);
  const [processingId, setProcessingId] = useState(null);

  useEffect(() => {
    checkConnection();
    loadPosts();
  }, []);

  const checkConnection = async () => {
    const connected = localStorage.getItem('linkedin_connected');
    setIsConnected(connected === 'true');
  };

  const connectLinkedIn = async () => {
    localStorage.setItem('linkedin_connected', 'true');
    setIsConnected(true);
    alert('LinkedIn connected! You can now schedule and post.');
  };

  const disconnectLinkedIn = async () => {
    localStorage.removeItem('linkedin_connected');
    setIsConnected(false);
    alert('LinkedIn disconnected');
  };

  const loadPosts = async () => {
    try {
      setLoading(true);
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data: vaults } = await supabase
        .from('vaults')
        .select('id')
        .eq('user_id', user.id)
        .limit(1);

      if (!vaults) return;

      const { data, error } = await supabase
        .from('linkedin_posts')
        .select('*')
        .eq('vault_id', vaults[0].id)
        .order('created_at', { ascending: false });

      if (error) throw error;
      setPosts(data || []);
    } catch (error) {
      console.error('Error loading posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateWithAI = async () => {
    setGeneratingPost(true);
    try {
      // Get current user
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        alert('Please log in first');
        return;
      }

      // Get user's vault
      const { data: vaults } = await supabase
        .from('vaults')
        .select('id')
        .eq('user_id', user.id)
        .limit(1);

      if (!vaults || vaults.length === 0) {
        alert('No vault found. Please create a vault first.');
        return;
      }

      // Create a generation request in database
      const { error } = await supabase
        .from('linkedin_posts')
        .insert({
          vault_id: vaults[0].id,
          user_id: user.id,
          content: 'Generating...',
          post_type: 'pending_ai_generation',
          status: 'generating',
          generated_at: new Date().toISOString()
        });

      if (error) {
        console.error('Error creating generation request:', error);
        alert('Failed to start AI generation: ' + error.message);
        return;
      }

      // Poll for the generated post (check every 2 seconds for up to 30 seconds)
      let attempts = 0;
      const maxAttempts = 15;
      
      const pollInterval = setInterval(async () => {
        attempts++;
        
        const { data: posts } = await supabase
          .from('linkedin_posts')
          .select('*')
          .eq('vault_id', vaults[0].id)
          .eq('status', 'pending_approval')
          .eq('ai_generated', true)
          .order('created_at', { ascending: false })
          .limit(1);

        if (posts && posts.length > 0) {
          // Post generated successfully!
          clearInterval(pollInterval);
          setGeneratingPost(false);
          alert('✅ AI post generated successfully! Check the pending posts.');
          loadPosts(); // Refresh the posts list
        } else if (attempts >= maxAttempts) {
          // Timeout
          clearInterval(pollInterval);
          setGeneratingPost(false);
          alert('⏰ Generation timed out. Please try again.');
        }
      }, 2000);

    } catch (error) {
      console.error('Generation error:', error);
      setGeneratingPost(false);
      alert('Failed to generate post: ' + error.message);
    }
  };

  const handleApprovePost = async (postId) => {
    try {
      setProcessingId(postId);
      
      const { error } = await supabase
        .from('linkedin_posts')
        .update({
          status: 'approved',
          approved_at: new Date().toISOString()
        })
        .eq('id', postId);
      
      if (error) throw error;
      
      setPosts(prev => prev.map(p => 
        p.id === postId ? { ...p, status: 'approved', approved_at: new Date().toISOString() } : p
      ));
      
      if (selectedPost?.id === postId) {
        setSelectedPost(null);
      }
      
      alert('✅ Post approved! It will be posted automatically.');
    } catch (error) {
      alert('❌ Failed to approve: ' + error.message);
    } finally {
      setProcessingId(null);
    }
  };

  const handleRejectPost = async (postId) => {
    try {
      setProcessingId(postId);
      
      const { error } = await supabase
        .from('linkedin_posts')
        .update({
          status: 'rejected',
          rejected_at: new Date().toISOString()
        })
        .eq('id', postId);
      
      if (error) throw error;
      
      setPosts(prev => prev.map(p => 
        p.id === postId ? { ...p, status: 'rejected', rejected_at: new Date().toISOString() } : p
      ));
      
      if (selectedPost?.id === postId) {
        setSelectedPost(null);
      }
      
      alert('✅ Post rejected.');
    } catch (error) {
      alert('❌ Failed to reject: ' + error.message);
    } finally {
      setProcessingId(null);
    }
  };

  const handleSchedulePost = async () => {
    if (!newPost.content.trim()) {
      alert('Please enter post content');
      return;
    }

    try {
      const { data: { user } } = await supabase.auth.getUser();
      const { data: vaults } = await supabase
        .from('vaults')
        .select('id')
        .eq('user_id', user.id)
        .limit(1);

      const { error } = await supabase
        .from('linkedin_posts')
        .insert({
          vault_id: vaults[0].id,
          content: newPost.content,
          scheduled_for: newPost.scheduledFor || null,
          status: newPost.scheduledFor ? 'scheduled' : 'draft'
        });

      if (error) throw error;

      alert('Post scheduled successfully!');
      setShowScheduleModal(false);
      setNewPost({ content: '', scheduledFor: '' });
      loadPosts();
    } catch (error) {
      alert('Error scheduling post: ' + error.message);
    }
  };

  const handlePostNow = async () => {
    if (!newPost.content.trim()) {
      alert('Please enter post content');
      return;
    }

    // Simulate posting to LinkedIn
    alert('Posting to LinkedIn... (In production, this would use LinkedIn API)');
    
    // For demo, just mark as posted
    try {
      const { data: { user } } = await supabase.auth.getUser();
      const { data: vaults } = await supabase
        .from('vaults')
        .select('id')
        .eq('user_id', user.id)
        .limit(1);

      const { error } = await supabase
        .from('linkedin_posts')
        .insert({
          vault_id: vaults[0].id,
          content: newPost.content,
          status: 'posted',
          posted_at: new Date().toISOString()
        });

      if (error) throw error;

      alert('Posted successfully!');
      setShowScheduleModal(false);
      setNewPost({ content: '', scheduledFor: '' });
      loadPosts();
    } catch (error) {
      alert('Error posting: ' + error.message);
    }
  };

  const handleDeletePost = async (postId) => {
    if (!confirm('Delete this post?')) return;

    try {
      await supabase
        .from('linkedin_posts')
        .delete()
        .eq('id', postId);

      loadPosts();
    } catch (error) {
      alert('Error deleting post: ' + error.message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'scheduled': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
      case 'approved': return 'text-green-400 bg-green-500/10 border-green-500/20';
      case 'posted': return 'text-green-400 bg-green-500/10 border-green-500/20';
      case 'pending_approval': return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'rejected': return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'draft': return 'text-dark-400 bg-dark-800 border-dark-700';
      default: return 'text-dark-400 bg-dark-800 border-dark-700';
    }
  };

  const stats = {
    total: posts.length,
    pending: posts.filter(p => p.status === 'pending_approval').length,
    approved: posts.filter(p => p.status === 'approved').length,
    scheduled: posts.filter(p => p.status === 'scheduled').length,
    posted: posts.filter(p => p.status === 'posted').length,
  };

  if (!isConnected) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-primary-900/20 flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-12 max-w-2xl w-full border border-dark-700 text-center"
        >
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center mx-auto mb-6">
            <Linkedin className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-4">Connect Your LinkedIn</h1>
          <p className="text-dark-300 text-lg mb-8 max-w-md mx-auto">
            Connect your LinkedIn account to schedule and automatically post content. 
            Your AI Employee will help you create engaging posts.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="glass p-4 rounded-lg">
              <CheckCircle className="w-8 h-8 text-primary-400 mx-auto mb-2" />
              <p className="text-sm text-dark-300">Auto-Post Content</p>
            </div>
            <div className="glass p-4 rounded-lg">
              <Calendar className="w-8 h-8 text-primary-400 mx-auto mb-2" />
              <p className="text-sm text-dark-300">Schedule Posts</p>
            </div>
            <div className="glass p-4 rounded-lg">
              <TrendingUp className="w-8 h-8 text-primary-400 mx-auto mb-2" />
              <p className="text-sm text-dark-300">Track Engagement</p>
            </div>
          </div>
          <button
            onClick={connectLinkedIn}
            className="btn-primary text-lg px-8 py-4"
          >
            <Linkedin className="w-5 h-5" />
            Connect LinkedIn Account
          </button>
          <p className="text-dark-400 text-sm mt-4">
            Secure OAuth connection • Disconnect anytime
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-primary-900/20">
      {/* Header */}
      <header className="sticky top-0 z-30 glass border-b border-dark-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                <Linkedin className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">LinkedIn Manager</h1>
                <p className="text-dark-300 text-sm">Schedule and manage your LinkedIn posts</p>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={loadPosts}
              className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-primary-500/10 border border-primary-500/20 hover:bg-primary-500/20 transition-all"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => setShowAiGenerateModal(true)}
              className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 transition-all text-white"
            >
              <Sparkles className="w-4 h-4" />
              <span>AI Generate</span>
            </button>
            <button
              onClick={() => setShowScheduleModal(true)}
              className="btn-primary"
            >
              <Plus className="w-4 h-4" />
              New Post
            </button>
            <button
              onClick={disconnectLinkedIn}
              className="px-4 py-2 rounded-lg border border-dark-300 hover:bg-dark-800 transition-all text-sm"
            >
              Disconnect
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-6">
          <StatCard
            icon={<Calendar className="w-5 h-5" />}
            label="Total"
            value={stats.total}
            color="primary"
          />
          <StatCard
            icon={<Clock className="w-5 h-5" />}
            label="Pending"
            value={stats.pending}
            color="red"
          />
          <StatCard
            icon={<CheckCircle className="w-5 h-5" />}
            label="Approved"
            value={stats.approved}
            color="green"
          />
          <StatCard
            icon={<Clock className="w-5 h-5" />}
            label="Scheduled"
            value={stats.scheduled}
            color="yellow"
          />
          <StatCard
            icon={<TrendingUp className="w-5 h-5" />}
            label="Posted"
            value={stats.posted}
            color="blue"
          />
        </div>

        {/* Posts List */}
        <div className="glass rounded-xl border border-dark-700 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-dark-300">Loading posts...</p>
            </div>
          ) : posts.length === 0 ? (
            <div className="p-8 text-center">
              <Calendar className="w-12 h-12 text-dark-500 mx-auto mb-4" />
              <p className="text-dark-300 mb-4">No posts yet</p>
              <button
                onClick={() => setShowScheduleModal(true)}
                className="btn-primary"
              >
                <Plus className="w-4 h-4" />
                Create Your First Post
              </button>
            </div>
          ) : (
            <div className="divide-y divide-dark-700">
              {posts.map((post) => (
                <PostItem
                  key={post.id}
                  post={post}
                  onDelete={() => handleDeletePost(post.id)}
                  onApprove={() => handleApprovePost(post.id)}
                  onReject={() => handleRejectPost(post.id)}
                  onView={(p) => setSelectedPost(p)}
                  isProcessing={processingId === post.id}
                />
              ))}
            </div>
          )}
        </div>

        {/* Schedule Modal */}
        {showScheduleModal && (
          <ScheduleModal
            newPost={newPost}
            setNewPost={setNewPost}
            onClose={() => setShowScheduleModal(false)}
            onSchedule={handleSchedulePost}
            onPostNow={handlePostNow}
          />
        )}

        {/* AI Generate Modal */}
        {showAiGenerateModal && (
          <AiGenerateModal
            onClose={() => setShowAiGenerateModal(false)}
            onGenerate={generateWithAI}
            isGenerating={generatingPost}
          />
        )}

        {/* Post Detail Modal */}
        {selectedPost && (
          <PostDetailModal
            post={selectedPost}
            onClose={() => setSelectedPost(null)}
            onApprove={() => handleApprovePost(selectedPost.id)}
            onReject={() => handleRejectPost(selectedPost.id)}
            isProcessing={processingId === selectedPost.id}
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
    gray: 'from-dark-500 to-dark-400',
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

function PostItem({ post, onDelete, onApprove, onReject, onView, isProcessing }) {
  const statusColor = getStatusColor(post.status);
  const needsApproval = post.status === 'pending_approval';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-6 hover:bg-dark-800/50 transition-all border-b border-dark-700 last:border-0"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColor}`}>
              {post.status?.replace('_', ' ')}
            </span>
            {needsApproval && (
              <span className="px-2 py-0.5 rounded-full text-xs bg-red-500/10 text-red-400 border border-red-500/20 animate-pulse">
                Action Required
              </span>
            )}
            {post.post_type && (
              <span className="px-2 py-0.5 rounded-full text-xs bg-primary-500/10 text-primary-400 border border-primary-500/20">
                {post.post_type}
              </span>
            )}
            {post.scheduled_for && (
              <span className="flex items-center space-x-1 text-xs text-dark-400">
                <Clock className="w-3 h-3" />
                <span>{new Date(post.scheduled_for).toLocaleString()}</span>
              </span>
            )}
          </div>
          <p className="text-dark-300 text-sm line-clamp-2 mb-2">{post.content}</p>
          
          {post.generated_at && (
            <div className="text-xs text-dark-500">
              Generated: {new Date(post.generated_at).toLocaleString()}
            </div>
          )}
          
          {post.posted_at && (
            <div className="mt-2 flex items-center space-x-4 text-xs text-dark-500">
              <span>Posted: {new Date(post.posted_at).toLocaleString()}</span>
              {post.linkedin_url && (
                <a
                  href={post.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1 text-primary-400 hover:text-primary-300"
                >
                  <span>View Post</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {needsApproval && (
            <>
              <button
                onClick={() => onApprove(post.id)}
                disabled={isProcessing}
                className="px-3 py-1.5 rounded-lg bg-green-500 hover:bg-green-600 transition-all text-sm flex items-center space-x-1 disabled:opacity-50"
              >
                <CheckCircle className="w-3 h-3" />
                <span>Approve</span>
              </button>
              <button
                onClick={() => onReject(post.id)}
                disabled={isProcessing}
                className="px-3 py-1.5 rounded-lg border border-red-500 text-red-400 hover:bg-red-500/10 transition-all text-sm flex items-center space-x-1 disabled:opacity-50"
              >
                <XCircle className="w-3 h-3" />
                <span>Reject</span>
              </button>
            </>
          )}
          <button
            onClick={() => onView(post)}
            className="p-2 rounded-lg hover:bg-primary-500/10 hover:text-primary-400 transition-all"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(post.id)}
            className="p-2 rounded-lg hover:bg-red-500/10 hover:text-red-400 transition-all"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}

function ScheduleModal({ newPost, setNewPost, onClose, onSchedule, onPostNow }) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass rounded-2xl border border-dark-700 max-w-2xl w-full"
      >
        <div className="p-6 border-b border-dark-700 flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">Create LinkedIn Post</h2>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-dark-800">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-2">
              Post Content
            </label>
            <textarea
              value={newPost.content}
              onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
              placeholder="What would you like to share on LinkedIn?"
              rows={6}
              className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-lg focus:outline-none focus:border-primary-500 text-white resize-none"
            />
            <p className="text-xs text-dark-500 mt-2">
              {newPost.content.length} characters
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-300 mb-2">
              Schedule for (optional)
            </label>
            <input
              type="datetime-local"
              value={newPost.scheduledFor}
              onChange={(e) => setNewPost({ ...newPost, scheduledFor: e.target.value })}
              className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-lg focus:outline-none focus:border-primary-500 text-white"
            />
            <p className="text-xs text-dark-500 mt-2">
              Leave empty to post immediately
            </p>
          </div>
        </div>

        <div className="p-6 border-t border-dark-700 flex space-x-3">
          <button
            onClick={onPostNow}
            className="flex-1 btn-primary py-3"
          >
            <Linkedin className="w-4 h-4" />
            Post Now
          </button>
          <button
            onClick={onSchedule}
            className="flex-1 py-3 rounded-lg border border-dark-300 hover:bg-dark-800 transition-all"
          >
            <Calendar className="w-4 h-4 inline mr-2" />
            Schedule
          </button>
        </div>
      </motion.div>
    </div>
  );
}

function AiGenerateModal({ onClose, onGenerate, isGenerating }) {
  const postTypes = [
    { value: 'insight', label: '💡 Insight', desc: 'Share a business lesson or learning' },
    { value: 'achievement', label: '🎉 Achievement', desc: 'Celebrate a milestone or progress' },
    { value: 'question', label: '❓ Question', desc: 'Engage your audience with a question' },
    { value: 'tip', label: '📌 Tip', desc: 'Share a helpful tip or best practice' },
    { value: 'motivation', label: '🔥 Motivation', desc: 'Inspire your network' },
  ];

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass rounded-2xl border border-dark-700 max-w-2xl w-full"
      >
        <div className="p-6 border-b border-dark-700 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">AI Generate Post</h2>
              <p className="text-dark-300 text-sm">Let AI create engaging content from your business goals</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-dark-800">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6">
          <div className="glass p-4 rounded-lg border border-primary-500/20 mb-6">
            <div className="flex items-start space-x-3">
              <Zap className="w-5 h-5 text-primary-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-primary-300 font-medium mb-1">How it works</p>
                <p className="text-sm text-dark-300">
                  AI will read your Business_Goals.md and generate an engaging LinkedIn post based on your objectives, 
                  projects, and progress. The post will be saved for your approval before publishing.
                </p>
              </div>
            </div>
          </div>

          <div className="text-center py-8">
            {isGenerating ? (
              <div>
                <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-white font-medium">🤖 AI is generating your post...</p>
                <p className="text-dark-400 text-sm mt-2">This takes a few seconds</p>
              </div>
            ) : (
              <button
                onClick={onGenerate}
                className="btn-primary py-4 px-8 text-lg"
              >
                <Sparkles className="w-6 h-6 mr-2 inline" />
                Generate Post with AI
              </button>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-6">
            {postTypes.map((type) => (
              <div
                key={type.value}
                className="glass p-3 rounded-lg border border-dark-700 text-center"
              >
                <div className="text-2xl mb-1">{type.label.split(' ')[0]}</div>
                <div className="text-sm font-medium text-white">{type.label.split(' ')[1]}</div>
                <div className="text-xs text-dark-400 mt-1">{type.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function PostDetailModal({ post, onClose, onApprove, onReject, isProcessing }) {
  const statusColor = getStatusColor(post.status);
  const needsApproval = post.status === 'pending_approval';

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass rounded-2xl border border-dark-700 max-w-3xl w-full max-h-[90vh] overflow-y-auto"
      >
        <div className="sticky top-0 bg-dark-900/90 backdrop-blur border-b border-dark-700 p-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Post Details</h2>
            <p className="text-dark-300 text-sm">Review before publishing</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-dark-800">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Status */}
          <div className="flex items-center space-x-2">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColor}`}>
              {post.status?.replace('_', ' ')}
            </span>
            {post.post_type && (
              <span className="px-3 py-1 rounded-full text-sm bg-primary-500/10 text-primary-400 border border-primary-500/20">
                {post.post_type}
              </span>
            )}
          </div>

          {/* Content */}
          <div>
            <label className="text-sm text-dark-400 mb-2 block">Post Content</label>
            <div className="glass p-4 rounded-lg border border-dark-700">
              <p className="text-white whitespace-pre-wrap">{post.content}</p>
            </div>
            <p className="text-xs text-dark-500 mt-2">{post.content.length} characters</p>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            {post.generated_at && (
              <div>
                <label className="text-dark-400">Generated</label>
                <p className="text-white">{new Date(post.generated_at).toLocaleString()}</p>
              </div>
            )}
            {post.scheduled_for && (
              <div>
                <label className="text-dark-400">Scheduled For</label>
                <p className="text-white">{new Date(post.scheduled_for).toLocaleString()}</p>
              </div>
            )}
            {post.approved_at && (
              <div>
                <label className="text-dark-400">Approved At</label>
                <p className="text-white">{new Date(post.approved_at).toLocaleString()}</p>
              </div>
            )}
          </div>

          {/* Approval Warning */}
          {needsApproval && (
            <div className="bg-yellow-500/10 border border-yellow-500/20 p-4 rounded-lg">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-yellow-400 font-medium">Approval Required</p>
                  <p className="text-sm text-dark-300 mt-1">
                    Approving this post will add it to the queue for automatic posting. 
                    It will be posted according to the schedule or immediately if no schedule is set.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        {needsApproval && (
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
                  <CheckCircle className="w-5 h-5 inline mr-2" />
                  Approve & Schedule
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
                  <XCircle className="w-5 h-5 inline mr-2" />
                  Reject
                </>
              )}
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}

export default LinkedIn;
