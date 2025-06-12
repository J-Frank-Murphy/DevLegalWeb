import express from 'express';
import { supabaseClient } from '../config/supabase.js';

export function createMainRoutes() {
  const router = express.Router();

  // Home page
  router.get('/', async (req, res) => {
    try {
      // Get latest published posts for homepage
      const { data: posts, error } = await supabaseClient
        .from('posts')
        .select(`
          id, title, slug, excerpt, featured_image, created_at,
          categories (name, slug)
        `)
        .eq('published', true)
        .order('created_at', { ascending: false })
        .limit(3);

      if (error) throw error;

      res.render('index.html', {
        title: 'DevLegal - Technology Law Experts',
        posts: posts || [],
        user: req.user,
        isAdmin: req.isAdmin
      });
    } catch (error) {
      console.error('Error loading homepage:', error);
      res.render('index.html', {
        title: 'DevLegal - Technology Law Experts',
        posts: [],
        user: req.user,
        isAdmin: req.isAdmin
      });
    }
  });

  // About page
  router.get('/about', (req, res) => {
    res.render('about.html', {
      title: 'About - DevLegal',
      user: req.user,
      isAdmin: req.isAdmin
    });
  });

  // Services page
  router.get('/services', (req, res) => {
    res.render('services.html', {
      title: 'Services - DevLegal',
      user: req.user,
      isAdmin: req.isAdmin
    });
  });

  // Contact page
  router.get('/contact', (req, res) => {
    res.render('contact.html', {
      title: 'Contact - DevLegal',
      user: req.user,
      isAdmin: req.isAdmin
    });
  });

  return router;
}