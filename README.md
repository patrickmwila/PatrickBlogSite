# Patrick's Portfolio & Blog Website

A modern, Flask-based portfolio and blog website designed for professional presentation and content management. This application features a clean, responsive design with a powerful admin interface for content management.

## Key Features

- 🎨 Responsive portfolio showcase
- 📝 Full-featured blog system with categories and tags
- 📱 Mobile-first, modern design
- 🔒 Secure authentication system
- 📂 Category and tag management
- 📝 TinyMCE rich text editor integration
- 🔍 SEO-friendly URLs
- 📊 Admin dashboard for content management

## Technical Stack

- **Backend**: Python 3.8+ with Flask framework
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Rich Text Editor**: TinyMCE
- **CSS Framework**: Bootstrap 5
- **Icons**: Font Awesome
- **Code Highlighting**: highlight.js

## Installation & Setup

### 1. Environment Setup

```bash
# Create a Python virtual environment
python -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the root directory:

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
TINYMCE_API_KEY=your-tinymce-key-here  # Optional for development
```

### 3. Database Initialization

```python
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### 4. Running the Application

```bash
# Development
flask run

# Production (using gunicorn)
gunicorn -w 4 app:app
```

## Project Structure

```
PatrickBlogSite/
├── static/               # Static files (CSS, JS, images)
│   ├── css/             # CSS stylesheets
│   ├── js/              # JavaScript files
│   └── uploads/         # Uploaded media files
├── templates/           # Jinja2 templates
│   ├── admin/          # Admin interface templates
│   └── auth/           # Authentication templates
├── instance/           # Instance-specific files
│   └── blog.db         # SQLite database
├── app.py              # Application factory and routes
├── admin.py            # Admin blueprint and routes
├── auth.py             # Authentication blueprint
├── models.py           # Database models
├── extensions.py       # Flask extensions
└── requirements.txt    # Python dependencies
```

## Database Management

### Why SQLite?

We chose SQLite for this project because:
1. **Simplicity**: No separate database server needed
2. **Portability**: Entire database in a single file
3. **Performance**: Excellent for sites with moderate traffic (up to ~100k hits/day)
4. **Reliability**: ACID-compliant and extremely stable

### When to Consider Migration to MySQL/PostgreSQL

Consider migrating from SQLite when:
- Daily traffic exceeds 100k hits
- Concurrent users regularly exceed 100
- Database size approaches 1GB
- You need advanced database features (full-text search, etc.)

## TinyMCE Integration

### Current Setup
The site uses TinyMCE's free tier, which is sufficient for basic content editing.

### Alternatives if Paid Features Needed:
1. **CKEditor**: Popular open-source alternative
2. **Quill**: Modern, open-source editor
3. **SimpleMDE**: Markdown-based editor

To switch editors, modify `templates/admin/create_post.html` and `edit_post.html`.

## Deployment Guide (Linux Server)

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade

# Install required packages
sudo apt install python3-pip python3-venv nginx
```

### 2. Application Setup
```bash
# Clone repository
git clone <your-repo-url>
cd PatrickBlogSite

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn  # For production serving
```

### 3. Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/PatrickBlogSite/static;
    }
}
```

### 4. Systemd Service
Create `/etc/systemd/system/patrickblog.service`:
```ini
[Unit]
Description=Patrick Blog Site
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/PatrickBlogSite
Environment="PATH=/path/to/PatrickBlogSite/venv/bin"
ExecStart=/path/to/PatrickBlogSite/venv/bin/gunicorn -w 4 app:app

[Install]
WantedBy=multi-user.target
```

### 5. Start Services
```bash
sudo systemctl start patrickblog
sudo systemctl enable patrickblog
sudo systemctl restart nginx
```

## Security Considerations

1. **Always use HTTPS** in production
2. Keep dependencies updated
3. Use strong passwords
4. Regularly backup the SQLite database
5. Set proper file permissions
6. Configure server firewall

## Backup Strategy

1. **Database**: Daily SQLite file backup
2. **Uploaded Media**: Regular backup of `/static/uploads`
3. **Configuration**: Backup `.env` and nginx configs

## Development Workflow

1. Create feature branch
2. Make changes
3. Test locally
4. Create pull request
5. Review and merge
6. Deploy to production

## Troubleshooting

Common issues and solutions:
1. **500 Error**: Check error logs in `/var/log/patrickblog/error.log`
2. **Database Locked**: Ensure proper file permissions
3. **Static Files Not Loading**: Check nginx configuration
4. **Editor Not Loading**: Verify TinyMCE API key

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

This project is licensed under the MIT License.
