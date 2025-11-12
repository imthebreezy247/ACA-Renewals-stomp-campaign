-- ACA Lead Extraction System - Supabase Database Schema
-- Run this SQL in Supabase SQL Editor to create the database tables

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Leads table
CREATE TABLE IF NOT EXISTS leads (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_name TEXT NOT NULL,
  client_phone TEXT NOT NULL,
  client_email TEXT,
  monthly_premium NUMERIC,
  aca_premium NUMERIC,
  annual_income INTEGER,
  referring_agent TEXT NOT NULL,
  application_number TEXT,
  policy_numbers TEXT[],
  household_size INTEGER,
  zip_code TEXT,
  date_of_birth DATE,
  dependents TEXT,
  contact_notes TEXT,
  thread_id TEXT UNIQUE NOT NULL,
  confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
  drive_folder_url TEXT,
  is_duplicate BOOLEAN DEFAULT FALSE,
  status TEXT DEFAULT 'pending_review',
  extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Attachments table
CREATE TABLE IF NOT EXISTS attachments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  mime_type TEXT,
  local_path TEXT,
  attachment_id TEXT,
  message_id TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_referring_agent ON leads(referring_agent);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_extracted_at ON leads(extracted_at);
CREATE INDEX IF NOT EXISTS idx_leads_client_phone ON leads(client_phone);
CREATE INDEX IF NOT EXISTS idx_leads_is_duplicate ON leads(is_duplicate);
CREATE INDEX IF NOT EXISTS idx_leads_thread_id ON leads(thread_id);
CREATE INDEX IF NOT EXISTS idx_attachments_lead_id ON attachments(lead_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE leads IS 'Stores extracted client lead information from agent referral emails';
COMMENT ON TABLE attachments IS 'Stores metadata for email attachments associated with leads';
COMMENT ON COLUMN leads.confidence IS 'Extraction confidence level: high, medium, or low';
COMMENT ON COLUMN leads.status IS 'Lead processing status (e.g., pending_review, ready_to_contact)';
COMMENT ON COLUMN leads.is_duplicate IS 'Flag indicating if this lead is a duplicate of an existing entry';
