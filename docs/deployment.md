# Deployment Guide

This guide explains how to deploy the Education Backend with database migrations.

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment to Vercel.

### Pipeline Stages

```mermaid
graph TD
    A[Push to Branch] --> B[Test]
    B --> C[Migration Check]
    C --> D{Branch?}
    D -->|bug_fix| E[Deploy to Staging]
    D -->|main| F[Deploy to Production]
    F --> G[Run Migrations]
    G --> H[Verify Migration]
```

### Environments

- **Staging**: `bug_fix` branch → Vercel preview deployment
- **Production**: `main` branch → Vercel production deployment + migrations

## Database Migrations

### Using the Migration Script

The `scripts/migrate.sh` script provides a comprehensive migration management tool:

```bash
# Check migration status
./scripts/migrate.sh status

# Check if migrations are needed
./scripts/migrate.sh check

# Apply all pending migrations
./scripts/migrate.sh apply

# Create database backup before migration
./scripts/migrate.sh backup

# Rollback last migration (in case of issues)
./scripts/migrate.sh rollback

# Generate new migration
./scripts/migrate.sh generate "Add new table"
```

### Environment Variables

Set these environment variables for migration operations:

```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
export MIGRATION_TOKEN="your-secure-token"  # For API endpoint auth
```

### Vercel Migration API

During deployment, migrations can be triggered via API:

```bash
# Check migration status
curl -X POST "https://your-app.vercel.app/api/migrate?action=status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Apply migrations
curl -X POST "https://your-app.vercel.app/api/migrate?action=apply" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Required Secrets

Add these secrets to your GitHub repository:

### Vercel Deployment
- `VERCEL_TOKEN`: Your Vercel API token
- `VERCEL_ORG_ID`: Your Vercel organization ID
- `VERCEL_PROJECT_ID`: Your Vercel project ID

### Database
- `DATABASE_URL`: Production database connection string

### Migration Security
- `MIGRATION_TOKEN`: Token for authorizing migration API calls

## Local Development

### Setting up the Database

1. **Install PostgreSQL** locally or use Docker:
```bash
docker run --name postgres-dev -e POSTGRES_PASSWORD=mypassword -d -p 5432:5432 postgres:15
```

2. **Set environment variables**:
```bash
export DATABASE_URL="postgresql://postgres:mypassword@localhost:5432/postgres"
```

3. **Run migrations**:
```bash
./scripts/migrate.sh apply
```

### Running Tests Locally

```bash
# Install dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src
```

## Deployment Checklist

### Pre-deployment
- [ ] All tests pass
- [ ] Migrations are generated and tested
- [ ] Environment variables are configured
- [ ] Secrets are set in GitHub

### Deployment Steps
1. **Merge to staging branch** (`bug_fix`):
   - Triggers staging deployment
   - No automatic migrations

2. **Merge to production** (`main`):
   - Triggers production deployment
   - Automatically runs migrations
   - Verifies migration success

### Post-deployment
- [ ] Verify application is running
- [ ] Check database migration status
- [ ] Monitor error logs
- [ ] Test critical functionality

## Troubleshooting

### Migration Issues

**Migration fails during deployment:**
```bash
# Check migration status
./scripts/migrate.sh status

# Check for issues
./scripts/migrate.sh check

# Manual rollback if needed
./scripts/migrate.sh rollback
```

**Database connection issues:**
- Verify `DATABASE_URL` format
- Check database server connectivity
- Ensure proper permissions

### Vercel Deployment Issues

**Build fails:**
- Check Vercel function logs
- Verify Python version compatibility
- Check dependency installation

**Migration API fails:**
- Verify `MIGRATION_TOKEN` is set
- Check Vercel function timeout (30s limit)
- Review Vercel function logs

## Security Considerations

- **Never commit database credentials** to version control
- **Use environment variables** for all sensitive configuration
- **Restrict migration API access** with proper authentication
- **Regular backup strategy** before migrations
- **Monitor migration logs** for anomalies

## Monitoring

After deployment, monitor:

- Application logs in Vercel dashboard
- Database performance metrics
- Migration execution times
- Error rates and patterns

## Rollback Strategy

If deployment fails:

1. **Application rollback**: Vercel can rollback to previous deployment
2. **Database rollback**: Use `./scripts/migrate.sh rollback`
3. **Data recovery**: Restore from backup if needed

## Support

For deployment issues:
1. Check Vercel function logs
2. Review GitHub Actions logs
3. Verify environment configuration
4. Test migrations locally first