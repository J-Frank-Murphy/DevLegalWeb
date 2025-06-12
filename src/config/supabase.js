import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const supabaseUrl = process.env.VITE_SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase configuration. Please check your environment variables.');
  process.exit(1);
}

export const supabaseClient = createClient(supabaseUrl, supabaseKey);

// Helper function to get authenticated user
export async function getAuthenticatedUser(req) {
  const token = req.session?.token || req.headers.authorization?.replace('Bearer ', '');
  
  if (!token) {
    return null;
  }
  
  try {
    const { data: { user }, error } = await supabaseClient.auth.getUser(token);
    if (error) throw error;
    return user;
  } catch (error) {
    console.error('Error getting authenticated user:', error);
    return null;
  }
}

// Helper function to check if user is admin
export async function isUserAdmin(userId) {
  try {
    const { data, error } = await supabaseClient
      .from('users')
      .select('is_admin')
      .eq('id', userId)
      .single();
    
    if (error) throw error;
    return data?.is_admin || false;
  } catch (error) {
    console.error('Error checking admin status:', error);
    return false;
  }
}