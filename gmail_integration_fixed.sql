-- ============================================
-- Gmail Integration - FIXED Version
-- ============================================
-- This SQL properly detects Google OAuth signups
-- and automatically enables Gmail integration.
--
-- Run this in Supabase SQL Editor:
-- https://supabase.com/dashboard
-- ============================================

-- ============================================
-- STEP 1: Add Gmail Columns to Profiles
-- ============================================

ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS gmail_access_token TEXT,
ADD COLUMN IF NOT EXISTS gmail_refresh_token TEXT,
ADD COLUMN IF NOT EXISTS gmail_token_expiry TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS gmail_connected BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS gmail_last_sync TIMESTAMP WITH TIME ZONE;

-- Create index for connected users
CREATE INDEX IF NOT EXISTS idx_profiles_gmail_connected ON public.profiles(gmail_connected);

-- ============================================
-- STEP 2: Improved Google OAuth Detection
-- ============================================

-- Update function to properly detect Google signups
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
    
    -- Method 2: Check providers array (newer Supabase versions)
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
    
    -- If Google signup, mark as connected
    IF v_is_google THEN
        UPDATE public.profiles
        SET 
            gmail_connected = true,
            updated_at = NOW()
        WHERE id = NEW.id;
        
        RAISE NOTICE 'Google signup detected for user %', NEW.email;
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
-- STEP 3: Manually Fix Existing Google Users
-- ============================================

-- Update all users who signed up with Google (via identities table)
UPDATE public.profiles p
SET 
    gmail_connected = true,
    gmail_last_sync = NOW()
WHERE EXISTS (
    SELECT 1 
    FROM auth.identities i 
    WHERE i.user_id = p.id 
    AND i.provider = 'google'
);

-- Also update based on metadata
UPDATE public.profiles p
SET 
    gmail_connected = true,
    gmail_last_sync = NOW()
WHERE EXISTS (
    SELECT 1 
    FROM auth.users u 
    WHERE u.id = p.id 
    AND (
        u.raw_user_meta_data->>'provider' = 'google'
        OR u.raw_user_meta_data->>'providers' LIKE '%google%'
    )
);

-- ============================================
-- STEP 4: Debug Queries
-- ============================================

-- Check how Google signups are stored in your Supabase
SELECT 
    u.id,
    u.email,
    u.raw_user_meta_data->>'provider' as provider,
    u.raw_user_meta_data->>'providers' as providers,
    p.gmail_connected,
    p.gmail_last_sync,
    (SELECT COUNT(*) FROM auth.identities i WHERE i.user_id = u.id AND i.provider = 'google') > 0 as has_google_identity
FROM auth.users u
JOIN public.profiles p ON p.id = u.id
ORDER BY u.created_at DESC
LIMIT 10;

-- Check identities table
SELECT 
    i.user_id,
    i.provider,
    i.identity_data,
    u.email
FROM auth.identities i
JOIN auth.users u ON u.id = i.user_id
ORDER BY i.created_at DESC
LIMIT 10;

-- ============================================
-- STEP 5: Emergency Fix - Enable All Users
-- ============================================
-- Uncomment this section if you want to enable Gmail for ALL users (for testing)

/*
-- Enable Gmail for ALL users (testing only - use with caution)
UPDATE public.profiles
SET 
    gmail_connected = true,
    gmail_last_sync = NOW()
WHERE gmail_connected = false;

-- Verify
SELECT 
    email,
    gmail_connected,
    gmail_last_sync
FROM public.profiles
ORDER BY created_at DESC;
*/

-- ============================================
-- STEP 6: Final Verification
-- ============================================

-- Show all users with their Gmail status
SELECT 
    u.email,
    u.raw_user_meta_data->>'provider' as provider,
    p.gmail_connected,
    p.gmail_last_sync,
    u.created_at as user_created_at
FROM auth.users u
JOIN public.profiles p ON p.id = u.id
ORDER BY u.created_at DESC;

-- ============================================
-- SETUP COMPLETE!
-- ============================================
-- 
-- What this SQL does:
-- 1. Adds Gmail columns to profiles table
-- 2. Creates improved trigger to detect Google signups
-- 3. Fixes existing Google users
-- 4. Provides debug queries to see what's happening
--
-- Next steps:
-- 1. Run this SQL in Supabase
-- 2. Check the debug query results
-- 3. If gmail_connected is still false, check debug queries
-- 4. Start the real-time email fetcher
-- 5. Test with a new Google signup
-- ============================================
