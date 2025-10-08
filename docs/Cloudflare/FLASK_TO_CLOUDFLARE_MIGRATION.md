# Flask to Cloudflare Migration Guide
**Short Term Land Lord Property Management System**

## Migration Overview

**Current Stack:**
- **Platform:** Google App Engine
- **Framework:** Flask (Python 3.9+)
- **Database:** SQLite (development) / PostgreSQL (production-ready)
- **Caching:** Redis
- **Frontend:** Jinja2 templates with Bootstrap 5

**Target Cloudflare Stack:**
- **Platform:** Cloudflare Workers (Python Workers)
- **Framework:** Hono or native Workers
- **Database:** Cloudflare D1 (SQLite-compatible)
- **Caching:** Cloudflare KV
- **File Storage:** Cloudflare R2
- **Frontend:** Static assets on Cloudflare Pages

## Why Migrate to Cloudflare?

### Benefits
- **Edge Computing:** Deploy globally, run at the edge near users
- **Cost Savings:** More predictable pricing than Google App Engine
- **Performance:** Sub-millisecond database queries with D1
- **Simplicity:** Integrated platform (Workers + Pages + D1 + KV + R2)
- **Scalability:** Auto-scales without configuration
- **Developer Experience:** Fast deployments, excellent CLI tools

### Challenges
- **Python Workers Limitation:** Limited Python support (consider Node.js/TypeScript rewrite)
- **Database Migration:** SQLAlchemy → D1 native queries
- **Stateless Architecture:** No filesystem storage (use R2)
- **Learning Curve:** New deployment patterns

## Migration Strategy

### Option 1: Python Workers (Limited)
Cloudflare has experimental Python Workers support, but it's limited:
- Restricted library support
- No SQLAlchemy
- Manual query building

**Verdict:** Not recommended for complex Flask apps

### Option 2: Hybrid Approach (Recommended)
- **API Layer:** Rewrite as Cloudflare Workers (TypeScript/JavaScript)
- **Database:** Migrate to Cloudflare D1
- **Frontend:** Serve static Jinja templates as HTML from Pages
- **File Storage:** Move uploads to R2
- **Caching:** Replace Redis with KV

### Option 3: Full Rewrite
- Complete rewrite to Next.js or Remix
- Modern React frontend
- Cloudflare Pages Functions for API
- Full Cloudflare stack integration

## Database Migration: PostgreSQL/SQLite → D1

### D1 Overview
- SQLite-compatible edge database
- Globally distributed
- Sub-millisecond reads at edge
- Strong consistency for writes

### Schema Migration

**Current SQLAlchemy Models → D1 SQL**

```sql
-- properties table
CREATE TABLE properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

-- users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- tasks table
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    assigned_to INTEGER,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL,
    due_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id)
);

-- calendar_events table
CREATE TABLE calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    guest_name TEXT,
    booking_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id)
);

-- cleaning_sessions table
CREATE TABLE cleaning_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    cleaner_id INTEGER NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    status TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (property_id) REFERENCES properties(id),
    FOREIGN KEY (cleaner_id) REFERENCES users(id)
);

-- Create indexes for performance
CREATE INDEX idx_properties_owner ON properties(owner_id);
CREATE INDEX idx_tasks_property ON tasks(property_id);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX idx_calendar_property ON calendar_events(property_id);
CREATE INDEX idx_calendar_dates ON calendar_events(start_date, end_date);
CREATE INDEX idx_cleaning_property ON cleaning_sessions(property_id);
CREATE INDEX idx_cleaning_cleaner ON cleaning_sessions(cleaner_id);
```

### D1 Setup Commands

```bash
# Create database
npx wrangler d1 create short-term-landlord-db

# Output will show database_id - save this!
# Add to wrangler.toml:
[[d1_databases]]
binding = "DB"
database_name = "short-term-landlord-db"
database_id = "your-database-id-here"

# Run migration
npx wrangler d1 execute short-term-landlord-db --file=./migrations/schema.sql --remote

# Verify
npx wrangler d1 execute short-term-landlord-db --command="SELECT name FROM sqlite_master WHERE type='table'" --remote
```

