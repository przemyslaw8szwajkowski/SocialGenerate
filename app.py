from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import LookupError as DropboxLookupError
from datetime import datetime
import logging
from urllib.parse import quote_plus
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', force=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'

def _build_database_uri():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgresql://'):
            return database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        return database_url

    pg_user = os.getenv('POSTGRES_USER')
    pg_password = os.getenv('POSTGRES_PASSWORD')
    pg_host = os.getenv('POSTGRES_HOST')
    pg_port = os.getenv('POSTGRES_PORT', '5432')
    pg_db = os.getenv('POSTGRES_DB')

    if all([pg_user, pg_password, pg_host, pg_db]):
        encoded_password = quote_plus(pg_password)
        return f"postgresql+psycopg://{pg_user}:{encoded_password}@{pg_host}:{pg_port}/{pg_db}?sslmode=require"

    return 'sqlite:///users.db'

app.config['SQLALCHEMY_DATABASE_URI'] = _build_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Utwórz folder uploads jeśli go nie ma
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

DROPBOX_ACCESS_TOKEN = "sl.u.AGRQD50xTaGB020dK_3w0Ru-TX5kD8Fx2CuUebk9274ZOSpKrd4fATEfvvUVtodHl-1biNWwnOSnSm2Jalvoh6LGBGHUvaaRKhJbniH2lArSePRTBmmLo6EMMBNkg1XopeCcgP9LoO05ha8XqsdnMtTGCvtj1i6Gt-Q-f5EQVyrU1-xGaxq34d6xmp-dzZhvUVU1NKv5u0PCGRoU43PywJIeaZk2rEp3LB_3MY6-BnI6HRAS__EH5teMzvMOpTKlCsxO7RMWYUPGY8d_GYetBAn6baNS1EFIjayY-WI0D36TLleJ_-fAhsPbjtSOPjUSLhACwF6JeQPkIxtHwDq4Xh29_eXFlgE-BAL_p2VAe9AMAFFTGv1_YFh9ZTovnKBpRCBYSCP1FNfd1Ck3_3_nM5F_vh5LtWydns2lY4zfeY23Yz3fLDcgvJGbaxohF8W4WlCjdF0e1wvMP0O8wK18jtQnflhnYgCS0QwqjqNYXRIyPRzTX_toAGAmWgIMRW8hgSYeOQYne4142r5_E4NgpVeC4ou2MeBuAsqo2WG96PeenvSix1o46llD1wXoFVeExONVQm7A9-WSBUYeOHATzfl0rtVO2ZJfMtaNGGhrdDLJAkX5uFe_sZQStewdfeR6TMZotHHsaaArqgpLYI2rJdHmIft4e2MTcXZKNxjKhaeOAr-5gkh-atV89cNFSokjDrqslOJ7PDzOmKP72GZLQ0v5QRdov2-IEoyeKl4oD4qOIBvyTTotxEZs5DRJ9R_9IDfwnNIP8J3B6CYIXdZHgLtlI3bjOCmhHaMboALCeu4m3QWGvdR9Fg6f9b5k3z5dKrOSpOZS9DZ_1kaEC9xbV4gRfY8FGLKWkFAnhn9oCpO6atvgAn3jNaAKrrk1l1OgAWESTL8RyKrUyW3Sdq_Dq3N-QKpxYLLxFrqouYLV4Gm6BKS3Dh-qVTuaQ8yz_YP2FWGLNK-jsa11FFq1XYI_a3K-NOBzMKhH09NhHH4hFzE4MqjOZQ-vESGrkx2v1KiZtLMC183JUDY9k4JLdA-PiLm4uvYVplLXBQ-BQN8tAI03cOhzA2HqqO4HVJVBHD-aNJPJxr_wMY5WUHITuEcXFjqq5-MZbcP-SFwfvlvCqY0wRQLIjUUWxU_2TMNHeinJ5MpLgC442CkrKIsKB6dIV1h-pJ1zEZT10CXKS4fgwtAgcg3scD8YjrfFv8LbVtSmHpN6vLUk0E7DAD7kWVLw5V9quvxUNVnlQQfOy0l-6SPOKrhwqFU3m-FYQVhkZTQ2-HOL1kwV-xGlRZeHxmfBz_39smrqSrCwjD6VWqC94tXhWV-5sYcqpWnx5CMywQTHoyhG5ZsBJGlpqqNdJ66bLDKk"

