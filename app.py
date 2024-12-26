from flask import Flask, render_template, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
import os
from pathlib import Path

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
BASE_DIR = Path.home()  # Default to user's home directory

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/files')
def list_files():
    path = request.args.get('path', '')
    current_dir = BASE_DIR / path if path else BASE_DIR
    
    try:
        if not current_dir.exists():
            return jsonify({'error': 'Directory not found'}), 404
        
        files = []
        for item in current_dir.iterdir():
            try:
                files.append({
                    'name': item.name,
                    'path': str(item.relative_to(BASE_DIR)),
                    'is_dir': item.is_dir(),
                    'size': os.path.getsize(item) if item.is_file() else None,
                    'modified': os.path.getmtime(item)
                })
            except (PermissionError, OSError):
                continue
                
        return jsonify({
            'current_path': str(current_dir.relative_to(BASE_DIR)) if current_dir != BASE_DIR else '',
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
    upload_dir = BASE_DIR / path if path else BASE_DIR
    
    try:
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
        file_path = BASE_DIR / path
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
        file_path = BASE_DIR / filepath
        if not file_path.exists() or not file_path.is_file():
            abort(404)
        return send_file(str(file_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
