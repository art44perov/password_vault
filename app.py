import os
import sys
import socket
import threading
import subprocess
import webbrowser
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, Response
from models import db, VaultConfig, VaultEntry
from crypto import (derive_key, generate_salt, hash_master_password,
                    verify_master_password, encrypt_data, decrypt_data,
                    generate_password, check_password_strength)
from auth import set_session_key, get_session_key, clear_session, is_authenticated
import backup as backup_module
import json
import base64
import io

def _is_frozen():
    return getattr(sys, 'frozen', False)

def resource_dir():
    """Bundled files (templates, static) live here."""
    if _is_frozen():
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def app_dir():
    """Writable files (database, backups) live next to the exe or script."""
    if _is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = app_dir()
RESOURCE_DIR = resource_dir()
DB_DIR = os.path.join(BASE_DIR, 'database')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

app = Flask(
    __name__,
    template_folder=os.path.join(RESOURCE_DIR, 'templates'),
    static_folder=os.path.join(RESOURCE_DIR, 'static'),
)
app.config['SECRET_KEY'] = os.urandom(32)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(DB_DIR, "vault.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db.init_app(app)

with app.app_context():
    db.create_all()

def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated():
            if request.is_json:
                return jsonify({'error': 'Unauthorized', 'redirect': '/'}), 401
            return redirect('/')
        return f(*args, **kwargs)
    return decorated

def is_setup_complete():
    with app.app_context():
        cfg = VaultConfig.query.filter_by(key='master_hash').first()
        return cfg is not None

# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    setup_done = is_setup_complete()
    if setup_done and is_authenticated():
        return redirect('/vault')
    return render_template('index.html', setup_done=setup_done)

@app.route('/vault')
@require_auth
def vault():
    return render_template('vault.html')

@app.route('/api/setup', methods=['POST'])
def setup():
    if is_setup_complete():
        return jsonify({'error': 'Already configured'}), 400
    
    data = request.get_json()
    password = data.get('password', '')
    
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    salt = generate_salt()
    master_hash = hash_master_password(password)
    enc_key = derive_key(password, salt)
    
    db.session.add(VaultConfig(key='master_hash', value=master_hash))
    db.session.add(VaultConfig(key='salt', value=base64.b64encode(salt).decode()))
    db.session.commit()
    
    set_session_key(enc_key)
    return jsonify({'success': True})

@app.route('/api/unlock', methods=['POST'])
def unlock():
    if not is_setup_complete():
        return jsonify({'error': 'Not configured'}), 400
    
    data = request.get_json()
    password = data.get('password', '')
    timeout = int(data.get('timeout', 15))
    
    master_hash_cfg = VaultConfig.query.filter_by(key='master_hash').first()
    salt_cfg = VaultConfig.query.filter_by(key='salt').first()
    
    if not master_hash_cfg or not salt_cfg:
        return jsonify({'error': 'Configuration error'}), 500
    
    if not verify_master_password(master_hash_cfg.value, password):
        return jsonify({'error': 'Invalid master password'}), 401
    
    salt = base64.b64decode(salt_cfg.value.encode())
    enc_key = derive_key(password, salt)
    set_session_key(enc_key, timeout)
    
    return jsonify({'success': True})

@app.route('/api/lock', methods=['POST'])
def lock():
    clear_session()
    return jsonify({'success': True})

@app.route('/api/entries', methods=['GET'])
@require_auth
def get_entries():
    key = get_session_key()
    category = request.args.get('category', '')
    search = request.args.get('search', '').lower()
    show_archived = request.args.get('archived', 'false') == 'true'
    favorites_only = request.args.get('favorites', 'false') == 'true'
    
    query = VaultEntry.query.filter_by(is_archived=show_archived)
    
    if favorites_only:
        query = query.filter_by(is_favorite=True, is_archived=False)
    
    if category and category != 'all':
        query = query.filter_by(category=category)
    
    entries = query.order_by(VaultEntry.sort_order, VaultEntry.updated_at.desc()).all()
    
    result = []
    for e in entries:
        d = e.to_dict()
        # Decrypt title and username for display
        try:
            d['title'] = decrypt_data(e.title, key)
        except:
            d['title'] = '[Encrypted]'
        try:
            d['username'] = decrypt_data(e.username, key) if e.username else ''
        except:
            d['username'] = ''
        try:
            d['url'] = decrypt_data(e.url, key) if e.url else ''
        except:
            d['url'] = ''
        try:
            d['description'] = decrypt_data(e.description, key) if e.description else ''
        except:
            d['description'] = ''
        
        # Check password strength
        try:
            pwd = decrypt_data(e.password, key) if e.password else ''
            strength = check_password_strength(pwd)
            d['password_strength'] = strength['strength']
            d['password_length'] = len(pwd)
        except:
            d['password_strength'] = 'unknown'
            d['password_length'] = 0
        
        # Search filter
        if search:
            searchable = f"{d['title']} {d['username']} {d['url']} {d['description']} {' '.join(d['tags'])}".lower()
            if search not in searchable:
                continue
        
        result.append(d)
    
    return jsonify(result)

@app.route('/api/entries/<int:entry_id>/password', methods=['GET'])
@require_auth
def get_password(entry_id):
    key = get_session_key()
    e = VaultEntry.query.get_or_404(entry_id)
    try:
        pwd = decrypt_data(e.password, key) if e.password else ''
        return jsonify({'password': pwd})
    except:
        return jsonify({'error': 'Decryption failed'}), 500

@app.route('/api/entries', methods=['POST'])
@require_auth
def create_entry():
    key = get_session_key()
    data = request.get_json()
    
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    tags = data.get('tags', [])
    if isinstance(tags, list):
        tags_str = ','.join(t.strip() for t in tags if t.strip())
    else:
        tags_str = str(tags)
    
    e = VaultEntry(
        title=encrypt_data(title, key),
        username=encrypt_data(data.get('username', ''), key),
        password=encrypt_data(data.get('password', ''), key),
        url=encrypt_data(data.get('url', ''), key),
        description=encrypt_data(data.get('description', ''), key),
        category=data.get('category', 'other'),
        tags=tags_str,
        color=data.get('color', 'default'),
        is_favorite=bool(data.get('is_favorite', False)),
    )
    db.session.add(e)
    db.session.commit()
    
    return jsonify({'success': True, 'id': e.id})

@app.route('/api/entries/<int:entry_id>', methods=['GET'])
@require_auth
def get_entry(entry_id):
    key = get_session_key()
    e = VaultEntry.query.get_or_404(entry_id)
    d = e.to_dict()
    try:
        d['title'] = decrypt_data(e.title, key)
        d['username'] = decrypt_data(e.username, key) if e.username else ''
        d['password'] = decrypt_data(e.password, key) if e.password else ''
        d['url'] = decrypt_data(e.url, key) if e.url else ''
        d['description'] = decrypt_data(e.description, key) if e.description else ''
    except:
        return jsonify({'error': 'Decryption failed'}), 500
    return jsonify(d)

@app.route('/api/entries/<int:entry_id>', methods=['PUT'])
@require_auth
def update_entry(entry_id):
    key = get_session_key()
    e = VaultEntry.query.get_or_404(entry_id)
    data = request.get_json()
    
    if 'title' in data:
        e.title = encrypt_data(data['title'], key)
    if 'username' in data:
        e.username = encrypt_data(data.get('username', ''), key)
    if 'password' in data:
        e.password = encrypt_data(data.get('password', ''), key)
    if 'url' in data:
        e.url = encrypt_data(data.get('url', ''), key)
    if 'description' in data:
        e.description = encrypt_data(data.get('description', ''), key)
    if 'category' in data:
        e.category = data['category']
    if 'tags' in data:
        tags = data['tags']
        if isinstance(tags, list):
            e.tags = ','.join(t.strip() for t in tags if t.strip())
        else:
            e.tags = str(tags)
    if 'color' in data:
        e.color = data['color']
    if 'is_favorite' in data:
        e.is_favorite = bool(data['is_favorite'])
    if 'is_archived' in data:
        e.is_archived = bool(data['is_archived'])
    if 'sort_order' in data:
        e.sort_order = int(data['sort_order'])
    
    e.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
@require_auth
def delete_entry(entry_id):
    e = VaultEntry.query.get_or_404(entry_id)
    db.session.delete(e)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/generate-password', methods=['POST'])
@require_auth
def gen_password():
    data = request.get_json() or {}
    pwd = generate_password(
        length=int(data.get('length', 16)),
        use_upper=bool(data.get('use_upper', True)),
        use_digits=bool(data.get('use_digits', True)),
        use_special=bool(data.get('use_special', True)),
        exclude_similar=bool(data.get('exclude_similar', False)),
    )
    strength = check_password_strength(pwd)
    return jsonify({'password': pwd, 'strength': strength})

@app.route('/api/check-strength', methods=['POST'])
@require_auth
def check_strength():
    data = request.get_json() or {}
    pwd = data.get('password', '')
    return jsonify(check_password_strength(pwd))

@app.route('/api/stats', methods=['GET'])
@require_auth
def stats():
    key = get_session_key()
    total = VaultEntry.query.filter_by(is_archived=False).count()
    favorites = VaultEntry.query.filter_by(is_favorite=True, is_archived=False).count()
    archived = VaultEntry.query.filter_by(is_archived=True).count()
    
    cats = db.session.query(VaultEntry.category, db.func.count(VaultEntry.id))\
        .filter_by(is_archived=False).group_by(VaultEntry.category).all()
    categories = {c: n for c, n in cats}
    
    # Count weak passwords
    weak = 0
    entries = VaultEntry.query.filter_by(is_archived=False).all()
    for e in entries:
        try:
            pwd = decrypt_data(e.password, key) if e.password else ''
            s = check_password_strength(pwd)
            if s['strength'] in ('weak', 'fair'):
                weak += 1
        except:
            pass
    
    recent = VaultEntry.query.filter_by(is_archived=False)\
        .order_by(VaultEntry.updated_at.desc()).limit(5).all()
    recent_list = []
    for e in recent:
        try:
            title = decrypt_data(e.title, key)
        except:
            title = '[Encrypted]'
        recent_list.append({
            'id': e.id,
            'title': title,
            'category': e.category,
            'updated_at': e.updated_at.isoformat() if e.updated_at else None
        })
    
    return jsonify({
        'total': total,
        'favorites': favorites,
        'archived': archived,
        'categories': categories,
        'weak_passwords': weak,
        'recent': recent_list
    })

@app.route('/api/export/json', methods=['GET'])
@require_auth
def export_json():
    key = get_session_key()
    entries = VaultEntry.query.filter_by(is_archived=False).all()
    result = []
    for e in entries:
        d = e.to_dict()
        try:
            d['title'] = decrypt_data(e.title, key)
            d['username'] = decrypt_data(e.username, key) if e.username else ''
            d['password'] = decrypt_data(e.password, key) if e.password else ''
            d['url'] = decrypt_data(e.url, key) if e.url else ''
            d['description'] = decrypt_data(e.description, key) if e.description else ''
        except:
            continue
        result.append(d)
    
    content = backup_module.export_json(result)
    return Response(
        content,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=vault_export_{datetime.now().strftime("%Y%m%d")}.json'}
    )

@app.route('/api/export/csv', methods=['GET'])
@require_auth
def export_csv():
    key = get_session_key()
    entries = VaultEntry.query.filter_by(is_archived=False).all()
    result = []
    for e in entries:
        d = e.to_dict()
        try:
            d['title'] = decrypt_data(e.title, key)
            d['username'] = decrypt_data(e.username, key) if e.username else ''
            d['password'] = decrypt_data(e.password, key) if e.password else ''
            d['url'] = decrypt_data(e.url, key) if e.url else ''
            d['description'] = decrypt_data(e.description, key) if e.description else ''
        except:
            continue
        result.append(d)
    
    content = backup_module.export_csv(result)
    return Response(
        content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=vault_export_{datetime.now().strftime("%Y%m%d")}.csv'}
    )

@app.route('/api/import', methods=['POST'])
@require_auth
def import_data():
    key = get_session_key()
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    
    content = file.read().decode('utf-8')
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.json'):
            entries = backup_module.import_json(content)
        elif filename.endswith('.csv'):
            entries = backup_module.import_csv(content)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
    except Exception as ex:
        return jsonify({'error': f'Parse error: {str(ex)}'}), 400
    
    imported = 0
    for entry in entries:
        try:
            tags = entry.get('tags', [])
            if isinstance(tags, list):
                tags_str = ','.join(tags)
            else:
                tags_str = str(tags)
            
            e = VaultEntry(
                title=encrypt_data(str(entry.get('title', '')), key),
                username=encrypt_data(str(entry.get('username', '')), key),
                password=encrypt_data(str(entry.get('password', '')), key),
                url=encrypt_data(str(entry.get('url', '')), key),
                description=encrypt_data(str(entry.get('description', '')), key),
                category=entry.get('category', 'other'),
                tags=tags_str,
                color=entry.get('color', 'default'),
            )
            db.session.add(e)
            imported += 1
        except:
            continue
    
    db.session.commit()
    return jsonify({'success': True, 'imported': imported})

@app.route('/api/backup', methods=['POST'])
@require_auth
def create_backup():
    key = get_session_key()
    entries = VaultEntry.query.all()
    result = []
    for e in entries:
        d = e.to_dict(include_encrypted=True)
        result.append(d)
    
    filepath = backup_module.create_backup(result, BACKUP_DIR)
    return jsonify({'success': True, 'path': filepath})

@app.route('/api/check-duplicates', methods=['GET'])
@require_auth
def check_duplicates():
    key = get_session_key()
    entries = VaultEntry.query.filter_by(is_archived=False).all()
    
    passwords = {}
    for e in entries:
        try:
            pwd = decrypt_data(e.password, key) if e.password else ''
            title = decrypt_data(e.title, key)
        except:
            continue
        if pwd:
            if pwd not in passwords:
                passwords[pwd] = []
            passwords[pwd].append({'id': e.id, 'title': title})
    
    duplicates = {k: v for k, v in passwords.items() if len(v) > 1}
    return jsonify({'duplicates': list(duplicates.values())})

@app.route('/api/session-status', methods=['GET'])
def session_status():
    return jsonify({'authenticated': is_authenticated()})

APP_TITLE = 'Password Vault Pro'
PREFERRED_PORT = 8000

def add_to_startup():
    """Add app to Windows startup"""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        if _is_frozen():
            command = f'"{sys.executable}"'
        else:
            command = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
        winreg.SetValueEx(key, "PasswordVaultPro", 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
    except:
        pass  # Not on Windows or no permission

def _log_path():
    return os.path.join(app_dir(), 'vault.log')

def _append_log(message):
    try:
        with open(_log_path(), 'a', encoding='utf-8') as f:
            f.write(message.rstrip() + '\n')
    except Exception:
        pass

def show_error(message):
    _append_log(message)
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, APP_TITLE, 0x10)
    except Exception:
        pass

def find_free_port(preferred=PREFERRED_PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(('127.0.0.1', preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def wait_for_server(url, timeout=20):
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=0.4)
            return True
        except Exception:
            time.sleep(0.12)
    return False

def start_server(host, port):
    try:
        from waitress import serve
        serve(app, host=host, port=port, threads=8, ident='PasswordVaultPro')
    except Exception:
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)

def open_webview(url):
    """Native desktop window (WebView2 on Windows, Cocoa on macOS, GTK on Linux)."""
    import webview

    gui = None
    if sys.platform.startswith('win'):
        gui = 'edgechromium'
    elif sys.platform == 'darwin':
        gui = 'cocoa'
    else:
        import gi
        gi.require_version('Gtk', '3.0')
        try:
            gi.require_version('WebKit2', '4.1')
        except ValueError:
            gi.require_version('WebKit2', '4.0')
        gui = 'gtk'

    webview.create_window(
        APP_TITLE,
        url,
        width=1280,
        height=860,
        min_size=(900, 600),
        text_select=True,
        confirm_close=False,
        background_color='#0f172a',
    )
    webview.start(gui=gui)

def _browser_candidates():
    env = os.environ
    local = env.get('LOCALAPPDATA', '')
    pf = env.get('PROGRAMFILES', r'C:\Program Files')
    pf86 = env.get('PROGRAMFILES(X86)', r'C:\Program Files (x86)')
    names = [
        os.path.join(pf86, r'Microsoft\Edge\Application\msedge.exe'),
        os.path.join(pf, r'Microsoft\Edge\Application\msedge.exe'),
        os.path.join(local, r'Microsoft\Edge\Application\msedge.exe'),
        os.path.join(pf, r'Google\Chrome\Application\chrome.exe'),
        os.path.join(local, r'Google\Chrome\Application\chrome.exe'),
        os.path.join(pf86, r'Google\Chrome\Application\chrome.exe'),
        'msedge',
        'chrome',
        'google-chrome-stable',
        'google-chrome',
        'chromium',
        'chromium-browser',
        'microsoft-edge',
    ]
    from shutil import which
    found = []
    for item in names:
        if os.path.sep in item or (len(item) > 1 and item[1] == ':'):
            if os.path.isfile(item):
                found.append(item)
        else:
            path = which(item)
            if path:
                found.append(path)
    return found

def open_chrome_app(url):
    """Tabless Chrome/Edge window — fallback if native webview is unavailable."""
    browsers = _browser_candidates()
    if not browsers:
        return False
    profile = os.path.join(app_dir(), '.vault-ui')
    os.makedirs(profile, exist_ok=True)
    args = [
        browsers[0],
        f'--app={url}',
        '--window-size=1280,860',
        f'--user-data-dir={profile}',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-extensions',
        '--disable-sync',
        '--disable-features=Translate',
        '--class=PasswordVaultPro',
    ]
    proc = subprocess.Popen(args)
    proc.wait()
    return True

def run_desktop():
    add_to_startup()
    host = '127.0.0.1'
    port = find_free_port()
    url = f'http://{host}:{port}'

    server = threading.Thread(target=start_server, args=(host, port), daemon=True)
    server.start()
    if not wait_for_server(url):
        show_error('Не удалось запустить локальный сервер Password Vault Pro.')
        sys.exit(1)

    try:
        open_webview(url)
        return
    except Exception as exc:
        _append_log(f'webview failed: {exc}')

    try:
        if open_chrome_app(url):
            return
    except Exception as exc:
        _append_log(f'chrome app failed: {exc}')

    webbrowser.open(url)
    server.join()

if __name__ == '__main__':
    run_desktop()
