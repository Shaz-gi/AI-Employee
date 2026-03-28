-- ============================================
-- Gmail Integration - Automatic Setup
-- ============================================

-- Add Gmail token storage to profiles table
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS gmail_access_token TEXT,
ADD COLUMN IF NOT EXISTS gmail_refresh_token TEXT,
ADD COLUMN IF NOT EXISTS gmail_token_expiry TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS gmail_connected BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS gmail_last_sync TIMESTAMP WITH TIME ZONE;

-- Create index for connected users
CREATE INDEX IF NOT EXISTS idx_profiles_gmail_connected ON public.profiles(gmail_connected);

-- Function to handle Google OAuth callback
CREATE OR REPLACE FUNCTION public.handle_google_auth()
RETURNS TRIGGER AS $$
BEGIN
    -- When user signs up with Google, mark as Gmail connected
    IF NEW.raw_user_meta_data->>'provider' = 'google' THEN
        UPDATE public.profiles
        SET 
            gmail_connected = true,
            updated_at = NOW()
        WHERE id = NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on new user signup
DROP TRIGGER IF EXISTS on_google_signup ON auth.users;
CREATE TRIGGER on_google_signup
    AFTER INSERT ON auth.users
    FOR EACH ROW
    WHEN (NEW.raw_user_meta_data->>'provider' = 'google')
    EXECUTE FUNCTION public.handle_google_auth();

-- ============================================
-- Gmail Email Fetching Function
-- ============================================
-- This function will be called by the backend orchestrator

CREATE OR REPLACE FUNCTION public.fetch_gmail_emails(
    p_user_id UUID,
    p_access_token TEXT,
    p_max_results INTEGER DEFAULT 10
)
RETURNS INTEGER AS $$
DECLARE
    v_vault_id UUID;
    v_email_count INTEGER := 0;
    v_email_record RECORD;
BEGIN
    -- Get or create user's vault
    SELECT id INTO v_vault_id
    FROM public.vaults
    WHERE user_id = p_user_id
    LIMIT 1;
    
    IF v_vault_id IS NULL THEN
        -- Create vault if doesn't exist
        INSERT INTO public.vaults (user_id, name, storage_path, is_active)
        VALUES (p_user_id, 'My Vault', p_user_id::text || '/my_vault', true)
        RETURNING id INTO v_vault_id;
    END IF;
    
    -- Note: Actual Gmail API fetching happens in Python backend
    -- This is just a placeholder for the database structure
    
    -- Update last sync time
    UPDATE public.profiles
    SET gmail_last_sync = NOW()
    WHERE id = p_user_id;
    
    RETURN v_email_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- Verification Query
-- ============================================

-- Show Gmail connection status for all users
SELECT 
    u.email,
    p.gmail_connected,
    p.gmail_last_sync,
    p.created_at
FROM auth.users u
JOIN public.profiles p ON p.id = u.id
ORDER BY p.created_at DESC;
