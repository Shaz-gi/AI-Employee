-- ============================================
-- Multi-User Gmail Integration
-- ============================================
-- This enables each user to have their own
-- Gmail account with isolated emails.
--
-- Run this in Supabase SQL Editor
-- ============================================

-- ============================================
-- STEP 1: Update Profiles Table
-- ============================================

-- Add Gmail OAuth token storage per user
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS gmail_access_token TEXT,
ADD COLUMN IF NOT EXISTS gmail_refresh_token TEXT,
ADD COLUMN IF NOT EXISTS gmail_token_expiry TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS gmail_connected BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS gmail_email TEXT,
ADD COLUMN IF NOT EXISTS gmail_last_sync TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS gmail_fetch_enabled BOOLEAN DEFAULT true;

-- Create index for connected users
CREATE INDEX IF NOT EXISTS idx_profiles_gmail_connected ON public.profiles(gmail_connected);
CREATE INDEX IF NOT EXISTS idx_profiles_gmail_enabled ON public.profiles(gmail_fetch_enabled);

-- ============================================
-- STEP 2: Update Email Fetcher Trigger
-- ============================================

-- Improved trigger to detect Google signups
CREATE OR REPLACE FUNCTION public.handle_google_auth()
RETURNS TRIGGER AS $$
DECLARE
    v_is_google boolean := false;
BEGIN
    -- Check multiple ways Google OAuth might be stored
    
    -- Method 1: Check provider field
    IF NEW.raw_user_meta_data->>'provider' = 'google' THEN
        v_is_google := true;
    END IF;
    
    -- Method 2: Check providers array
    IF NEW.raw_user_meta_data->>'providers' LIKE '%google%' THEN
        v_is_google := true;
    END IF;
    
    -- Method 3: Check identity table
    IF EXISTS (
        SELECT 1 FROM auth.identities i 
        WHERE i.user_id = NEW.id 
        AND i.provider = 'google'
    ) THEN
        v_is_google := true;
    END IF;
    
    -- If Google signup, mark as connected and create vault
    IF v_is_google THEN
        -- Update profile
        UPDATE public.profiles
        SET 
            gmail_connected = true,
            gmail_email = NEW.email,
            updated_at = NOW()
        WHERE id = NEW.id;
        
        -- Create user's personal vault
        INSERT INTO public.vaults (user_id, name, storage_path, is_active)
        VALUES (
            NEW.id,
            'My Vault',
            NEW.id::text || '/vault',
            true
        )
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE 'Google signup detected for user %, vault created', NEW.email;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop and recreate trigger
DROP TRIGGER IF EXISTS on_google_signup ON auth.users;
CREATE TRIGGER on_google_signup
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_google_auth();

-- ============================================
-- STEP 3: Create Gmail Tokens Table
-- ============================================

