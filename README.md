# Real Estate Listing Platform - Django Backend

Backend for real estate listing management with Django REST Framework.

## Features

- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Role-based Access Control**: Admin and Operator roles with different permissions
- **Listing Management**: Full CRUD for property listings with image uploads
- **Advanced Filtering**: Filter by district, property type, deal type, rooms count
- **Phone Search**: Search listings by property owner phone number
- **Dashboard Statistics**: Real-time statistics for the dashboard
- **Flexible Storage**: Local media storage or DigitalOcean Spaces (S3-compatible)
- **Professional Admin Panel**: Jazzmin theme for modern Django admin interface
- **API Documentation**: Interactive Swagger/ReDoc documentation with drf-spectacular

## Tech Stack

- Django 5.0.7
- Django REST Framework 3.15.1
- PostgreSQL (production) / SQLite (development)
- JWT Authentication (djangorestframework-simplejwt)
- Django Filter
- DigitalOcean Spaces (django-storages) - optional
- Django Jazzmin - Admin theme
- drf-spectacular - API documentation
- Python Telegram Bot - Telegram integration

## Setup Instructions

### 1. Install Dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Security
SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
# Leave empty to use SQLite (for development)
# Fill in to use PostgreSQL (for production)
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432

# DigitalOcean Spaces (Optional - for image storage)
# Leave empty to use local storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
AWS_S3_REGION_NAME=nyc3

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# REST Framework
PAGE_SIZE=20

# API Documentation
API_TITLE=Real Estate Listing API
API_DESCRIPTION=API for real estate listing management platform
API_VERSION=1.0.0

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME_HOURS=24
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
JWT_ROTATE_REFRESH_TOKENS=True
JWT_BLACKLIST_AFTER_ROTATION=True

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://reiltor-erp.vercel.app
CORS_ALLOW_CREDENTIALS=True