## API Migration: Flask Routes → Cloudflare Workers

### Flask → Workers Pattern

**Before (Flask):**
```python
from flask import Blueprint, jsonify, request
from app.models import Property

properties_bp = Blueprint('properties', __name__)

@properties_bp.route('/api/properties', methods=['GET'])
def get_properties():
    properties = Property.query.filter_by(owner_id=current_user.id).all()
    return jsonify([p.to_dict() for p in properties])

@properties_bp.route('/api/properties', methods=['POST'])
def create_property():
    data = request.json
    property = Property(**data)
    db.session.add(property)
    db.session.commit()
    return jsonify(property.to_dict()), 201
```

**After (Cloudflare Workers):**
```typescript
// functions/api/properties.ts
export async function onRequest(context: any) {
  const { request, env } = context

  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
    'Access-Control-Allow-Headers': 'Content-Type',
  }

  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders })
  }

  try {
    if (request.method === 'GET') {
      // Get user ID from auth header/session
      const userId = await getUserFromRequest(request, env)

      const properties = await env.DB.prepare(
        'SELECT * FROM properties WHERE owner_id = ?'
      ).bind(userId).all()

      return new Response(JSON.stringify(properties.results), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      })
    }

    if (request.method === 'POST') {
      const data = await request.json()
      const userId = await getUserFromRequest(request, env)

      const result = await env.DB.prepare(
        'INSERT INTO properties (name, address, description, owner_id) VALUES (?, ?, ?, ?)'
      ).bind(data.name, data.address, data.description, userId).run()

      // Get the created property
      const property = await env.DB.prepare(
        'SELECT * FROM properties WHERE id = ?'
      ).bind(result.meta.last_row_id).first()

      return new Response(JSON.stringify(property), {
        status: 201,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      })
    }

    return new Response('Method not allowed', { status: 405 })
  } catch (error: any) {
    console.error('Error:', error)
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    })
  }
}

async function getUserFromRequest(request: Request, env: any): Promise<number> {
  // Implement your auth logic here
  // Could use JWT, session tokens stored in KV, etc.
  const authHeader = request.headers.get('Authorization')
  // ... verify and return user ID
  return 1 // placeholder
}
```

## Caching: Redis → Cloudflare KV

### KV Overview
- Global key-value store
- Sub-100ms reads worldwide
- Eventually consistent
- Perfect for caching, sessions, configuration

### Migration Examples

**Before (Redis):**
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.cached(timeout=600, key_prefix='user_dashboard')
def get_user_dashboard(user_id):
    # Expensive query
    return dashboard_data
```

**After (KV):**
```typescript
// Cache user dashboard data
async function getUserDashboard(userId: number, env: any) {
  const cacheKey = `user_dashboard:${userId}`

  // Try to get from cache
  const cached = await env.KV.get(cacheKey, { type: 'json' })
  if (cached) return cached

  // Generate fresh data
  const dashboard = await generateDashboardData(userId, env.DB)

  // Store in cache (600 seconds = 10 minutes)
  await env.KV.put(cacheKey, JSON.stringify(dashboard), { expirationTtl: 600 })

  return dashboard
}
```

### KV Setup

```toml
# wrangler.toml
[[kv_namespaces]]
binding = "KV"
id = "your-kv-namespace-id"
```

```bash
# Create KV namespace
npx wrangler kv:namespace create "CACHE"

# List keys
npx wrangler kv:key list --binding=KV

# Get value
npx wrangler kv:key get "user_dashboard:1" --binding=KV

