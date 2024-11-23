from datetime import datetime
from flask_login import UserMixin
from extensions import db
from slugify import slugify

tags_posts = db.Table('tags_posts',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    posts = db.relationship('Post', backref=db.backref('author', lazy=True))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    posts = db.relationship('Post', backref='category', lazy=True)

    def __init__(self, *args, **kwargs):
        if not kwargs.get('slug') and kwargs.get('name'):
            kwargs['slug'] = slugify(kwargs.get('name'))
        super().__init__(*args, **kwargs)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    posts = db.relationship('Post', secondary=tags_posts, backref=db.backref('tags', lazy=True))

    def __init__(self, *args, **kwargs):
        if not kwargs.get('slug') and kwargs.get('name'):
            kwargs['slug'] = slugify(kwargs.get('name'))
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f'<Tag {self.name}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    summary = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_draft = db.Column(db.Boolean, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, *args, **kwargs):
        if not kwargs.get('slug') and kwargs.get('title'):
            kwargs['slug'] = slugify(kwargs.get('title'))
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f'<Post {self.title}>'

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255))
    project_url = db.Column(db.String(255))
    source_code_url = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Project {self.title}>'
