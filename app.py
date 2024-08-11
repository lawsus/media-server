from flask import Flask, render_template, send_from_directory, request, abort
import os
import ssl

app = Flask(__name__)

# Configuration
MEDIA_FOLDER = 'media file path'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}
ITEMS_PER_PAGE = 50

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files_and_folders(path):
    items = os.listdir(path)
    files = sorted([f for f in items if os.path.isfile(os.path.join(path, f)) and allowed_file(f)])
    folders = sorted([f for f in items if os.path.isdir(os.path.join(path, f))])
    return files, folders

def get_adjacent_files(current_file, file_list):
    current_index = file_list.index(current_file)
    prev_file = file_list[current_index - 1] if current_index > 0 else None
    next_file = file_list[current_index + 1] if current_index < len(file_list) - 1 else None
    return prev_file, next_file

@app.route('/')
@app.route('/<path:subpath>')
def index(subpath=''):
    full_path = os.path.join(MEDIA_FOLDER, subpath)
    if not os.path.exists(full_path) or not os.path.commonpath([MEDIA_FOLDER, full_path]) == MEDIA_FOLDER:
        return "Invalid path", 404

    files, folders = get_files_and_folders(full_path)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    paginated_files = files[start:end]
    
    parent = os.path.dirname(subpath) if subpath else None
    total_pages = (len(files) - 1) // ITEMS_PER_PAGE + 1
    
    return render_template('index.html', 
                           files=paginated_files, 
                           folders=folders, 
                           current_path=subpath, 
                           parent=parent, 
                           page=page, 
                           total_pages=total_pages)

@app.route('/view/<path:filepath>')
def view_media(filepath):
    full_path = os.path.join(MEDIA_FOLDER, filepath)
    if not os.path.exists(full_path) or not os.path.commonpath([MEDIA_FOLDER, full_path]) == MEDIA_FOLDER:
        abort(404)
    
    filename = os.path.basename(filepath)
    folder_path = os.path.dirname(filepath)
    files, _ = get_files_and_folders(os.path.join(MEDIA_FOLDER, folder_path))
    prev_file, next_file = get_adjacent_files(filename, files)
    
    file_type = 'video' if filename.lower().endswith(('.mp4', '.avi', '.mov')) else 'image'
    
    return render_template('view_media.html', 
                           filename=filename,
                           filepath=filepath,
                           file_type=file_type,
                           prev_file=prev_file,
                           next_file=next_file,
                           folder_path=folder_path)

@app.route('/media/<path:filename>')
def serve_media(filename):
    return send_from_directory(MEDIA_FOLDER, filename)

@app.template_global()
def join_paths(*args):
    return os.path.join(*args)

if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('server.crt', 'server.key')
    
    app.run(host='0.0.0.0', port=8000, ssl_context=context, debug=True)