# Set value
npx wrangler kv:key put "config:test" "value" --binding=KV
```

## File Storage: Local Filesystem → R2

### R2 Overview
- S3-compatible object storage
- No egress fees
- Perfect for images, videos, PDFs
- Direct uploads from frontend

### Migration Examples

**Before (Local Storage):**
```python
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return jsonify({'url': f'/uploads/{filename}'})
```

**After (R2):**
```typescript
// functions/api/upload.ts
export async function onRequest(context: any) {
  const { request, env } = context

  if (request.method === 'POST') {
    const formData = await request.formData()
    const file = formData.get('file') as File

    if (!file) {
      return new Response('No file provided', { status: 400 })
    }

    // Generate unique filename
    const filename = `${Date.now()}-${file.name}`
    const key = `uploads/${filename}`

    // Upload to R2
    await env.BUCKET.put(key, file.stream(), {
      httpMetadata: {
        contentType: file.type
      }
    })

    // Return public URL
    const url = `https://files.yourdomain.com/${key}`
    return new Response(JSON.stringify({ url }), {
      headers: { 'Content-Type': 'application/json' }
    })
  }
}
```

### R2 Setup

```toml
# wrangler.toml
[[r2_buckets]]
binding = "BUCKET"
bucket_name = "short-term-landlord-files"
```

```bash
# Create bucket
npx wrangler r2 bucket create short-term-landlord-files

# List buckets
npx wrangler r2 bucket list

# Upload file (for testing)
npx wrangler r2 object put short-term-landlord-files/test.txt --file=./test.txt
```

## Frontend: Jinja2 → Static Pages

### Option 1: Keep Server-Side Rendering
Use Cloudflare Pages with a framework like:
- Remix (React with SSR)
- SvelteKit
- Astro

### Option 2: Convert to SPA
- React + Vite
- Static HTML + vanilla JS
- Serve from Cloudflare Pages

### Option 3: Hybrid (Recommended)
- Static pages on Cloudflare Pages
- API calls to Workers
- Client-side rendering for dynamic content

## Authentication Migration

### Flask-Login → JWT with KV Sessions

```typescript
// functions/api/auth/login.ts
import * as bcrypt from 'bcryptjs'
import * as jwt from '@tsndr/cloudflare-worker-jwt'

export async function onRequest(context: any) {
  const { request, env } = context

  if (request.method === 'POST') {
    const { email, password } = await request.json()

    // Get user from database
    const user = await env.DB.prepare(
      'SELECT * FROM users WHERE email = ?'
    ).bind(email).first()

    if (!user || !await bcrypt.compare(password, user.password_hash)) {
      return new Response('Invalid credentials', { status: 401 })
    }

    // Create JWT
    const token = await jwt.sign({
      sub: user.id,
      email: user.email,
      role: user.role,
      exp: Math.floor(Date.now() / 1000) + (60 * 60 * 24) // 24 hours
    }, env.JWT_SECRET)

    // Store session in KV
    await env.KV.put(`session:${token}`, JSON.stringify(user), {
      expirationTtl: 86400 // 24 hours
    })

    return new Response(JSON.stringify({ token, user }), {
      headers: { 'Content-Type': 'application/json' }
    })
  }
}

// Middleware to verify token
async function requireAuth(request: Request, env: any) {
  const authHeader = request.headers.get('Authorization')
  if (!authHeader?.startsWith('Bearer ')) {
    throw new Error('Unauthorized')
  }

  const token = authHeader.substring(7)

  // Verify JWT
  const isValid = await jwt.verify(token, env.JWT_SECRET)
  if (!isValid) {
    throw new Error('Invalid token')
  }

  // Check session in KV
  const session = await env.KV.get(`session:${token}`)
  if (!session) {
    throw new Error('Session expired')
  }

  const payload = jwt.decode(token)
  return payload.payload
}
```

## Deployment Workflow

### Development
```bash
# Install Wrangler
npm install -g wrangler

# Login to Cloudflare
npx wrangler login

# Create project structure
mkdir -p functions/api
mkdir -p public
mkdir -p migrations

