# AssessBridge Authentication System

A complete authentication system for AssessBridge using JWT tokens, MySQL database, FastAPI backend, and React frontend.

## Features

✅ **User Registration**: Create new accounts with email, username, and password  
✅ **User Login**: Authenticate with email and password  
✅ **JWT Tokens**: Secure token-based authentication  
✅ **Password Security**: Bcrypt password hashing with salt  
✅ **Protected Routes**: Automatic redirection for unauthenticated users  
✅ **Session Management**: Automatic token verification and user state persistence  
✅ **API Protection**: All conversion endpoints require authentication  
✅ **Clean UI**: Professional login/register pages with responsive design  

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Login Page   │  │ Register     │  │ Convert Page     │  │
│  │              │  │ Page         │  │ (Protected)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         ▲                  ▲                  ▲              │
│         │                  │                  │              │
│  ┌────────────────────────────────────────────────────┐     │
│  │           AuthContext (State Management)          │     │
│  │  - login()  - register()  - logout()  - user     │     │
│  └────────────────────────────────────────────────────┘     │
│         ▲                  ▲                  ▲              │
│         └──────────────────┴──────────────────┘              │
│                      │                                      │
│                   axios API                                │
└───────────────────────┼──────────────────────────────────────┘
                        │ HTTP/JSON
┌───────────────────────┼──────────────────────────────────────┐
│                       ▼                                      │
│              Backend (FastAPI)                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Auth Routes                                          │  │
│  │ - POST /api/auth/register                           │  │
│  │ - POST /api/auth/login                              │  │
│  │ - GET  /api/auth/me                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Protected Endpoint                                   │  │
│  │ - POST /api/convert (requires token)                │  │
│  └──────────────────────────────────────────────────────┘  │
│         ▲                                                  │
│         │                                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Security Layer                                       │  │
│  │ - JWT Token generation & verification               │  │
│  │ - Bcrypt password hashing                            │  │
│  │ - Header-based auth validation                       │  │
│  └──────────────────────────────────────────────────────┘  │
│         ▲                                                  │
│         │                                                  │
└─────────┼──────────────────────────────────────────────────┘
          │ SQL
┌─────────┼──────────────────────────────────────────────────┐
│         ▼                                                  │
│     MySQL Database                                        │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ users table                                          │ │
│  │ - id (int, primary key)                             │ │
│  │ - email (varchar, unique)                           │ │
│  │ - username (varchar, unique)                        │ │
│  │ - hashed_password (varchar)                         │ │
│  │ - is_active (boolean)                               │ │
│  │ - created_at (datetime)                             │ │
│  │ - updated_at (datetime)                             │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend
- **Framework**: FastAPI (Python web framework)
- **Database**: MySQL (relational database)
- **ORM**: SQLAlchemy (database abstraction)
- **Auth**: JWT (JSON Web Tokens)
- **Passwords**: Bcrypt (password hashing)
- **Validation**: Pydantic (data validation)

### Frontend
- **Framework**: React 19 (UI library)
- **Routing**: React Router v6 (client-side routing)
- **HTTP**: Axios (HTTP client)
- **State**: React Context API (state management)

## File Organization

### Backend Files

```
backend/
├── main.py              # FastAPI app, routes & middleware
├── config.py            # Configuration settings
├── database.py          # Database connection & session
├── models.py            # SQLAlchemy User model
├── schemas.py           # Pydantic request/response schemas
├── security.py          # Password hashing & JWT utilities
├── auth_routes.py       # Authentication endpoints
├── setup_db.py          # Database initialization script
├── .env.example         # Environment variables template
└── requirements.txt     # Python dependencies
```

### Frontend Files

```
frontend/src/
├── App.jsx              # Main app with routing
├── App.css              # Application styles
├── api.js               # API service with axios
├── AuthContext.jsx      # Authentication context provider
├── ProtectedRoute.jsx   # Route protection wrapper
└── pages/
    ├── Login.jsx        # Login page
    ├── Register.jsx     # Registration page
    ├── Convert.jsx      # File conversion page (protected)
    └── Auth.css         # Authentication pages styling
```

## Data Flow

### Registration Flow

```
User → Register Form → API (POST /api/auth/register)
  → Validate inputs → Hash password → Save to database
  → Return user object → Show success message
```

### Login Flow

```
User → Login Form → API (POST /api/auth/login)
  → Find user → Verify password → Generate JWT token
  → Return token → Store in localStorage → Redirect to /convert
```

### Protected Endpoint Flow

