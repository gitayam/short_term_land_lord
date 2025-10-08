# Cloudflare Migration Roadmap
**Short Term Land Lord - Flask to Cloudflare Workers Migration**

## Overview
This roadmap tracks the complete migration from Google App Engine (Flask + PostgreSQL/SQLite) to Cloudflare Workers + Pages + D1 + KV + R2.

**Last Updated:** October 8, 2025
**Current Phase:** Phase 1 Complete, Phase 2 In Progress

---

## Phase 1: Infrastructure Foundation ✅ COMPLETED

**Timeline:** October 8, 2025
**Status:** ✅ **COMPLETE**

### Completed Tasks
- [x] Create `cloudflare-migration` git branch
- [x] Set up Cloudflare account and login wrangler
- [x] Create D1 database: `short-term-landlord-db`
- [x] Set up KV namespace for caching/sessions
- [x] Create R2 bucket for file storage
- [x] Configure `wrangler.toml` with all bindings
- [x] Convert SQLAlchemy models to D1 SQL schema
- [x] Create and execute initial migration (15 tables)
- [x] Set up TypeScript configuration
- [x] Create package.json with helpful scripts
- [x] Build basic API middleware (CORS, logging)
- [x] Create health check endpoint
- [x] Implement authentication (login endpoint)
- [x] Create properties CRUD endpoints
- [x] Create tasks endpoints
- [x] Update all Cloudflare documentation
- [x] Create MIGRATION_PROGRESS.md tracker
- [x] Commit initial setup to git

### Infrastructure Details
```
D1 Database ID: fb1bde66-9837-4358-8c71-19be2a88cfee
KV Namespace ID: 48afc9fe53a3425b8757e9dc526c359e
R2 Bucket: short-term-landlord-files
Region: ENAM (Eastern North America)
```

---

## Phase 2: Core API Development 🚧 IN PROGRESS

**Timeline:** October 8-15, 2025
**Status:** 🚧 **40% COMPLETE**

### Priority 1: Authentication & Security (Week 1)
- [ ] Implement bcrypt password hashing
  - [ ] Install/configure bcrypt for Workers
  - [ ] Update login endpoint with password verification
  - [ ] Add password strength validation
- [ ] Implement JWT token signing
  - [ ] Install @tsndr/cloudflare-worker-jwt
  - [ ] Sign tokens with secret from environment
  - [ ] Add token expiration (24h access, 7d refresh)
- [ ] Add authentication middleware
  - [ ] Create `requireAuth` middleware
  - [ ] Extract user from JWT token
  - [ ] Validate session in KV
- [ ] Complete authentication endpoints
  - [ ] POST `/api/auth/register` - New user registration
  - [ ] POST `/api/auth/logout` - Invalidate session
  - [ ] POST `/api/auth/refresh` - Refresh access token
  - [ ] POST `/api/auth/verify-email` - Email verification
  - [ ] POST `/api/auth/forgot-password` - Password reset request
  - [ ] POST `/api/auth/reset-password` - Password reset completion

### Priority 2: Property Management API (Week 1-2)
- [ ] Enhance property endpoints
  - [ ] Add property image upload to R2
  - [ ] GET `/api/properties/[id]/images` - List property images
  - [ ] POST `/api/properties/[id]/images` - Upload image
  - [ ] DELETE `/api/properties/[id]/images/[imageId]` - Delete image
  - [ ] Add property search/filtering
  - [ ] Add pagination to property list
- [ ] Property access management
  - [ ] POST `/api/properties/[id]/access/guest` - Generate guest access token
  - [ ] POST `/api/properties/[id]/access/worker` - Generate worker calendar token
  - [ ] GET `/api/properties/access/[token]` - Get property by access token

### Priority 3: Calendar Integration (Week 2)
- [ ] Calendar management endpoints
  - [ ] GET `/api/calendar/[propertyId]/calendars` - List connected calendars
  - [ ] POST `/api/calendar/[propertyId]/connect` - Connect new calendar (Airbnb, VRBO)
  - [ ] DELETE `/api/calendar/[propertyId]/calendars/[id]` - Disconnect calendar
  - [ ] GET `/api/calendar/[propertyId]/events` - Get all events
  - [ ] POST `/api/calendar/[propertyId]/sync` - Manual sync trigger
