import express from 'express';
import bcrypt from 'bcryptjs';
import { supabaseClient } from '../config/supabase.js';
import { requireAuth, requireAdmin } from '../middleware/auth.js';

export function createAdminRoutes() {
  const router = express.Router();

  // Login page
  router.get('/login', (req, res) => {
    if (req.user) {
      return res.redirect('/admin');
    }
    res.render('admin/login.html', {
      title: 'Admin Login - DevLegal'
    });
  });

  // Login POST
  router.post('/login', async (req, res) => {
    try {
      const { username, password } = req.body;

      if (!username || !password) {
        return res.status(400).json({ error: 'Username and password required' });
      }

      // Get user from database
      const { data: user, error } = await supabaseClient
        .from('users')
        .select('id, username, password_hash, is_admin')
        .eq('username', username)
        .single();

      if (error || !user) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      // Verify password
      const isValidPassword = await bcrypt.compare(password, user.password_hash);
      if (!isValidPassword) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      // Store user session
      req.session.userId = user.id;
      req.session.isAdmin = user.is_admin;

      res.json({ success: true, redirect: '/admin' });
    } catch (error) {
      console.error('Login error:', error);
      res.status(500).json({ error: 'Login failed' });
    }
  });

  // Logout
  router.post('/logout', (req, res) => {
    req.session.destroy((err) => {
      if (err) {
        console.error('Logout error:', err);
      }
      res.redirect('/admin/login');
    });
  });

  // Admin dashboard (requires auth)
  router.get('/', requireAuth, requireAdmin, async (req, res) => {
    try {
      // Get dashboard stats
      const { data: postsCount } = await supabaseClient
        .from('posts')
        .select('id', { count: 'exact' });

      const { data: commentsCount } = await supabaseClient
        .from('comments')
        .select('id', { count: 'exact' })
        .eq('approved', false);

      res.render('admin/index.html', {
        title: 'Admin Dashboard - DevLegal',
        stats: {
          posts: postsCount?.length || 0,
          pendingComments: commentsCount?.length || 0
        },
        user: req.user,
        isAdmin: req.isAdmin
      });
    } catch (error) {
      console.error('Dashboard error:', error);
      res.status(500).render('500.html');
    }
  });

  // Posts management
  router.get('/posts', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { data: posts, error } = await supabaseClient
        .from('posts')
        .select(`
          id, title, slug, published, created_at, updated_at, views,
          categories (name)
        `)
        .order('created_at', { ascending: false });

      if (error) throw error;

      res.render('admin/posts.html', {
        title: 'Manage Posts - Admin',
        posts: posts || [],
        user: req.user,
        isAdmin: req.isAdmin
      });
    } catch (error) {
      console.error('Error loading posts:', error);
      res.status(500).render('500.html');
    }
  });

  // Categories management
  router.get('/categories', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { data: categories, error } = await supabaseClient
        .from('categories')
        .select('*')
        .order('name');

      if (error) throw error;

      res.render('admin/categories.html', {
        title: 'Manage Categories - Admin',
        categories: categories || [],
        user: req.user,
        isAdmin: req.isAdmin
      });
    } catch (error) {
      console.error('Error loading categories:', error);
      res.status(500).render('500.html');
    }
  });

  // Tags management
  router.get('/tags', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { data: tags, error } = await supabaseClient
        .from('tags')
        .select('*')
        .order('name');

      if (error) throw error;

      res.render('admin/tags.html', {
        title: 'Manage Tags - Admin',
        tags: tags || [],
        user: req.user,
        isAdmin: req.isAdmin
      });
    } catch (error) {
      console.error('Error loading tags:', error);
      res.status(500).render('500.html');
    }
  });

  // Comments management
  router.get('/comments', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { data: comments, error } = await supabaseClient
        .from('comments')
        .select(`
          id, name, email, content, approved, created_at,
          posts (title, slug)
        `)
        .order('created_at', { ascending: false });

      if (error) throw error;

      res.render('admin/comments.html', {
        title: 'Manage Comments - Admin',
        comments: comments || [],
        user: req.user,
        isAdmin: req.isAdmin
      });
    } catch (error) {
      console.error('Error loading comments:', error);
      res.status(500).render('500.html');
    }
  });

  return router;
}