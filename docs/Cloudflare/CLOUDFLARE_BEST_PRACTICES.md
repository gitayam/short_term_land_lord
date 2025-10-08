# Cloudflare Platform Best Practices
**Short Term Land Lord Property Management System**

## General Cloudflare Principles

### Edge-First Architecture
- Deploy logic close to users
- Minimize round trips to origin
- Use edge caching aggressively
- Keep Workers lightweight

### Data Storage Strategy
- **D1**: Relational data (properties, users, bookings)
- **KV**: Cache, sessions, configuration (high read, low write)
- **R2**: Files, images, videos, documents
- **Durable Objects**: Real-time features, coordination

## D1 Database Best Practices

### Schema Design
```sql
-- Use appropriate data types
CREATE TABLE properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price_per_night REAL NOT NULL,  -- Use REAL for decimals
    bedrooms INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1,    -- SQLite uses INTEGER for booleans (0/1)
    amenities TEXT,                  -- Store JSON for complex data
    created_at TEXT DEFAULT (datetime('now'))  -- ISO 8601 format
);

-- Create indexes for frequently queried columns
CREATE INDEX idx_properties_active ON properties(is_active);
CREATE INDEX idx_properties_price ON properties(price_per_night);
CREATE INDEX idx_properties_created ON properties(created_at);
```

### Query Optimization
```typescript
// ✅ Use prepared statements (prevents SQL injection)
const property = await env.DB.prepare(
  'SELECT * FROM properties WHERE id = ?'
).bind(propertyId).first()

// ✅ Use indexes in WHERE clauses
const activeProperties = await env.DB.prepare(
  'SELECT * FROM properties WHERE is_active = 1 ORDER BY created_at DESC'
).all()

// ✅ Limit results for large datasets
const recentBookings = await env.DB.prepare(
  'SELECT * FROM bookings ORDER BY created_at DESC LIMIT 50'
).all()

// ❌ Avoid SELECT * in production
// ✅ Select only needed columns
const propertyNames = await env.DB.prepare(
  'SELECT id, name FROM properties'
).all()
```

### Migrations
```bash
# Always add to wrangler.toml first
[[d1_databases]]
binding = "DB"
database_name = "short-term-landlord-db"
database_id = "your-database-id"

# Run migrations with --remote for production
npx wrangler d1 execute short-term-landlord-db --file=./migrations/001_initial.sql --remote

# Verify migration
npx wrangler d1 execute short-term-landlord-db --command="SELECT COUNT(*) FROM properties" --remote
```

## KV Storage Best Practices

### Use Cases
- ✅ Session storage
- ✅ User preferences
- ✅ API response caching
- ✅ Rate limiting counters
- ✅ Feature flags
- ❌ Frequently updated data (use D1)
- ❌ Relational queries (use D1)

### Key Naming Conventions
```typescript
// Use namespace prefixes
const cacheKey = `cache:dashboard:${userId}`
const sessionKey = `session:${token}`
const rateLimitKey = `ratelimit:${ip}:${endpoint}`
const configKey = `config:feature:${featureName}`

// Store with appropriate TTL
await env.KV.put(cacheKey, JSON.stringify(data), {
  expirationTtl: 600  // 10 minutes for dashboard cache
})

await env.KV.put(sessionKey, JSON.stringify(session), {
  expirationTtl: 86400  // 24 hours for sessions
})
```

### Caching Pattern
```typescript
async function getCachedPropertyStats(propertyId: number, env: any) {
  const cacheKey = `cache:property_stats:${propertyId}`

  // Try cache first
  const cached = await env.KV.get(cacheKey, { type: 'json' })
  if (cached) {
    console.log('Cache hit for property stats')
    return cached
  }

  // Cache miss - query database
  console.log('Cache miss - querying database')
  const stats = await env.DB.prepare(`
    SELECT
      COUNT(*) as total_bookings,
      AVG(rating) as avg_rating,
      SUM(revenue) as total_revenue
    FROM bookings
    WHERE property_id = ?
  `).bind(propertyId).first()

  // Store in cache (30 minutes)
  await env.KV.put(cacheKey, JSON.stringify(stats), {
    expirationTtl: 1800
  })

  return stats
}
```

