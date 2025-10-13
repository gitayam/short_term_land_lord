# Direct Booking System - Airbnb Alternative
## Vision: Enable property owners to convert good guests into direct booking clients

---

## 🎯 **Core Value Proposition**

**For Property Owners:**
- Save 15-20% Airbnb commission fees
- Build direct relationships with quality guests
- Full control over pricing and policies
- No platform restrictions
- Keep all guest data

**For Guests:**
- Lower prices (no Airbnb fees)
- Direct communication with owners
- Exclusive access to properties
- Loyalty rewards and discounts
- Better personalized service

---

## 📋 **Complete Feature Breakdown**

### **PHASE 1: Property Showcase & Public Booking** (MVP - Week 1-2)

#### 1.1 Public Property Pages
- **Shareable Property Links**
  - Unique URL per property: `yoursite.com/p/[share-token]`
  - QR code generation for easy sharing
  - Social media sharing buttons
  - Embed code for owner's website
  - Analytics tracking (views, clicks)

- **Property Showcase Page Design**
  ```
  - Hero section with primary image
  - Image gallery slider (10+ photos)
  - Property overview (beds, baths, guests, sqft)
  - Amenities grid with icons
  - Full description
  - House rules and policies
  - Location map (Google Maps)
  - Availability calendar
  - Pricing display
  - "Request to Book" CTA button
  - Guest reviews section
  - FAQ accordion
  - Contact owner button
  ```

- **Property Images System** ⚠️ NEED TO IMPLEMENT
  - Upload multiple photos
  - Drag-and-drop reordering
  - Set primary/featured image
  - Image captions
  - Photo categories (exterior, interior, amenities, neighborhood)
  - Professional photo mode (highlight best images)

- **Room Details** ⚠️ NEED TO IMPLEMENT
  - List each bedroom with bed types
  - Bathroom details (ensuite, shared)
  - Common areas
  - Outdoor spaces
  - Parking information

#### 1.2 Booking Request System
- **Guest Request Form**
  ```
  Fields:
  - Check-in / Check-out dates
  - Number of guests (adults, children, pets)
  - Guest name and email
  - Phone number
  - Message to owner
  - Special requests
  - How they heard about property
  - Previous stay experience (if return guest)
  ```

- **Instant Availability Check**
  - Real-time calendar checking
  - Block unavailable dates
  - Show minimum stay requirements
  - Dynamic pricing display
  - Calculate total with breakdown

- **Request Submission Flow**
  ```
  1. Guest fills form
  2. System creates pending booking request
  3. Email sent to owner with request details
  4. Email sent to guest with confirmation
  5. Owner reviews in dashboard
  6. Owner approves or rejects with message
  7. If approved: booking confirmed, calendar blocked
  8. If rejected: guest notified with reason
  ```

#### 1.3 Owner Management Dashboard
- **Booking Requests View**
  - List all pending requests
  - Filter by property, date range, status
  - One-click approve/reject
  - View guest details and message
  - Set custom pricing for request
  - Add notes visible only to owner

- **Request Details Page**
  - Guest information
  - Requested dates and pricing
  - Calendar preview showing availability
  - Guest message and special requests
  - Action buttons: Approve, Reject, Counter-Offer
  - Communication thread

---

### **PHASE 2: Guest Management & Invitations** (Week 3-4)

#### 2.1 Guest Profiles
- **Guest Account System**
  - Email + password login
  - Social login (Google, Facebook)
  - Profile completion
  - Verified email/phone
  - Profile photo
  - Bio / About me
  - Travel preferences
  - Pet information

- **Guest Dashboard**
  - My bookings (upcoming, past, cancelled)
  - My favorite properties
  - My reviews (given and received)
  - Payment history
  - Saved payment methods
  - Communication with owners

#### 2.2 Invitation System
- **Invite Past Guests**
  ```
  Owner workflow:
  1. View past bookings/guests
  2. Select "Invite for Direct Booking"
  3. Choose invitation type:
     - Specific property
     - All properties
     - Property portfolio access
  4. Set special pricing/discount
  5. Add personal message
  6. Send invitation email
  ```

