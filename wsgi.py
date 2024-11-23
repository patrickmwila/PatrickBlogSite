import sys
import os

# Add the application directory to the Python path
sys.path.insert(0, '/var/www/PatrickBlogSite')

# Set environment variables if needed
os.environ['FLASK_ENV'] = 'production'

# Import the Flask application
from app import app as application
