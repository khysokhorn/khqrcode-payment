# 🚨 CRITICAL - Data Safety Procedures

## NEVER Execute These Commands

```bash
❌ docker-compose down -v           # DELETES DATABASE!
❌ docker volume rm payment_postgres_data  # DELETES DATA!
❌ rm -rf env/                      # DELETES ENVIRONMENT!
```

## Safe Commands

```bash
✅ docker-compose down              # Safe - just stops containers
✅ docker-compose up                # Restart with preserved data
✅ docker-compose restart           # Restart services
✅ ./env/bin/python migrate.py     # Migrate schema safely
```

## If You Need to Reset Database

**YOU MUST EXPLICITLY REQUEST THIS**

Required steps:

1. Export/backup existing data first
2. Get explicit user confirmation
3. Use migration tools, NOT volume deletion
4. Document the reset in git commit

## Database Backup

To backup database before any major changes:

```bash
docker-compose exec payment_db pg_dump -U postgres payment_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

To restore from backup:

```bash
docker-compose exec -T payment_db psql -U postgres payment_db < backup_YYYYMMDD_HHMMSS.sql
```

## Emergency Data Recovery

If data was accidentally deleted:

1. Check Docker Desktop for volume backups
2. Check git history for schema migration files
3. Contact system administrator for storage backups

---

**REMEMBER**: Data is precious. Always ask before destructive operations.
