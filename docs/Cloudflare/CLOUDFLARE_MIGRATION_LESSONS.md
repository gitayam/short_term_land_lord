# Cloudflare Migration Lessons Learned
**Short Term Land Lord Property Management System**

## Migration Status
Planning phase for migration from Google App Engine to Cloudflare infrastructure.

## Migration Overview
Migration of Short Term Land Lord property management system from Google App Engine to Cloudflare's edge platform for improved performance and reduced costs.

## Technical Stack Changes
- **From:** Flask on Google App Engine with PostgreSQL/SQLite and Redis
- **To:** Cloudflare Workers (TypeScript) + Pages with D1, KV, and R2
- **Migration Path:** Hybrid approach with phased rollout

## Critical Migration Challenges & Solutions

### 1. Database Schema Translation (HIGH PRIORITY)
**Challenge:** Converting SQLAlchemy ORM models to D1 SQL schema

**Considerations:**
- Flask uses SQLAlchemy ORM with relationships and lazy loading
- D1 uses raw SQL with manual relationship management
- Need to preserve foreign keys and indexes
- Calendar events, properties, tasks, users all interconnected

**Approach:**
1. Export schema from SQLAlchemy as pure SQL
2. Adapt to SQLite syntax (D1 compatible)
3. Add explicit indexes for performance
4. Test with sample data before full migration

**Key Tables to Migrate:**
- `properties` - Core property data
- `users` - Property owners, cleaners, maintenance staff, guests
- `tasks` - Cleaning and maintenance assignments
- `calendar_events` - Bookings from Airbnb, VRBO, etc.
- `cleaning_sessions` - Tracking cleaner work
- `inventory_items` - Property supplies

### 2. Authentication System Migration
**Challenge:** Converting Flask-Login session-based auth to stateless JWT

**Current State:**
- Flask-Login with server-side sessions
- Redis session storage
- Role-based access control (owner, cleaner, maintenance, guest)

**Migration Path:**
1. Implement JWT authentication in Workers
2. Store sessions in KV with TTL
3. Maintain role-based access patterns
4. Keep backward compatibility during transition

**Solution Pattern:**
```typescript
// JWT-based auth with KV session storage
async function authenticateUser(request: Request, env: any) {
  const token = request.headers.get('Authorization')?.replace('Bearer ', '')
  if (!token) throw new Error('Unauthorized')

  const session = await env.KV.get(`session:${token}`, { type: 'json' })
  if (!session) throw new Error('Session expired')

  return session.user
}
```

### 3. Flask Routes to Workers Functions Migration
**Challenge:** Converting Flask Blueprint routes to Cloudflare Pages Functions

**Flask Pattern (Before):**
```python
@app.route('/api/properties/<int:property_id>', methods=['GET'])
@login_required
def get_property(property_id):
    property = Property.query.get_or_404(property_id)
    return jsonify(property.to_dict())
```

**Workers Pattern (After):**
```typescript
// functions/api/properties/[id].ts
export async function onRequest(context: any) {
  const { params, env, request } = context
  const user = await authenticateUser(request, env)

  const property = await env.DB.prepare(
    'SELECT * FROM properties WHERE id = ? AND owner_id = ?'
  ).bind(params.id, user.id).first()

  if (!property) {
    return new Response('Not found', { status: 404 })
  }

  return new Response(JSON.stringify(property), {
    headers: { 'Content-Type': 'application/json' }
  })
}
```

### 4. Calendar Integration Challenges
**Challenge:** Preserving iCal sync functionality with Airbnb, VRBO

**Considerations:**
- Current system uses background tasks to fetch iCal feeds
- Workers are stateless and event-driven
- Need scheduled jobs for periodic calendar sync

**Solution:** Use Cloudflare Cron Triggers
```toml
# wrangler.toml
[triggers]
crons = ["0 */6 * * *"]  # Sync calendars every 6 hours
```

### 5. File Upload Migration (Photos, Videos)
**Challenge:** Moving from local file system / GCS to R2

