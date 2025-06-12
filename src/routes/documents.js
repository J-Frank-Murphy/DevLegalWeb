import express from 'express';
import multer from 'multer';
import path from 'path';
import { fileURLToPath } from 'url';
import { requireAuth, requireAdmin } from '../middleware/auth.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export function createDocumentsRoutes() {
  const router = express.Router();

  // Configure multer for file uploads
  const storage = multer.diskStorage({
    destination: (req, file, cb) => {
      const uploadPath = path.join(__dirname, '../uploads');
      cb(null, uploadPath);
    },
    filename: (req, file, cb) => {
      const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
      cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
  });

  const upload = multer({
    storage: storage,
    limits: {
      fileSize: 10 * 1024 * 1024 // 10MB limit
    },
    fileFilter: (req, file, cb) => {
      const allowedExtensions = [
        '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
        '.xls', '.xlsx', '.csv',
        '.ppt', '.pptx',
        '.zip', '.rar', '.7z',
        '.md', '.json', '.xml', '.html', '.css', '.js'
      ];
      
      const fileExtension = path.extname(file.originalname).toLowerCase();
      if (allowedExtensions.includes(fileExtension)) {
        cb(null, true);
      } else {
        cb(new Error('File type not allowed'), false);
      }
    }
  });

  // Documents management page
  router.get('/', requireAuth, requireAdmin, async (req, res) => {
    try {
      const fs = await import('fs');
      const uploadsPath = path.join(__dirname, '../uploads');
      
      let files = [];
      if (fs.existsSync(uploadsPath)) {
        const fileNames = fs.readdirSync(uploadsPath);
        files = fileNames.map(fileName => {
          const filePath = path.join(uploadsPath, fileName);
          const stats = fs.statSync(filePath);
          return {
            name: fileName,
            size: stats.size,
            modified: stats.mtime,
            url: `/uploads/${fileName}`
          };
        });
      }

      res.render('admin/documents/index.html', {
        title: 'Document Management - Admin',
        files,
        user: req.user,
        isAdmin: req.isAdmin
      });
    } catch (error) {
      console.error('Error loading documents:', error);
      res.status(500).render('500.html');
    }
  });

  // Upload document
  router.post('/upload', requireAuth, requireAdmin, upload.single('document'), (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
      }

      res.json({
        success: true,
        file: {
          name: req.file.filename,
          originalName: req.file.originalname,
          size: req.file.size,
          url: `/uploads/${req.file.filename}`
        }
      });
    } catch (error) {
      console.error('Error uploading document:', error);
      res.status(500).json({ error: 'Failed to upload document' });
    }
  });

  // Delete document
  router.delete('/:filename', requireAuth, requireAdmin, async (req, res) => {
    try {
      const { filename } = req.params;
      const fs = await import('fs');
      const filePath = path.join(__dirname, '../uploads', filename);

      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        res.json({ success: true });
      } else {
        res.status(404).json({ error: 'File not found' });
      }
    } catch (error) {
      console.error('Error deleting document:', error);
      res.status(500).json({ error: 'Failed to delete document' });
    }
  });

  return router;
}