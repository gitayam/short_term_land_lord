# Cloudflare Deployment Guide
**Short Term Land Lord - Property Management System**

## 🌐 Live Deployment

**Production URL**: https://short-term-landlord.pages.dev
**Dashboard**: https://dash.cloudflare.com/04eac09ae835290383903273f68c79b0/pages/view/short-term-landlord

## Prerequisites

- Wrangler CLI installed and logged in
- Cloudflare account with Pages access
- Node.js 18+ installed

## Quick Deploy

```bash
# Build and deploy
npm run deploy

# Or manually
npm run build
wrangler pages deploy dist --project-name=short-term-landlord
```

## Production Configuration

### 1. Configure Service Bindings

The application requires D1, KV, and R2 bindings. Configure these in the Cloudflare Dashboard:

**Navigate to**: Pages > short-term-landlord > Settings > Functions

**Add the following bindings**:

#### D1 Database
- Variable name: `DB`
- D1 database: `short-term-landlord-db`
- Database ID: `fb1bde66-9837-4358-8c71-19be2a88cfee`

#### KV Namespace
- Variable name: `KV`
- KV namespace: Short Term Landlord Sessions
- Namespace ID: `48afc9fe53a3425b8757e9dc526c359e`

#### R2 Bucket
- Variable name: `BUCKET`
- R2 bucket: `short-term-landlord-files`

### 2. Set Environment Variables

**Navigate to**: Pages > short-term-landlord > Settings > Environment Variables

**Production variables**:
```
ENVIRONMENT=production
FRONTEND_URL=https://short-term-landlord.pages.dev
EMAIL_PROVIDER=mailgun
EMAIL_FROM=noreply@yourdomain.com
```

### 3. Configure Secrets

Use wrangler to set sensitive secrets:

```bash
# JWT Secret (generate with: openssl rand -base64 32)
wrangler pages secret put JWT_SECRET --project-name=short-term-landlord
# Paste your secret when prompted

# Mailgun Configuration (if using Mailgun)
wrangler pages secret put MAILGUN_API_KEY --project-name=short-term-landlord
wrangler pages secret put MAILGUN_DOMAIN --project-name=short-term-landlord

# OR SendGrid (if using SendGrid)
wrangler pages secret put SENDGRID_API_KEY --project-name=short-term-landlord
```

List all secrets:
```bash
wrangler pages secret list --project-name=short-term-landlord
```

### 4. Verify Database Migration

Ensure the D1 database has the latest schema:

```bash
# Run remote migration
npm run db:migrate

# Verify tables exist
npm run db:list-tables
```

### 5. Test the Deployment

Visit https://short-term-landlord.pages.dev and verify:

- [ ] Login page loads
- [ ] Registration works
- [ ] Dashboard loads after login
- [ ] API endpoints respond (check browser console)
- [ ] Authentication persists across page refreshes

## Development Workflow

### Local Development

```bash
# Start frontend dev server (port 5173)
npm run dev

# In another terminal, start backend/functions
npm run dev:wrangler

# Or run both after building
npm run dev:full
```

### Making Changes

```bash
# 1. Make your changes to src/ or functions/
# 2. Test locally
npm run dev

# 3. Build and test production build
npm run build
npm run preview

# 4. Deploy to Cloudflare
npm run deploy
```

### Branch Strategy

- `main` - Stable production code
- `cloudflare-migration` - Active migration branch (currently deployed)
- Feature branches as needed

## Monitoring & Logs

### View Deployment Logs

```bash
# List recent deployments
wrangler pages deployment list --project-name=short-term-landlord

# View logs for latest deployment
npm run logs

# Or specific deployment
wrangler pages deployment tail <deployment-id>
```

### Dashboard Monitoring

**Analytics**: https://dash.cloudflare.com/04eac09ae835290383903273f68c79b0/pages/view/short-term-landlord/analytics

**Real-time Logs**: https://dash.cloudflare.com/04eac09ae835290383903273f68c79b0/pages/view/short-term-landlord/logs

## Troubleshooting

### Deployment Fails

```bash
# Check build locally first
npm run build

# Ensure functions compile
tsc --noEmit

# Check for uncommitted changes
git status
```

### API Errors in Production

1. Check environment variables are set correctly
2. Verify service bindings (D1, KV, R2) are configured
3. Check function logs in dashboard
4. Verify database migration ran successfully

### Authentication Not Working

1. Ensure `JWT_SECRET` is set
2. Verify `FRONTEND_URL` matches your domain
3. Check browser console for CORS errors
4. Verify KV namespace is bound correctly

## Rollback

If needed, rollback to a previous deployment:

```bash
# List deployments
wrangler pages deployment list --project-name=short-term-landlord

# Promote a specific deployment to production
wrangler pages deployment promote <deployment-id> --project-name=short-term-landlord
```

## Custom Domain Setup

1. Go to: Pages > short-term-landlord > Custom domains
2. Click "Set up a custom domain"
3. Enter your domain (e.g., `app.yourdomain.com`)
4. Add the provided DNS records to your domain registrar
5. Wait for DNS propagation (~24 hours max)

## Performance Optimization

### Caching Strategy

The application uses multiple caching layers:

1. **CDN Edge Cache**: Static assets (HTML, CSS, JS)
2. **KV Cache**: Session data, calendar events, file URLs
3. **Browser Cache**: API responses, images

### Cache Invalidation

```bash
# Deploy new version (invalidates all caches)
npm run deploy

# Or purge cache manually in dashboard
# Pages > short-term-landlord > Cache > Purge Cache
```

## Security Checklist

- [ ] JWT_SECRET is set and unique
- [ ] Email provider credentials are set as secrets
- [ ] FRONTEND_URL uses HTTPS in production
- [ ] D1 database is only accessible via Workers
- [ ] R2 bucket has proper access controls
- [ ] CORS is configured correctly for production domain
- [ ] Rate limiting is enabled (future enhancement)

## Support & Resources

- **Cloudflare Pages Docs**: https://developers.cloudflare.com/pages/
- **D1 Documentation**: https://developers.cloudflare.com/d1/
- **KV Documentation**: https://developers.cloudflare.com/kv/
- **R2 Documentation**: https://developers.cloudflare.com/r2/
- **Wrangler CLI**: https://developers.cloudflare.com/workers/wrangler/

## Next Steps

1. Configure production environment variables
2. Set up email provider (Mailgun or SendGrid)
3. Test all features in production
4. Set up custom domain (optional)
5. Configure monitoring and alerts
6. Plan data migration from Flask app
