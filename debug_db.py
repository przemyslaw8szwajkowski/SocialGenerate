#!/usr/bin/env python
"""Debug script - sprawdza zawartość bazy danych"""

from app import app, db, Post, User

with app.app_context():
    # Sprawdź jakie posty są w bazie
    posts = Post.query.all()
    print(f'=== DATABASE INSPECTION ===')
    print(f'Liczba postów: {len(posts)}')
    print()
    
    if len(posts) == 0:
        print('❌ Brak postów w bazie!')
    else:
        for post in posts:
            print(f'📝 Post ID {post.id}:')
            print(f'  User ID: {post.user_id}')
            print(f'  Description: {post.description[:50] if post.description else "BRAK"}')
            print(f'  Images raw: {repr(post.images)}')
            print(f'  Images type: {type(post.images).__name__}')
            
            if post.images:
                images_list = post.images.split(',')
                print(f'  Images split ({len(images_list)} items):')
                for idx, img in enumerate(images_list):
                    print(f'    [{idx}] {repr(img)}')
            
            print(f'  Video: {post.video}')
            print(f'  Dropbox folder: {post.dropbox_folder}')
            print(f'  Send at: {post.send_at}')
            print(f'  Created at: {post.created_at}')
            print()
