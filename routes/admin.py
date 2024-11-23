from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Post, Category, Tag
from slugify import slugify
from datetime import datetime

admin = Blueprint('admin', __name__)

@admin.route('/admin/posts')
@login_required
def manage_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/manage_posts.html', posts=posts)

@admin.route('/admin/post/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            category_id = request.form.get('category')
            tags = request.form.getlist('tags')
            is_published = bool(request.form.get('is_published'))
            
            # Create slug from title
            slug = slugify(title)
            
            # Check if slug already exists
            if Post.query.filter_by(slug=slug).first():
                base_slug = slug
                counter = 1
                while Post.query.filter_by(slug=f"{base_slug}-{counter}").first():
                    counter += 1
                slug = f"{base_slug}-{counter}"
            
            post = Post(
                title=title,
                content=content,
                slug=slug,
                category_id=category_id,
                is_published=is_published,
                author_id=current_user.id
            )
            
            # Add tags
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name, slug=slugify(tag_name))
                    db.session.add(tag)
                post.tags.append(tag)
            
            db.session.add(post)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Post created successfully!',
                'redirect_url': url_for('admin.manage_posts')
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error creating post: {str(e)}'
            })
    
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('admin/create_post.html', categories=categories, tags=tags)

@admin.route('/admin/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    try:
        post = Post.query.get_or_404(post_id)
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
            'message': f'Error deleting post: {str(e)}'
        })

@admin.route('/admin/categories')
@login_required
def manage_categories():
    categories = Category.query.all()
    return render_template('admin/manage_categories.html', categories=categories)

@admin.route('/admin/category/create', methods=['POST'])
@login_required
def create_category():
    try:
        name = request.form.get('name')
        if not name:
            return jsonify({
                'success': False,
                'message': 'Category name is required'
            })
        
        # Create slug from name
        slug = slugify(name)
        
        # Check if category with this name or slug already exists
        if Category.query.filter((Category.name == name) | (Category.slug == slug)).first():
            return jsonify({
                'success': False,
                'message': 'A category with this name already exists'
            })
        
        category = Category(name=name, slug=slug)
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category created successfully!',
            'category_id': category.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating category: {str(e)}'
        })

@admin.route('/admin/category/<int:category_id>/update', methods=['POST'])
@login_required
def update_category(category_id):
    try:
        category = Category.query.get_or_404(category_id)
        name = request.form.get('name')
        
        if not name:
            return jsonify({
                'success': False,
                'message': 'Category name is required'
            })
        
        # Create slug from new name
        slug = slugify(name)
        
        # Check if another category with this name or slug already exists
        existing = Category.query.filter(
            (Category.name == name) | (Category.slug == slug),
            Category.id != category_id
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'A category with this name already exists'
            })
        
        category.name = name
        category.slug = slug
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category updated successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating category: {str(e)}'
        })

@admin.route('/admin/category/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    try:
        category = Category.query.get_or_404(category_id)
        
        # Check if category has posts
        if category.posts:
            return jsonify({
                'success': False,
                'message': 'Cannot delete category with associated posts'
            })
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category deleted successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting category: {str(e)}'
        }), 400

@admin.route('/admin/cleanup-tags', methods=['POST'])
@login_required
def cleanup_tags():
    try:
        # Find tags that aren't associated with any posts
        unused_tags = Tag.query.filter(~Tag.posts.any()).all()
        deleted_count = len(unused_tags)
        
        # Delete unused tags
        for tag in unused_tags:
            db.session.delete(tag)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} unused tags',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error cleaning up tags: {str(e)}'
        })
