-- ============================================
-- AI Employee Pro - Database Schema
-- Free Tier Optimized
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS TABLE (extends Supabase auth.users)
-- ============================================
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    
    -- Subscription & Usage
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'business', 'enterprise')),
    emails_sent_this_month INTEGER DEFAULT 0,
    emails_limit INTEGER DEFAULT 100,
    posts_scheduled_this_month INTEGER DEFAULT 0,
    posts_limit INTEGER DEFAULT 10,
    
    -- Settings
    timezone TEXT DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- VAULTS TABLE (one per user)
-- ============================================
CREATE TABLE public.vaults (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL DEFAULT 'My Vault',
    
    -- Storage location (Supabase Storage path)
    storage_path TEXT NOT NULL,
    
    -- Settings
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, name)
);

-- ============================================
-- EMAILS TABLE (track processed emails)
-- ============================================
CREATE TABLE public.emails (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    vault_id UUID REFERENCES public.vaults(id) ON DELETE CASCADE NOT NULL,
    
    -- Email metadata
    gmail_message_id TEXT,
    from_address TEXT NOT NULL,
    to_address TEXT,
    subject TEXT NOT NULL,
    body_preview TEXT,
    
    -- Processing status
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'processing', 'pending_approval', 'approved', 'sent', 'failed')),
    
    -- AI processing
    ai_analysis TEXT,
    ai_draft_response TEXT,
    requires_approval BOOLEAN DEFAULT false,
    
    -- Timestamps
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- LINKEDIN_POSTS TABLE
-- ============================================
CREATE TABLE public.linkedin_posts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    vault_id UUID REFERENCES public.vaults(id) ON DELETE CASCADE NOT NULL,
    
    -- Post content
    content TEXT NOT NULL,
    image_url TEXT,
    scheduled_for TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'posting', 'posted', 'failed')),
    
    -- LinkedIn metadata
    linkedin_post_id TEXT,
    linkedin_url TEXT,
    
    -- Engagement (updated after posting)
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    
    -- Timestamps
    posted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- AUDIT_LOGS TABLE (for compliance)
-- ============================================
CREATE TABLE public.audit_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    vault_id UUID REFERENCES public.vaults(id) ON DELETE CASCADE,
    
    -- Action details
    action_type TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    
    -- Metadata
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    
    -- Result
    status TEXT CHECK (status IN ('success', 'failure', 'warning')),
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- USAGE_TRACKING TABLE (for billing)
-- ============================================
CREATE TABLE public.usage_tracking (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    
    -- Usage type
    usage_type TEXT NOT NULL CHECK (usage_type IN ('email_sent', 'post_scheduled', 'ai_request', 'storage_mb')),
    
    -- Quantity
    quantity INTEGER NOT NULL DEFAULT 1,
    
    -- Period
    period_start DATE NOT NULL DEFAULT DATE_TRUNC('month', NOW()),
    period_end DATE NOT NULL DEFAULT (DATE_TRUNC('month', NOW()) + INTERVAL '1 month' - INTERVAL '1 day'),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, usage_type, period_start)
);

