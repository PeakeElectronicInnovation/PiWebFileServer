from flask import Flask, render_template, request, jsonify, send_file, abort, redirect, url_for
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import psutil
import socket
import time
from datetime import datetime
import config
import logging
import ssl
from werkzeug.middleware.proxy_fix import ProxyFix
import mimetypes
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

# Log configuration on startup
logger.info(f"Starting Pi File Server")
logger.info(f"Base Directory: {config.BASE_DIR}")
logger.info(f"Working Directory: {os.getcwd()}")

# Redirect HTTP to HTTPS
@app.before_request
def before_request():
    if not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

def get_system_stats():
    # Get system information
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(config.BASE_DIR)
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    
    return {
        'hostname': socket.gethostname(),
        'ip_address': socket.gethostbyname(socket.gethostname()),
        'uptime': str(uptime).split('.')[0],  # Remove microseconds
        'cpu_usage': f"{cpu_percent}%",
        'ram_total': f"{memory.total / (1024**3):.1f} GB",
        'ram_used': f"{memory.used / (1024**3):.1f} GB",
        'ram_percent': f"{memory.percent}%",
        'disk_total': f"{disk.total / (1024**3):.1f} GB",
        'disk_used': f"{disk.used / (1024**3):.1f} GB",
        'disk_free': f"{disk.free / (1024**3):.1f} GB",
        'disk_percent': f"{disk.percent}%"
    }