- **Invitation Types**
  - **VIP Guests**: Automatic approval, special pricing, exclusive properties
  - **Repeat Guests**: 10% discount, priority booking
  - **Referral Guests**: Referred by existing guests, 5% discount
  - **Seasonal Guests**: Long-term stay guests, monthly rates

- **Invitation Management**
  - Track invitation status (sent, viewed, accepted)
  - Set expiration dates
  - Limit number of uses
  - Revoke invitations
  - Invitation analytics

#### 2.3 Guest Loyalty Program
- **Reward Tiers**
  ```
  Bronze (1-2 stays):
  - 5% discount on next booking
  - Early check-in when available

  Silver (3-5 stays):
  - 10% discount on next booking
  - Late checkout when available
  - Welcome amenity

  Gold (6+ stays):
  - 15% discount on all bookings
  - Guaranteed early check-in/late checkout
  - Premium welcome package
  - First access to new properties
  ```

- **Points System** (Optional)
  - Earn points per dollar spent
  - Redeem points for discounts
  - Referral bonuses
  - Review bonuses

---

### **PHASE 3: Payment & Booking Management** (Week 5-6)

#### 3.1 Payment Integration
- **Stripe Connect Setup**
  - Owner onboarding to Stripe Connect
  - Bank account verification
  - Automatic payouts
  - Multi-currency support

- **Payment Flow**
  ```
  1. Booking approved → Payment request sent
  2. Guest pays deposit (30% or custom)
  3. Remaining balance due X days before check-in
  4. Security deposit held (refunded after checkout)
  5. Owner receives payout after check-in
  6. Automatic refund processing
  ```

- **Payment Methods**
  - Credit/debit cards
  - ACH bank transfers
  - Apple Pay / Google Pay
  - PayPal (optional)
  - Crypto (future)

- **Payment Tracking**
  - Payment history
  - Pending payments
  - Refund requests
  - Payout schedule
  - Tax reporting (1099 forms)

#### 3.2 Security Deposits
- **Deposit Handling**
  - Automatic hold on guest's card
  - Custom deposit amounts per property
  - Damage claim process
  - Photo documentation
  - Dispute resolution
  - Automatic release after checkout + X days

#### 3.3 Cancellation Policies
- **Policy Types**
  - Flexible: Full refund up to 24 hours before
  - Moderate: Full refund up to 5 days before
  - Strict: 50% refund up to 30 days before
  - Custom: Owner-defined rules

- **Cancellation Flow**
  ```
  Guest cancels:
  1. Calculate refund based on policy
  2. Process refund automatically
  3. Unblock calendar
  4. Notify owner
  5. Optional: Offer to rebook
  ```

---

### **PHASE 4: Communication & Automation** (Week 7-8)

#### 4.1 Messaging System
- **In-App Messaging**
  - Real-time chat between guest and owner
  - Message history
  - File attachments (photos, documents)
  - Read receipts
  - Push notifications

- **Message Templates**
  - Pre-arrival welcome
  - Check-in instructions
  - House rules reminder
  - Check-out instructions
  - Post-stay thank you
  - Review request

#### 4.2 Email Automation
- **Automated Emails**
  ```
  Timeline:
  - Booking confirmed → Welcome email
  - 7 days before → Pre-arrival checklist
  - 1 day before → Check-in details (code, WiFi, etc.)
  - Check-in day → Welcome & local recommendations
  - During stay → Mid-stay check-in (optional)
  - Check-out day → Check-out reminder
  - 1 day after → Thank you + review request
  - 7 days after → Come back soon offer
  ```

- **Email Customization**
  - Owner can edit all email templates
  - Add property-specific information
  - Include custom branding
  - Personalization tokens (guest name, dates, etc.)

#### 4.3 SMS Notifications (Optional)
- **Text Message Alerts**
  - Booking confirmation
  - Payment reminders
  - Check-in code delivery
  - Emergency contact
  - Review requests

---

### **PHASE 5: Reviews & Trust** (Week 9-10)

#### 5.1 Review System
- **Two-Way Reviews**
  - Guests review properties
  - Owners review guests
  - Both published after checkout + 14 days

