# Property Guidebook Feature Specification

**OpenBNB - Digital Guest Guidebook**
**Version:** 1.0
**Date:** October 2025

---

## Overview

A comprehensive digital guidebook that hosts can create for each property to provide guests with all the information they need during their stay. Based on 2025 best practices from Airbnb, VRBO, and leading vacation rental platforms.

---

## Research Findings: What Makes a Great Guidebook

### Core Benefits
- **Reduces host workload:** Answers FAQs before guests ask (30-40% reduction in messages)
- **Improves reviews:** Listings with clear guidebooks earn more 5-star reviews
- **Enhances guest experience:** Guests have all info at their fingertips
- **Professional appearance:** Shows attention to detail and care

### Essential Sections (Industry Standard)

1. **Welcome Message**
   - Warm greeting from host
   - Express hope for great stay
   - Personal touch

2. **Property Access**
   - Check-in instructions (time, location, key/code)
   - Check-out instructions (time, procedures)
   - Parking details
   - Building access (if apartment/condo)

3. **House Rules**
   - Quiet hours
   - Smoking policy
   - Pet policy
   - Party policy
   - Guest limits
   - Security deposit terms

4. **Property Guide**
   - WiFi name & password
   - Heating/AC instructions
   - TV & entertainment systems
   - Kitchen appliances
   - Washer/dryer
   - Thermostat
   - Alarm system (if any)
   - Hot tub/pool instructions (if applicable)

5. **Emergency Information**
   - Host contact (phone, email)
   - Emergency services (911)
   - Nearest hospital
   - Police/Fire station
   - Utility emergency contacts
   - First aid kit location
   - Fire extinguisher location

6. **Local Recommendations**
   - Restaurants (by category: breakfast, lunch, dinner, takeout)
   - Coffee shops
   - Grocery stores
   - Pharmacies
   - Gas stations
   - Attractions & activities
   - Parks & outdoor spaces
   - Entertainment venues
   - Shopping

7. **Transportation**
   - Nearest airport (distance, transport options)
   - Public transit info
   - Taxi/Uber/Lyft availability
   - Bike rentals
   - Car rentals

8. **Additional Resources**
   - Weather tips
   - Local events
   - Cultural etiquette
   - Tipping customs
   - Best times to visit attractions

---

## Database Schema

### Table: `guidebook_sections`
Stores guidebook content organized by section type for each property.

```sql
CREATE TABLE guidebook_sections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  property_id INTEGER NOT NULL REFERENCES property(id) ON DELETE CASCADE,
  section_type TEXT NOT NULL, -- 'welcome', 'access', 'rules', 'property', 'emergency', 'local', 'transportation', 'additional'
  title TEXT NOT NULL,
  content TEXT NOT NULL, -- Markdown supported
  display_order INTEGER DEFAULT 0,
  icon TEXT, -- Emoji or icon identifier
  is_published BOOLEAN DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_guidebook_property ON guidebook_sections(property_id);
CREATE INDEX idx_guidebook_section_type ON guidebook_sections(section_type);
```

### Table: `guidebook_recommendations`
Stores structured local recommendations (restaurants, attractions, etc.)

```sql
CREATE TABLE guidebook_recommendations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  property_id INTEGER NOT NULL REFERENCES property(id) ON DELETE CASCADE,
  category TEXT NOT NULL, -- 'restaurant', 'coffee', 'grocery', 'attraction', 'activity', 'park', 'shopping'
  name TEXT NOT NULL,
  description TEXT,
  address TEXT,
  phone TEXT,
  website TEXT,
  distance_miles REAL,
  walking_time_minutes INTEGER,
  price_level INTEGER, -- 1-4 ($, $$, $$$, $$$$)
  rating REAL, -- 1.0-5.0
  hours TEXT, -- "Mon-Fri: 9am-9pm, Sat-Sun: 10am-6pm"
  tags TEXT, -- JSON array: ["kid-friendly", "outdoor seating", "reservations recommended"]
  image_url TEXT,
  display_order INTEGER DEFAULT 0,
  is_featured BOOLEAN DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recommendations_property ON guidebook_recommendations(property_id);
CREATE INDEX idx_recommendations_category ON guidebook_recommendations(category);
```

---

## User Interface Design

### Host Portal (Admin)

**Guidebook Editor:**
- Tab-based interface for each section
- Rich text editor with markdown support
- Drag-and-drop for reordering sections
- Preview mode to see guest view
- Templates for common sections
- Auto-save drafts

**Recommendations Manager:**
- Add/edit recommendations by category
- Import from Google Maps/Yelp (future)
- Bulk upload via CSV
- Map view showing all recommendations
- Distance auto-calculation from property

### Guest View

**Desktop:**
- Sticky sidebar navigation (sections)
- Smooth scrolling to sections
- Printable version (PDF export)
- Search within guidebook

**Mobile:**
- Collapsible accordion sections
- Bottom sheet navigation
- One-tap phone calls
- One-tap directions (Google Maps integration)
- Offline mode (PWA)

**Features:**
- QR code access (printed in property)
- Shareable link (expires after checkout)
- Bookmark favorite places
- "Add to Calendar" for local events