db_client = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.String(500), nullable=False)
    images = db.Column(db.Text)  # CSV paths
    video = db.Column(db.String(200))
    location = db.Column(db.String(300), nullable=True)  # współrzędne lub nazwa lokalizacji
    created_at = db.Column(db.DateTime, default=db.func.now())
    send_at = db.Column(db.DateTime, nullable=True)
    dropbox_folder = db.Column(db.String(300), nullable=True)  # ścieżka folderu na Dropboxie
    n8n_sent = db.Column(db.Boolean, default=False)  # czy wysłano do n8n

with app.app_context():
    db.create_all()

    # Dostosowanie schematu dla PostgreSQL, jeśli tabela user powstała wcześniej z krótkim hasłem
    if db.engine.dialect.name == 'postgresql':
        db.session.execute(text('ALTER TABLE "user" ALTER COLUMN password TYPE VARCHAR(300)'))
        db.session.commit()

    if not User.query.filter_by(username='Admin').first():
        admin = User(username='Admin', password=generate_password_hash('Admin'))
        db.session.add(admin)
        db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Błędny login lub hasło')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    # Upload to Dropbox
    with open(file_path, 'rb') as f:
        dbx_path = f"/SocialMediaUploads/{filename}"
        db_client.files_upload(f.read(), dbx_path, mode=dropbox.files.WriteMode.overwrite)
    return jsonify({'message': 'File uploaded', 'filename': filename, 'dropbox_path': dbx_path})

