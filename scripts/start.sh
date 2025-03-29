#!/bin/sh

# Set environment to production if not specified
export DJANGO_ENV=${DJANGO_ENV:-production}

echo "Starting application in $DJANGO_ENV mode..."

# Change to the project root directory
cd /app

# Run Django migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Start Gunicorn for production or runserver for development
if [ "$DJANGO_ENV" = "production" ]; then
    echo "Starting Gunicorn server..."
    gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 --daemon
    
    echo "Starting Nginx server..."
    # Make sure Nginx listens on 0.0.0.0:80
    sed -i 's/listen 80;/listen 0.0.0.0:80;/g' /etc/nginx/conf.d/default.conf
    nginx -g "daemon off;"
else
    echo "Starting Django development server..."
    python manage.py runserver 0.0.0.0:8000
fi
