# Changelog

All notable changes to Workspace Guardian will be documented in this file.

## [1.1.0] - 2025-10-09

### Changed
- **BREAKING**: Migrated from file path-based Delta tables to Unity Catalog managed tables
  - Changed `DELTA_TABLE_PATH` environment variable to `DELTA_TABLE_NAME`
  - Format changed from `/dbfs/path` to `catalog.schema.table`
  - Default table: `main.workspace_guardian.approved_apps`

### Added
- Unity Catalog integration with full governance support
- Automatic catalog, schema, and table creation
- MERGE operations for atomic upserts
- SQL UPDATE operations for revocations
- Comprehensive Unity Catalog documentation (UNITY_CATALOG.md)
- Table comments and column descriptions
- Support for two-level and three-level table names

### Improved
- Better error handling and logging
- More robust table initialization
- Enhanced data integrity with ACID operations
- Simplified configuration

### Migration Guide
Users upgrading from v1.0.0 need to:
1. Update `.env` file: Replace `DELTA_TABLE_PATH` with `DELTA_TABLE_NAME`
2. Set value to Unity Catalog table name (e.g., `main.workspace_guardian.approved_apps`)
3. Optionally migrate existing data to Unity Catalog table
4. Grant appropriate Unity Catalog permissions

See UNITY_CATALOG.md for detailed migration instructions.

## [1.0.0] - 2025-10-09

### Added
- Initial release of Workspace Guardian
- Multi-workspace support with dropdown selector
- List all Databricks resources (Apps, Model Serving, Vector Search, Lakehouse Postgres)
- Approve apps with required justification
- Optional expiration dates for approvals
- Revoke approvals while maintaining history
- Delta table storage (file path based)
- Real-time app state refresh
- Statistics dashboard
- Modern React UI with FastAPI backend
- Complete REST API
- Comprehensive documentation
- Helper scripts for setup and development