def is_previewable(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        return False
        
    previewable_types = [
        'text/',
        'image/',
        'application/pdf',
        'application/json',
        'application/javascript',
        'application/xml',
        'application/x-httpd-php',
    ]
    
    return any(mime_type.startswith(t) for t in previewable_types)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/system-stats')
def system_stats():
    return jsonify(get_system_stats())

@app.route('/api/files')
def list_files():
    path = request.args.get('path', '')
    
    # Ensure the path is within the allowed base directory
    try:
        requested_path = Path(config.BASE_DIR) / path
        requested_path = requested_path.resolve()
        if not str(requested_path).startswith(config.BASE_DIR):
            return jsonify({'error': 'Access denied: Path is outside base directory'}), 403
        
        if not requested_path.exists():
            return jsonify({'error': 'Directory not found'}), 404
        
        files = []
        for item in requested_path.iterdir():
            try:
                is_file = item.is_file()
                files.append({
                    'name': item.name,
                    'path': str(item.relative_to(Path(config.BASE_DIR))),
                    'is_dir': not is_file,
                    'size': os.path.getsize(item) if is_file else None,
                    'modified': os.path.getmtime(item),
                    'previewable': is_previewable(item.name) if is_file else False
                })
            except (PermissionError, OSError):
                continue
                
        return jsonify({
            'current_path': str(requested_path.relative_to(Path(config.BASE_DIR))) if str(requested_path) != config.BASE_DIR else '',
            'files': files
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    path = request.form.get('path', '')
    
    try:
        upload_dir = Path(config.BASE_DIR) / path
        upload_dir = upload_dir.resolve()
        if not str(upload_dir).startswith(config.BASE_DIR):
            return jsonify({'error': 'Access denied: Upload path is outside base directory'}), 403
        
        if not upload_dir.exists():
            return jsonify({'error': 'Upload directory not found'}), 404
        
        filename = secure_filename(file.filename)
        file_path = upload_dir / filename
        file.save(str(file_path))
        
        return jsonify({'message': 'File uploaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def delete_file():
    path = request.json.get('path', '')
    if not path:
        return jsonify({'error': 'No path specified'}), 400
    
    try:
        file_path = Path(config.BASE_DIR) / path
        file_path = file_path.resolve()
        if not str(file_path).startswith(config.BASE_DIR):
            return jsonify({'error': 'Access denied: Delete path is outside base directory'}), 403
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        if file_path.is_file():
            file_path.unlink()
        else:
            file_path.rmdir()  # Only delete empty directories
            
        return jsonify({'message': 'Deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<path:filepath>')
def download_file(filepath):
    try:
        file_path = Path(config.BASE_DIR) / filepath
        file_path = file_path.resolve()
        if not str(file_path).startswith(config.BASE_DIR):
            return jsonify({'error': 'Access denied: Download path is outside base directory'}), 403
            
        if not file_path.exists() or not file_path.is_file():
            abort(404)
            
        download_mode = request.args.get('download', 'false').lower() == 'true'
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        if download_mode:
            return send_file(
                str(file_path),
                as_attachment=True,
                download_name=file_path.name
            )
        else:
            return send_file(
                str(file_path),
                mimetype=mime_type if mime_type else 'application/octet-stream'
            )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-directory', methods=['POST'])
def create_directory():
    path = request.json.get('path', '')
    name = request.json.get('name', '').strip()
    
    if not name:
        return jsonify({'error': 'Directory name is required'}), 400
    
    if any(char in name for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
        return jsonify({'error': 'Invalid directory name'}), 400
    
    try:
        parent_dir = Path(config.BASE_DIR) / path
        parent_dir = parent_dir.resolve()
        if not str(parent_dir).startswith(config.BASE_DIR):
            return jsonify({'error': 'Access denied: Path is outside base directory'}), 403
        
        new_dir = parent_dir / name
        if new_dir.exists():
            return jsonify({'error': 'Directory already exists'}), 409
            
        new_dir.mkdir(parents=True)
        return jsonify({'message': 'Directory created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bulk-delete', methods=['POST'])
def bulk_delete():
    paths = request.json.get('paths', [])
    if not paths:
        return jsonify({'error': 'No paths specified'}), 400
    
    results = []
    for path in paths:
        try:
            file_path = Path(config.BASE_DIR) / path
            file_path = file_path.resolve()
            if not str(file_path).startswith(config.BASE_DIR):
                results.append({'path': path, 'success': False, 'error': 'Access denied'})
                continue
                
            if not file_path.exists():
                results.append({'path': path, 'success': False, 'error': 'Not found'})
                continue
                
            if file_path.is_file():
                file_path.unlink()
            else:
                file_path.rmdir()  # Only delete empty directories
            results.append({'path': path, 'success': True})
        except Exception as e:
            results.append({'path': path, 'success': False, 'error': str(e)})
    
    return jsonify({'results': results})

@app.route('/api/bulk-move', methods=['POST'])
def bulk_move():
    paths = request.json.get('paths', [])
    target = request.json.get('target', '')
    if not paths:
        return jsonify({'error': 'No paths specified'}), 400
        
    try:
        # Handle root directory case
        target_dir = Path(config.BASE_DIR)
        if target:  # Only append target path if it's not empty
            target_dir = target_dir / target
        target_dir = target_dir.resolve()
        
        if not str(target_dir).startswith(config.BASE_DIR):
            return jsonify({'error': 'Access denied: Target is outside base directory'}), 403
        if not target_dir.is_dir():
            return jsonify({'error': 'Target is not a directory'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    results = []
    for path in paths:
        try:
            source_path = Path(config.BASE_DIR) / path
            source_path = source_path.resolve()
            if not str(source_path).startswith(config.BASE_DIR):
                results.append({'path': path, 'success': False, 'error': 'Access denied'})
                continue
                
            if not source_path.exists():
                results.append({'path': path, 'success': False, 'error': 'Not found'})
                continue
                
            new_path = target_dir / source_path.name
            if new_path.exists():
                results.append({'path': path, 'success': False, 'error': 'Target already exists'})
                continue
                
            source_path.rename(new_path)
            results.append({'path': path, 'success': True})
        except Exception as e:
            results.append({'path': path, 'success': False, 'error': str(e)})
    
    return jsonify({'results': results})

@app.route('/api/bulk-download', methods=['POST'])
def bulk_download():
    # Handle both JSON and form data
    if request.is_json:
        paths = request.json.get('paths', [])
    else:
        paths = request.form.get('paths', '')
        try:
            paths = json.loads(paths)
        except:
            paths = []
            
    if not paths:
        return jsonify({'error': 'No paths specified'}), 400
        
    # Create a temporary zip file
    import tempfile
    import zipfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    try:
        zip_path = Path(temp_dir) / 'download.zip'
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for path in paths:
                try:
                    file_path = Path(config.BASE_DIR) / path
                    file_path = file_path.resolve()
                    if not str(file_path).startswith(config.BASE_DIR):
                        continue
                    if not file_path.exists() or not file_path.is_file():
                        continue
                    # Store files with relative paths in the zip
                    rel_path = file_path.relative_to(Path(config.BASE_DIR))
                    zipf.write(file_path, str(rel_path))
                except Exception as e:
                    app.logger.error(f"Error adding file to zip: {e}")
                    continue
                    
        return send_file(
            zip_path,
            as_attachment=True,
            download_name='download.zip',
            mimetype='application/zip'
        )
    finally:
        # Clean up temp directory in the background
        def cleanup():
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        import threading
        threading.Timer(60, cleanup).start()

if __name__ == '__main__':
    ssl_context = None
    if os.path.exists(config.SSL_CERT) and os.path.exists(config.SSL_KEY):
        ssl_context = (config.SSL_CERT, config.SSL_KEY)
        logger.info(f"Using SSL certificates from {config.SSL_DIR}")
    else:
        logger.warning("SSL certificates not found, running in HTTP mode")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        ssl_context=ssl_context,
        debug=True
    )
