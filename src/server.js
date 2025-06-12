import express from 'express';
import session from 'express-session';
import rateLimit from 'express-rate-limit';
import helmet from 'helmet';
import cors from 'cors';
import cookieParser from 'cookie-parser';
import compression from 'compression';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

// Import routes
import { createBlogRoutes } from './routes/blog.js';
import { createAdminRoutes } from './routes/admin.js';
import { createApiRoutes } from './routes/api.js';
import { createMainRoutes } from './routes/main.js';
import { createNewsLinksRoutes } from './routes/news-links.js';
import { createDocumentsRoutes } from './routes/documents.js';

// Import middleware
import { authMiddleware } from './middleware/auth.js';
import { supabaseClient } from './config/supabase.js';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      imgSrc: ["'self'", "data:", "https:", "http:"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
    },
  },
}));

app.use(cors());
app.use(compression());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use(limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(cookieParser());

// Session configuration
app.use(session({
  secret: process.env.SECRET_KEY || 'your-secret-key-change-in-production',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Static files
app.use('/static', express.static(path.join(__dirname, 'static')));
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// View engine setup (using simple template rendering)
app.set('view engine', 'html');
app.set('views', path.join(__dirname, 'templates'));

// Custom template rendering middleware
app.engine('html', async (filePath, options, callback) => {
  try {
    const fs = await import('fs');
    let html = String(fs.readFileSync(filePath, 'utf8'));
    
    // Simple template variable replacement
    if (options) {
      for (const [key, value] of Object.entries(options)) {
        const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
        // Ensure value is a primitive type before using in replace
        let replacementValue = '';
        if (value !== null && value !== undefined) {
          if (typeof value === 'object') {
            replacementValue = '';
          } else {
            try {
              replacementValue = String(value);
            } catch (error) {
              replacementValue = '';
            }
          }
        }
        html = html.replace(regex, replacementValue);
      }
    }
    
    callback(null, html);
  } catch (err) {
    callback(err);
  }
});

// Auth middleware
app.use(authMiddleware);

// Routes
app.use('/', createMainRoutes());
app.use('/blog', createBlogRoutes());
app.use('/admin', createAdminRoutes());
app.use('/api', createApiRoutes());
app.use('/news-links', createNewsLinksRoutes());
app.use('/documents', createDocumentsRoutes());

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).render('404.html', { title: 'Page Not Found' });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
});

export default app;