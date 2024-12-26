from flask import Flask, render_template, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import psutil
import socket
import time
from datetime import datetime
import config

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

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
                files.append({
                    'name': item.name,
                    'path': str(item.relative_to(Path(config.BASE_DIR))),
                    'is_dir': item.is_dir(),
                    'size': os.path.getsize(item) if item.is_file() else None,
                    'modified': os.path.getmtime(item)
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
        return send_file(str(file_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=True)
