# Django Store API with JWT Authentication

## Project Structure

This project follows a standard Django project structure with a single-container deployment approach:

```
project-store/
├── .github/                  # GitHub Actions workflows
├── .gitignore
├── README.md
├── requirements.txt          # All Python dependencies 
├── docker-compose.yml        # For local development
├── Dockerfile                # Works in both dev and prod
├── .env.example              # Environment variables template
├── manage.py                 # Django management script
├── static/                   # Collected static files
├── media/                    # User-uploaded content
├── templates/                # Shared templates
├── core/                     # Main Django project directory
│   ├── settings/
│   │   ├── base.py           # Base settings
│   │   ├── development.py    # Dev-specific settings
│   │   └── production.py     # Production-specific settings
├── authapi/                  # Auth application
├── nginx/                    # Nginx configuration
├── frontend/                 # Frontend code
└── scripts/                  # Helper scripts
```

## Development Setup

### Using Docker (Recommended)

1. Clone the repository
2. Copy `.env.example` to `.env` and adjust as needed:
   ```
   cp .env.example .env
   ```
3. Start the development environment:
   ```
   docker-compose up
   ```
4. Access the application at http://localhost:8000

### Local Development

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and adjust as needed
4. Run migrations:
   ```
   python manage.py migrate
   ```
5. Run the server:
   ```
   python manage.py runserver
   ```

## Deployment

### Fly.io Deployment

The project is set up for easy deployment to Fly.io:

```
fly launch    # First time only
fly deploy
```

Or use the GitHub Actions workflow defined in `.github/workflows/fly-deploy.yml` by pushing to the main branch.

### Environment Variables

Critical environment variables to set in production:
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: Connection string for your database
- `EMAIL_*`: SMTP settings for email functionality
- `DJANGO_ENV`: Set to 'production' for production deployment
- `ALLOWED_HOST`: Your domain name

## API Endpoints

### Authentication
- `/api/auth/signup/` - User registration
- `/api/auth/login/` - User login (returns JWT tokens)
- `/api/auth/refresh/` - Refresh JWT token
- `/api/auth/verify/` - Verify JWT token

## Features

- JWT Authentication
- Email verification
- User activity tracking
- Rate limiting for security
- Containerized deployment