- [ ] Implement iCal parser
  - [ ] Install ical.js or similar
  - [ ] Parse iCal feed from URL
  - [ ] Extract events (title, dates, guest info)
  - [ ] Store events in calendar_events table
  - [ ] Handle event updates/deletions
- [ ] Create cron job for automatic sync
  - [ ] Implement scheduled function (every 6 hours)
  - [ ] GET all active calendars from D1
  - [ ] Fetch and parse each iCal feed
  - [ ] Update calendar_events table
  - [ ] Log sync results to KV or D1
  - [ ] Send notifications on sync errors

### Priority 4: Task Management (Week 2)
- [ ] Complete task endpoints
  - [ ] PUT `/api/tasks/[id]` - Update task
  - [ ] DELETE `/api/tasks/[id]` - Delete task
  - [ ] POST `/api/tasks/[id]/assign` - Assign task to user
  - [ ] POST `/api/tasks/[id]/complete` - Mark task complete
  - [ ] GET `/api/tasks/overdue` - Get overdue tasks
  - [ ] POST `/api/tasks/recurring` - Create recurring task
- [ ] Task assignments
  - [ ] GET `/api/tasks/[id]/assignments` - List assignments
  - [ ] POST `/api/tasks/[id]/assignments` - Add assignment
  - [ ] DELETE `/api/tasks/[id]/assignments/[userId]` - Remove assignment

### Priority 5: Cleaning Sessions (Week 2)
- [ ] Cleaning session endpoints
  - [ ] GET `/api/cleaning/sessions` - List sessions
  - [ ] POST `/api/cleaning/sessions/start` - Start session
  - [ ] PUT `/api/cleaning/sessions/[id]` - Update session
  - [ ] POST `/api/cleaning/sessions/[id]/complete` - Complete session
  - [ ] POST `/api/cleaning/sessions/[id]/photos` - Upload photos to R2
  - [ ] GET `/api/cleaning/sessions/[id]/photos` - Get session photos

---

## Phase 3: Frontend Development 📅 PLANNED

**Timeline:** October 16-30, 2025
**Status:** 📅 **PLANNED**

### Week 3: Project Setup & Core Layout
- [ ] Initialize Vite + React project
  - [ ] Set up project structure
  - [ ] Configure Tailwind CSS
  - [ ] Set up React Router
  - [ ] Configure environment variables
- [ ] Create core layout components
  - [ ] Header with navigation
  - [ ] Sidebar for role-based menu
  - [ ] Footer
  - [ ] Loading states
  - [ ] Error boundaries
- [ ] Set up state management
  - [ ] Install Zustand
  - [ ] Create auth store
  - [ ] Create property store
  - [ ] Create task store
- [ ] Implement authentication flow
  - [ ] Login page
  - [ ] Register page
  - [ ] Protected route wrapper
  - [ ] Auto-refresh token
  - [ ] Logout functionality

### Week 4: Property & Task Management UI
- [ ] Property management pages
  - [ ] Property list view with cards
  - [ ] Property detail view
  - [ ] Property create/edit form
  - [ ] Property image gallery
  - [ ] Image upload with drag-and-drop
- [ ] Task management pages
  - [ ] Task list with filters (status, priority, property)
  - [ ] Task detail view
  - [ ] Task create/edit form
  - [ ] Task assignment selector
  - [ ] Drag-and-drop task board (Kanban)

### Week 5: Calendar & Dashboard
- [ ] Calendar view
  - [ ] Integrate FullCalendar.js
  - [ ] Display events from all properties
  - [ ] Color-code by platform (Airbnb red, VRBO blue)
  - [ ] Property selector/filter
  - [ ] Calendar sync status indicator
- [ ] Dashboard views (role-based)
  - [ ] Property Owner dashboard
    - Upcoming bookings
    - Pending tasks
    - Property stats
  - [ ] Cleaner dashboard
    - Assigned tasks
    - Upcoming cleaning sessions
  - [ ] Maintenance dashboard
    - Assigned repairs
    - Inventory alerts

---

## Phase 4: Data Migration 📅 PLANNED

**Timeline:** November 1-7, 2025
**Status:** 📅 **PLANNED**

