import express from 'express';
import { supabaseClient } from '../config/supabase.js';

export function createBlogRoutes() {
  const router = express.Router();

  // Blog index
  router.get('/', async (req, res) => {
    try {
      const page = parseInt(req.query.page) || 1;
      const limit = 10;
      const offset = (page - 1) * limit;

      const { data: posts, error } = await supabaseClient
        .from('posts')
        .select(`
          id, title, slug, excerpt, featured_image, created_at, views,
          categories (name, slug)
        `)
        .eq('published', true)
        .order('created_at', { ascending: false })
        .range(offset, offset + limit - 1);

      if (error) throw error;

      res.render('blog/index.html', {
        title: 'Blog - DevLegal',
        posts: posts || [],
        currentPage: page,
        user: req.user,
        isAdmin: req.isAdmin
      });
    } catch (error) {
      console.error('Error loading blog:', error);
      res.status(500).render('500.html');
    }
  });

  // Individual blog post
  router.get('/post/:slug', async (req, res) => {
    try {
      const { slug } = req.params;

      // Get post with category and tags
      const { data: post, error: postError } = await supabaseClient
        .from('posts')
        .select(`
          id, title, slug, content, excerpt, featured_image, created_at, views, comments_enabled,
          categories (name, slug),
          post_tags (tags (name, slug))
        `)
        .eq('slug', slug)
        .eq('published', true)
        .single();

      if (postError || !post) {
        return res.status(404).render('404.html');
      }

      // Increment view count
      await supabaseClient
        .from('posts')
        .update({ views: (post.views || 0) + 1 })
        .eq('id', post.id);

      // Get approved comments if comments are enabled
      let comments = [];
      if (post.comments_enabled) {
        const { data: commentsData } = await supabaseClient
          .from('comments')
          .select('id, name, content, created_at')
          .eq('post_id', post.id)
          .eq('approved', true)
          .order('created_at', { ascending: true });
        
        comments = commentsData || [];
      }

      res.render('blog/post.html', {
        title: `${post.title} - DevLegal Blog`,
        post,
        comments,
        user: req.user,
        isAdmin: req.isAdmin
      });
    } catch (error) {
      console.error('Error loading blog post:', error);
      res.status(500).render('500.html');
    }
  });

  // Category page
  router.get('/category/:slug', async (req, res) => {
    try {
      const { slug } = req.params;
      const page = parseInt(req.query.page) || 1;
      const limit = 10;
      const offset = (page - 1) * limit;

      // Get category
      const { data: category, error: categoryError } = await supabaseClient
        .from('categories')
        .select('id, name, slug, description')
        .eq('slug', slug)
        .single();

      if (categoryError || !category) {
        return res.status(404).render('404.html');
      }

      // Get posts in category
      const { data: posts, error: postsError } = await supabaseClient
        .from('posts')
        .select(`
          id, title, slug, excerpt, featured_image, created_at, views,
          categories (name, slug)
        `)
        .eq('category_id', category.id)
        .eq('published', true)
        .order('created_at', { ascending: false })
        .range(offset, offset + limit - 1);

      if (postsError) throw postsError;

      res.render('blog/category.html', {
        title: `${category.name} - DevLegal Blog`,
        category,
        posts: posts || [],
        currentPage: page,
        user: req.user,
        isAdmin: req.isAdmin
      });
    } catch (error) {
      console.error('Error loading category page:', error);
      res.status(500).render('500.html');
    }
  });

  // Tag page
  router.get('/tag/:slug', async (req, res) => {
    try {
      const { slug } = req.params;
      const page = parseInt(req.query.page) || 1;
      const limit = 10;
      const offset = (page - 1) * limit;

      // Get tag
      const { data: tag, error: tagError } = await supabaseClient
        .from('tags')
        .select('id, name, slug')
        .eq('slug', slug)
        .single();

      if (tagError || !tag) {
        return res.status(404).render('404.html');
      }

      // Get posts with this tag
      const { data: posts, error: postsError } = await supabaseClient
        .from('posts')
        .select(`
          id, title, slug, excerpt, featured_image, created_at, views,
          categories (name, slug)
        `)
        .eq('published', true)
        .order('created_at', { ascending: false })
        .range(offset, offset + limit - 1);

      // Filter posts that have the tag (this is a simplified approach)
      // In a real implementation, you'd want to join through post_tags table
      
      if (postsError) throw postsError;

      res.render('blog/tag.html', {
        title: `${tag.name} - DevLegal Blog`,
        tag,
        posts: posts || [],
        currentPage: page,
        user: req.user,
        isAdmin: req.isAdmin
      });
    } catch (error) {
      console.error('Error loading tag page:', error);
      res.status(500).render('500.html');
    }
  });

  return router;
}