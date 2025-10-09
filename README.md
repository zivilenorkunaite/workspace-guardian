# Workspace Guardian

Approval system for Databricks resources including Apps, Model Serving Endpoints, Vector Search, and Lakehouse Postgres.

## Features

✅ **Multi-Resource Management**
- Databricks Apps
- Model Serving Endpoints
- Vector Search Endpoints
- Lakehouse Postgres Connections

✅ **Approval Workflow**
- Approve/revoke access to resources
- Time-based expiration
- Audit trail in Delta Lake
- Justification tracking

✅ **Migration System**
- Schema-wide migrations
- Version controlled
- ORM standard fields
- Automatic schema creation

✅ **Modern Stack**
- Backend: FastAPI + Databricks SDK
- Frontend: React + Lucide icons
- Storage: Delta Lake + Unity Catalog
- Compute: SQL Warehouse

## Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   # Backend
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

2. **Configure environment** (`.env` for local development only):
   ```bash
   # Local development only - not needed for Databricks App
   DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
   DATABRICKS_TOKEN=your-token
   
   # Required for both local and app deployment
   DATABRICKS_WAREHOUSE_ID=your-warehouse-id
   APP_CATALOG=main
   APP_SCHEMA=workspace_guardian
   ```

3. **Run locally**:
   ```bash
   # Start backend
   ./start-backend.sh
   
   # Start frontend (in another terminal)
   cd frontend && npm run dev
   ```

4. **Access**: http://localhost:5173

### Deploy to Databricks

Deploy as a Databricks App:

```bash
./deploy.sh
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## Project Structure

```
workspace-guardian/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── main.py       # FastAPI app
│   │   ├── databricks_client.py  # Databricks API
│   │   ├── delta_manager.py      # Delta operations
│   │   └── migrations.py         # Schema migrations
│   └── requirements.txt
├── frontend/              # React frontend
│   ├── src/
│   │   ├── App.jsx       # Main component
│   │   ├── components/   # UI components
│   │   └── App.css       # Styles
│   └── package.json
├── app/                   # Deployed app (generated)
├── databricks.yml         # Bundle configuration
├── deploy.sh             # Deployment script
└── DEPLOYMENT.md         # Deployment guide
```

## Architecture

### Backend
- **FastAPI**: REST API server
- **Databricks SDK**: Interact with Databricks APIs
- **SQL Warehouse**: Execute SQL queries
- **Delta Lake**: Store approval data

### Frontend
- **React**: UI framework
- **Fetch API**: Call backend APIs
- **Lucide Icons**: Modern icons
- **CSS**: Custom styling

### Storage
- **Unity Catalog**: Governance layer
- **Delta Lake**: ACID transactions
- **Schema**: `{catalog}.{schema}.approved_apps`
- **Migrations**: `{catalog}.{schema}.migration_definitions`

## API Endpoints

- `GET /api/workspaces` - List workspaces
- `GET /api/apps?workspace_id=X` - List apps
- `POST /api/approve` - Approve resource
- `POST /api/revoke` - Revoke approval
- `GET /api/health` - Health check

## Migration System

Migrations are version controlled and tracked:

```python
# backend/app/migrations.py
{
    'version': 1,
    'description': 'Initial schema',
    'sql': 'CREATE TABLE ...',
    'migration_type': 'schema_init',
    'affected_tables': ['approved_apps']
}
```

Check migration status:
```bash
cd backend && python scripts/check_migrations.py
```

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Add Migration
1. Edit `backend/app/migrations.py`
2. Add new migration with incremented version
3. Restart backend to apply

### Linting
```bash
# Backend
cd backend && python -m pylint app/

# Frontend
cd frontend && npm run lint
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required For |
|----------|-------------|---------|--------------|
| `DATABRICKS_HOST` | Workspace URL | - | Local dev only |
| `DATABRICKS_TOKEN` | Auth token | - | Local dev only |
| `DATABRICKS_WAREHOUSE_ID` | SQL Warehouse ID | Required | Both |
| `APP_CATALOG` | Unity Catalog name | `main` | Both |
| `APP_SCHEMA` | Schema name | `workspace_guardian` | Both |
| `APP_VERSION` | App version | `1.0.0` | Both |

**Note**: When deployed as a Databricks App, `DATABRICKS_HOST` and `DATABRICKS_TOKEN` are not needed. The app uses automatic authentication.

### Bundle Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `catalog` | Unity Catalog name | `main` |
| `schema` | Schema name | `workspace_guardian` |
| `warehouse_id` | SQL Warehouse ID | Auto-detect |

## Security

### Authentication

- **Databricks App**: Uses automatic authentication via the app's identity (no tokens)
- **Local Development**: Requires `DATABRICKS_HOST` and `DATABRICKS_TOKEN` in `.env`

### Permissions Required

The app's service principal needs:
- `USE CATALOG` on target catalog
- `CREATE SCHEMA` on target catalog
- `USE SCHEMA` on target schema
- `SELECT`, `INSERT`, `UPDATE` on tables
- SQL Warehouse access
- Workspace read access

### Catalog Creation

**IMPORTANT**: Catalogs must be pre-created by admin:

```sql
CREATE CATALOG IF NOT EXISTS main;
GRANT USE CATALOG ON CATALOG main TO `<service-principal>`;
GRANT CREATE SCHEMA ON CATALOG main TO `<service-principal>`;
```

The app will auto-create schemas and tables.

## Troubleshooting

### Backend Fails to Start
- Check `.env` file exists and has correct values
- Verify SQL Warehouse is running
- Check catalog exists (must be pre-created)

### Migrations Fail
- Verify catalog exists
- Check service principal permissions
- Review logs: `tail -f backend.log`

### Frontend Not Loading
- Check backend is running on port 8000
- Verify CORS is configured
- Check browser console for errors

### Deployment Issues
- Validate bundle: `databricks bundle validate`
- Check secrets: `databricks secrets list-secrets workspace-guardian`
- Review app logs: `databricks apps logs workspace-guardian-dev`

## Contributing

1. Create feature branch
2. Make changes
3. Test locally
4. Submit pull request

## License

Proprietary - Internal Use Only

## Support

For issues or questions, contact the development team.
