# SMS Marketing Platform - Backend

A professional SMS marketing and bulk messaging platform built with FastAPI and PostgreSQL.

## Features

- **User Management**: Admin and client roles with JWT authentication
- **Contact Management**: Organize contacts into groups
- **Campaign Management**: Create, schedule, and monitor SMS campaigns
- **Template System**: Create and manage SMS message templates
- **File Upload**: Import contacts from CSV/TXT files
- **Reporting**: Track delivery status and campaign performance
- **Sender ID Management**: Approval workflow for sender IDs

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Robust relational database
- **SQLAlchemy**: Python SQL toolkit and ORM
- **JWT**: JSON Web Tokens for authentication
- **Pydantic**: Data validation using Python type annotations
- **Celery**: Distributed task queue for background processing
- **Redis**: In-memory data structure store

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb sms_platform
   
   # Run migrations (if using Alembic)
   alembic upgrade head
   ```

4. **Run the Application**
   ```bash
   python main.py
   ```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `SMS_VENDOR_URL`: SMS service provider API URL
- `SMS_VENDOR_API_KEY`: SMS service provider API key
- `REDIS_URL`: Redis connection string for Celery

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

### Dashboard
- `GET /dashboard/stats` - Get dashboard statistics

### Users
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user profile
- `GET /users/` - List all users (admin only)
- `GET /users/{user_id}` - Get user by ID (admin only)

### Contacts
- `GET /contacts/` - List contacts
- `POST /contacts/` - Create contact
- `GET /contacts/{contact_id}` - Get contact
- `PUT /contacts/{contact_id}` - Update contact
- `DELETE /contacts/{contact_id}` - Delete contact

### Contact Groups
- `GET /contacts/groups/` - List contact groups
- `POST /contacts/groups/` - Create contact group
- `GET /contacts/groups/{group_id}` - Get contact group
- `PUT /contacts/groups/{group_id}` - Update contact group
- `DELETE /contacts/groups/{group_id}` - Delete contact group

### Campaigns
- `GET /campaigns/` - List campaigns
- `POST /campaigns/` - Create campaign
- `GET /campaigns/{campaign_id}` - Get campaign
- `PUT /campaigns/{campaign_id}` - Update campaign
- `DELETE /campaigns/{campaign_id}` - Delete campaign
- `POST /campaigns/{campaign_id}/send` - Send campaign

### Templates
- `GET /templates/` - List templates
- `POST /templates/` - Create template
- `GET /templates/{template_id}` - Get template
- `PUT /templates/{template_id}` - Update template
- `DELETE /templates/{template_id}` - Delete template

### Admin
- `GET /admin/templates` - List all templates (admin)
- `PUT /admin/templates/{template_id}/approve` - Approve template
- `GET /admin/sender-ids` - List sender IDs
- `POST /admin/sender-ids` - Create sender ID
- `PUT /admin/sender-ids/{sender_id_id}/approve` - Approve sender ID

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
```

### Type Checking
```bash
mypy .
```
