/*
  # Create Dev Legal Website Database Schema

  1. New Tables
    - `users`
      - `id` (uuid, primary key)
      - `username` (text, unique)
      - `password_hash` (text)
      - `is_admin` (boolean, default false)
    
    - `categories`
      - `id` (serial, primary key)
      - `name` (text, not null)
      - `slug` (text, unique)
      - `description` (text)
    
    - `tags`
      - `id` (serial, primary key)
      - `name` (text, not null)
      - `slug` (text, unique)
    
    - `posts`
      - `id` (serial, primary key)
      - `title` (text, not null)
      - `slug` (text, unique)
      - `excerpt` (text)
      - `content` (text, not null)
      - `content_format` (text, default 'html')
      - `featured_image` (text)
      - `published` (boolean, default false)
      - `comments_enabled` (boolean, default true)
      - `views` (integer, default 0)
      - `category_id` (integer, foreign key)
      - `created_at` (timestamptz, default now())
      - `updated_at` (timestamptz, default now())
    
    - `post_tags` (junction table)
      - `post_id` (integer, foreign key)
      - `tag_id` (integer, foreign key)
    
    - `comments`
      - `id` (serial, primary key)
      - `post_id` (integer, foreign key)
      - `name` (text, not null)
      - `email` (text, not null)
      - `content` (text, not null)
      - `approved` (boolean, default false)
      - `created_at` (timestamptz, default now())
    
    - `news_links`
      - `id` (serial, primary key)
      - `url` (text, not null)
      - `date_of_article` (date)
      - `date_fetched` (date, default current_date)
      - `article_written` (boolean, default false)
      - `focus_of_article` (text)

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users to manage content
    - Add policies for public read access to published content
*/

-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  username text UNIQUE NOT NULL,
  password_hash text NOT NULL,
  is_admin boolean DEFAULT false
);

-- Create categories table
CREATE TABLE IF NOT EXISTS categories (
  id serial PRIMARY KEY,
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  description text
);

-- Create tags table
CREATE TABLE IF NOT EXISTS tags (
  id serial PRIMARY KEY,
  name text NOT NULL,
  slug text UNIQUE NOT NULL
);

-- Create posts table
CREATE TABLE IF NOT EXISTS posts (
  id serial PRIMARY KEY,
  title text NOT NULL,
  slug text UNIQUE NOT NULL,
  excerpt text,
  content text NOT NULL,
  content_format text DEFAULT 'html',
  featured_image text,
  published boolean DEFAULT false,
  comments_enabled boolean DEFAULT true,
  views integer DEFAULT 0,
  category_id integer REFERENCES categories(id),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create post_tags junction table
CREATE TABLE IF NOT EXISTS post_tags (
  post_id integer REFERENCES posts(id) ON DELETE CASCADE,
  tag_id integer REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (post_id, tag_id)
);

-- Create comments table
CREATE TABLE IF NOT EXISTS comments (
  id serial PRIMARY KEY,
  post_id integer REFERENCES posts(id) ON DELETE CASCADE,
  name text NOT NULL,
  email text NOT NULL,
  content text NOT NULL,
  approved boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);

-- Create news_links table
CREATE TABLE IF NOT EXISTS news_links (
  id serial PRIMARY KEY,
  url text NOT NULL,
  date_of_article date,
  date_fetched date DEFAULT current_date,
  article_written boolean DEFAULT false,
  focus_of_article text
);

-- Enable Row Level Security on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_links ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY "Users can read own data"
  ON users
  FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Admin users can read all users"
  ON users
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = auth.uid() AND is_admin = true
    )
  );

-- Create policies for categories table
CREATE POLICY "Anyone can read categories"
  ON categories
  FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Admin users can manage categories"
  ON categories
  FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = auth.uid() AND is_admin = true
    )
  );

-- Create policies for tags table
CREATE POLICY "Anyone can read tags"
  ON tags
  FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Admin users can manage tags"
  ON tags
  FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = auth.uid() AND is_admin = true
    )
  );

-- Create policies for posts table
CREATE POLICY "Anyone can read published posts"
  ON posts
  FOR SELECT
  TO anon, authenticated
  USING (published = true);

CREATE POLICY "Admin users can read all posts"
  ON posts
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = auth.uid() AND is_admin = true
    )
  );

CREATE POLICY "Admin users can manage posts"
  ON posts
  FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = auth.uid() AND is_admin = true
    )
  );

-- Create policies for post_tags table
CREATE POLICY "Anyone can read post tags"
  ON post_tags
  FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Admin users can manage post tags"
  ON post_tags
  FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = auth.uid() AND is_admin = true
    )
  );

-- Create policies for comments table
CREATE POLICY "Anyone can read approved comments"
  ON comments
  FOR SELECT
  TO anon, authenticated
  USING (approved = true);

CREATE POLICY "Admin users can read all comments"
  ON comments
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = auth.uid() AND is_admin = true
    )
  );

CREATE POLICY "Anyone can create comments"
  ON comments
  FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

CREATE POLICY "Admin users can manage comments"
  ON comments
  FOR UPDATE, DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = auth.uid() AND is_admin = true
    )
  );

-- Create policies for news_links table
CREATE POLICY "Admin users can manage news links"
  ON news_links
  FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = auth.uid() AND is_admin = true
    )
  );

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at on posts
CREATE TRIGGER update_posts_updated_at 
    BEFORE UPDATE ON posts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default categories
INSERT INTO categories (name, slug, description) VALUES
  ('Technology Law', 'technology-law', 'Legal issues related to technology and software'),
  ('Open Source', 'open-source', 'Open source software licensing and compliance'),
  ('Data Privacy', 'data-privacy', 'Data protection and privacy regulations'),
  ('Intellectual Property', 'intellectual-property', 'Patents, trademarks, and copyright'),
  ('Compliance', 'compliance', 'Legal and regulatory compliance matters'),
  ('Drafts', 'drafts', 'Draft posts and work in progress')
ON CONFLICT (slug) DO NOTHING;

-- Insert default tags
INSERT INTO tags (name, slug) VALUES
  ('Software Licensing', 'software-licensing'),
  ('GDPR', 'gdpr'),
  ('CCPA', 'ccpa'),
  ('Patents', 'patents'),
  ('Trademarks', 'trademarks'),
  ('Copyright', 'copyright'),
  ('SaaS', 'saas'),
  ('API', 'api'),
  ('Terms of Service', 'terms-of-service'),
  ('Privacy Policy', 'privacy-policy')
ON CONFLICT (slug) DO NOTHING;