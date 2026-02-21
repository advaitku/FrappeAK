# Local Bench Environment

## Overview

| Item | Value |
|------|-------|
| Bench directory | `~/frappe-bench` |
| Frappe version | 16.9.0 (version-16 branch) |
| Site | `dev.localhost` |
| Admin login | `Administrator` / `admin` |
| Web URL | http://dev.localhost:8000 |
| MariaDB root password | `root` |

## Services

| Service | Port | Notes |
|---------|------|-------|
| Web (Werkzeug) | 8000 | Development server |
| SocketIO | 9000 | Realtime events |
| Redis Cache | 13000 | Managed by bench (not the system Redis on 6379) |
| Redis Queue | 11000 | Background job queue |
| MariaDB | 3306 | System Homebrew service |
| Redis (system) | 6379 | System Homebrew service (not used by bench) |

## Installed Software (Homebrew)

| Package | Version | Notes |
|---------|---------|-------|
| Python | 3.14 | Keg-only; use `/opt/homebrew/opt/python@3.14/libexec/bin` |
| Node.js | 24 | Keg-only; use `/opt/homebrew/opt/node@24/bin` |
| MariaDB | 12.2.2 | `brew services start mariadb` |
| Redis | 8.6.0 | `brew services start redis` |
| yarn | 1.22.x | Required by Frappe for frontend builds |

## PATH Setup

Node 24 and Python 3.14 are keg-only in Homebrew, so they are not in the default PATH. When running bench commands manually, export this first:

```bash
export PATH="/opt/homebrew/opt/node@24/bin:/opt/homebrew/opt/python@3.14/libexec/bin:/opt/homebrew/bin:/usr/bin:/usr/local/bin:$PATH"
```

## Common Commands

```bash
# Start all services (web, redis, worker, socketio, watch)
cd ~/frappe-bench && bench start

# Run migrations after code changes
bench --site dev.localhost migrate

# Rebuild frontend assets
bench build --app automation_ak

# Open Frappe console
bench --site dev.localhost console

# View installed apps
bench --site dev.localhost list-apps

# Clear cache
bench --site dev.localhost clear-cache
```

## Installed Apps

| App | Version | Branch |
|-----|---------|--------|
| frappe | 16.9.0 | version-16 |
| automation_ak | 0.0.1 | main |
| erpnext | 16.6.1 | version-16 |
| telephony | 0.0.1 | develop |
| helpdesk | 1.20.0 | develop |
| crm | 2.0.0-dev | develop |

## App Symlink

The AutomationAK source code lives at `/Users/ak/Documents/GitHub/FrappeAK` and is symlinked into the bench:

```
~/frappe-bench/apps/automation_ak -> /Users/ak/Documents/GitHub/FrappeAK
```

Any edits to the source repo are immediately reflected in the bench. After changing Python files, the Werkzeug dev server auto-reloads. After changing JS files, the `watch` process auto-rebuilds. After changing DocType JSON files, run `bench --site dev.localhost migrate`.

## MariaDB Config

Frappe requires `utf8mb4` charset. The config is at:

```
/opt/homebrew/etc/my.cnf.d/frappe.cnf
```

```ini
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
```