### Data Export from Flask
- [ ] Create export scripts for Flask/PostgreSQL
  - [ ] Export users table to JSON
  - [ ] Export properties table to JSON
  - [ ] Export tasks table to JSON
  - [ ] Export calendar_events table to JSON
  - [ ] Export cleaning_sessions table to JSON
  - [ ] Export inventory tables to JSON
- [ ] Export files from GCS/local storage
  - [ ] List all property images
  - [ ] List all cleaning photos/videos
  - [ ] Create file manifest

### Data Import to Cloudflare
- [ ] Create import scripts for D1
  - [ ] Parse JSON exports
  - [ ] Generate SQL INSERT statements
  - [ ] Batch import (1000 rows at a time)
  - [ ] Verify foreign key relationships
  - [ ] Handle duplicate detection
- [ ] Migrate files to R2
  - [ ] Upload property images to R2
  - [ ] Upload cleaning media to R2
  - [ ] Update database references with R2 URLs
  - [ ] Verify file accessibility
- [ ] Data validation
  - [ ] Compare row counts (Flask vs D1)
  - [ ] Spot-check random records
  - [ ] Test logins with migrated users
  - [ ] Verify property-task relationships

---

## Phase 5: Testing & Optimization 📅 PLANNED

**Timeline:** November 8-14, 2025
**Status:** 📅 **PLANNED**

### API Testing
- [ ] Create API test suite
  - [ ] Test authentication flows
  - [ ] Test CRUD operations for all resources
  - [ ] Test error handling
  - [ ] Test authorization (users can't access others' data)
- [ ] Performance testing
  - [ ] Benchmark API response times
  - [ ] Test with 1000+ properties
  - [ ] Test with 10,000+ events
  - [ ] Optimize slow queries
- [ ] Load testing
  - [ ] Simulate 100 concurrent users
  - [ ] Test rate limiting
  - [ ] Verify KV cache effectiveness

### Frontend Testing
- [ ] Create component tests
  - [ ] Test form submissions
  - [ ] Test navigation
  - [ ] Test authentication flows
- [ ] E2E testing
  - [ ] Test complete user workflows
  - [ ] Test on mobile devices
  - [ ] Cross-browser testing

### Optimization
- [ ] Database optimization
  - [ ] Add missing indexes
  - [ ] Optimize complex queries
  - [ ] Implement query caching in KV
- [ ] Caching strategy
  - [ ] Cache property lists (10min TTL)
  - [ ] Cache task lists (5min TTL)
  - [ ] Cache user sessions (24h TTL)
  - [ ] Implement cache invalidation
- [ ] Performance improvements
  - [ ] Lazy load images
  - [ ] Implement virtual scrolling for long lists
  - [ ] Code splitting for routes
  - [ ] Optimize bundle size

---

## Phase 6: Parallel Deployment 📅 PLANNED

**Timeline:** November 15-21, 2025
**Status:** 📅 **PLANNED**

### Setup Parallel Systems
- [ ] Deploy Cloudflare Workers to production
  - [ ] Set up production environment variables
  - [ ] Configure custom domain (e.g., cf.shorttermlandlord.com)
  - [ ] Set up SSL certificate
  - [ ] Configure DNS
- [ ] Keep Flask running on Google App Engine
- [ ] Set up monitoring
  - [ ] Cloudflare Analytics
  - [ ] Error tracking (Sentry or similar)
  - [ ] Performance monitoring
  - [ ] Uptime monitoring

### Beta Testing
- [ ] Invite beta testers
  - [ ] Select 10-20 existing users
  - [ ] Provide access to Cloudflare version
  - [ ] Collect feedback
- [ ] Monitor for issues
  - [ ] Track error rates
  - [ ] Monitor performance
  - [ ] Watch for edge cases
- [ ] Iterate on feedback
  - [ ] Fix reported bugs
  - [ ] Improve UX based on feedback
  - [ ] Optimize performance bottlenecks

---

## Phase 7: Gradual Traffic Shift 📅 PLANNED

**Timeline:** November 22-30, 2025
**Status:** 📅 **PLANNED**

### Week 1: 10% Traffic to Cloudflare
- [ ] Configure traffic split
  - [ ] Use Cloudflare Load Balancer or similar
  - [ ] Route 10% of traffic to Workers
  - [ ] Keep 90% on Flask
