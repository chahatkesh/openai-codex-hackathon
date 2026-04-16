# Alembic Migrations

Run migrations from the repository root:

```bash
alembic -c infra/alembic.ini upgrade head
```

Create a new migration:

```bash
alembic -c infra/alembic.ini revision --autogenerate -m "message"
```
