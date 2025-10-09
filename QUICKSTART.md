# Quick Start Guide

Get Workspace Guardian up and running in 5 minutes!

## Prerequisites

- Python 3.9+
- Node.js 16+
- Databricks workspace with a personal access token

## Step 1: Initialize Project (2 minutes)

```bash
# Run the automated setup script
./scripts/init_project.sh
```

This will:
- Create Python virtual environment
- Install backend dependencies
- Install frontend dependencies
- Create .env template files

## Step 2: Configure Credentials (1 minute)

Edit the `.env` file in the root directory:

```bash
# Open in your favorite editor
nano .env  # or vim, code, etc.
```

Update these values:

```bash
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi1234567890abcdef  # Get from Databricks > User Settings > Access Tokens
DELTA_TABLE_PATH=/dbfs/workspace_guardian/approved_apps
```

## Step 3: Start Backend (30 seconds)

```bash
cd backend
source venv/bin/activate
export $(cat ../.env | xargs)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be running at `http://localhost:8000`

## Step 4: Start Frontend (30 seconds)

Open a new terminal:

```bash
cd frontend
npm run dev
```

Frontend will be running at `http://localhost:3000`

## Step 5: Use the App! (1 minute)

1. Open `http://localhost:3000` in your browser
2. Select your workspace from the dropdown
3. View all Databricks resources (Apps, Model Serving, Vector Search, Lakehouse Postgres)
4. Click "Approve App" on any unapproved app
5. Add justification and optional expiration date
6. Submit!

## Quick Test

Want to test your setup without starting the servers?

```bash
cd backend
source venv/bin/activate
export $(cat ../.env | xargs)
python ../scripts/test_connection.py
```

## Common Issues

### "Command not found: uvicorn"
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### "Failed to connect to Databricks"
- Check your `DATABRICKS_HOST` URL (should start with https://)
- Verify your `DATABRICKS_TOKEN` is valid
- Test in browser: `https://your-workspace.cloud.databricks.com`

### Frontend shows "Failed to load workspaces"
- Make sure backend is running on port 8000
- Check backend terminal for errors
- Try accessing `http://localhost:8000/api/health` directly

## Next Steps

- Read [SETUP.md](SETUP.md) for detailed configuration
- Read [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Review [README.md](README.md) for architecture details

## Pro Tips

### Run both services at once (using tmux or screen)

```bash
# Terminal 1
tmux new-session -d -s guardian-backend 'cd backend && source venv/bin/activate && export $(cat ../.env | xargs) && uvicorn app.main:app --reload'

# Terminal 2
tmux new-session -d -s guardian-frontend 'cd frontend && npm run dev'

# View logs
tmux attach -t guardian-backend
tmux attach -t guardian-frontend
```

### Quick restart after code changes

Backend auto-reloads with `--reload` flag.

Frontend auto-reloads with Vite.

No restart needed! 🎉

### Access API directly

```bash
# Health check
curl http://localhost:8000/api/health

# List workspaces
curl http://localhost:8000/api/workspaces

# List apps
curl http://localhost:8000/api/apps
```

## Need Help?

- Check the [README.md](README.md) for architecture overview
- Review [SETUP.md](SETUP.md) for detailed setup
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Check application logs in the terminal

Happy monitoring! 🚀