- **Review Categories**
  ```
  Property Reviews (Guest → Property):
  - Overall rating (1-5 stars)
  - Cleanliness
  - Accuracy of listing
  - Communication
  - Location
  - Value for money
  - Written review
  - Photos (optional)

  Guest Reviews (Owner → Guest):
  - Overall rating (1-5 stars)
  - Communication
  - Cleanliness
  - Respect for house rules
  - Would host again (yes/no)
  - Private notes (only owner sees)
  ```

- **Review Display**
  - Show on property page
  - Average ratings prominently displayed
  - Recent reviews highlighted
  - Response from owner (optional)
  - Verified booking badge

#### 5.2 Trust & Safety
- **Guest Verification**
  - Email verification (required)
  - Phone verification (recommended)
  - ID verification (Stripe Identity)
  - Social media linking
  - Reference checks (for first-time guests)

- **Damage Protection**
  - Security deposit holds
  - Photo documentation before/after
  - Damage claim process with evidence
  - Insurance integration (optional)
  - Dispute resolution process

- **Screening Questions**
  - Purpose of stay
  - Who will be staying
  - Pet information
  - Special requirements
  - How they found the property

---

### **PHASE 6: Advanced Features** (Week 11-12)

#### 6.1 Dynamic Pricing
- **Smart Pricing Tools**
  - Base price + seasonal adjustments
  - Weekend pricing
  - Holiday pricing
  - Last-minute discounts
  - Long-stay discounts (weekly, monthly)
  - Competitor pricing analysis

- **Pricing Calendar**
  - Set custom prices per date
  - Bulk pricing updates
  - Price recommendations based on demand
  - Revenue optimization

#### 6.2 Multi-Property Booking
- **Package Deals**
  - Book multiple properties for events
  - Group bookings (weddings, retreats)
  - Exclusive venue access
  - Custom pricing for packages

#### 6.3 Owner Analytics
- **Booking Analytics**
  - Conversion rate (views → bookings)
  - Average booking value
  - Guest acquisition source
  - Seasonal trends
  - Revenue projections

- **Guest Analytics**
  - Return guest rate
  - Average stay duration
  - Most popular amenities
  - Review sentiment analysis

#### 6.4 API & Integrations
- **Channel Manager Integration**
  - Import bookings from Airbnb, VRBO
  - Sync calendars automatically
  - Prevent double bookings

- **Property Management Tools**
  - Sync with Guesty, Hostfully, etc.
  - Cleaning schedule automation
  - Maintenance tracking

---

## 🗄️ **Database Schema Requirements**

### New Tables Needed:

```sql
-- Public property sharing
CREATE TABLE property_public_link (
    id TEXT PRIMARY KEY,
    property_id TEXT NOT NULL,
    share_token TEXT UNIQUE NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT (datetime('now')),
    access_count INTEGER DEFAULT 0,
    FOREIGN KEY (property_id) REFERENCES property(id)
);

-- Booking requests
CREATE TABLE booking_request (
    id TEXT PRIMARY KEY,
    property_id TEXT NOT NULL,
    guest_email TEXT NOT NULL,
    guest_name TEXT NOT NULL,
    guest_phone TEXT,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    num_guests INTEGER NOT NULL,
    num_adults INTEGER,
    num_children INTEGER,
    num_pets INTEGER,
    message TEXT,
    special_requests TEXT,
    status TEXT DEFAULT 'pending', -- pending, approved, rejected, cancelled
    total_price REAL,
    custom_price REAL,
    reviewed_by_id TEXT,
    reviewed_at DATETIME,
    review_notes TEXT,
    created_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (property_id) REFERENCES property(id),
    FOREIGN KEY (reviewed_by_id) REFERENCES users(id)
);

-- Confirmed bookings
CREATE TABLE booking (
    id TEXT PRIMARY KEY,
    property_id TEXT NOT NULL,
    guest_id TEXT,
    guest_email TEXT NOT NULL,
    guest_name TEXT NOT NULL,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    num_guests INTEGER NOT NULL,
    status TEXT DEFAULT 'confirmed', -- confirmed, checked_in, checked_out, cancelled
    total_price REAL NOT NULL,
    deposit_amount REAL,
    deposit_paid INTEGER DEFAULT 0,
    balance_paid INTEGER DEFAULT 0,
    security_deposit REAL,
    security_deposit_status TEXT DEFAULT 'pending',
    special_requests TEXT,
    booking_source TEXT DEFAULT 'direct', -- direct, airbnb, vrbo, etc.
    created_at DATETIME DEFAULT (datetime('now')),
    confirmed_at DATETIME,
    checked_in_at DATETIME,
    checked_out_at DATETIME,
    FOREIGN KEY (property_id) REFERENCES property(id),
    FOREIGN KEY (guest_id) REFERENCES users(id)
);

-- Guest invitations (enhanced)
CREATE TABLE guest_invitation_v2 (
    id TEXT PRIMARY KEY,
    property_id TEXT, -- null = all properties
    guest_email TEXT NOT NULL,
    guest_name TEXT,
    invitation_type TEXT DEFAULT 'standard', -- vip, repeat, referral
    discount_percent REAL DEFAULT 0,
    discount_amount REAL DEFAULT 0,
    invitation_token TEXT UNIQUE NOT NULL,
    message TEXT,
    expires_at DATETIME,
    accepted_at DATETIME,
    booking_count INTEGER DEFAULT 0,
    invited_by_id TEXT NOT NULL,
    created_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (property_id) REFERENCES property(id),
    FOREIGN KEY (invited_by_id) REFERENCES users(id)
);

-- Guest profiles
CREATE TABLE guest_profile (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE,
    guest_email TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    bio TEXT,
    profile_image TEXT,
    verified_email INTEGER DEFAULT 0,
    verified_phone INTEGER DEFAULT 0,
    verified_id INTEGER DEFAULT 0,
    total_bookings INTEGER DEFAULT 0,
    loyalty_tier TEXT DEFAULT 'bronze', -- bronze, silver, gold
    loyalty_points INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Payments
CREATE TABLE payment (
    id TEXT PRIMARY KEY,
    booking_id TEXT NOT NULL,
    amount REAL NOT NULL,
    payment_type TEXT NOT NULL, -- deposit, balance, security_deposit, refund
    payment_method TEXT, -- card, bank, paypal
    payment_status TEXT DEFAULT 'pending', -- pending, completed, failed, refunded
    stripe_payment_id TEXT,
    stripe_refund_id TEXT,
    processed_at DATETIME,
    refunded_at DATETIME,
    created_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (booking_id) REFERENCES booking(id)
);

-- Messages
CREATE TABLE message_v2 (
    id TEXT PRIMARY KEY,
    booking_id TEXT,
    property_id TEXT,
    sender_id TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    read_at DATETIME,
    created_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (booking_id) REFERENCES booking(id),
    FOREIGN KEY (property_id) REFERENCES property(id),
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (recipient_id) REFERENCES users(id)
);
```

---

## 🎨 **UI/UX Design Principles**

### Property Showcase Page
- **Airbnb-inspired but unique**
- Clean, minimalist design
- Mobile-first responsive
- Fast loading (optimized images)
- Clear CTAs
- Trust indicators (reviews, verified, etc.)

### Booking Flow
- **3-Step Process**
  1. Select dates & guests
  2. Enter guest details
  3. Review & submit request
- Progress indicator
- Easy navigation
- Clear pricing breakdown
- No surprises

### Owner Dashboard
- **Booking management central**
- Notification center
- Quick actions
- Mobile-optimized
- Real-time updates

---

## 📱 **Marketing & Sharing Features**

### Share Options
- **Email**: Direct email invitations
- **SMS**: Text message links
- **Social Media**: Facebook, Instagram, Twitter
- **QR Code**: Print for in-person sharing
- **Embed**: Widget for owner's website
- **Business Cards**: Printable cards with QR code

### Owner Marketing Tools
- **Property landing pages**
- **Custom domain mapping** (premium feature)
- **SEO optimization**
- **Google Analytics integration**
- **Social media auto-posting**
- **Email campaigns** to past guests

