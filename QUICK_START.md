# AssessBridge Authentication - Quick Start Guide

Complete setup and run the application with authentication in under 5 minutes.

## Prerequisites

- MySQL running on localhost
- Python 3.8+
- Node.js 16+

## Step 1: Backend Setup (2 minutes)

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Setup database (creates tables)
python setup_db.py
```

Expected output:
```
Setting up AssessBridge database...
✓ Database 'assessbridge' created successfully
✓ Tables created successfully
✓ Database setup completed successfully!
```

## Step 2: Start Backend Server

```bash
# From backend directory
uvicorn main:app --reload
```

Server starts at: `http://localhost:8000`

## Step 3: Frontend Setup (2 minutes)

In a new terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend starts at: `http://localhost:5173`

## Step 4: Test the Application

1. **Open browser**: Go to `http://localhost:5173`
2. **Create account**: Click "Register" and fill in details
   - Email: `test@example.com`
   - Username: `testuser`
   - Password: `TestPass123!` (min 8 chars)
3. **Login**: Use your credentials
4. **Convert files**: Upload .docx files and convert to LMS format
5. **Logout**: Click "Logout" button in top right

## API Endpoints Quick Reference

All requests except `/register` and `/login` require the `Authorization: Bearer <token>` header.

### Authentication Endpoints

```bash
# Register
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePassword123"
}

# Login (returns access token)
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123"
}

# Get current user (requires token)
GET /api/auth/me
Authorization: Bearer YOUR_TOKEN
```

### Conversion Endpoint

```bash
POST /api/convert
Authorization: Bearer YOUR_TOKEN
Content-Type: multipart/form-data

files: [docx files]
format: "moodle_xml" | "qti" | "blackboard"
```

## Troubleshooting

### "Connection refused" error

**Problem**: Backend not running  
**Solution**: Make sure you ran `uvicorn main:app --reload` in the backend directory

### "Database connection error"

**Problem**: MySQL not running or wrong credentials  
**Solution**: 
- Start MySQL: `mysql -u root -p`
- Check `.env` file has correct `DATABASE_URL`
- Run `python setup_db.py` again

### "Blank page on localhost:5173"

**Problem**: Frontend not started or vite issue  
**Solution**: 
- Make sure you ran `npm run dev` in frontend directory
- Kill and restart the process
- Clear browser cache

### "CORS errors in console"

**Problem**: Frontend/backend not communicating  
**Solution**: Make sure both servers are running on correct ports:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## Common Commands

```bash
# Backend
cd backend
pip install -r requirements.txt          # Install dependencies
python setup_db.py                       # Setup database
uvicorn main:app --reload                # Start server (dev)
uvicorn main:app --port 8001            # Use different port

# Frontend
cd frontend
npm install                              # Install dependencies
npm run dev                              # Start dev server
npm run build                            # Build for production
npm run preview                          # Preview production build
```

## File Permissions

Make sure these files are readable:

```bash
# Backend
backend/config.py
backend/database.py
backend/models.py
backend/schemas.py
backend/security.py
backend/auth_routes.py
backend/setup_db.py

# Frontend
frontend/src/api.js
frontend/src/AuthContext.jsx
frontend/src/ProtectedRoute.jsx
frontend/src/pages/Login.jsx
frontend/src/pages/Register.jsx
frontend/src/pages/Convert.jsx
```

## Next Steps

After getting this running:

1. Read [AUTHENTICATION_SETUP.md](./AUTHENTICATION_SETUP.md) for detailed documentation
2. Customize the styling in `frontend/src/pages/Auth.css` and `frontend/src/App.css`
3. Update the `SECRET_KEY` in `backend/.env` for production
4. Set up HTTPS for production deployment
5. Implement refresh tokens for better security

## Environment Variables Reference

**Backend (.env file)**

```
DATABASE_URL=mysql+mysql-connector-python://root:@localhost:3306/assessbridge
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Accessing the Application

After startup:

| Component | URL | Purpose |
|-----------|-----|---------|
| Frontend | `http://localhost:5173` | User interface |
| Backend API | `http://localhost:8000` | API endpoints |
| API Docs | `http://localhost:8000/docs` | Interactive API documentation |
| MySQL | `localhost:3306` | Database |

## Support

- FastAPI Docs: `http://localhost:8000/docs`
- Check server logs for errors
- Read AUTHENTICATION_SETUP.md for detailed troubleshooting
