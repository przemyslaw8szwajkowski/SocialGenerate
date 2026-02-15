#!/usr/bin/env python
"""Debug script - testuje endpoint dropbox-file"""

from app import app, db, Post, db_client
from urllib.parse import quote
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with app.app_context():
    # Pobierz pierwszy post z zdjęciami
    post = Post.query.filter(Post.images != None).first()
    
    if not post:
        print("Brak postów z zdjęciami")
        exit(1)
    
    images = post.images.split(',')
    first_image = images[0].strip() if images else None
    
    if not first_image:
        print("Brak zdjęć w post.images")
        exit(1)
    
    print(f"=== DROPBOX FILE ENDPOINT TEST ===")
    print(f"Image path: {repr(first_image)}")
    print()
    
    # Test 1: Sprawdź czy plik istnieje na Dropboxie
    print("Test 1: Czy plik istnieje na Dropboxie?")
    try:
        metadata = db_client.files_get_metadata(first_image)
        print(f"✓ Plik istnieje na Dropboxie")
        print(f"  Name: {metadata.name}")
        print(f"  Size: {metadata.size} bytes")
    except Exception as e:
        print(f"✗ Błąd: {str(e)}")
    print()
    
    # Test 2: Spróbuj pobrać plik
    print("Test 2: Pobieranie pliku z Dropboxa")
    try:
        metadata, response = db_client.files_download(first_image)
        print(f"✓ Plik pobrany")
        print(f"  Name: {metadata.name}")
        print(f"  Content length: {len(response.content)} bytes")
    except Exception as e:
        print(f"✗ Błąd: {str(e)}")
    print()
    
    # Test 3: Sprawdź jak będzie zakodowana ścieżka
    print("Test 3: URL encoding")
    encoded = quote(first_image, safe='')
    print(f"  Original: {first_image}")
    print(f"  Encoded: {encoded}")
    print(f"  URL: /dropbox-file/{encoded}")
