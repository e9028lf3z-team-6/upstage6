# backend
Start-Process powershell -ArgumentList "uv run uvicorn backend.main:app --reload --port 8000"

# frontend
Start-Process powershell -ArgumentList "cd frontend; npm run dev"
