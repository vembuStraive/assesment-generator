Stop existing processes:

pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "vite" 2>/dev/null

Start backend:
cd /Users/e402412/Desktop/AssessBridge/backend
python3 -m uvicorn main:app --reload --port 8000

Start frontend (new terminal tab):
cd /Users/e402412/Desktop/AssessBridge/frontend
npx vite --host