---

## 🚀 **Implementation Roadmap**

### **Sprint 1 (Week 1-2): MVP - Property Showcase**
- [ ] Property images system (upload, gallery, reorder)
- [ ] Property rooms system (bedroom/bathroom details)
- [ ] Public property page with shareable link
- [ ] Image gallery slider
- [ ] Availability calendar display
- [ ] Basic property information display

### **Sprint 2 (Week 2-3): Booking Requests**
- [ ] Booking request form (guest-facing)
- [ ] Booking request API endpoints
- [ ] Owner booking request dashboard
- [ ] Approve/reject workflow
- [ ] Email notifications (basic)
- [ ] Calendar blocking on approval

### **Sprint 3 (Week 3-4): Guest Management**
- [ ] Guest profile system
- [ ] Guest dashboard
- [ ] Invitation system
- [ ] Special pricing for invited guests
- [ ] Guest loyalty tiers

### **Sprint 4 (Week 4-5): Payment Integration**
- [ ] Stripe Connect setup
- [ ] Payment collection flow
- [ ] Security deposit handling
- [ ] Refund processing
- [ ] Payment tracking dashboard

### **Sprint 5 (Week 5-6): Communication**
- [ ] In-app messaging system
- [ ] Email automation (welcome, check-in, etc.)
- [ ] SMS notifications (optional)
- [ ] Message templates

### **Sprint 6 (Week 6-7): Reviews & Polish**
- [ ] Review system (two-way)
- [ ] Review display on property pages
- [ ] Trust & safety features
- [ ] Analytics dashboard
- [ ] Mobile optimization

---

## ✅ **Success Metrics**

### KPIs to Track
- **Conversion Rate**: Views → Booking Requests → Confirmed Bookings
- **Response Time**: How fast owners respond to requests
- **Approval Rate**: % of requests approved
- **Return Guest Rate**: % of guests who book again
- **Average Booking Value**: Total revenue per booking
- **Owner Satisfaction**: NPS score
- **Guest Satisfaction**: Review ratings

### Goals
- **Year 1**: 50 properties, 500 bookings, $100K GMV
- **Year 2**: 200 properties, 2,000 bookings, $500K GMV
- **Year 3**: 500 properties, 5,000 bookings, $1M+ GMV

---

## 🔐 **Legal & Compliance**

### Required Legal Documents
- [ ] Terms of Service
- [ ] Privacy Policy
- [ ] Rental Agreement Template
- [ ] Cancellation Policy
- [ ] Payment Terms
- [ ] Damage Policy
- [ ] Cookie Policy
- [ ] GDPR Compliance

### Insurance & Liability
- [ ] Host liability insurance options
- [ ] Guest damage protection
- [ ] Cancellation insurance
- [ ] Legal disclaimer language

---

## 💡 **Competitive Advantages**

### vs Airbnb
✅ No commission fees (save 15-20%)
✅ Direct guest relationships
✅ Full control over policies
✅ Better margins for owners
✅ Personalized service

### vs VRBO/Booking.com
✅ No listing fees
✅ Built for repeat guests
✅ Loyalty program
✅ Property management tools included
✅ Lower transaction fees

### vs Direct Website
✅ Professional booking system
✅ Payment processing built-in
✅ Calendar management
✅ Review system
✅ Guest communication tools

---

## 🎯 **Next Immediate Actions**

1. **Implement Property Images** (Critical Path)
   - property_image table already exists
   - Build upload interface
   - Build gallery display
   - Image optimization

2. **Implement Property Rooms** (Critical Path)
   - property_room table already exists
   - Build room management interface
   - Display on public page

3. **Create Public Property Page** (Critical Path)
   - Generate shareable links
   - Design property showcase template
   - Implement calendar display
   - Add "Request to Book" button

4. **Build Booking Request System**
   - Create booking_request table
   - Build request form
   - Owner review dashboard
   - Email notifications

This is a MAJOR undertaking but has the potential to be a game-changer for the platform. The direct booking model could generate significant value for property owners and create a competitive moat against Airbnb.
