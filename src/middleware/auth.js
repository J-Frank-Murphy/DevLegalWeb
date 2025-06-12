import { getAuthenticatedUser, isUserAdmin } from '../config/supabase.js';

export async function authMiddleware(req, res, next) {
  // Add user to request if authenticated
  req.user = await getAuthenticatedUser(req);
  req.isAdmin = req.user ? await isUserAdmin(req.user.id) : false;
  
  // Add helper functions to response locals
  res.locals.user = req.user;
  res.locals.isAdmin = req.isAdmin;
  
  next();
}

export function requireAuth(req, res, next) {
  if (!req.user) {
    if (req.path.startsWith('/api/')) {
      return res.status(401).json({ error: 'Authentication required' });
    }
    return res.redirect('/admin/login');
  }
  next();
}

export function requireAdmin(req, res, next) {
  if (!req.user || !req.isAdmin) {
    if (req.path.startsWith('/api/')) {
      return res.status(403).json({ error: 'Admin access required' });
    }
    return res.redirect('/admin/login');
  }
  next();
}