---

## Implementation Phases

### Phase 1: Core Guidebook (MVP)
**Effort:** 3-4 days
- Database schema & migrations
- Basic CRUD API endpoints
- Simple markdown editor for hosts
- Guest view with basic styling
- Essential sections: Welcome, Access, Rules, Property, Emergency

### Phase 2: Local Recommendations
**Effort:** 2-3 days
- Recommendations database
- Category-based display
- Map integration (OpenStreetMap)
- Distance calculations
- Featured recommendations

### Phase 3: Enhanced UX
**Effort:** 2-3 days
- Rich text editor (Tiptap or similar)
- Drag-and-drop reordering
- Image uploads for sections
- QR code generation
- PDF export

### Phase 4: Advanced Features
**Effort:** 3-4 days (future)
- Templates library
- Import from Google Maps
- Multi-language support
- Analytics (most viewed sections)
- Guest feedback on recommendations

---

## API Endpoints

### For Hosts (Admin)
```
GET    /api/admin/properties/:id/guidebook
POST   /api/admin/properties/:id/guidebook/sections
PUT    /api/admin/properties/:id/guidebook/sections/:sectionId
DELETE /api/admin/properties/:id/guidebook/sections/:sectionId

GET    /api/admin/properties/:id/guidebook/recommendations
POST   /api/admin/properties/:id/guidebook/recommendations
PUT    /api/admin/properties/:id/guidebook/recommendations/:recId
DELETE /api/admin/properties/:id/guidebook/recommendations/:recId
```

### For Guests (Public)
```
GET /api/guidebook/:propertySlug
GET /api/guidebook/:propertySlug/recommendations?category=restaurant
GET /api/guidebook/:propertySlug/pdf (PDF export)
```

---

## Sample Data Structure

### Welcome Section (JSON)
```json
{
  "section_type": "welcome",
  "title": "Welcome to Elegant Suite!",
  "content": "Hi there! We're thrilled to have you as our guest. This charming suite is perfect for exploring downtown Fayetteville. We've prepared this guidebook to help make your stay as comfortable and enjoyable as possible. If you need anything during your stay, don't hesitate to reach out!\n\n**Your Hosts,**\nThe OpenBNB Team",
  "icon": "👋",
  "display_order": 1
}
```

### Property Access Section (JSON)
```json
{
  "section_type": "access",
  "title": "Check-In & Property Access",
  "content": "### Check-In Time\n3:00 PM - 10:00 PM\n\n### Check-Out Time\n11:00 AM\n\n### Entry Instructions\n1. The front door code is **1234** (valid from your check-in date)\n2. Enter through the main entrance\n3. Your suite is on the 2nd floor, door #4\n\n### Parking\nFree street parking available on Levenhall Dr. Please do not block driveways.\n\n### Late Check-In\nIf arriving after 10 PM, please text us at (555) 123-4567",
  "icon": "🔑",
  "display_order": 2
}
```

### Local Recommendation (JSON)
```json
{
  "category": "restaurant",
  "name": "Joe's Diner",
  "description": "Classic American diner serving breakfast all day. Famous for their pancakes and friendly service!",
  "address": "123 Main St, Fayetteville, NC 28301",
  "phone": "(910) 555-1234",
  "website": "https://joesdiner.com",
  "distance_miles": 0.3,
  "walking_time_minutes": 6,
  "price_level": 2,
  "rating": 4.5,
  "hours": "Mon-Fri: 6am-3pm, Sat-Sun: 7am-3pm",
  "tags": ["breakfast", "kid-friendly", "cash-only"],
  "is_featured": true
}
```

---

## Design Inspiration

**Reference Sites:**
- Airbnb Guidebook (clean, mobile-first)
- Hostfully (comprehensive digital guidebook platform)
- Touchstay (QR code integration, offline mode)
- Welcome Book (template examples)

**Visual Style:**
- Clean, scannable layout
- Generous whitespace
- Icon-based navigation
- Mobile-friendly cards
- Dark mode support

---

## Success Metrics

**Host Engagement:**
- % of properties with complete guidebooks
- Average time to create guidebook
- Sections most commonly used

**Guest Engagement:**
- Guidebook views per booking
- Most viewed sections
- Average time spent in guidebook
- Recommendations clicked/used

**Impact on Business:**
- Reduction in guest support messages
- Correlation with 5-star reviews
- Guest satisfaction scores

---

## Future Enhancements

1. **AI-Powered Content Generation**
   - Auto-generate welcome message from property details
   - Suggest local recommendations based on location
   - Translate guidebook to guest's language

2. **Interactive Features**
   - Real-time chat with host
   - Report issues (lightbulb out, etc.)
   - Request early check-in/late checkout
   - Book local experiences

3. **Integrations**
   - Google Maps API for recommendations
   - Yelp API for ratings/reviews
   - Local event APIs (Eventbrite, etc.)
   - Weather API for 7-day forecast

4. **Smart Home Integration**
   - Control lights, thermostat via guidebook
   - Video tutorials for appliances
   - Automated check-in with smart locks

---

**Next Steps:** Implement Phase 1 (Core Guidebook) alongside features 1-5 from the roadmap.
