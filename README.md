# Dev Legal Website

A professional website for a legal practice specializing in technology law, IP licensing, and open source software.

## Features

- Modern, responsive design
- Blog system with categories and tags
- Admin interface for content management
- Contact form and newsletter subscription
- SEO optimized

## Tech Stack

- Node.js with Express framework
- Supabase for database and authentication
- Multer for file uploads
- bcryptjs for password hashing
- Session-based authentication

## Deployment

This application is configured for easy deployment on Render.com or similar platforms.

## Local Development

1. Clone this repository
2. Install dependencies: `npm install`
3. Set up environment variables (see below)
4. Run the application: `npm run dev`

## Environment Variables

Create a `.env` file in the project root with the following variables:

### Required for Database Functionality
- `VITE_SUPABASE_URL`: Your Supabase project URL (e.g., https://your-project-id.supabase.co)
- `VITE_SUPABASE_ANON_KEY`: Your Supabase anonymous public key

### Application Configuration
- `SECRET_KEY`: Secret key for session security (defaults to 'dev-legal-secret-key-2025')
- `NODE_ENV`: Environment mode (development/production)
- `PORT`: Server port (defaults to 3000)

### Admin Configuration
- `ADMIN_USERNAME`: Admin username (defaults to 'admin')
- `ADMIN_PASSWORD`: Admin password (defaults to 'devlegal2025')

## Supabase Setup

1. Create a new project at [Supabase](https://supabase.com)
2. Go to Settings > API in your Supabase dashboard
3. Copy your Project URL and anon/public key
4. Update your `.env` file with these values
5. Run the database migrations in the `supabase/migrations` folder

## Database Schema

The application uses the following main tables:
- `users`: User accounts and admin access
- `posts`: Blog posts with content and metadata
- `categories`: Post categories
- `tags`: Post tags
- `post_tags`: Many-to-many relationship between posts and tags
- `comments`: User comments on posts
- `news_links`: News article links for content management

## Running Without Database

The application can run in demo mode without Supabase configuration. In this mode:
- Static pages will load normally
- Database-dependent features will show empty states
- Admin functionality will be limited

To enable full functionality, configure Supabase as described above.