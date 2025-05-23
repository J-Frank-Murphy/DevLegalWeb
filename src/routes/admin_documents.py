from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

# Create blueprint
documents_bp = Blueprint('documents', __name__, url_prefix='/admin/documents')

def allowed_document(filename):
    """Check if a filename has an allowed document extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_DOCUMENT_EXTENSIONS', 
                                                                      {'pdf', 'docx', 'doc', 'txt', 'rtf', 'odt', 'xlsx', 'xls', 'csv', 'zip', 'pptx', 'ppt'})

def save_document(file):
    """Save an uploaded document and return the path"""
    if file and allowed_document(file.filename):
        # Generate a secure filename with a unique identifier
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Get the upload folder from app config
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        # Create documents subdirectory if it doesn't exist
        documents_dir = os.path.join(upload_folder, 'documents')
        os.makedirs(documents_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(documents_dir, unique_filename)
        file.save(file_path)
        
        # Return the relative path for database storage
        if 'UPLOADS_URL_PATH' in current_app.config:
            # For persistent storage on Render
            return f"documents/{unique_filename}"
        else:
            # For local development
            return f"uploads/documents/{unique_filename}"
    
    return None

@documents_bp.route('/')
@login_required
def index():
    """Document management page"""
    # Get list of uploaded documents
    upload_folder = current_app.config['UPLOAD_FOLDER']
    documents_dir = os.path.join(upload_folder, 'documents')
    
    # Create directory if it doesn't exist
    os.makedirs(documents_dir, exist_ok=True)
    
    # Get all files in the documents directory
    documents = []
    for filename in os.listdir(documents_dir):
        file_path = os.path.join(documents_dir, filename)
        if os.path.isfile(file_path):
            # Get file stats
            stats = os.stat(file_path)
            size_kb = stats.st_size / 1024
            modified_time = datetime.fromtimestamp(stats.st_mtime)
            
            # Get file extension
            _, extension = os.path.splitext(filename)
            extension = extension.lstrip('.')
            
            # Create document info
            document = {
                'filename': filename,
                'original_name': '_'.join(filename.split('_')[1:]) if '_' in filename else filename,
                'size_kb': round(size_kb, 2),
                'modified': modified_time,
                'extension': extension,
                'url': url_for('uploaded_file', filename=f"documents/{filename}") 
                      if 'UPLOADS_URL_PATH' in current_app.config 
                      else url_for('static', filename=f"uploads/documents/{filename}")
            }
            documents.append(document)
    
    # Sort documents by modified time (newest first)
    documents.sort(key=lambda x: x['modified'], reverse=True)
    
    return render_template('admin/documents/index.html',
                          title="Document Management",
                          documents=documents)

@documents_bp.route('/upload', methods=['POST'])
@login_required
def upload_document():
    """Handle document uploads"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_document(file.filename):
        file_path = save_document(file)
        if file_path:
            # Get the URL for the uploaded document
            if 'UPLOADS_URL_PATH' in current_app.config:
                # For persistent storage on Render
                url = url_for('uploaded_file', filename=file_path)
            else:
                # For local development
                url = url_for('static', filename=file_path)
                
            # Return success response with document info
            return jsonify({
                'success': True,
                'url': url,
                'filename': os.path.basename(file_path),
                'original_name': file.filename
            })
    
    return jsonify({'error': 'Invalid file type'}), 400

@documents_bp.route('/delete/<path:filename>', methods=['POST'])
@login_required
def delete_document(filename):
    """Delete an uploaded document"""
    try:
        # Get the upload folder from app config
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        # Construct the full path to the file
        file_path = os.path.join(upload_folder, 'documents', filename)
        
        # Check if the file exists
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Delete the file
            os.remove(file_path)
            flash('Document deleted successfully!', 'success')
        else:
            flash('Document not found!', 'error')
            
    except Exception as e:
        current_app.logger.error(f"Error deleting document: {e}")
        flash(f'Error deleting document: {str(e)}', 'error')
    
    return redirect(url_for('documents.index'))