```
User Request → Include JWT in header
  → Backend validates token → Get user from database
  → Process request → Return response
  → If token invalid → 401 Unauthorized → Redirect to login
```

## API Endpoints

### Authentication Endpoints

#### 1. Register User
```
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePassword123"
}

Response:
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

#### 2. Login User
```
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. Get Current User
```
GET /api/auth/me
Authorization: Bearer YOUR_TOKEN

Response:
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

### Protected Endpoints

#### 4. Convert Files
```
POST /api/convert
Authorization: Bearer YOUR_TOKEN
Content-Type: multipart/form-data

files: [docx files]
format: "moodle_xml" | "qti" | "blackboard"

Response: ZIP file download
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Email already registered"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid email or password"
}
```

### 403 Forbidden
```json
{
  "detail": "User account is disabled"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": "No files uploaded."
}
```

## Security Features

### Password Security
- **Hashing**: Bcrypt with 12 rounds (configurable)
- **Storage**: Only hashed passwords stored in database
- **Validation**: Minimum 8 characters required
- **Comparison**: Constant-time comparison to prevent timing attacks

### Token Security
- **Type**: JWT (JSON Web Tokens)
- **Algorithm**: HS256
- **Expiration**: 30 minutes (configurable)
- **Claims**: Subject (email) included in token
- **Validation**: Verified on every protected request

### Database Security
- **Constraints**: Unique constraints on email and username
- **Isolation**: Each session gets fresh database connection
- **Transactions**: Automatic rollback on errors

### API Security
- **CORS**: Configured for localhost development
- **HTTPS**: Recommended for production
- **Headers**: Authorization header required for protected endpoints
- **Rate Limiting**: Can be added via middleware

## Configuration

### Environment Variables (.env)

```bash
# Database Connection
DATABASE_URL=mysql+mysql-connector-python://user:password@localhost:3306/assessbridge

# JWT Configuration
SECRET_KEY=your-random-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend Configuration

API URL is hardcoded to `http://localhost:8000` in `src/api.js`

To change for production:
```javascript
const API_URL = 'https://api.yourdomain.com/api'
```

## Setup Instructions

### Quick Start
Follow [QUICK_START.md](./QUICK_START.md) for fast setup (5 minutes)

### Detailed Setup
Follow [AUTHENTICATION_SETUP.md](./AUTHENTICATION_SETUP.md) for comprehensive guide

## Common Tasks

### Change Token Expiration
Edit `backend/.env`:
```
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Change Database
Edit `backend/.env`:
```
DATABASE_URL=mysql+mysql-connector-python://user:pass@host:3306/dbname
```

### Add New User Manually
```bash
# In backend directory
python -c "
from database import SessionLocal
from models import User
from security import hash_password

db = SessionLocal()
user = User(
    email='test@example.com',
    username='testuser',
    hashed_password=hash_password('password123')
)
db.add(user)
db.commit()
print('User created!')
"
```

### View All Users
```bash
# In backend directory
python -c "
from database import SessionLocal
from models import User

db = SessionLocal()
users = db.query(User).all()
for user in users:
    print(f'{user.id}: {user.email} (@{user.username})')
"
```

## Deployment Checklist

- [ ] Change `SECRET_KEY` to a strong random string
- [ ] Set up HTTPS/SSL certificates
- [ ] Update `DATABASE_URL` with production credentials
- [ ] Update CORS origins to production domain
- [ ] Update `API_URL` in frontend to production API
- [ ] Set `ACCESS_TOKEN_EXPIRE_MINUTES` appropriately
- [ ] Enable HTTPS only cookies
- [ ] Set up logging and monitoring
- [ ] Implement refresh tokens
- [ ] Add rate limiting
- [ ] Set up database backups
- [ ] Use environment-specific configuration files

## Troubleshooting

See [AUTHENTICATION_SETUP.md](./AUTHENTICATION_SETUP.md) for detailed troubleshooting guide.

## Future Enhancements

- [ ] Refresh token rotation
- [ ] Email verification
- [ ] Password reset via email
- [ ] Two-factor authentication (2FA)
- [ ] OAuth integration (Google, GitHub)
- [ ] Role-based access control (RBAC)
- [ ] Audit logging
- [ ] Session management dashboard
- [ ] Account deactivation
- [ ] Social login integration

## License

Same license as AssessBridge project

## Support

For issues or questions:
1. Check the troubleshooting section in AUTHENTICATION_SETUP.md
2. Review FastAPI and SQLAlchemy documentation
3. Check browser console for frontend errors
4. Check server logs for backend errors
