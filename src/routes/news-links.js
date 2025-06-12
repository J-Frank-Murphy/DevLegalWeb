import express from 'express';
import { supabaseClient } from '../config/supabase.js';
import { requireAuth, requireAdmin } from '../middleware/auth.js';

export function createNewsLinksRoutes() {
  const router = express.Router();

  // Get all news links (admin only)
  router.get('/', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { data: newsLinks, error } = await supabaseClient
        .from('news_links')
        .select('*')
        .order('date_fetched', { ascending: false });

      if (error) throw error;

      res.render('admin/news_links/index.html', {
        title: 'News Links - Admin',
        newsLinks: newsLinks || [],
        user: req.user,
        isAdmin: req.isAdmin
      });
    } catch (error) {
      console.error('Error loading news links:', error);
      res.status(500).render('500.html');
    }
  });

  // API endpoints for news links
  router.get('/api', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { data: newsLinks, error } = await supabaseClient
        .from('news_links')
        .select('*')
        .order('date_fetched', { ascending: false });

      if (error) throw error;

      res.json({ newsLinks: newsLinks || [] });
    } catch (error) {
      console.error('Error fetching news links:', error);
      res.status(500).json({ error: 'Failed to fetch news links' });
    }
  });

  // Create news link
  router.post('/api', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { url, date_of_article, focus_of_article } = req.body;

      if (!url) {
        return res.status(400).json({ error: 'URL is required' });
      }

      const { data: newsLink, error } = await supabaseClient
        .from('news_links')
        .insert({
          url,
          date_of_article: date_of_article || null,
          focus_of_article: focus_of_article || null,
          date_fetched: new Date().toISOString().split('T')[0],
          article_written: false
        })
        .select()
        .single();

      if (error) throw error;

      res.status(201).json({ newsLink });
    } catch (error) {
      console.error('Error creating news link:', error);
      res.status(500).json({ error: 'Failed to create news link' });
    }
  });

  // Update news link
  router.put('/api/:id', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { id } = req.params;
      const { url, date_of_article, focus_of_article, article_written } = req.body;

      const updateData = {};
      if (url !== undefined) updateData.url = url;
      if (date_of_article !== undefined) updateData.date_of_article = date_of_article;
      if (focus_of_article !== undefined) updateData.focus_of_article = focus_of_article;
      if (article_written !== undefined) updateData.article_written = article_written;

      const { data: newsLink, error } = await supabaseClient
        .from('news_links')
        .update(updateData)
        .eq('id', id)
        .select()
        .single();

      if (error) throw error;

      res.json({ newsLink });
    } catch (error) {
      console.error('Error updating news link:', error);
      res.status(500).json({ error: 'Failed to update news link' });
    }
  });

  // Delete news link
  router.delete('/api/:id', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { id } = req.params;

      const { error } = await supabaseClient
        .from('news_links')
        .delete()
        .eq('id', id);

      if (error) throw error;

      res.json({ success: true });
    } catch (error) {
      console.error('Error deleting news link:', error);
      res.status(500).json({ error: 'Failed to delete news link' });
    }
  });

  return router;
}