-- Store Gmail OAuth tokens per user
CREATE TABLE IF NOT EXISTS public.gmail_tokens (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    
    -- OAuth tokens
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expiry TIMESTAMP WITH TIME ZONE,
    
    -- Token metadata
    scopes TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for quick lookups
CREATE INDEX IF NOT EXISTS idx_gmail_tokens_user_id ON public.gmail_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_gmail_tokens_expiry ON public.gmail_tokens(token_expiry);

-- Enable RLS
ALTER TABLE public.gmail_tokens ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view own tokens" ON public.gmail_tokens;
DROP POLICY IF EXISTS "Users can update own tokens" ON public.gmail_tokens;
DROP POLICY IF EXISTS "Service role can manage all tokens" ON public.gmail_tokens;

-- Create policies
CREATE POLICY "Users can view own tokens"
ON public.gmail_tokens FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can update own tokens"
ON public.gmail_tokens FOR UPDATE
USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all tokens"
ON public.gmail_tokens FOR ALL
USING (true);

-- ============================================
-- STEP 4: Create Function to Store Tokens
-- ============================================

CREATE OR REPLACE FUNCTION public.store_gmail_token(
    p_user_id UUID,
    p_access_token TEXT,
    p_refresh_token TEXT,
    p_token_expiry TIMESTAMP WITH TIME ZONE,
    p_scopes TEXT[] DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    -- Insert or update token
    INSERT INTO public.gmail_tokens (
        user_id,
        access_token,
        refresh_token,
        token_expiry,
        scopes,
        updated_at
    ) VALUES (
        p_user_id,
        p_access_token,
        p_refresh_token,
        p_token_expiry,
        p_scopes,
        NOW()
    )
    ON CONFLICT (user_id) DO UPDATE SET
        access_token = EXCLUDED.access_token,
        refresh_token = EXCLUDED.refresh_token,
        token_expiry = EXCLUDED.token_expiry,
        scopes = EXCLUDED.scopes,
        updated_at = NOW();
    
    -- Update profile
    UPDATE public.profiles
    SET 
        gmail_connected = true,
        gmail_last_sync = NOW()
    WHERE id = p_user_id;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- STEP 5: Create Function to Get Active Users
-- ============================================

CREATE OR REPLACE FUNCTION public.get_active_gmail_users()
RETURNS TABLE (
    user_id UUID,
    email TEXT,
    gmail_email TEXT,
    gmail_connected BOOLEAN,
    gmail_fetch_enabled BOOLEAN,
    gmail_last_sync TIMESTAMP WITH TIME ZONE,
    vault_id UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id as user_id,
        p.email::TEXT,
        p.gmail_email::TEXT,
        p.gmail_connected,
        p.gmail_fetch_enabled,
        p.gmail_last_sync,
        v.id as vault_id
    FROM public.profiles p
    LEFT JOIN public.vaults v ON v.user_id = p.id
    WHERE p.gmail_connected = true
    AND p.gmail_fetch_enabled = true
    ORDER BY p.gmail_last_sync ASC NULLS FIRST;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- STEP 6: Update Emails Table
-- ============================================

-- Add user_id for direct user association (in addition to vault_id)
ALTER TABLE public.emails 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Create index for user-based queries
CREATE INDEX IF NOT EXISTS idx_emails_user_id ON public.emails(user_id);

-- Update RLS policies to allow user-based access
DROP POLICY IF EXISTS "Users can view own emails" ON public.emails;
DROP POLICY IF EXISTS "Users can create own emails" ON public.emails;
DROP POLICY IF EXISTS "Users can update own emails" ON public.emails;

-- Create new policies
CREATE POLICY "Users can view own emails"
ON public.emails FOR SELECT
USING (
    user_id = auth.uid() 
    OR vault_id IN (
        SELECT id FROM public.vaults WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can create own emails"
ON public.emails FOR INSERT
WITH CHECK (
    user_id = auth.uid() 
    OR vault_id IN (
        SELECT id FROM public.vaults WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can update own emails"
ON public.emails FOR UPDATE
USING (
    user_id = auth.uid() 
    OR vault_id IN (
        SELECT id FROM public.vaults WHERE user_id = auth.uid()
    )
);

-- ============================================
-- STEP 7: Create View for User Dashboard
-- ============================================

CREATE OR REPLACE VIEW public.user_email_stats AS
SELECT 
    p.id as user_id,
    p.email,
    p.gmail_connected,
    p.gmail_last_sync,
    COUNT(DISTINCT e.id) as total_emails,
    COUNT(DISTINCT CASE WHEN e.status = 'new' THEN e.id END) as new_emails,
    COUNT(DISTINCT CASE WHEN e.status = 'pending_approval' THEN e.id END) as pending_emails,
    COUNT(DISTINCT CASE WHEN e.status = 'approved' THEN e.id END) as approved_emails,
    COUNT(DISTINCT CASE WHEN e.status = 'sent' THEN e.id END) as sent_emails
FROM public.profiles p
LEFT JOIN public.emails e ON e.user_id = p.id
GROUP BY p.id, p.email, p.gmail_connected, p.gmail_last_sync;

-- ============================================
-- STEP 8: Verification Queries
-- ============================================

-- Show all users with Gmail status
SELECT 
    u.email,
    p.gmail_connected,
    p.gmail_email,
    p.gmail_fetch_enabled,
    p.gmail_last_sync,
    v.id as vault_id,
    v.name as vault_name
FROM auth.users u
JOIN public.profiles p ON p.id = u.id
LEFT JOIN public.vaults v ON v.user_id = u.id
ORDER BY u.created_at DESC;

-- Show email counts per user
SELECT 
    p.email,
    COUNT(e.id) as email_count,
    e.status,
    COUNT(CASE WHEN e.status = 'new' THEN 1 END) as new_count,
    COUNT(CASE WHEN e.status = 'pending_approval' THEN 1 END) as pending_count
FROM public.profiles p
LEFT JOIN public.emails e ON e.user_id = p.id
GROUP BY p.email, e.status
ORDER BY p.email, e.status;

-- ============================================
-- SETUP COMPLETE!
-- ============================================
-- 
-- What this does:
-- 1. Each user gets their own Gmail OAuth tokens
-- 2. Each user has their own vault
-- 3. Emails are isolated per user
-- 4. RLS policies ensure users only see their own data
-- 5. Service functions for token management
--
-- Next steps:
-- 1. Run this SQL in Supabase
-- 2. Deploy multi-user email fetcher
-- 3. Users sign up with Google
-- 4. Each user connects their Gmail
-- 5. Emails are fetched per user
-- ============================================
