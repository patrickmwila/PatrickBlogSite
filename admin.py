from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Post, Category, Tag, Project
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from slugify import slugify
import shutil
import mimetypes

admin = Blueprint('admin', __name__, url_prefix='/admin')

# Configure upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm'}  # Added video support
ALLOWED_MIMETYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'video/mp4', 'video/webm'
}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB limit for images
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB limit for videos

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_mimetype(file):
    if not file.content_type:
        # Try to guess the mimetype from the filename if content_type is not set
        guessed_type = mimetypes.guess_type(file.filename)[0]
        return guessed_type in ALLOWED_MIMETYPES
    return file.content_type in ALLOWED_MIMETYPES

def get_max_size(file):
    if file.content_type and file.content_type.startswith('video/'):
        return MAX_VIDEO_SIZE
    return MAX_IMAGE_SIZE

@admin.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        if not allowed_mimetype(file):
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_MIMETYPES)}'}), 400
        
        # Check file size
        max_size = get_max_size(file)
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > max_size:
            return jsonify({'error': f'File too large. Maximum size is {max_size/1024/1024}MB'}), 400
        
        # Create year/month based subdirectory
        today = datetime.now()
        upload_subdir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(today.year), str(today.month).zfill(2))
        os.makedirs(upload_subdir, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        filename = f"{today.strftime('%Y%m%d_%H%M%S')}_{filename}"
        file_path = os.path.join(upload_subdir, filename)
        
        # Save the file
        file.save(file_path)
        
        # Generate URL path (relative to static/uploads)
        relative_path = os.path.join('uploads', str(today.year), str(today.month).zfill(2), filename)
        url = url_for('static', filename=relative_path)
        
        return jsonify({
            'location': url,
            'success': True
        })
    except Exception as e:
        current_app.logger.error(f"Image upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin.route('/create-category', methods=['POST'])
@login_required
def create_category():
    name = request.form.get('name')
    if not name:
        return jsonify({'success': False, 'message': 'Category name is required'})
    
    # Check if category already exists
    existing = Category.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'message': 'Category already exists'})
    
    try:
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'Category created successfully',
            'category': {
                'id': category.id,
                'name': category.name
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category')
        is_draft = bool(request.form.get('draft'))
        summary = request.form.get('summary', '')
        
        # Handle tags
        tags_string = request.form.get('tags', '')
        tag_names = [t.strip() for t in tags_string.split(',') if t.strip()]
        tags = []
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            tags.append(tag)
        
        post = Post(
            title=title,
            content=content,
            category_id=category_id,
            is_draft=is_draft,
            summary=summary,
            author=current_user
        )
        post.tags = tags
        
        try:
            db.session.add(post)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Post created successfully!',
                'redirect_url': url_for('post', slug=post.slug)
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error creating post: {str(e)}'
            })

    categories = Category.query.all()
    return render_template('admin/create_post.html', categories=categories)

@admin.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.category_id = request.form.get('category')
        post.is_draft = bool(request.form.get('is_draft'))  
        post.summary = request.form.get('summary', '')
        
        # Handle tags
        tags_string = request.form.get('tags', '')
        tag_names = [t.strip() for t in tags_string.split(',') if t.strip()]
        tags = []
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            tags.append(tag)
        post.tags = tags
        
        try:
            db.session.commit()
            flash('Post updated successfully!', 'success')
            return redirect(url_for('post', slug=post.slug))
        except Exception as e:
            db.session.rollback()
            flash('Error updating post. Please try again.', 'danger')
            print(f"Error: {str(e)}")  
    
    categories = Category.query.all()
    return render_template('admin/edit_post.html', post=post, categories=categories)

@admin.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    try:
        db.session.delete(post)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Post deleted successfully!',
            'redirect_url': url_for('admin.manage_posts')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error deleting post. Please try again.'
        })

@admin.route('/manage-posts')
@login_required
def manage_posts():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/manage_posts.html', posts=posts, categories=categories)

