import express from 'express';
import { supabaseClient } from '../config/supabase.js';
import { requireAuth, requireAdmin } from '../middleware/auth.js';
import slugify from 'slugify';
import { marked } from 'marked';
import createDOMPurify from 'dompurify';
import { JSDOM } from 'jsdom';

const window = new JSDOM('').window;
const DOMPurify = createDOMPurify(window);

export function createApiRoutes() {
  const router = express.Router();

  // Posts API
  router.get('/posts', async (req, res) => {
    try {
      const { published, category, tag, search, page = 1, limit = 10 } = req.query;
      const offset = (page - 1) * limit;

      let query = supabaseClient
        .from('posts')
        .select(`
          id, title, slug, excerpt, content, featured_image, published, 
          created_at, updated_at, views, comments_enabled,
          categories (id, name, slug),
          post_tags (tags (id, name, slug))
        `);

      // Apply filters
      if (published !== undefined) {
        query = query.eq('published', published === 'true');
      }

      if (category) {
        query = query.eq('categories.slug', category);
      }

      if (search) {
        query = query.or(`title.ilike.%${search}%,content.ilike.%${search}%`);
      }

      const { data: posts, error } = await query
        .order('created_at', { ascending: false })
        .range(offset, offset + limit - 1);

      if (error) throw error;

      res.json({ posts: posts || [], page: parseInt(page), limit: parseInt(limit) });
    } catch (error) {
      console.error('Error fetching posts:', error);
      res.status(500).json({ error: 'Failed to fetch posts' });
    }
  });

  // Create post
  router.post('/posts', requireAuth, requireAdmin, async (req, res) => {
    try {
      const {
        title,
        content,
        excerpt,
        category_id,
        tags,
        featured_image,
        published = false,
        comments_enabled = true
      } = req.body;

      if (!title || !content) {
        return res.status(400).json({ error: 'Title and content are required' });
      }

      const slug = slugify(title, { lower: true, strict: true });

      // Process content if it's markdown
      const processedContent = content.startsWith('#') || content.includes('**') 
        ? DOMPurify.sanitize(marked(content))
        : DOMPurify.sanitize(content);

      const { data: post, error } = await supabaseClient
        .from('posts')
        .insert({
          title,
          slug,
          content: processedContent,
          excerpt,
          category_id: category_id || null,
          featured_image,
          published,
          comments_enabled
        })
        .select()
        .single();

      if (error) throw error;

      // Handle tags if provided
      if (tags && Array.isArray(tags) && tags.length > 0) {
        const tagInserts = tags.map(tagId => ({
          post_id: post.id,
          tag_id: tagId
        }));

        await supabaseClient
          .from('post_tags')
          .insert(tagInserts);
      }

      res.status(201).json({ post });
    } catch (error) {
      console.error('Error creating post:', error);
      res.status(500).json({ error: 'Failed to create post' });
    }
  });

  // Update post
  router.put('/posts/:id', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { id } = req.params;
      const {
        title,
        content,
        excerpt,
        category_id,
        tags,
        featured_image,
        published,
        comments_enabled
      } = req.body;

      const updateData = {};
      
      if (title) {
        updateData.title = title;
        updateData.slug = slugify(title, { lower: true, strict: true });
      }
      
      if (content) {
        updateData.content = content.startsWith('#') || content.includes('**') 
          ? DOMPurify.sanitize(marked(content))
          : DOMPurify.sanitize(content);
      }
      
      if (excerpt !== undefined) updateData.excerpt = excerpt;
      if (category_id !== undefined) updateData.category_id = category_id;
      if (featured_image !== undefined) updateData.featured_image = featured_image;
      if (published !== undefined) updateData.published = published;
      if (comments_enabled !== undefined) updateData.comments_enabled = comments_enabled;

      const { data: post, error } = await supabaseClient
        .from('posts')
        .update(updateData)
        .eq('id', id)
        .select()
        .single();

      if (error) throw error;

      // Update tags if provided
      if (tags && Array.isArray(tags)) {
        // Remove existing tags
        await supabaseClient
          .from('post_tags')
          .delete()
          .eq('post_id', id);

        // Add new tags
        if (tags.length > 0) {
          const tagInserts = tags.map(tagId => ({
            post_id: id,
            tag_id: tagId
          }));

          await supabaseClient
            .from('post_tags')
            .insert(tagInserts);
        }
      }

      res.json({ post });
    } catch (error) {
      console.error('Error updating post:', error);
      res.status(500).json({ error: 'Failed to update post' });
    }
  });

  // Delete post
  router.delete('/posts/:id', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { id } = req.params;

      const { error } = await supabaseClient
        .from('posts')
        .delete()
        .eq('id', id);

      if (error) throw error;

      res.json({ success: true });
    } catch (error) {
      console.error('Error deleting post:', error);
      res.status(500).json({ error: 'Failed to delete post' });
    }
  });

  // Categories API
  router.get('/categories', async (req, res) => {
    try {
      const { data: categories, error } = await supabaseClient
        .from('categories')
        .select('*')
        .order('name');

      if (error) throw error;

      res.json({ categories: categories || [] });
    } catch (error) {
      console.error('Error fetching categories:', error);
      res.status(500).json({ error: 'Failed to fetch categories' });
    }
  });

  // Create category
  router.post('/categories', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { name, description } = req.body;

      if (!name) {
        return res.status(400).json({ error: 'Name is required' });
      }

      const slug = slugify(name, { lower: true, strict: true });

      const { data: category, error } = await supabaseClient
        .from('categories')
        .insert({ name, slug, description })
        .select()
        .single();

      if (error) throw error;

      res.status(201).json({ category });
    } catch (error) {
      console.error('Error creating category:', error);
      res.status(500).json({ error: 'Failed to create category' });
    }
  });

  // Tags API
  router.get('/tags', async (req, res) => {
    try {
      const { data: tags, error } = await supabaseClient
        .from('tags')
        .select('*')
        .order('name');

      if (error) throw error;

      res.json({ tags: tags || [] });
    } catch (error) {
      console.error('Error fetching tags:', error);
      res.status(500).json({ error: 'Failed to fetch tags' });
    }
  });

  // Create tag
  router.post('/tags', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { name } = req.body;

      if (!name) {
        return res.status(400).json({ error: 'Name is required' });
      }

      const slug = slugify(name, { lower: true, strict: true });

      const { data: tag, error } = await supabaseClient
        .from('tags')
        .insert({ name, slug })
        .select()
        .single();

      if (error) throw error;

      res.status(201).json({ tag });
    } catch (error) {
      console.error('Error creating tag:', error);
      res.status(500).json({ error: 'Failed to create tag' });
    }
  });

  // Comments API
  router.get('/comments', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { approved, post_id } = req.query;

      let query = supabaseClient
        .from('comments')
        .select(`
          id, name, email, content, approved, created_at,
          posts (id, title, slug)
        `);

      if (approved !== undefined) {
        query = query.eq('approved', approved === 'true');
      }

      if (post_id) {
        query = query.eq('post_id', post_id);
      }

      const { data: comments, error } = await query
        .order('created_at', { ascending: false });

      if (error) throw error;

      res.json({ comments: comments || [] });
    } catch (error) {
      console.error('Error fetching comments:', error);
      res.status(500).json({ error: 'Failed to fetch comments' });
    }
  });

  // Approve/reject comment
  router.put('/comments/:id', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { id } = req.params;
      const { approved } = req.body;

      const { data: comment, error } = await supabaseClient
        .from('comments')
        .update({ approved })
        .eq('id', id)
        .select()
        .single();

      if (error) throw error;

      res.json({ comment });
    } catch (error) {
      console.error('Error updating comment:', error);
      res.status(500).json({ error: 'Failed to update comment' });
    }
  });

  // Delete comment
  router.delete('/comments/:id', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { id } = req.params;

      const { error } = await supabaseClient
        .from('comments')
        .delete()
        .eq('id', id);

      if (error) throw error;

      res.json({ success: true });
    } catch (error) {
      console.error('Error deleting comment:', error);
      res.status(500).json({ error: 'Failed to delete comment' });
    }
  });

  return router;
}