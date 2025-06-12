import express from 'express';
import session from 'express-session';
import bcrypt from 'bcryptjs';
import multer from 'multer';
import { marked } from 'marked';
import slugify from 'slugify';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import cookieParser from 'cookie-parser';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize Supabase client
const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

let supabase = null;
let supabaseConfigured = false;

console.log('Supabase URL:', supabaseUrl ? 'Set' : 'Not set');
console.log('Supabase Key:', supabaseAnonKey ? 'Set' : 'Not set');

if (supabaseUrl && supabaseAnonKey) {
  try {
    // Validate URL format
    new URL(supabaseUrl); // This will throw if URL is invalid
    
    supabase = createClient(supabaseUrl, supabaseAnonKey);
    supabaseConfigured = true;
    console.log('✅ Supabase client initialized successfully');
  } catch (error) {
    console.error('❌ Failed to initialize Supabase client:', error.message);
    console.error('Please check your VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY environment variables');
    supabaseConfigured = false;
  }
} else {
  console.warn('⚠️  Supabase environment variables not found');
  console.warn('Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your .env file');
  supabaseConfigured = false;
}

// Middleware
app.use(helmet({
  contentSecurityPolicy: false // Disable CSP for development
}));
app.use(compression());
app.use(cors());
app.use(cookieParser());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Session configuration
app.use(session({
  secret: process.env.SECRET_KEY || 'dev-legal-secret-key-2025',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: false, // Set to true in production with HTTPS
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Static files
app.use('/static', express.static(path.join(__dirname, 'static')));
app.use('/uploads', express.static(path.join(__dirname, 'static', 'uploads')));

// View engine setup (using simple template replacement)
app.set('views', path.join(__dirname, 'templates'));

// File upload configuration
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadDir = path.join(__dirname, 'static', 'uploads');
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({ 
  storage: storage,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB limit
  },
  fileFilter: function (req, file, cb) {
    const allowedTypes = /jpeg|jpg|png|gif|webp|pdf|doc|docx|txt|rtf|odt|xls|xlsx|csv|ppt|pptx|zip|rar|7z|md|json|xml|html|css|js/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);
    
    if (mimetype && extname) {
      return cb(null, true);
    } else {
      cb(new Error('Invalid file type'));
    }
  }
});

// Helper function to render templates
async function renderTemplate(templatePath, data = {}) {
  try {
    const fullPath = path.join(__dirname, 'templates', templatePath);
    let template = fs.readFileSync(fullPath, 'utf8');
    
    // Simple template replacement
    for (const [key, value] of Object.entries(data)) {
      const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
      template = template.replace(regex, value || '');
    }
    
    return template;
  } catch (error) {
    console.error('Template rendering error:', error);
    return '<h1>Template Error</h1>';
  }
}

// Authentication middleware
function requireAuth(req, res, next) {
  if (req.session.user) {
    next();
  } else {
    res.redirect('/admin/login');
  }
}

function requireAdmin(req, res, next) {
  if (req.session.user && req.session.user.is_admin) {
    next();
  } else {
    res.status(403).send('Access denied');
  }
}

// Database operation wrapper
async function executeSupabaseQuery(operation) {
  if (!supabaseConfigured) {
    console.log('Database operation skipped - Supabase not configured');
    return { data: [], error: { message: 'Database not configured' } };
  }
  try {
    const result = await operation();
    return result;
  } catch (error) {
    console.error('Database operation failed:', error);
    return { data: null, error: error };
  }
}

// Routes

// Home page
app.get('/', async (req, res) => {
  try {
    // Get latest published posts
    const { data: posts, error } = await executeSupabaseQuery(async () => {
      return await supabase
        .from('posts')
        .select(`
          *,
          categories (name, slug),
          post_tags (
            tags (name, slug)
          )
        `)
        .eq('published', true)
        .order('created_at', { ascending: false })
        .limit(3);
    });

    if (error && supabaseConfigured) {
      console.error('Error fetching posts:', error);
    }

    const template = await renderTemplate('index.html', {
      title: 'DevLegal - Technology Law Specialists',
      posts: posts || []
    });
    
    res.send(template);
  } catch (error) {
    console.error('Home page error:', error);
    res.status(500).send('Server error');
  }
});

// Blog routes
app.get('/blog', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = 10;
    const offset = (page - 1) * limit;

    const { data: posts, error } = await executeSupabaseQuery(async () => {
      return await supabase
        .from('posts')
        .select(`
          *,
          categories (name, slug),
          post_tags (
            tags (name, slug)
          )
        `)
        .eq('published', true)
        .order('created_at', { ascending: false })
        .range(offset, offset + limit - 1);
    });

    if (error && supabaseConfigured) {
      console.error('Error fetching posts:', error);
    }

    const template = await renderTemplate('blog/index.html', {
      title: 'Blog - DevLegal',
      posts: posts || [],
      currentPage: page
    });
    
    res.send(template);
  } catch (error) {
    console.error('Blog page error:', error);
    res.status(500).send('Server error');
  }
});

app.get('/blog/post/:slug', async (req, res) => {
  try {
    const { data: post, error } = await executeSupabaseQuery(async () => {
      return await supabase
        .from('posts')
        .select(`
          *,
          categories (name, slug),
          post_tags (
            tags (name, slug)
          )
        `)
        .eq('slug', req.params.slug)
        .eq('published', true)
        .single();
    });

    if (error || !post) {
      return res.status(404).send('Post not found');
    }

    // Increment view count
    if (supabaseConfigured) {
      await supabase
        .from('posts')
        .update({ views: (post.views || 0) + 1 })
        .eq('id', post.id);
    }

    // Get comments
    const { data: comments } = await executeSupabaseQuery(async () => {
      return await supabase
        .from('comments')
        .select('*')
        .eq('post_id', post.id)
        .eq('approved', true)
        .order('created_at', { ascending: true });
    });

    const template = await renderTemplate('blog/post.html', {
      title: `${post.title} - DevLegal`,
      post: post,
      comments: comments || []
    });
    
    res.send(template);
  } catch (error) {
    console.error('Blog post error:', error);
    res.status(500).send('Server error');
  }
});

