# FMS POC — Digital Letter / Order Movement & Multi-Level Approval

Django 5 + PostgreSQL 16 + Django Templates. Implements the workflow from POC_Plan.docx.

## Roles
- **Director** (Super Admin): creates letters, forwards to Minister or Employees, manages users.
- **Minister**: reviews letters forwarded by Director, comments, returns.
- **Employee (Level 1..N)**: receives, comments, forwards to next level or back; last level marks Complete.

## Quick start (Docker)
```bash
cp .env.example .env
docker compose up --build
# in another terminal:
docker compose exec web python manage.py createsuperuser
# then open http://localhost:8000/admin to set role=DIRECTOR on that user,
# and create Minister + Employee (level 1,2,3) users via the app UI.
```

## Quick start (local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
createdb fms   # requires local Postgres, user 'fms' password 'fms'
cp .env.example .env
python manage.py makemigrations accounts letters workflow audit
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then in Django admin, edit the superuser to set **role=DIRECTOR**. Login at
`/accounts/login/` and use the app to create Minister/Employee accounts.

## Reference number
Auto-generated on create using PG sequence `letter_ref_seq` → `FMS/{YYYY}/{000123}`.

## Structure
- `apps/accounts` — custom User with `role` + `level`
- `apps/letters` — Letter model with `django-fsm` state machine
- `apps/workflow` — Movement (history) + Comment
- `apps/audit` — AuditLog written via post_save signal on Movement

## Workflow states
`DRAFT → WITH_DIRECTOR ↔ WITH_MINISTER`
`WITH_DIRECTOR → WITH_EMPLOYEE (chain) → COMPLETE`
Employees can also return to Director.