# Start local development
npx wrangler pages dev public --compatibility-date=2024-09-21
```

### Production Deployment
```bash
# Build frontend (if applicable)
npm run build

# Deploy to Cloudflare Pages
npx wrangler pages deploy public --project-name=short-term-landlord

# Deploy with specific branch
npx wrangler pages deploy public --project-name=short-term-landlord --branch=main
```

## Migration Checklist

### Pre-Migration
- [ ] Audit current Flask routes and endpoints
- [ ] Document all database queries and models
- [ ] Identify file upload/storage usage
- [ ] Map Redis cache keys and TTLs
- [ ] Review authentication/session management
- [ ] List all environment variables and secrets

### Database Migration
- [ ] Create D1 database
- [ ] Write migration SQL scripts
- [ ] Create indexes for performance
- [ ] Test queries with sample data
- [ ] Plan data migration strategy (export/import)

### API Migration
- [ ] Rewrite Flask routes as Workers functions
- [ ] Implement authentication middleware
- [ ] Add CORS headers
- [ ] Test all endpoints locally
- [ ] Add error handling and logging

### Caching Migration
- [ ] Create KV namespace
- [ ] Migrate Redis cache keys to KV
- [ ] Update cache TTLs
- [ ] Test cache invalidation

### File Storage Migration
- [ ] Create R2 bucket
- [ ] Migrate existing files to R2
- [ ] Update upload endpoints
- [ ] Test file access and permissions
- [ ] Set up CDN/public access if needed

### Frontend Migration
- [ ] Choose frontend strategy (SSR/SPA/Hybrid)
- [ ] Convert templates or build new frontend
- [ ] Update API calls to Workers endpoints
- [ ] Test all user flows
- [ ] Optimize bundle size

### Security
- [ ] Store secrets in Cloudflare dashboard
- [ ] Implement rate limiting
- [ ] Add input validation
- [ ] Set up CORS properly
- [ ] Enable security headers

### Testing
- [ ] Test all API endpoints
- [ ] Verify authentication flows
- [ ] Test file uploads/downloads
- [ ] Check caching behavior
- [ ] Load test with production-like data

### Go-Live
- [ ] Set up custom domain
- [ ] Configure DNS
- [ ] Test production deployment
- [ ] Monitor logs and errors
- [ ] Set up alerting

## Cost Comparison

### Google App Engine (Current)
- Instance hours: Variable
- Database: PostgreSQL pricing
- Redis: Separate service
- Storage: Google Cloud Storage

### Cloudflare (Target)
- Workers: $5/month for 10M requests
- D1: Free tier (5GB storage, 5M reads/day)
- KV: $0.50/GB storage + $0.50/1M reads
- R2: $0.015/GB storage (no egress fees!)
- Pages: Free for unlimited sites

**Estimated Savings:** 40-60% depending on traffic

## Performance Improvements

- **Database:** Sub-ms reads at edge (vs 10-50ms to PostgreSQL)
- **Caching:** KV reads < 100ms globally (vs Redis latency)
- **API:** Workers run at edge, closer to users
- **Static Assets:** Cloudflare CDN caching worldwide

## Support Resources

- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [D1 Database Docs](https://developers.cloudflare.com/d1/)
- [KV Storage Docs](https://developers.cloudflare.com/workers/runtime-apis/kv/)
- [R2 Storage Docs](https://developers.cloudflare.com/r2/)
- [Cloudflare Pages Docs](https://developers.cloudflare.com/pages/)
- [Wrangler CLI Docs](https://developers.cloudflare.com/workers/wrangler/)

## Next Steps

1. Review this migration guide
2. Set up Cloudflare account
3. Create test project with D1 + Workers
4. Migrate one API endpoint as POC
5. Test and validate approach
6. Plan phased migration
7. Execute migration
8. Monitor and optimize

---

*Last Updated: 2025-10-08*
*Project: Short Term Land Lord*
*Target Platform: Cloudflare Workers + Pages + D1 + KV + R2*