// Admin routes
app.get('/admin/login', async (req, res) => {
  if (req.session.user) {
    return res.redirect('/admin');
  }
  
  const template = await renderTemplate('admin/login.html', {
    title: 'Admin Login - DevLegal'
  });
  
  res.send(template);
});

app.post('/admin/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    if (!supabaseConfigured) {
      // Demo mode - use default credentials
      const defaultUsername = process.env.ADMIN_USERNAME || 'admin';
      const defaultPassword = process.env.ADMIN_PASSWORD || 'devlegal2025';
      
      if (username === defaultUsername && password === defaultPassword) {
        req.session.user = {
          id: 'demo-user',
          username: username,
          is_admin: true
        };
        return res.redirect('/admin');
      } else {
        return res.redirect('/admin/login?error=invalid');
      }
    }
    
    const { data: user, error } = await executeSupabaseQuery(async () => {
      return await supabase
        .from('users')
        .select('*')
        .eq('username', username)
        .single();
    });

    if (error || !user) {
      return res.redirect('/admin/login?error=invalid');
    }

    const isValidPassword = await bcrypt.compare(password, user.password_hash);
    
    if (!isValidPassword) {
      return res.redirect('/admin/login?error=invalid');
    }

    req.session.user = {
      id: user.id,
      username: user.username,
      is_admin: user.is_admin
    };

    res.redirect('/admin');
  } catch (error) {
    console.error('Login error:', error);
    res.redirect('/admin/login?error=server');
  }
});

app.get('/admin/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/');
});

app.get('/admin', requireAuth, async (req, res) => {
  try {
    // Get dashboard stats
    const { data: postsCount } = await executeSupabaseQuery(async () => {
      return await supabase
        .from('posts')
        .select('id', { count: 'exact' });
    });
    
    const { data: commentsCount } = await executeSupabaseQuery(async () => {
      return await supabase
        .from('comments')
        .select('id', { count: 'exact' });
    });

    const template = await renderTemplate('admin/index.html', {
      title: 'Admin Dashboard - DevLegal',
      user: req.session.user,
      postsCount: postsCount?.length || 0,
      commentsCount: commentsCount?.length || 0
    });
    
    res.send(template);
  } catch (error) {
    console.error('Admin dashboard error:', error);
    res.status(500).send('Server error');
  }
});

// Admin posts management
app.get('/admin/posts', requireAuth, async (req, res) => {
  try {
    const { data: posts, error } = await executeSupabaseQuery(async () => {
      return await supabase
        .from('posts')
        .select(`
          *,
          categories (name, slug)
        `)
        .order('created_at', { ascending: false });
    });

    if (error && supabaseConfigured) {
      console.error('Error fetching posts:', error);
    }

    const template = await renderTemplate('admin/posts.html', {
      title: 'Manage Posts - DevLegal',
      user: req.session.user,
      posts: posts || []
    });
    
    res.send(template);
  } catch (error) {
    console.error('Admin posts error:', error);
    res.status(500).send('Server error');
  }
});

// API routes for AJAX operations
app.get('/api/posts', async (req, res) => {
  try {
    const { data: posts, error } = await executeSupabaseQuery(async () => {
      return await supabase
        .from('posts')
        .select(`
          *,
          categories (name, slug),
          post_tags (
            tags (name, slug)
          )
        `)
        .eq('published', true)
        .order('created_at', { ascending: false });
    });

    if (error) {
      console.error('API posts error:', error);
      return res.json([]); // Return empty array instead of error for demo mode
    }

    res.json(posts || []);
  } catch (error) {
    console.error('API posts error:', error);
    res.json([]); // Return empty array for demo mode
  }
});

app.get('/api/categories', async (req, res) => {
  try {
    const { data: categories, error } = await executeSupabaseQuery(async () => {
      return await supabase
        .from('categories')
        .select('*')
        .order('name');
    });

    if (error) {
      console.error('API categories error:', error);
      return res.json([]);
    }

    res.json(categories || []);
  } catch (error) {
    console.error('API categories error:', error);
    res.json([]);
  }
});

app.get('/api/tags', async (req, res) => {
  try {
    const { data: tags, error } = await executeSupabaseQuery(async () => {
      return await supabase
        .from('tags')
        .select('*')
        .order('name');
    });

    if (error) {
      console.error('API tags error:', error);
      return res.json([]);
    }

    res.json(tags || []);
  } catch (error) {
    console.error('API tags error:', error);
    res.json([]);
  }
});

// File upload endpoint
app.post('/admin/upload', requireAuth, upload.single('file'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const fileUrl = `/uploads/${req.file.filename}`;
    res.json({ 
      success: true, 
      filename: req.file.filename,
      url: fileUrl,
      originalName: req.file.originalname
    });
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: 'Upload failed' });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).send('Something went wrong!');
});

// 404 handler
app.use((req, res) => {
  res.status(404).send('Page not found');
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📱 Visit: http://localhost:${PORT}`);
  
  if (supabaseConfigured) {
    console.log('✅ Database: Connected to Supabase');
  } else {
    console.log('⚠️  Database: Running in demo mode');
    console.log('   To connect to Supabase:');
    console.log('   1. Check your .env file');
    console.log('   2. Ensure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are set correctly');
    console.log('   3. Restart the server');
  }
});