- [ ] Monitor metrics
  - [ ] Compare error rates
  - [ ] Compare response times
  - [ ] Watch for issues

### Week 2: 50% Traffic to Cloudflare
- [ ] Increase traffic split to 50/50
- [ ] Continue monitoring
- [ ] Address any issues quickly

### Week 3: 90% Traffic to Cloudflare
- [ ] Route 90% to Workers
- [ ] Keep Flask as fallback
- [ ] Final performance validation

---

## Phase 8: Full Cutover 📅 PLANNED

**Timeline:** December 1-7, 2025
**Status:** 📅 **PLANNED**

### Complete Migration
- [ ] Route 100% traffic to Cloudflare
- [ ] Update DNS to point to Workers domain
- [ ] Decommission Flask app (keep for 30 days backup)
- [ ] Celebrate! 🎉

### Post-Migration
- [ ] Monitor for 1 week
- [ ] Address any remaining issues
- [ ] Collect user feedback
- [ ] Document lessons learned

---

## Success Metrics

### Performance
- [ ] API response time < 100ms (95th percentile)
- [ ] Database query time < 10ms (95th percentile)
- [ ] Page load time < 2s
- [ ] Time to interactive < 3s

### Reliability
- [ ] Uptime > 99.9%
- [ ] Error rate < 0.1%
- [ ] Zero data loss during migration

### User Experience
- [ ] User satisfaction score > 4.5/5
- [ ] Task completion rate > 95%
- [ ] Support ticket reduction by 20%

### Cost
- [ ] Infrastructure cost reduction of 40-60%
- [ ] Reduced maintenance overhead
- [ ] Improved scalability without cost increases

---

## Risk Mitigation

### Technical Risks
1. **Data Loss During Migration**
   - Mitigation: Export all data to JSON before migration
   - Keep Flask running for 30 days as backup
   - Implement rollback plan

2. **Performance Degradation**
   - Mitigation: Extensive load testing before cutover
   - Monitor metrics closely during shift
   - Quick rollback capability

3. **Calendar Sync Failures**
   - Mitigation: Test with all platforms (Airbnb, VRBO)
   - Implement retry logic
   - Send alerts on failures

4. **Authentication Issues**
   - Mitigation: Test password migration thoroughly
   - Keep old sessions valid during transition
   - Provide password reset option

### User Impact Risks
1. **Learning Curve for New UI**
   - Mitigation: Maintain similar UI/UX patterns
   - Provide user guide
   - Offer training sessions

2. **Downtime During Cutover**
   - Mitigation: Perform cutover during low-traffic hours
   - Use gradual traffic shift
   - Communicate timeline to users

---

## Resource Requirements

### Development Time
- **Phase 1:** 1 day (Complete)
- **Phase 2:** 7 days (API development)
- **Phase 3:** 14 days (Frontend development)
- **Phase 4:** 7 days (Data migration)
- **Phase 5:** 7 days (Testing & optimization)
- **Phase 6:** 7 days (Parallel deployment)
- **Phase 7:** 9 days (Gradual shift)
- **Phase 8:** 7 days (Full cutover)

**Total:** ~60 days (8-9 weeks)

### Infrastructure Costs
- **Cloudflare Workers:** ~$5/month
- **D1 Database:** Free tier (5GB, 5M reads/day)
- **KV Storage:** ~$0.50/month
- **R2 Storage:** ~$0.15/GB (no egress fees)
- **Estimated Monthly:** $10-20 (vs $100-200 on GAE)

---

## Next Actions (This Week)

### Immediate (Today/Tomorrow)
1. [ ] Install bcrypt for Workers
2. [ ] Implement password hashing in login endpoint
3. [ ] Create authentication middleware
4. [ ] Add register endpoint
5. [ ] Add logout endpoint

### This Week
1. [ ] Complete all authentication endpoints
2. [ ] Add property image upload to R2
3. [ ] Start calendar integration
4. [ ] Set up iCal parser
5. [ ] Create first cron job

### Next Week
1. [ ] Complete calendar sync functionality
2. [ ] Add cleaning session endpoints
3. [ ] Start React frontend setup
4. [ ] Create basic layout components

---

**Document Status:** Living Document - Updated Daily
**Owner:** Development Team
**Last Review:** October 8, 2025
**Next Review:** October 9, 2025
