# MySQL Setup for AssessBridge

If you see the error `Can't connect to MySQL server on 'localhost'`, MySQL is not running. Follow the steps below.

## Starting MySQL

### Option 1: Using Homebrew (if you installed MySQL via Homebrew)

```bash
# Check if MySQL is installed
brew services list

# Start MySQL
brew services start mysql

# Verify it's running
brew services list
```

You should see `mysql started` in the output.

### Option 2: Using MAMP (if installed)

1. Open MAMP
2. Click "Start Servers"
3. Wait for the status to turn green

### Option 3: Using XAMPP (if installed)

1. Open XAMPP Control Panel
2. Click "Start" next to MySQL

### Option 4: Check if MySQL is already running

```bash
# Check running processes
ps aux | grep mysql
```

If you see `mysqld` in the output, MySQL is already running.

## After Starting MySQL

Once MySQL is running, go back to the terminal and run:

```bash
cd /Users/e402412/Desktop/AssessBridge/backend
source ../.venv/bin/activate
python setup_db.py
```

You should see:
```
Setting up AssessBridge database...

✓ Database 'assessbridge' created successfully
✓ Tables created successfully

✓ Database setup completed successfully!
```

## Troubleshooting

### Still getting "Connection refused"?

1. Verify MySQL is running: `brew services list`
2. Check if it's on a different port: `mysql -u root -p -P 3307` (change 3307 to your port)
3. If your MySQL has a password, update `.env`:
   ```
   DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/assessbridge
   ```

### Can't find MySQL commands?

If `brew services` or similar commands don't work:

1. Find where MySQL is installed:
   ```bash
   which mysql
   which mysqld
   ```

2. Or check if it's in:
   ```bash
   /opt/homebrew/bin/mysql
   /usr/local/mysql/bin/mysql
   /Applications/MAMP/Library/bin/mysql
   ```

### MySQL won't start?

1. Check if the port is already in use:
   ```bash
   lsof -i :3306
   ```

2. Look for error logs:
   ```bash
   # For Homebrew installation
   tail -f /opt/homebrew/var/mysql/$(hostname).err
   ```

3. If corrupted, try:
   ```bash
   brew reinstall mysql
   ```

## Verify Everything Works

Once MySQL is running and setup is complete:

```bash
# Start backend
source ../.venv/bin/activate
uvicorn main:app --reload

# In another terminal, start frontend
cd ../frontend
npm run dev
```

Then open `http://localhost:5173` and create an account!

## Quick Reference

| Task | Command |
|------|---------|
| Start MySQL | `brew services start mysql` |
| Stop MySQL | `brew services stop mysql` |
| Restart MySQL | `brew services restart mysql` |
| Check status | `brew services list` |
| Setup database | `python setup_db.py` |
| Start backend | `uvicorn main:app --reload` |
| Start frontend | `npm run dev` |

---

**Note**: MySQL runs on port `3306` by default. If you need a different port, update the `DATABASE_URL` in `.env`.
