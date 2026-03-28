-- LinkedIn Posts Table Migration
-- Run this in Supabase SQL Editor to update linkedin_posts table

-- Add user_id column if it doesn't exist (for easier queries)
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'linkedin_posts' 
        AND column_name = 'user_id'
    ) THEN
        ALTER TABLE public.linkedin_posts ADD COLUMN user_id UUID;
        
        -- Populate user_id from vaults table
        UPDATE public.linkedin_posts lp
        SET user_id = v.user_id
        FROM public.vaults v
        WHERE lp.vault_id = v.id;
        
        -- Add foreign key to profiles
        ALTER TABLE public.linkedin_posts 
        ADD CONSTRAINT linkedin_posts_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
        
        RAISE NOTICE 'Added user_id column to linkedin_posts';
    ELSE
        RAISE NOTICE 'user_id column already exists';
    END IF;
END $$;

-- Add missing columns if they don't exist
DO $$ 
BEGIN 
    -- Add post_type
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'linkedin_posts' AND column_name = 'post_type'
    ) THEN
        ALTER TABLE public.linkedin_posts ADD COLUMN post_type TEXT DEFAULT 'insight';
    END IF;
    
    -- Add approved_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'linkedin_posts' AND column_name = 'approved_at'
    ) THEN
        ALTER TABLE public.linkedin_posts ADD COLUMN approved_at TIMESTAMP WITH TIME ZONE;
    END IF;
    
    -- Add rejected_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'linkedin_posts' AND column_name = 'rejected_at'
    ) THEN
        ALTER TABLE public.linkedin_posts ADD COLUMN rejected_at TIMESTAMP WITH TIME ZONE;
    END IF;
    
    -- Add generated_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'linkedin_posts' AND column_name = 'generated_at'
    ) THEN
        ALTER TABLE public.linkedin_posts ADD COLUMN generated_at TIMESTAMP WITH TIME ZONE;
    END IF;
    
    -- Add requires_approval
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'linkedin_posts' AND column_name = 'requires_approval'
    ) THEN
        ALTER TABLE public.linkedin_posts ADD COLUMN requires_approval BOOLEAN DEFAULT true;
    END IF;
    
    -- Add ai_generated
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'linkedin_posts' AND column_name = 'ai_generated'
    ) THEN
        ALTER TABLE public.linkedin_posts ADD COLUMN ai_generated BOOLEAN DEFAULT false;
    END IF;
    
    -- Add error_message
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'linkedin_posts' AND column_name = 'error_message'
    ) THEN
        ALTER TABLE public.linkedin_posts ADD COLUMN error_message TEXT;
    END IF;
    
    RAISE NOTICE 'Added missing columns to linkedin_posts';
END $$;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_vault_id ON public.linkedin_posts(vault_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_user_id ON public.linkedin_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_status ON public.linkedin_posts(status);
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_scheduled_for ON public.linkedin_posts(scheduled_for) WHERE status = 'scheduled';
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_pending_approval ON public.linkedin_posts(status) WHERE status = 'pending_approval';

-- Enable RLS
ALTER TABLE public.linkedin_posts ENABLE ROW LEVEL SECURITY;

-- Create policies (drop if exists first)
DROP POLICY IF EXISTS "Users can view their own posts" ON public.linkedin_posts;
CREATE POLICY "Users can view their own posts"
    ON public.linkedin_posts
    FOR SELECT
    USING (
        vault_id IN (SELECT id FROM public.vaults WHERE user_id = auth.uid())
        OR
        user_id = auth.uid()
    );

DROP POLICY IF EXISTS "Users can insert their own posts" ON public.linkedin_posts;
CREATE POLICY "Users can insert their own posts"
    ON public.linkedin_posts
    FOR INSERT
    WITH CHECK (
        vault_id IN (SELECT id FROM public.vaults WHERE user_id = auth.uid())
        OR
        user_id = auth.uid()
    );

DROP POLICY IF EXISTS "Users can update their own posts" ON public.linkedin_posts;
CREATE POLICY "Users can update their own posts"
    ON public.linkedin_posts
    FOR UPDATE
    USING (
        vault_id IN (SELECT id FROM public.vaults WHERE user_id = auth.uid())
        OR
        user_id = auth.uid()
    );

DROP POLICY IF EXISTS "Users can delete their own posts" ON public.linkedin_posts;
CREATE POLICY "Users can delete their own posts"
    ON public.linkedin_posts
    FOR DELETE
    USING (
        vault_id IN (SELECT id FROM public.vaults WHERE user_id = auth.uid())
        OR
        user_id = auth.uid()
    );

-- Service role can do everything
DROP POLICY IF EXISTS "Service role full access" ON public.linkedin_posts;
CREATE POLICY "Service role full access"
    ON public.linkedin_posts
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_linkedin_posts_updated_at ON public.linkedin_posts;
CREATE TRIGGER update_linkedin_posts_updated_at
    BEFORE UPDATE ON public.linkedin_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comment
COMMENT ON TABLE public.linkedin_posts IS 'LinkedIn posts with AI generation and approval workflow';
COMMENT ON COLUMN public.linkedin_posts.post_type IS 'Type of post: insight, achievement, question, tip, update, motivation';
COMMENT ON COLUMN public.linkedin_posts.status IS 'Status: draft, pending_approval, approved, scheduled, posted, rejected';