### Cache Invalidation
```typescript
// When property is updated, invalidate related caches
async function updateProperty(propertyId: number, updates: any, env: any) {
  // Update database
  await env.DB.prepare(
    'UPDATE properties SET name = ?, price_per_night = ? WHERE id = ?'
  ).bind(updates.name, updates.price, propertyId).run()

  // Invalidate caches
  await env.KV.delete(`cache:property:${propertyId}`)
  await env.KV.delete(`cache:property_stats:${propertyId}`)
  await env.KV.delete(`cache:dashboard:${updates.ownerId}`)

  console.log(`Invalidated caches for property ${propertyId}`)
}
```

## R2 Storage Best Practices

### File Organization
```typescript
// Organize by type and date
const fileKey = `properties/${propertyId}/photos/${Date.now()}-${filename}`
const documentKey = `documents/${userId}/${year}/${month}/${filename}`
const backupKey = `backups/${date}/${tableName}.json`

// Upload with metadata
await env.BUCKET.put(fileKey, fileStream, {
  httpMetadata: {
    contentType: file.type,
    cacheControl: 'public, max-age=31536000'  // 1 year for immutable files
  },
  customMetadata: {
    uploadedBy: userId.toString(),
    propertyId: propertyId.toString(),
    originalName: file.name
  }
})
```

### Direct Uploads from Frontend
```typescript
// Generate presigned URL for client-side upload
export async function onRequest(context: any) {
  const { request, env } = context
  const { filename, contentType } = await request.json()

  const key = `uploads/${Date.now()}-${filename}`

  // Create presigned URL (valid for 1 hour)
  const uploadUrl = await env.BUCKET.createPresignedUrl(key, {
    expiresIn: 3600,
    method: 'PUT',
    httpMetadata: {
      contentType
    }
  })

  return new Response(JSON.stringify({ uploadUrl, key }), {
    headers: { 'Content-Type': 'application/json' }
  })
}
```

### File Access Patterns
```typescript
// Public read access
const publicUrl = `https://files.yourdomain.com/${fileKey}`

// Authenticated access
export async function onRequest(context: any) {
  const { request, env } = context
  const url = new URL(request.url)
  const key = url.pathname.substring(1)  // Remove leading /

  // Verify user has access
  const userId = await getUserFromRequest(request, env)
  if (!await hasAccessToFile(userId, key, env.DB)) {
    return new Response('Forbidden', { status: 403 })
  }

  // Get file from R2
  const object = await env.BUCKET.get(key)
  if (!object) {
    return new Response('Not found', { status: 404 })
  }

  // Return file with proper headers
  return new Response(object.body, {
    headers: {
      'Content-Type': object.httpMetadata?.contentType || 'application/octet-stream',
      'Cache-Control': 'private, max-age=3600',
      'Content-Disposition': `inline; filename="${object.key.split('/').pop()}"`
    }
  })
}
```

## Workers Performance

### Minimize Cold Starts
```typescript
// ✅ Import only what you need
import { verify } from '@tsndr/cloudflare-worker-jwt'

// ❌ Avoid importing entire libraries
// import * as everything from 'massive-library'

