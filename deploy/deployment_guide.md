# Deployment Guide for Patrick's Blog Site

This guide details how to deploy the Flask application on Ubuntu 18.04 with Apache2.

## Prerequisites

1. Ubuntu 18.04 server with root/sudo access
2. Domain name pointing to your server (patrickmwila.ictaz.org.zm)
3. SSH access to your server

## Step 1: Update System and Install Dependencies

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install python3-pip python3-venv apache2 libapache2-mod-wsgi-py3 -y
```

## Step 2: Install and Configure SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-apache -y

# Get SSL certificate
sudo certbot --apache -d patrickmwila.ictaz.org.zm
```

## Step 3: Set Up Application Directory

```bash
# Create application directory
sudo mkdir -p /var/www/PatrickBlogSite
cd /var/www/PatrickBlogSite

# Clone your repository (replace with your actual repository URL)
sudo git clone https://github.com/yourusername/PatrickBlogSite.git .

# Set proper permissions
sudo chown -R www-data:www-data /var/www/PatrickBlogSite
```

## Step 4: Set Up Python Virtual Environment

```bash
# Create and activate virtual environment
sudo python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 5: Configure Apache

1. Copy the Apache configuration file:
```bash
sudo cp /var/www/PatrickBlogSite/deploy/apache2_config.conf /etc/apache2/sites-available/patrickblog.conf
```

2. Enable required Apache modules:
```bash
sudo a2enmod ssl
sudo a2enmod wsgi
sudo a2enmod rewrite
```

3. Enable the site:
```bash
sudo a2ensite patrickblog
sudo a2dissite 000-default  # disable default site
```

## Step 6: Set Up Environment Variables

Create a .env file in the application directory:
```bash
sudo nano /var/www/PatrickBlogSite/.env
```

Add your environment variables:
```
FLASK_ENV=production
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:////var/www/PatrickBlogSite/instance/blog.db
```

## Step 7: Initialize Database

```bash
# Activate virtual environment if not already activated
source /var/www/PatrickBlogSite/venv/bin/activate

# Initialize database
flask db upgrade
```

## Step 8: Restart Apache

```bash
sudo systemctl restart apache2
```

## Step 9: Test Your Deployment

Visit your domain: https://patrickmwila.ictaz.org.zm

## Troubleshooting

1. Check Apache error logs:
```bash
sudo tail -f /var/log/apache2/patrickblog-error.log
```

2. Check Apache access logs:
```bash
sudo tail -f /var/log/apache2/patrickblog-access.log
```

3. Check Apache configuration:
```bash
sudo apache2ctl configtest
```

## Security Considerations

1. Make sure your .env file has restricted permissions:
```bash
sudo chmod 600 /var/www/PatrickBlogSite/.env
```

2. Keep your system and packages updated:
```bash
sudo apt update && sudo apt upgrade -y
```

3. Configure UFW firewall:
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## Maintenance

1. To update the application:
```bash
cd /var/www/PatrickBlogSite
sudo git pull
sudo chown -R www-data:www-data .
sudo systemctl restart apache2
```

2. To update SSL certificates:
```bash
sudo certbot renew
```