@admin.route('/cleanup-tags', methods=['POST'])
@login_required
def cleanup_tags():
    try:
        # Get all tags
        tags = Tag.query.all()
        count = 0
        
        # Check each tag
        for tag in tags:
            if not tag.posts:
                db.session.delete(tag)
                count += 1
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Cleaned up {count} unused tags'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin.route('/category/<int:category_id>/delete', methods=['POST', 'DELETE'])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    # Check if category has posts
    if Post.query.filter_by(category_id=category_id).first():
        return jsonify({
            'success': False,
            'message': 'Cannot delete category that has posts. Please reassign or delete the posts first.'
        })
    
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Category deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting category: {str(e)}'
        })

@admin.route('/manage-projects')
@login_required
def manage_projects():
    projects = Project.query.order_by(Project.date_created.desc()).all()
    return render_template('admin/manage_projects.html', projects=projects)

@admin.route('/create-project', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        project_url = request.form.get('project_url')
        source_code_url = request.form.get('source_code_url')
        
        project = Project(
            title=title,
            description=description,
            project_url=project_url,
            source_code_url=source_code_url
        )
        
        # Handle image/video upload
        if 'project_image' in request.files:
            file = request.files['project_image']
            if file and allowed_file(file.filename) and allowed_mimetype(file):
                try:
                    # Check file size
                    max_size = get_max_size(file)
                    file.seek(0, os.SEEK_END)
                    size = file.tell()
                    file.seek(0)
                    
                    if size > max_size:
                        flash(f'File too large. Maximum size is {max_size/1024/1024}MB', 'danger')
                        return redirect(url_for('admin.create_project'))

                    # Create year/month based subdirectory
                    today = datetime.now()
                    upload_subdir = os.path.join('projects', str(today.year), str(today.month).zfill(2))
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_subdir)
                    os.makedirs(upload_path, exist_ok=True)
                    
                    # Generate unique filename
                    filename = secure_filename(file.filename)
                    filename = f"{today.strftime('%Y%m%d_%H%M%S')}_{filename}"
                    file_path = os.path.join(upload_path, filename)
                    
                    # Save the file
                    file.save(file_path)
                    
                    # Store relative path in database
                    project.image_path = os.path.join('uploads', upload_subdir, filename)
                    
                except Exception as e:
                    flash(f'Error uploading file: {str(e)}', 'danger')
                    return redirect(url_for('admin.create_project'))
        
        try:
            db.session.add(project)
            db.session.commit()
            flash('Project created successfully!', 'success')
            return redirect(url_for('admin.manage_projects'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating project: {str(e)}', 'danger')
    
    return render_template('admin/create_project.html')

@admin.route('/edit-project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        project.project_url = request.form.get('project_url')
        project.source_code_url = request.form.get('source_code_url')
        
        # Handle image/video upload
        if 'project_image' in request.files:
            file = request.files['project_image']
            if file and allowed_file(file.filename) and allowed_mimetype(file):
                try:
                    # Delete old image if it exists
                    if project.image_path:
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], project.image_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    
                    # Check file size
                    max_size = get_max_size(file)
                    file.seek(0, os.SEEK_END)
                    size = file.tell()
                    file.seek(0)
                    
                    if size > max_size:
                        flash(f'File too large. Maximum size is {max_size/1024/1024}MB', 'danger')
                        return redirect(url_for('admin.edit_project', project_id=project.id))

                    # Create year/month based subdirectory
                    today = datetime.now()
                    upload_subdir = os.path.join('projects', str(today.year), str(today.month).zfill(2))
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_subdir)
                    os.makedirs(upload_path, exist_ok=True)
                    
                    # Generate unique filename
                    filename = secure_filename(file.filename)
                    filename = f"{today.strftime('%Y%m%d_%H%M%S')}_{filename}"
                    file_path = os.path.join(upload_path, filename)
                    
                    # Save the file
                    file.save(file_path)
                    
                    # Store relative path in database
                    project.image_path = os.path.join('uploads', upload_subdir, filename)
                    
                except Exception as e:
                    flash(f'Error uploading file: {str(e)}', 'danger')
                    return redirect(url_for('admin.edit_project', project_id=project.id))
        
        try:
            db.session.commit()
            flash('Project updated successfully!', 'success')
            return redirect(url_for('admin.manage_projects'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating project: {str(e)}', 'danger')
    
    return render_template('admin/edit_project.html', project=project)

@admin.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        # Delete project image if it exists
        if project.image_path:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], project.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(project)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Project deleted successfully!',
            'redirect_url': url_for('admin.manage_projects')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting project: {str(e)}'
        })
