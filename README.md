# FileFlow — Digital Letter & Order Workflow POC

FileFlow is a Django proof of concept for moving official letters and orders through a controlled, multi-level approval workflow. It implements the workflow defined in `POC_Plan.docx`: Director creation, Minister review, sequential employee processing, optional comments, status tracking, and a complete movement audit trail.

## What it does

- Creates letters and orders with an automatic reference number in the format `FMS/YYYY/000001`.
- Routes correspondence from the Director to the Minister and back, or through a configurable employee chain.
- Enforces sequential employee routing: Director → Level 1 → Level 2 → … → final level → Complete.
- Allows an optional forwarding note and separate comments at every stage.
- Shows the current holder, state, comments, and timestamped movement history to all signed-in roles.
- Lets the Director (Super Admin) create Minister and employee accounts, including employee workflow levels.
- Provides a responsive sidebar-based interface for the dashboard, tracking, correspondence detail, and user management screens.

## Roles

| Role | Capabilities |
| --- | --- |
| Director (Super Admin) | Creates letters/orders, sends an item to the Minister or Level 1 employee, tracks all items, and manages users. |
| Minister | Reviews items received from the Director, comments, and returns them to the Director. |
| Next Level Employee | Views assigned items, comments, forwards to the next numbered level, or returns an item to the Director. The highest configured level can mark an item complete. |

## Workflow

```text
Director → Minister → Director
        └→ Employee Level 1 → Level 2 → … → Final Level → Complete
                                      └→ Director (return)
```

Comments are mandatory and would be show in every level of previous against the correspondence reference number. All creates, forwards, returns, and completions are recorded in the movement history and audit log.

## Local setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16+ (or a compatible PostgreSQL version)

### Install and run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a PostgreSQL database, then create `.env` in the project root:

```env
DJANGO_SECRET_KEY=change-this-for-your-environment
DJANGO_DEBUG=1
DATABASE_URL=postgres://fms:fms@localhost:5432/fms
```

Run migrations and start the server:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/accounts/login/`. In Django admin (`/admin/`), update the superuser’s role to **Director (Super Admin)**. Then use **User management** to create a Minister and employees with levels `1`, `2`, `3`, and so on.

## Project layout

- `apps/accounts` — custom user model, roles, and Director-managed account creation
- `apps/letters` — correspondence model, forms, screens, and workflow transitions
- `apps/workflow` — movement history and comments
- `apps/audit` — audit log entries for movement events
- `templates` — responsive FileFlow interface and pages

