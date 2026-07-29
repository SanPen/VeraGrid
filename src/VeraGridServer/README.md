# VeraGridServer

`VeraGridServer` is the HTTP server package that exposes VeraGrid functionality over a FastAPI service.
It is not the desktop GUI. It is the backend layer used to:

- run remote VeraGrid jobs
- store VeraGrid files and models in PostgreSQL
- expose an admin console for organizations, users, files, models, jobs, and logs
- register child servers under a master server
- serve a TLS certificate to clients that need to trust the instance

This README is the operator and developer view of the package as it exists in `src/VeraGridServer`.

## What Is In This Package

Core files:

- `main.py`: builds the FastAPI app, mounts routers, creates the database schema on startup, exposes `/`, `/favicon.ico`, and `/get_cert`
- `run.py`: CLI/server launcher and TLS bootstrap
- `settings.py`: in-process runtime settings and file-write lock registry
- `db/database.py`: PostgreSQL schema creation and low-level DB helpers
- `db/model_ops.py`: file/model persistence helpers
- `db/user_ops.py`: user and organization persistence helpers
- `endpoints/admin.py`: server-rendered admin console
- `endpoints/file_management.py`: authenticated database file API under `/api/db`
- `endpoints/jobs.py`: job upload, listing, cancel, delete, and results download
- `endpoints/register_in_master.py`: child-server self-registration during startup
- `endpoints/register_sub_servers.py`: master-side child registry
- `generate_ssl_key.py`: self-signed certificate generation helpers

## Runtime Model

At startup, `run.py` fills the process-global `settings` object and launches `uvicorn`.

The server runtime has these main modes:

- `master` mode: the instance accepts child registrations and is treated as the primary node
- `child` mode: on startup the instance calls the configured master at `/register_child_server`
- `secure` mode: the instance generates or reuses a self-signed certificate and starts with HTTPS
- `non-secure` mode: plain HTTP
- `database-enabled` mode: PostgreSQL settings are complete, so DB-backed endpoints and admin sections are active
- `database-disabled` mode: DB-backed sections remain unavailable and some admin pages show a disabled state

## Dependencies

From `setup.py`, the main runtime dependencies are:

- `fastapi`
- `uvicorn`
- `requests`
- `websockets`
- `cryptography`
- `psycopg`
- `numpy`
- `VeraGridEngine` with the exact same version as `VeraGridServer`

Optional extra:

- `tables` for HDF5 compatibility via the `gch5 files` extra

## Installation

Typical editable install from the repo root:

```bash
python3 -m pip install -e ./src/VeraGridServer
```

Or install the whole repo environment the way your project normally does, as long as `VeraGridEngine` and `VeraGridServer` versions stay aligned.

The package defines this console entry point:

```bash
veragridserver
```

Important: in `setup.py`, the entry point targets `VeraGridServer.run:start_server`. That function is directly callable, but the full CLI argument parsing lives under:

```bash
python3 -m VeraGridServer.run
```

If you need command-line flags, prefer `python3 -m VeraGridServer.run ...`.

## How To Start It

Minimal local HTTP server:

```bash
python3 -m VeraGridServer.run --secure false --master true --port 8000
```

Local HTTPS server with self-signed cert generation:

```bash
python3 -m VeraGridServer.run --secure true --master true --port 8000
```

Child server registering into a master:

```bash
python3 -m VeraGridServer.run \
  --secure true \
  --master false \
  --master_host https://master-host \
  --master_port 8000 \
  --port 8001 \
  --user child-name \
  --pwd child-password
```

Server with PostgreSQL enabled:

```bash
python3 -m VeraGridServer.run \
  --secure true \
  --master true \
  --port 8000 \
  --user admin \
  --pwd strong-api-key \
  --db_host 127.0.0.1 \
  --db_port 5432 \
  --db_name veragrid \
  --db_user veragrid \
  --db_password secret \
  --db_schema veragrid
```

## CLI Arguments

Defined in `run.py`:

- `--key_fname`: TLS private key file path, default `key.pem`
- `--cert_fname`: TLS certificate file path, default `cert.pem`
- `--host`: domain/host name used for certificate generation, default `0.0.0.0`
- `--port`: listen port, default `8000`
- `--secure`: `true` or `false`
- `--master`: `true` or `false`
- `--master_host`: master base host used by child registration
- `--master_port`: master port used by child registration
- `--user`: runtime username stored in `settings.this_username`
- `--pwd`: runtime password used as the API key and admin password source
- `--db_host`: PostgreSQL server host name or IP address used by VeraGridServer to connect to the database instance
- `--db_port`: PostgreSQL TCP port, usually `5432`
- `--db_name`: target PostgreSQL database name that VeraGridServer should create/use for its data
- `--db_user`: PostgreSQL login user name used for schema creation and normal reads/writes
- `--db_password`: password for `--db_user`
- `--db_schema`: PostgreSQL schema name inside `--db_name`; default is `veragrid`

## TLS Behavior

If `secure` is `true`, `run.py` calls `generate_ssl_certificate(...)` before launching Uvicorn.

Behavior to know:

- relative key/cert file names are resolved relative to `src/VeraGridServer`
- `/get_cert` serves `cert.pem` when it exists
- if the cert file does not exist, `/get_cert` returns `404`
- the generated certificate is self-signed, so client trust usually needs explicit handling

Runtime artifacts that matter:

- `src/VeraGridServer/key.pem`
- `src/VeraGridServer/cert.pem`

## Authentication Model

There are two closely related authentication surfaces:

### API key authentication

Used by DB file-management endpoints.

- header name: `API-Key`
- expected value: `settings.this_password`
- missing header: `401`
- password not configured: `503`
- wrong key: `403`

### Admin console password

The admin console login also depends on the configured server password.

Operationally, if you do not provide `--pwd`, authenticated admin functionality is not properly usable.

This is simple process-local auth, not a full IAM system. Treat it as instance-level protection, not multi-tenant security by itself.

## Database Behavior

The database layer is optional at launch time.

The server considers DB configuration complete only when all of these are set:

- `db_host`
- `db_port > 0`
- `db_name`
- `db_user`
- `db_password`

On FastAPI startup, `main.py` does this:

- if DB settings are complete, it calls `create_veragrid_schema(...)`
- if DB settings are incomplete, it logs that DB creation was skipped

What that means:

- schema/database bootstrap is automatic on startup
- DB-backed endpoints depend on launch-time settings, not environment variables
- some admin sections intentionally degrade to a disabled state if DB config is absent

### File-write locking

`settings.py` includes a process-local lock registry keyed by:

```text
schema_name:file_idtag
```

This prevents concurrent writes in the same server process from trampling the same stored file.

Scope caveat:

- this is process-local only
- it does not coordinate across multiple worker processes or multiple hosts

If you later deploy multiple Uvicorn workers or multiple app instances writing the same DB rows, this lock is not enough by itself.

## FastAPI App Surface

Mounted routers:

- `register_in_master`
- `register_sub_servers`
- `calculations`
- `jobs`
- `admin`
- `file_management`

Base app routes from `main.py`:

- `GET /`: redirects to `/admin`
- `GET /favicon.ico`
- `GET /get_cert`

### Current endpoint inventory

#### Child registration

- `POST /register_child_server`
- `GET /registered_child_servers`

#### Jobs

- `POST /upload_job/`
- `GET /jobs_list`
- `DELETE /jobs/{job_id}`
- `POST /jobs/{job_id}/cancel`
- `GET /download_results/{job_id}`

#### Database file API

Prefix: `/api/db`

- `GET /api/db/files`
- `GET /api/db/files/{file_idtag}`
- `GET /api/db/files/{file_idtag}/download`
- `DELETE /api/db/files/{file_idtag}`
- `DELETE /api/db/files/{file_idtag}/models/{model_idtag}`
- `POST /api/db/files/{file_idtag}/replace`

#### Admin console

Main routes:

- `GET /admin/login`
- `POST /admin/login`
- `POST /admin/logout`
- `GET /admin`

Mutation routes include:

- organization create/update/delete
- user create/update/delete
- file create/update/delete
- model create/update/delete
- model upload

## Admin Console

The admin console in `endpoints/admin.py` is server-side rendered HTML, not a separate SPA.

What it manages:

- organizations
- users
- stored files
- stored models
- jobs
- live in-memory log buffer
- registered child servers
- database status

What to expect:

- it is meant to stay usable on large tables by using paging and search filters server-side
- if DB configuration is missing, DB-backed sections explicitly show that they are disabled
- the root route `/` sends you here

## Job Execution Model

`endpoints/jobs.py` accepts a VeraGrid job payload, reconstructs a `MultiCircuit`, creates a `RemoteJob`, and runs it through `VeraGridEngine.IO.veragrid.remote.run_job`.

Important behavior:

- jobs are tracked in the in-memory `JOBS_LIST` dictionary
- job IDs are normalized to UUID hex form
- results download expects a ZIP path under VeraGrid’s server job folder
- job state is not persisted across restarts

Operational caveats from the current code:

- `POST /upload_job/` runs the job inline in the request path
- the in-memory job entry is removed after completion in that same endpoint
- because of that, the results-download path is not a durable queue/worker system
- this is useful as a synchronous remote execution endpoint, not as a production-grade distributed scheduler yet

## Database File API

The DB API under `/api/db` is the clearest programmatic API in the package today.

It supports:

- listing stored file trees
- reading one file and its model metadata
- exporting a whole multiverse archive
- exporting only the base model
- exporting one selected model as a flat circuit archive
- replacing a stored file from an uploaded VeraGrid archive
- deleting a whole file
- deleting one model

The endpoints use:

- `API-Key` header auth
- PostgreSQL-backed file/model persistence
- temporary `.veragrid` files for download serialization

## Master / Child Registration

If `settings.am_i_master` is `false`, `register_in_master.py` performs startup registration against:

```text
{master_host}:{master_port}/register_child_server
```

The child sends:

- detected local IP
- its listen port
- username
- password

The master stores registrations in an in-memory `registered_services` dictionary.

Current caveats:

- this registry is not persistent
- duplicates are rejected
- there is no heartbeat or expiry mechanism
- `master_host` is concatenated directly into the URL, so in practice you should pass a scheme-bearing host like `https://host` when secure transport is expected

## Important Paths

Paths relative to `src/VeraGridServer`:

- `key.pem`: generated or reused TLS private key
- `cert.pem`: generated or reused TLS certificate
- `data/VeraGrid_icon.ico`: favicon/admin icon

Paths managed through VeraGridEngine helpers:

- server jobs folder: `<veragrid user folder>/server_jobs`

## Development Notes

### Running from source

Direct module execution is the most reliable way to test launch flags:

```bash
python3 -m VeraGridServer.run --secure false --master true --port 8000
```

### Swagger / OpenAPI

Because the app is a plain FastAPI app with `app = FastAPI()`, the usual FastAPI docs routes should be available unless middleware or deployment settings disable them:

- `/docs`
- `/openapi.json`

That is useful for endpoint discovery while developing.

### Version coupling

`setup.py` pins:

```text
VeraGridEngine == VeraGridServer version
```

Do not mix server and engine versions casually.

## Known Design Constraints

These are not guesses. They follow from the current code.

- Runtime configuration is passed through function arguments and CLI flags, then stored in one global `settings` object.
- There is no environment-variable configuration layer in this package today.
- Security is intentionally simple: one instance password doubles as the API key source and admin auth source.
- Child-server registration and job tracking are in-memory, so restarts forget them.
- The file lock registry only protects writes inside one process.
- `endpoints/calculations.py` currently exposes a router but no public routes.
- `connection_example.py` contains a WebSocket sender example, but the active FastAPI app in this package does not define a matching WebSocket endpoint.

## Practical First Steps

If you only need to get productive fast:

1. Start one local HTTP instance:

```bash
python3 -m VeraGridServer.run --secure false --master true --port 8000 --pwd devkey
```

2. Open:

```text
http://127.0.0.1:8000/admin
```

3. If you need DB-backed file storage, restart with PostgreSQL settings.

4. For API use, send `API-Key: <your --pwd value>` to `/api/db/...`.

5. If you need TLS trust material, call:

```text
GET /get_cert
```

## Testing

The generic project tests live under `src/tests`.

For VeraGridServer-specific changes, at minimum validate:

- the server still starts
- `/admin` still loads
- `/get_cert` works in secure mode
- `/api/db/files` behaves correctly with and without DB config
- child registration still works if you changed master/child code

There is no point pretending this package is fully documented by one file, but this README should give you the important runtime truths without forcing a source dive first.