-- ============================================
-- API_KEYS TABLE (for developer API access)
-- ============================================
CREATE TABLE public.api_keys (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,  -- Store hashed key, not plain text
    
    -- Permissions
    permissions JSONB DEFAULT '{"emails": true, "posts": true, "analytics": false}',
    
    -- Rate limiting
    rate_limit_per_minute INTEGER DEFAULT 60,
    requests_this_minute INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- ============================================
-- ROW LEVEL SECURITY (RLS) - CRITICAL FOR MULTI-TENANCY
-- ============================================

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vaults ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.linkedin_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;

-- ============================================
-- RLS POLICIES
-- ============================================

-- Profiles: Users can only see their own profile
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Vaults: Users can only access their own vaults
CREATE POLICY "Users can view own vaults"
    ON public.vaults FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own vaults"
    ON public.vaults FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own vaults"
    ON public.vaults FOR UPDATE
    USING (auth.uid() = user_id);

-- Emails: Users can only access emails in their vaults
CREATE POLICY "Users can view emails in own vaults"
    ON public.emails FOR SELECT
    USING (
        vault_id IN (
            SELECT id FROM public.vaults WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create emails in own vaults"
    ON public.emails FOR INSERT
    WITH CHECK (
        vault_id IN (
            SELECT id FROM public.vaults WHERE user_id = auth.uid()
        )
    );

-- LinkedIn Posts: Same pattern
CREATE POLICY "Users can view posts in own vaults"
    ON public.linkedin_posts FOR SELECT
    USING (
        vault_id IN (
            SELECT id FROM public.vaults WHERE user_id = auth.uid()
        )
    );

-- Audit Logs: Users can only see their own logs
CREATE POLICY "Users can view own audit logs"
    ON public.audit_logs FOR SELECT
    USING (auth.uid() = user_id);

-- Usage Tracking: Users can only see their own usage
CREATE POLICY "Users can view own usage"
    ON public.usage_tracking FOR SELECT
    USING (auth.uid() = user_id);

-- API Keys: Users can only manage their own keys
CREATE POLICY "Users can view own API keys"
    ON public.api_keys FOR SELECT
    USING (auth.uid() = user_id);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Function to create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on user signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables with updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_vaults_updated_at BEFORE UPDATE ON public.vaults
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_linkedin_posts_updated_at BEFORE UPDATE ON public.linkedin_posts
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Function to track usage
CREATE OR REPLACE FUNCTION public.track_usage(
    p_user_id UUID,
    p_usage_type TEXT,
    p_quantity INTEGER DEFAULT 1
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO public.usage_tracking (user_id, usage_type, quantity)
    VALUES (p_user_id, p_usage_type, p_quantity)
    ON CONFLICT (user_id, usage_type, period_start)
    DO UPDATE SET quantity = usage_tracking.quantity + p_quantity;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check usage limits
CREATE OR REPLACE FUNCTION public.check_usage_limit(
    p_user_id UUID,
    p_usage_type TEXT
)
RETURNS TABLE (
    current_usage INTEGER,
    limit_value INTEGER,
    is_exceeded BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(ut.quantity), 0)::INTEGER as current_usage,
        CASE 
            WHEN p_usage_type = 'email_sent' THEN p.emails_limit
            WHEN p_usage_type = 'post_scheduled' THEN p.posts_limit
            ELSE 999999
        END as limit_value,
        (COALESCE(SUM(ut.quantity), 0) >= 
            CASE 
                WHEN p_usage_type = 'email_sent' THEN p.emails_limit
                WHEN p_usage_type = 'post_scheduled' THEN p.posts_limit
                ELSE 999999
            END
        ) as is_exceeded
    FROM public.profiles p
    LEFT JOIN public.usage_tracking ut ON 
        ut.user_id = p.id AND 
        ut.usage_type = p_usage_type AND
        ut.period_start = DATE_TRUNC('month', NOW())
    WHERE p.id = p_user_id
    GROUP BY p.emails_limit, p.posts_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- INDEXES (for performance)
-- ============================================

CREATE INDEX idx_emails_vault_id ON public.emails(vault_id);
CREATE INDEX idx_emails_status ON public.emails(status);
CREATE INDEX idx_linkedin_posts_vault_id ON public.linkedin_posts(vault_id);
CREATE INDEX idx_linkedin_posts_status ON public.linkedin_posts(status);
CREATE INDEX idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX idx_usage_tracking_user_id ON public.usage_tracking(user_id);
CREATE INDEX idx_api_keys_user_id ON public.api_keys(user_id);

-- ============================================
-- STORAGE BUCKETS (for vault files)
-- ============================================

-- Create storage bucket for vault files
INSERT INTO storage.buckets (id, name, public)
VALUES ('vaults', 'vaults', false)  -- Private bucket
ON CONFLICT (id) DO NOTHING;

-- RLS for storage
CREATE POLICY "Users can access own vault files"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'vaults' AND
    (storage.foldername(name))[1]::uuid IN (
        SELECT id FROM public.vaults WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can upload to own vault"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'vaults' AND
    (storage.foldername(name))[1]::uuid IN (
        SELECT id FROM public.vaults WHERE user_id = auth.uid()
    )
);

-- ============================================
-- SEED DATA (for testing)
-- ============================================

-- Free tier limits
-- Pro: 1000 emails, 50 posts
-- Business: 5000 emails, 200 posts
-- Enterprise: unlimited

COMMENT ON TABLE public.profiles IS 'User profiles with subscription and usage tracking';
COMMENT ON TABLE public.vaults IS 'User vaults (isolated per user)';
COMMENT ON TABLE public.emails IS 'Processed emails with AI analysis';
COMMENT ON TABLE public.linkedin_posts IS 'Scheduled and posted LinkedIn content';
COMMENT ON TABLE public.audit_logs IS 'Audit trail for compliance';
COMMENT ON TABLE public.usage_tracking IS 'Monthly usage tracking for billing';
COMMENT ON TABLE public.api_keys IS 'API keys for developer access';