# Admin Panel (Jazzmin Theme)
ADMIN_SITE_TITLE=Real Estate Admin
ADMIN_SITE_HEADER=Real Estate Platform
ADMIN_WELCOME_SIGN=Welcome to Real Estate Platform
ADMIN_COPYRIGHT=Real Estate Platform
ADMIN_THEME_SIDEBAR=#1e293b
ADMIN_THEME_HEADER=#ffffff
ADMIN_THEME_ACCENT=#3b82f6
ADMIN_THEME_BREADCRUMBS=#e2e8f0
```

**Note**: If AWS credentials are not provided, images will be stored locally in the `media/` folder.

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

### 6. Start Telegram Bot (Optional)

```bash
python manage.py start_bot
```

**Note**: Make sure to set `TELEGRAM_BOT_TOKEN` in your `.env` file before starting the bot.

## Admin Panel

Access the professional admin panel at `/admin/` with Jazzmin theme:

- **Modern UI**: Clean, responsive interface with dark sidebar
- **Enhanced Features**: Better navigation, search, and filtering
- **Custom Menus**: Quick access to API documentation from admin panel
- **User Management**: Create and manage users with role-based access
- **Listing Management**: Full CRUD for listings with inline image management
- **District Management**: View and manage all districts

**Admin Features:**
- Custom theme with dark sidebar (#1e293b) and white header
- FontAwesome icons for better visual experience
- Top menu with quick links to Home, Documentation, and API Docs
- Enhanced list views with better filtering and search
- Inline image management for listings

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

**Documentation Features:**
- Auto-generated from code with detailed descriptions
- Try-it-out functionality for all endpoints
- Authentication support (JWT tokens)
- Request/response examples
- Parameter descriptions and validation rules
- Model schemas and field descriptions

## API Endpoints

### Authentication

- `POST /api/auth/login/` - Login and get JWT token
- `POST /api/auth/refresh/` - Refresh JWT token
- `POST /api/auth/change-password/` - Change own password

### Users (Admin only)

- `GET /api/auth/users/` - List users
- `POST /api/auth/users/` - Create new user
- `GET /api/auth/users/{id}/` - Get user details
- `PATCH /api/auth/users/{id}/` - Update user
- `DELETE /api/auth/users/{id}/` - Delete user
- `POST /api/auth/users/{id}/reset-password/` - Reset user password

### Listings

- `GET /api/listings/` - List listings (with filtering and search)
- `POST /api/listings/` - Create new listing
- `GET /api/listings/{id}/` - Get listing details
- `PATCH /api/listings/{id}/` - Update listing
- `DELETE /api/listings/{id}/` - Delete listing
- `POST /api/listings/{id}/images/` - Upload images (max 15)
- `DELETE /api/listings/{id}/images/{image_id}/` - Delete image

### Search

- `GET /api/search/by-phone/?phone=+998907770264` - Search by phone number

### Districts

- `GET /api/districts/` - List all districts

### Dashboard

- `GET /api/dashboard/stats/` - Get dashboard statistics

## Filtering Examples

```
GET /api/listings/?district=1&property_type=novostroyka&deal_type=sale&rooms_count=2
GET /api/listings/?search=+998901234567
```

## Storage Configuration

The system supports two storage modes:

### Local Storage (Default)
When AWS credentials are not configured in `.env`:
- Images are stored in `media/` folder
- Served at `/media/` URL
- No additional setup required

### DigitalOcean Spaces Storage
When AWS credentials are configured in `.env`:
- Images are stored on S3-compatible storage
- Served from the bucket URL
- Requires valid AWS credentials

## Running Tests

```bash
python manage.py test accounts
```

Tests include:
- Role-based permissions verification
- User management permissions

## Admin Panel

Access the Django admin at `/admin/` to:
- Create and manage users
- View and manage listings
- Manage districts

## Districts

The system includes 12 districts (excluding Bektemir):
- Chilonzor
- Yunusobod
- Mirzo Ulug'bek
- Shayxontohur
- Yashnobod
- Uchtepa
- Yakkasaroy
- Sergeli
- Olmazor
- Mirobod
- Yangihayot
- Qo'qon (placeholder - confirm with owner)

## Image Upload

- Maximum 15 images per listing
- Storage location depends on configuration (local or S3)
- Path structure: `listings/{listing_id}/{filename}`

## Permissions

| Action | Admin | Operator |
|--------|-------|----------|
| Create/edit/delete listings | ✅ | ✅ |
| View all listings | ✅ | ✅ |
| Create users | ✅ | ❌ |
| Reset user passwords | ✅ | ❌ |
| Delete users | ✅ | ❌ |
| Change own password | ✅ | ✅ |
| View users list | ✅ | ❌ |

## Telegram Bot

The project includes a Telegram bot for easy access to listing information.

### Bot Features:
- **Start Command**: `/start` - Welcome message with instructions
- **Help Command**: `/help` - Usage instructions
- **Listing Search**: Send listing ID to get full information
- **Rich Formatting**: Beautiful message layout with emojis
- **Image Display**: All listing images sent in sequence
- **Contact Button**: One-tap phone number copy

### Bot Commands:
- `/start` - Start bot and get welcome message
- `/help` - Get help and usage instructions
- Send listing ID (e.g., `18`) - Get listing details

### Message Format:
```
🏢 Novostroyka

📍 Tuman: Chilonzor
🏠 Xonalar: 2
🏢 Qavat: 23/34
📐 Maydon: 11212.00 m²
💰 Tur: Prodaja
💵 Narx: $123,405.00
📊 Narx m²: $11.01
📞 Telefon: 998(97)6039505
👤 Egasi: Ko'rsatilmagan
📅 Ro'yxatdan o'tgan: 30.08.2026

📸 Rasmlar: 15 ta
```

### Setup:
1. Get Telegram bot token from [@BotFather](https://t.me/botfather)
2. Add to `.env`: `TELEGRAM_BOT_TOKEN=your_token_here`
3. Start bot: `python manage.py start_bot`

### Production Deployment (Systemd Service):

For production, use systemd to keep the bot running automatically:

1. **Create service file:**
   ```bash
   sudo nano /etc/systemd/system/rieltor-bot.service
   ```

2. **Paste the configuration:**
   ```ini
   [Unit]
   Description=Rieltor Telegram Bot
   After=network.target postgresql.service

   [Service]
   Type=simple
   User=your_username
   Group=your_username
   WorkingDirectory=/path/to/Rieltor
   Environment="PATH=/path/to/Rieltor/venv/bin"
   ExecStart=/path/to/Rieltor/venv/bin/python manage.py start_bot
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable rieltor-bot
   sudo systemctl start rieltor-bot
   ```

4. **Check status:**
   ```bash
   sudo systemctl status rieltor-bot
   ```

5. **View logs:**
   ```bash
   sudo journalctl -u rieltor-bot -f
   ```

### Error Handling:
- Invalid ID: Shows error message
- Listing not found: Shows not found message
- Image errors: Shows warning for failed images
