# Authentication Setup Guide for AssessBridge

This guide walks through setting up the authentication system for AssessBridge using MySQL, FastAPI, and React.

## Prerequisites

- Python 3.8+
- Node.js 16+
- MySQL Server (already installed on your system)

## Backend Setup

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Create Environment Configuration

Create a `.env` file in the backend directory:

```bash
cp .env.example .env
```

Edit `.env` and update the values if needed:

```
DATABASE_URL=mysql+mysql-connector-python://root:@localhost:3306/assessbridge
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Important for Production:** Change the `SECRET_KEY` to a strong random string.

### 3. Set Up the Database

Run the database setup script to create the database and tables:

```bash
python setup_db.py
```

You should see output like:
```
Setting up AssessBridge database...

✓ Database 'assessbridge' created successfully
✓ Tables created successfully

✓ Database setup completed successfully!
```

### 4. Start the Backend Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

**Available endpoints:**
- `GET /api/health` - Health check
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user (requires token)
- `POST /api/convert` - Convert DOCX files (requires authentication)

## Frontend Setup

### 1. Install Node Dependencies

```bash
cd frontend
npm install
```

### 2. Start the Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Testing Authentication

### Register a New User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "SecurePassword123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123"
  }'
```

Response will include an access token:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Get Current User

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Use Convert API with Authentication

```bash
curl -X POST http://localhost:8000/api/convert \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "files=@document.docx" \
  -F "format=moodle_xml"
```

## File Structure

### Backend Files Added/Modified

```
backend/
├── main.py                 (modified - added auth routes & protection)
├── config.py              (new - configuration management)
├── database.py            (new - database connection setup)
├── models.py              (new - SQLAlchemy User model)
├── schemas.py             (new - Pydantic request/response models)
├── security.py            (new - password hashing & JWT management)
├── auth_routes.py         (new - authentication endpoints)
├── setup_db.py            (new - database initialization script)
├── .env.example           (new - environment configuration template)
└── requirements.txt       (modified - added new dependencies)
```

### Frontend Files Added/Modified

```
frontend/src/
├── App.jsx                (modified - routing & auth integration)
├── App.css                (modified - added user header styles)
├── api.js                 (new - API service with axios)
├── AuthContext.jsx        (new - authentication context provider)
├── ProtectedRoute.jsx     (new - route protection component)
├── pages/
│   ├── Login.jsx          (new - login page)
│   ├── Register.jsx       (new - registration page)
│   ├── Convert.jsx        (new - convert page with auth)
│   └── Auth.css           (new - authentication page styles)
├── package.json           (modified - added react-router-dom & axios)
└── main.jsx              (unchanged)
```

## Database Schema

### Users Table

```sql
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## Security Considerations

1. **Password Hashing**: Passwords are hashed using bcrypt (cost factor: 12)
2. **JWT Tokens**: Tokens expire after 30 minutes (configurable)
3. **CORS**: Configured to accept requests from frontend at `http://localhost:5173`
4. **Secret Key**: Change the `SECRET_KEY` in production
5. **HTTPS**: Use HTTPS in production
6. **Token Storage**: Tokens are stored in localStorage (consider using httpOnly cookies in production)

## Troubleshooting

### Database Connection Error

If you get a connection error:

1. Make sure MySQL is running: `mysql -u root -p -e "SELECT 1"`
2. Check the `DATABASE_URL` in `.env` file
3. Verify the database exists: `mysql -u root -e "SHOW DATABASES;"`

### Port Already in Use

If port 8000 or 5173 is already in use:

**Backend (port 8000):**
```bash
uvicorn main:app --reload --port 8001
```

**Frontend (port 5173):**
```bash
npm run dev -- --port 5174
```

### CORS Errors

If you see CORS errors in the browser console:

1. Make sure both backend and frontend are running
2. Check that the frontend URL in `CORS_ORIGINS` in `main.py` matches your frontend URL

### Authentication Token Issues

If tokens are not being accepted:

1. Verify the token is being sent in the `Authorization` header
2. Check that the token hasn't expired (30 minutes by default)
3. Ensure the `SECRET_KEY` matches between registration and login

## Next Steps

1. Create a production-ready database setup (use environment-specific credentials)
2. Implement refresh tokens for better security
3. Add email verification
4. Add password reset functionality
5. Implement role-based access control (RBAC)
6. Add logging and monitoring
7. Set up HTTPS/SSL

## Support

For issues or questions about the authentication implementation, refer to:

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Documentation](https://jwt.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