**Current State:**
- Cleaning session photos/videos stored in Google Cloud Storage
- Property images stored locally or in GCS

**Migration Strategy:**
1. Upload existing files to R2 bucket
2. Update file references in database
3. Implement presigned URL generation for uploads
4. Update frontend to use R2 URLs

## Expected Performance Improvements
- **Database Queries**: Sub-millisecond reads at edge (vs 10-50ms to PostgreSQL)
- **Caching**: KV reads < 100ms globally (vs Redis latency)
- **API Responses**: Workers run at edge, closer to users
- **Static Assets**: Cloudflare CDN caching worldwide
- **Cost Reduction**: 40-60% savings on infrastructure costs

## Migration Tools & Scripts
1. **schema-export.py**: Export SQLAlchemy schema as SQL
2. **data-migration.py**: Export/import data to D1
3. **test-endpoints.sh**: Verify API compatibility
4. **performance-compare.py**: Benchmark old vs new stack

## Migration Recommendations

### Pre-Migration Phase
- [ ] Audit all Flask routes and database queries
- [ ] Document authentication and authorization patterns
- [ ] Map Redis cache keys and usage
- [ ] Inventory file storage (photos, videos, documents)
- [ ] Create test dataset for validation
- [ ] Set up Cloudflare account and test environment

### During Migration
- [ ] Start with read-only API endpoints
- [ ] Migrate database schema to D1
- [ ] Test authentication with subset of users
- [ ] Implement caching in KV
- [ ] Migrate file storage to R2
- [ ] Run parallel deployments for comparison

### Post-Migration
- [ ] Performance benchmarking (response times, DB queries)
- [ ] Monitor error rates and logs
- [ ] Validate calendar sync functionality
- [ ] Test all user roles (owner, cleaner, maintenance, guest)
- [ ] Update documentation
- [ ] Train team on new deployment workflow

## Migration Status
### Phase 1: Planning (Current)
- [x] Review current architecture
- [x] Document migration strategy
- [ ] Create proof-of-concept Workers endpoint
- [ ] Test D1 database with sample data

### Phase 2: Infrastructure Setup
- [ ] Set up D1 database
- [ ] Configure KV namespaces
- [ ] Create R2 bucket
- [ ] Set up Wrangler configuration

### Phase 3: API Migration
- [ ] Convert property management endpoints
- [ ] Migrate task management endpoints
- [ ] Implement calendar sync Workers
- [ ] Convert authentication system

### Phase 4: Data Migration
- [ ] Export production data
- [ ] Import to D1
- [ ] Migrate files to R2
- [ ] Verify data integrity

### Phase 5: Frontend Updates
- [ ] Update API endpoints
- [ ] Test all user flows
- [ ] Performance optimization

### Phase 6: Go-Live
- [ ] Set up custom domain
- [ ] Configure DNS
- [ ] Monitor production metrics
- [ ] Gradual traffic shift

## Key Takeaways
- **Start Small**: Migrate one endpoint at a time, validate before moving forward
- **Database Schema First**: Get D1 schema right before data migration
- **Authentication is Critical**: Test auth thoroughly with all user roles
- **Calendar Sync Complexity**: Background jobs need Cron Triggers
- **File Migration Takes Time**: Plan R2 migration carefully, verify all uploads
- **Cache Everything Possible**: Use KV aggressively to reduce D1 queries
- **Monitor Closely**: Set up logging and alerting from day one

## Flask to Cloudflare Best Practices
1. Export SQLAlchemy schema, adapt to pure SQL
2. Use prepared statements in D1 (like SQLAlchemy)
3. Implement JWT auth with KV sessions
4. Use Cron Triggers for scheduled tasks
5. Test role-based access control thoroughly
6. Keep Flask running in parallel during migration

## Resources
- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [D1 Database Docs](https://developers.cloudflare.com/d1/)
- [Flask to Workers Migration Guide](./FLASK_TO_CLOUDFLARE_MIGRATION.md)
- [Cloudflare Best Practices](./CLOUDFLARE_BEST_PRACTICES.md)