// ✅ Use lightweight alternatives
// Instead of: import bcrypt from 'bcryptjs'
// Use: built-in Web Crypto API
```

### Efficient Error Handling
```typescript
export async function onRequest(context: any) {
  const { request, env } = context

  try {
    // Your logic here
    const data = await processRequest(request, env)

    return new Response(JSON.stringify(data), {
      headers: { 'Content-Type': 'application/json' }
    })
  } catch (error: any) {
    // Log error (visible in wrangler tail)
    console.error('Request failed:', {
      error: error.message,
      stack: error.stack,
      url: request.url,
      method: request.method
    })

    // Return user-friendly error
    return new Response(JSON.stringify({
      error: 'Internal server error',
      message: process.env.NODE_ENV === 'development' ? error.message : undefined
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
}
```

### Rate Limiting
```typescript
async function checkRateLimit(ip: string, endpoint: string, env: any): Promise<boolean> {
  const key = `ratelimit:${ip}:${endpoint}`
  const limit = 100  // requests
  const window = 3600  // 1 hour in seconds

  // Get current count
  const countStr = await env.KV.get(key)
  const count = countStr ? parseInt(countStr) : 0

  if (count >= limit) {
    return false  // Rate limit exceeded
  }

  // Increment counter
  await env.KV.put(key, (count + 1).toString(), {
    expirationTtl: window
  })

  return true  // Within rate limit
}

// Use in Worker
export async function onRequest(context: any) {
  const { request, env } = context
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown'
  const endpoint = new URL(request.url).pathname

  if (!await checkRateLimit(ip, endpoint, env)) {
    return new Response('Rate limit exceeded', {
      status: 429,
      headers: {
        'Retry-After': '3600'
      }
    })
  }

  // Continue with request...
}
```

## Security Best Practices

### Input Validation
```typescript
// Validate and sanitize all inputs
function validatePropertyInput(data: any): { valid: boolean; errors: string[] } {
  const errors: string[] = []

  if (!data.name || typeof data.name !== 'string' || data.name.length > 100) {
    errors.push('Invalid property name')
  }

  if (!data.price || typeof data.price !== 'number' || data.price <= 0) {
    errors.push('Invalid price')
  }

  if (data.bedrooms && (!Number.isInteger(data.bedrooms) || data.bedrooms < 0)) {
    errors.push('Invalid bedrooms count')
  }

  return {
    valid: errors.length === 0,
    errors
  }
}
```

### Secrets Management
```bash
# Never commit secrets to git
# Store in Cloudflare dashboard

# Set secret
npx wrangler pages secret put DATABASE_URL --project-name short-term-landlord
npx wrangler pages secret put JWT_SECRET --project-name short-term-landlord

# Access in Worker
export async function onRequest(context: any) {
  const { env } = context
  const jwtSecret = env.JWT_SECRET
  const dbUrl = env.DATABASE_URL
}
```

### CORS Configuration
```typescript
const corsHeaders = {
  'Access-Control-Allow-Origin': 'https://yourdomain.com',  // Specific domain, not *
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '86400',  // 24 hours
}

// Handle OPTIONS preflight
if (request.method === 'OPTIONS') {
  return new Response(null, {
    status: 204,
    headers: corsHeaders
  })
}
```

## Monitoring & Debugging

### Structured Logging
```typescript
// Use structured logging for better searchability
console.log(JSON.stringify({
  level: 'info',
  message: 'Property created',
  propertyId: property.id,
  userId: user.id,
  timestamp: new Date().toISOString()
}))

console.error(JSON.stringify({
  level: 'error',
  message: 'Database query failed',
  error: error.message,
  stack: error.stack,
  query: 'SELECT * FROM properties',
  timestamp: new Date().toISOString()
}))
```

### Tail Logs
```bash
# Tail production logs in real-time
npx wrangler pages deployment tail --project-name short-term-landlord --format pretty

# Filter logs
npx wrangler pages deployment tail --project-name short-term-landlord | grep ERROR
```

### Analytics
```typescript
// Track custom metrics
env.ANALYTICS?.writeDataPoint({
  blobs: ['property_created', userId],
  doubles: [price],
  indexes: [propertyId]
})
```

## Cost Optimization

### Reduce Worker Invocations
- Cache static assets on Pages (free)
- Use KV for read-heavy data
- Batch database operations
- Implement client-side caching

### Optimize D1 Usage
- Use indexes on WHERE clauses
- Limit query results
- Cache expensive queries in KV
- Use batch operations for multiple writes

### R2 Optimization
- Compress files before upload
- Use appropriate cache headers
- Implement lifecycle policies
- Delete unused files

## Common Pitfalls

### ❌ Don't
- Store secrets in code or git
- Use SELECT * in production queries
- Forget to add indexes to D1
- Cache indefinitely (always use TTL)
- Use KV for frequently changing data
- Ignore rate limiting
- Return sensitive data in error messages

### ✅ Do
- Use environment variables for secrets
- Select only needed columns
- Add indexes for WHERE/ORDER BY columns
- Set appropriate cache TTLs
- Use D1 for relational/transactional data
- Implement rate limiting
- Log errors, return generic messages to users

## Next Steps

1. Review [FLASK_TO_CLOUDFLARE_MIGRATION.md](./FLASK_TO_CLOUDFLARE_MIGRATION.md) for migration guide
2. Review [lessonslearned-gpt-cloudflare-workers.md](./lessonslearned-gpt-cloudflare-workers.md) for AI integration
3. Set up Cloudflare account and test project
4. Prototype one API endpoint as POC
5. Plan and execute phased migration

---

*Last Updated: 2025-10-08*
*Project: Short Term Land Lord*
*Platform: Cloudflare Workers + Pages + D1 + KV + R2*
