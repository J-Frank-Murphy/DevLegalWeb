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
import fs from 'fs';

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

// Simple template rendering function
function renderTemplate(templatePath, data = {}) {
  try {
    let html = fs.readFileSync(templatePath, 'utf8');
    
    // Simple template variable replacement
    if (data && typeof data === 'object') {
      for (const [key, value] of Object.entries(data)) {
        // Skip Express internal properties and non-string keys
        if (typeof key !== 'string' || 
            key.startsWith('_') || 
            key === 'settings' || 
            key === 'cache' ||
            key === 'locals') {
          continue;
        }
        
        const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
        
        // Convert value to safe string
        let replacementValue = '';
        if (value === null || value === undefined) {
          replacementValue = '';
        } else if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
          replacementValue = String(value);
        } else if (Array.isArray(value)) {
          // For arrays, don't render in templates
          replacementValue = '';
        } else if (typeof value === 'object') {
          // For objects, don't render in templates
          replacementValue = '';
        } else {
          replacementValue = String(value);
        }
        
        html = html.replace(regex, replacementValue);
      }
    }
    
    return html;
  } catch (err) {
    throw err;
  }
}

// Custom template engine
app.engine('html', (filePath, options, callback) => {
  try {
    const html = renderTemplate(filePath, options);
    callback(null, html);
  } catch (err) {
    callback(err);
  }
});

// Basic routes
app.get('/', (req, res) => {
  res.render('index.html', {
    title: 'DevLegal - Technology Law Experts'
  });
});

app.get('/blog', (req, res) => {
  res.render('blog/index.html', {
    title: 'Blog - DevLegal'
  });
});

app.get('/admin/login', (req, res) => {
  res.render('admin/login.html', {
    title: 'Admin Login - DevLegal'
  });
});

app.get('/admin', (req, res) => {
  res.render('admin/index.html', {
    title: 'Admin Dashboard - DevLegal'
  });
});

// API routes
app.get('/api/posts', (req, res) => {
  res.json([]);
});

app.get('/api/categories', (req, res) => {
  res.json([]);
});

app.get('/api/tags', (req, res) => {
  res.json([]);
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({ error: 'Something went wrong!' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).render('404.html', { title: 'Page Not Found' });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Node.js server running on port ${PORT}`);
  console.log(`📱 Visit: http://localhost:${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
});

export default app;