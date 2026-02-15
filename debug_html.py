#!/usr/bin/env python
"""Debug script - sprawdza jak Jinja renderuje template"""

from app import app, db, Post, User

with app.app_context():
    from flask import render_template_string
    
    # Pobierz posty
    posts_to_send = Post.query.filter_by(user_id=1).filter(Post.send_at != None).order_by(Post.send_at).all()
    posts_sent = Post.query.filter_by(user_id=1).filter(Post.send_at == None).order_by(Post.created_at.desc()).all()
    
    print(f'=== HTML RENDERING CHECK ===')
    print(f'Posts to send: {len(posts_to_send)}')
    print(f'Posts sent: {len(posts_sent)}')
    print()
    
    # Sprawdź jak Jinja renderuje - pokaz fragment HTML'a
    template_fragment = """
    {% for post in posts_to_send %}
    Post {{ post.id }}:
      Raw images: {{ post.images }}
      Split images:
      {% for img in post.images.split(',') %}
        - img="{{ img }}"
        - data-dropbox-path="{{ img }}"
      {% endfor %}
    {% endfor %}
    """
    
    from jinja2 import Template
    t = Template(template_fragment)
    rendered = t.render(posts_to_send=posts_to_send)
    print("=== RENDERED HTML FRAGMENT ===")
    print(rendered)
