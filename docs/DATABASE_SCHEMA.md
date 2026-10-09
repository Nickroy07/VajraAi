# DATABASE SCHEMA

## Engine
SQLite (local development placeholder).

## Initial placeholder tables
- `schema_migrations`
  - `id INTEGER PRIMARY KEY`
  - `applied_at TEXT NOT NULL`

## Notes
This is intentionally minimal and safe for bootstrap. Future iterations will add task, policy, approval, and audit tables.
