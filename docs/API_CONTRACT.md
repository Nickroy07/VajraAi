# API CONTRACT

## Conventions
- IDs use UUID strings.
- Timestamps use ISO-8601 UTC.
- Status fields use explicit enums.
- Error responses use:
  ```json
  {
    "error": {
      "code": "string",
      "message": "string",
      "details": {}
    }
  }
  ```

## Current backend endpoints
- `GET /health`
  - Returns service name, status, and timestamp.

## Shared schemas
- `shared/contracts/task.schema.json`
- `shared/contracts/tool-call.schema.json`
- `shared/contracts/events.schema.json`
