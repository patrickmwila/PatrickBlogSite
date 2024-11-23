from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from datetime import datetime
import os
from slugify import slugify

from extensions import db, login_manager
from models import User, Category, Post, Tag, Project

def create_app():
    app = Flask(__name__, static_folder='static')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.template_filter('slugify')
    def slugify_filter(s):
        return slugify(s)

    # Add current year to all templates
    @app.context_processor
    def inject_year():
        return {'current_year': datetime.now().year}

    # Import and register blueprints
    from admin import admin
    from auth import auth
    app.register_blueprint(admin)
    app.register_blueprint(auth)

    # Routes
    @app.route('/')
    @app.route('/home')  # Adding an alias for /home to maintain compatibility
    def home():
        # Get the 3 most recent blog posts for the homepage
        recent_posts = Post.query.order_by(Post.date_posted.desc()).limit(3).all()
        projects = Project.query.order_by(Project.date_created.desc()).all()
        posts = Post.query.order_by(Post.date_posted.desc()).all()
        return render_template('home.html', projects=projects, posts=posts, recent_posts=recent_posts)

    @app.route('/projects')
    def projects():
        projects = Project.query.order_by(Project.date_created.desc()).all()
        return render_template('projects.html', projects=projects)

    @app.route('/blog')
    def blog():
        page = request.args.get('page', 1, type=int)
        per_page = 5  # Number of posts per page
        
        category_id = request.args.get('category')
        tag_id = request.args.get('tag')
        search_query = request.args.get('q')
        
        query = Post.query.filter_by(is_draft=False)
        
        if category_id:
            category = Category.query.get_or_404(category_id)
            query = query.filter_by(category=category)
        
        if tag_id:
            tag = Tag.query.get_or_404(tag_id)
            query = query.filter(Post.tags.contains(tag))
            
        if search_query:
            search = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Post.title.ilike(search),
                    Post.content.ilike(search)
                )
            )
        
        pagination = query.order_by(Post.date_posted.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        posts = pagination.items
        
        categories = Category.query.all()
        tags = Tag.query.all()
        
        return render_template('blog.html', 
                             posts=posts, 
                             categories=categories, 
                             tags=tags, 
                             search_query=search_query,
                             pagination=pagination)

    @app.route('/post/<int:post_id>')
    @app.route('/post/<string:slug>')
    def post(post_id=None, slug=None):
        if post_id:
            post = Post.query.get_or_404(post_id)
        else:
            post = Post.query.filter_by(slug=slug).first_or_404()
            
        # Get the next post by date
        next_post = Post.query.filter(Post.date_posted < post.date_posted).order_by(Post.date_posted.desc()).first()
        return render_template('post.html', post=post, next_post=next_post)

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/contact')
    def contact():
        return render_template('contact.html')

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