@app.route('/upload-map-screenshot', methods=['POST'])
def upload_map_screenshot():
    """Endpoint do wysyłania screenshot'u mapy"""
    import base64
    from io import BytesIO
    
    data = request.get_json()
    screenshot_data = data.get('screenshot')
    lat = data.get('lat', '')
    lng = data.get('lng', '')
    
    if not screenshot_data:
        return jsonify({'error': 'Brak danych screenshot\'u'}), 400
    
    try:
        # Usuń prefix data:image/png;base64,
        if screenshot_data.startswith('data:image'):
            screenshot_data = screenshot_data.split(',')[1]
        
        # Dekoduj base64
        image_data = base64.b64decode(screenshot_data)
        
        # Wygeneruj nazwę pliku
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"mapa_{timestamp}_{current_user.id}.png"
        
        # Zapisz lokalnie
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        # Upload do Dropboxa
        dbx_path = f"/SocialMediaScreenshots/{current_user.username}/{filename}"
        db_client.files_upload(image_data, dbx_path, mode=dropbox.files.WriteMode.overwrite)
        
        logger.info(f"✓ Screenshot mapy zapisany: {filename} (koord: {lat}, {lng})")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'message': f'Screenshot mapy zapisany'
        }), 200
        
    except Exception as e:
        logger.error(f"✗ Błąd przy zapisywaniu screenshot\'u: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-description', methods=['POST'])
def generate_description():
    data = request.get_json(silent=True) or {}
    user_text = data.get('text', '')
    # Placeholder for description generation logic
    description = f"Opis wygenerowany na podstawie: {user_text}"
    return jsonify({'description': description})

@app.route('/publish', methods=['POST'])
def publish():
    """Wysłanie posta do n8n, Instagram, Facebook, YouTube"""
    try:
        data = request.get_json()
        
        post_id = data.get('post_id')
        platform = data.get('platform', 'all')  # all, instagram, facebook, youtube
        
        logger.info(f"📤 Wysyłanie posta #{post_id} na platform(ę): {platform}")
        
        if post_id:
            post = Post.query.get(post_id)
            if not post or post.user_id != current_user.id:
                return jsonify({'error': 'Post nie znaleziony'}), 404
            
            # Oznacz jako wysłane do n8n
            post.n8n_sent = True
            db.session.commit()
            
            return jsonify({
                'status': 'sent to n8n',
                'post_id': post.id,
                'platform': platform,
                'dropbox_folder': post.dropbox_folder,
                'message': f'Post wysłany do n8n (platforma: {platform})'
            }), 200
        else:
            return jsonify({'error': 'Brak post_id'}), 400
            
    except Exception as e:
        logger.error(f"✗ Błąd wysyłania do n8n: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts', methods=['GET'])
def get_posts():
    """API: Lista postów zalogowanego użytkownika"""
    try:
        posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all()
        
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.id,
                'description': post.description,
                'location': post.location,
                'images': post.images.split(',') if post.images else [],
                'video': post.video,
                'created_at': post.created_at.isoformat(),
                'send_at': post.send_at.isoformat() if post.send_at else None,
                'dropbox_folder': post.dropbox_folder,
                'n8n_sent': post.n8n_sent
            })
        
        return jsonify({
            'status': 'success',
            'count': len(posts_data),
            'posts': posts_data
        }), 200
        
    except Exception as e:
        logger.error(f"✗ Błąd pobierania postów: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """API: Szczegóły konkretnego posta"""
    try:
        post = Post.query.get(post_id)
        if not post or post.user_id != current_user.id:
            return jsonify({'error': 'Post nie znaleziony'}), 404
        
        return jsonify({
            'status': 'success',
            'post': {
                'id': post.id,
                'description': post.description,
                'location': post.location,
                'images': post.images.split(',') if post.images else [],
                'video': post.video,
                'created_at': post.created_at.isoformat(),
                'send_at': post.send_at.isoformat() if post.send_at else None,
                'dropbox_folder': post.dropbox_folder,
                'n8n_sent': post.n8n_sent
            }
        }), 200
        
    except Exception as e:
        logger.error(f"✗ Błąd pobierania posta: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>/send-to-n8n', methods=['POST'])
def send_to_n8n(post_id):
    """API: Wysłanie posta do n8n na zdefiniowane platformy"""
    try:
        post = Post.query.get(post_id)
        if not post or post.user_id != current_user.id:
            return jsonify({'error': 'Post nie znaleziony'}), 404
        
        data = request.get_json(silent=True) or {}
        platforms = data.get('platforms', ['instagram', 'facebook', 'youtube'])
        
        logger.info(f"📤 Wysyłam post #{post_id} do: {', '.join(platforms)}")
        
        # Oznacz jako wysłane
        post.n8n_sent = True
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Post #{post_id} wysłany do n8n',
            'platforms': platforms,
            'post_id': post_id,
            'post_data': {
                'description': post.description,
                'location': post.location,
                'dropbox_folder': post.dropbox_folder,
                'images': post.images.split(',') if post.images else [],
                'video': post.video
            }
        }), 200
        
    except Exception as e:
        logger.error(f"✗ Błąd wysyłania do n8n: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-description', methods=['POST'])
def api_generate_description():
    """API: Generowanie popisów na podstawie tekstu"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Brak tekstu'}), 400
        
        # Tutaj można dodać AI generowanie opisu
        description = f"📱 {text} #socialmedia #content"
        
        return jsonify({
            'status': 'success',
            'input_text': text,
            'generated_description': description
        }), 200
        
    except Exception as e:
        logger.error(f"✗ Błąd generowania opisu: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
@login_required
def index():
    return render_template('index.html', username=current_user.username)

@app.route('/api/debugpost/<int:post_id>')
@login_required
def debug_post(post_id):
    """Debug endpoint - pokazuje dokładnie co jest w bazie dla posta"""
    post = Post.query.get(post_id)
    if not post or post.user_id != current_user.id:
        return jsonify({'error': 'Nie masz dostępu do tego posta'}), 403
    
    logger.info(f"DEBUG POST {post_id}:")
    logger.info(f"  Images: {post.images}")
    logger.info(f"  Video: {post.video}")
    
    return jsonify({
        'id': post.id,
        'description': post.description,
        'images_raw': post.images,
        'images_split': post.images.split(',') if post.images else [],
        'video': post.video,
        'location': post.location,
        'created_at': post.created_at.isoformat(),
        'send_at': post.send_at.isoformat() if post.send_at else None,
        'dropbox_folder': post.dropbox_folder,
        'n8n_sent': post.n8n_sent
    }), 200

@app.route('/wygeneruj-sociale', methods=['GET', 'POST'])
@login_required
def wygeneruj_sociale():
    error = None
    success = None
    preview_images = []
    preview_video = None
    
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        images = request.files.getlist('images')
        video = request.files.get('video')
        send_at_str = request.form.get('send_at', '').strip()
        map_screenshot_file = request.files.get('map_screenshot_file')
        
        logger.info(f"📝 START - Nowa próba wysłania posta od: {current_user.username}")
        logger.info(f"Description: {description[:50] if description else 'BRAK'}...")
        logger.info(f"Images: {len(images)} file(s)")
        logger.info(f"Video: {video.filename if video else 'BRAK'}")
        logger.info(f"Map screenshot: {map_screenshot_file.filename if map_screenshot_file else 'BRAK'}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Form keys: {list(request.form.keys())}")
        logger.info(f"Files keys: {list(request.files.keys())}")
        
        # WALIDACJA 1: Opis
        if not description or len(description) < 10 or len(description) > 500:
            error = 'Opis postu jest wymagany (min. 10, max. 500 znaków).'
            logger.error(f"✗ Błąd walidacji: Opis za krótki lub pusty - '{description}'")
        
        # WALIDACJA 2: Zdjęcia wymagane
        elif not images or all(img.filename == '' for img in images):
            error = 'Musisz przesłać przynajmniej jedno zdjęcie.'
            logger.error(f"✗ Błąd walidacji: Brak zdjęć - {[img.filename for img in images]}")
        
        else:
            # Inicjalizacja zmiennych
            send_at = None
            dropbox_image_paths = []  # Ścieżki na Dropboxie
            dropbox_video_path = None
            
            logger.info(f"✓ Walidacja przeszła - przystępuję do wysyłania na Dropbox'a")
            
            # WALIDACJA 3: Data wysłania (jeśli podana)
            if send_at_str:
                try:
                    send_at = datetime.strptime(send_at_str, '%Y-%m-%dT%H:%M')
                    if send_at < datetime.now():
                        error = 'Data wysłania nie może być wcześniejsza niż dzisiejsza data i godzina.'
                        logger.error(f"✗ Błąd: Data wysłania w przeszłości: {send_at_str}")
                except ValueError:
                    error = 'Nieprawidłowy format daty wysłania.'
                    logger.error(f"✗ Błąd: Zły format daty: {send_at_str}")
            
            # WYSYŁANIE NA DROPBOX'A - BEZ LOKALNEGO ZAPISU
            if not error and images:
                folder_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                dropbox_folder = f"/SocialMedia/{current_user.username}/{folder_date}"
                
                logger.info(f"➤ WYSYŁANIE NA DROPBOX'A")
                logger.info(f"➤ Folder: {dropbox_folder}")
                logger.info(f"➤ Zdjęć: {len(images)} | Video: {'Tak' if video else 'Nie'}")
                
                # Wysłanie zdjęć – bezpośrednio z request.files na Dropbox'a
                for idx, img in enumerate(images, 1):
                    if img.filename == '':
                        logger.warning(f"⚠ Pusty filename, pomijam")
                        continue
                    if not img.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                        error = f'Zdjęcie {img.filename} musi być w formacie JPG lub PNG.'
                        logger.error(f"✗ Błąd: Zdjęcie w złym formacie: {img.filename}")
                        break
                    
                    try:
                        filename = secure_filename(img.filename)
                        dbx_path = f"{dropbox_folder}/{filename}"
                        
                        # Wyślij bezpośrednio z request na Dropbox'a
                        img.seek(0)  # Reset position po ewentualnych czytaniach
                        db_client.files_upload(img.read(), dbx_path, mode=dropbox.files.WriteMode.overwrite)
                        
                        dropbox_image_paths.append(dbx_path)
                        preview_images.append(filename)
                        logger.info(f"✓ [{idx}/{len(images)}] Zdjęcie na Dropbox'a: {filename}")
                    except Exception as e:
                        error = f"Błąd uploadu zdjęcia {img.filename}: {str(e)}"
                        logger.error(f"✗ Błąd uploadu: {img.filename} - {str(e)}")
                        break
                
                # Wysłanie wideo – bezpośrednio na Dropbox'a
                if not error and video and video.filename:
                    logger.info(f"➤ Wysyłam video: {video.filename}")
                    if not video.filename.lower().endswith(('.mp4', '.mov', '.avi')):
                        error = f'Film {video.filename} musi być w formacie MP4, MOV lub AVI.'
                        logger.error(f"✗ Błąd: Film w złym formacie: {video.filename}")
                    else:
                        try:
                            filename = secure_filename(video.filename)
                            dbx_path = f"{dropbox_folder}/{filename}"
                            
                            video.seek(0)
                            db_client.files_upload(video.read(), dbx_path, mode=dropbox.files.WriteMode.overwrite)
                            
                            dropbox_video_path = dbx_path
                            preview_video = filename
                            logger.info(f"✓ Film na Dropbox'a: {filename}")
                        except Exception as e:
                            error = f"Błąd uploadu wideo: {str(e)}"
                            logger.error(f"✗ Błąd uploadu wideo: {str(e)}")
                
                # Wysłanie screenshot'u mapy – bezpośrednio na Dropbox'a
                if not error:
                    map_screenshot_file = request.files.get('map_screenshot_file')
                    if map_screenshot_file and map_screenshot_file.filename:
                        try:
                            filename = map_screenshot_file.filename
                            dbx_path = f"{dropbox_folder}/{filename}"
                            
                            map_screenshot_file.seek(0)
                            db_client.files_upload(map_screenshot_file.read(), dbx_path, mode=dropbox.files.WriteMode.overwrite)
                            logger.info(f"✓ Screenshot mapy na Dropbox'a: {filename}")
                        except Exception as e:
                            logger.error(f"⚠ Błąd przy wysyłaniu screenshot'u: {str(e)}")
                            # To nie jest błąd krytyczny, post i tak się wyśle
                
                # Wysłanie opisu kao .txt
                if not error:
                    desc_filename = f"opis.txt"
                    desc_content = f"Opis postu:\n{description}\n\nDnia id lokalizacji: {request.form.get('location', 'brak')}\n\nData utworzenia: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    try:
                        dbx_path = f"{dropbox_folder}/{desc_filename}"
                        db_client.files_upload(desc_content.encode(), dbx_path, mode=dropbox.files.WriteMode.overwrite)
                        logger.info(f"✓ Opis na Dropbox'a: {desc_filename}")
                    except Exception as e:
                        error = f"Błąd uploadu opisu: {str(e)}"
                        logger.error(f"✗ Błąd uploadu opisu: {str(e)}")
                
                # Zapis do bazy danych – TYLKO ścieżki do Dropboxa
                if not error:
                    try:
                        post = Post(
                            user_id=current_user.id,
                            description=description,
                            images=','.join(dropbox_image_paths),  # Ścieżki na Dropboxie
                            video=dropbox_video_path,  # Ścieżka na Dropboxie
                            send_at=send_at,
                            location=request.form.get('location', ''),
                            dropbox_folder=dropbox_folder,
                            n8n_sent=False
                        )
                        db.session.add(post)
                        db.session.commit()
                        logger.info(f"✓ Post zapisany w bazie: ID={post.id}")
                        logger.info(f"✓ DATA WYSŁANIA: {send_at.strftime('%Y-%m-%d %H:%M') if send_at else 'Natychmiastowe'}")
                        logger.info(f"✓ ════════════════════════════════════════════════════")
                        success = f'✓ Post wysłany na Dropbox\'a! Folder: {dropbox_folder}'
                    except Exception as e:
                        error = f"Błąd zapisu do bazy: {str(e)}"
                        logger.error(f"✗ Błąd zapisu do bazy: {str(e)}")
            elif error:
                logger.error(f"✗ BŁĄD WALIDACJI: {error}")
            else:
                logger.warning(f"⚠ BRAK ZDJĘĆ - post nie wysłany")
                error = 'Brak zdjęć do wysłania'
    
    # Jeśli to AJAX request (fetch), zwróć JSON
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        if error:
            return jsonify({'success': False, 'message': f'✗ {error}'}), 400
        elif success:
            return jsonify({'success': True, 'message': success}), 200
        else:
            return jsonify({'success': False, 'message': '✗ Nieznany błąd'}), 400
    
    # Dla normalnych requestów (GET) - zwróć HTML
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all()
    return render_template('wygeneruj_sociale.html', username=current_user.username, error=error, success=success, preview_images=preview_images, preview_video=preview_video, posts=posts)

@app.route('/dropbox-file', methods=['GET'])
@app.route('/dropbox-file/<path:dropbox_path>', methods=['GET'])
@login_required
def get_dropbox_file(dropbox_path=None):
    """Pobiera plik z Dropboxa i zwraca jako binarny plik"""
    try:
        # Dekoduj ścieżkę
        import urllib.parse
        from flask import send_file
        from io import BytesIO
        import mimetypes

        dropbox_path = request.args.get('path') or dropbox_path
        if not dropbox_path:
            return jsonify({'error': 'Brak ścieżki pliku'}), 400
        
        dropbox_path = urllib.parse.unquote(dropbox_path)
        
        logger.info(f"🔵 REQUEST: Pobieranie z Dropboxa")
        logger.info(f"  Raw path: {dropbox_path}")
        logger.info(f"  Path type: {type(dropbox_path)}")
        logger.info(f"  Path length: {len(dropbox_path)}")
        
        # Pobierz plik bezpośrednio z Dropboxa
        logger.info(f"➤ Wywołuję files_download...")
        metadata, response = db_client.files_download(dropbox_path)
        file_content = response.content
        
        logger.info(f"✓ Pobrano: {metadata.name} ({len(file_content)} bytes)")
        
        # Ustal MIME type na podstawie rozszerzenia
        mime_type, _ = mimetypes.guess_type(dropbox_path)
        if not mime_type:
            if dropbox_path.lower().endswith(('.jpg', '.jpeg')):
                mime_type = 'image/jpeg'
            elif dropbox_path.lower().endswith('.png'):
                mime_type = 'image/png'
            elif dropbox_path.lower().endswith('.mp4'):
                mime_type = 'video/mp4'
            else:
                mime_type = 'application/octet-stream'
        
        logger.info(f"  MIME type: {mime_type}")
        
        # Zwróć plik
        return send_file(
            BytesIO(file_content),
            mimetype=mime_type,
            as_attachment=False,
            download_name=metadata.name
        )
        
    except ApiError as e:
        logger.error(f"✗ Błąd API Dropboxa: {str(e)}")
        logger.error(f"  Error type: {type(e)}")
        return jsonify({'error': f'Plik nie znaleziony: {str(e)}'}), 404
    except Exception as e:
        logger.error(f"✗ Błąd przy pobieraniu z Dropboxa: {str(e)}")
        logger.error(f"  Type: {type(e).__name__}")
        logger.error(f"  Traceback:", exc_info=True)
        return jsonify({'error': f'Błąd serwera: {str(e)}'}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Kompatybilność - teraz nic się nie przechowuje lokalnie"""
    return jsonify({'error': 'Pliki są przechowywane na Dropboxie'}), 404

@app.route('/podsumowanie-socialmedia')
@login_required
def podsumowanie_socialmedia():
    # Posty które mają być wysłane (posortowane po dacie wysłania)
    posts_to_send = Post.query.filter_by(user_id=current_user.id).filter(Post.send_at != None).order_by(Post.send_at).all()
    # Posty już wysłane (bez daty wysłania)
    posts_sent = Post.query.filter_by(user_id=current_user.id).filter(Post.send_at == None).order_by(Post.created_at.desc()).all()
    
    # Debug logging
    for post in posts_to_send + posts_sent:
        logger.info(f"Post ID {post.id}:")
        logger.info(f"  Images: {post.images}")
        logger.info(f"  Video: {post.video}")
        logger.info(f"  Dropbox folder: {post.dropbox_folder}")
    
    return render_template('podsumowanie_socialmedia.html', username=current_user.username, posts_to_send=posts_to_send, posts_sent=posts_sent)

if __name__ == '__main__':
    app.run(debug=True)

