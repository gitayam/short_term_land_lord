-- ================================================================
-- GUEST PORTAL & GUIDEBOOK SYSTEM
-- Property guidebooks and guest access portals
-- ================================================================

-- ================================================================
-- PROPERTY GUIDEBOOKS TABLE
-- Main guidebook configuration per property
-- ================================================================
CREATE TABLE IF NOT EXISTS property_guidebook (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL UNIQUE,

    -- Basic Info
    welcome_message TEXT,
    property_image_url TEXT,

    -- Check-in/Check-out
    checkin_time TEXT DEFAULT '3:00 PM',
    checkout_time TEXT DEFAULT '11:00 AM',
    checkin_instructions TEXT,
    checkout_instructions TEXT,

    -- WiFi
    wifi_network TEXT,
    wifi_password TEXT,

    -- Contact Info
    emergency_contact TEXT,
    emergency_phone TEXT,
    host_phone TEXT,
    host_email TEXT,

    -- Parking
    parking_info TEXT,
    parking_instructions TEXT,

    -- House Rules
    house_rules TEXT,
    quiet_hours TEXT,
    max_guests INTEGER,
    smoking_allowed INTEGER DEFAULT 0,
    pets_allowed INTEGER DEFAULT 0,
    parties_allowed INTEGER DEFAULT 0,

    -- Status
    is_published INTEGER DEFAULT 0,
    last_updated TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE
);

CREATE INDEX idx_guidebook_property ON property_guidebook(property_id);
CREATE INDEX idx_guidebook_published ON property_guidebook(is_published);

-- ================================================================
-- GUIDEBOOK SECTIONS TABLE
-- Customizable sections for local recommendations, amenities, etc.
-- ================================================================
CREATE TABLE IF NOT EXISTS guidebook_section (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guidebook_id INTEGER NOT NULL,

    -- Section Details
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    section_type TEXT, -- amenities, recommendations, appliances, trash, laundry, etc.
    icon TEXT, -- emoji or icon identifier

    -- Display
    display_order INTEGER DEFAULT 0,
    is_visible INTEGER DEFAULT 1,

    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (guidebook_id) REFERENCES property_guidebook(id) ON DELETE CASCADE
);

CREATE INDEX idx_section_guidebook ON guidebook_section(guidebook_id);
CREATE INDEX idx_section_order ON guidebook_section(display_order);
CREATE INDEX idx_section_visible ON guidebook_section(is_visible);

-- ================================================================
-- GUEST ACCESS CODES TABLE
-- Temporary access codes for guests to view guidebook
-- ================================================================
CREATE TABLE IF NOT EXISTS guest_access_code (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    booking_id INTEGER,

    -- Access Code
    access_code TEXT NOT NULL UNIQUE,
    guest_name TEXT NOT NULL,
    guest_email TEXT,
    guest_phone TEXT,

    -- Validity
    valid_from TEXT NOT NULL,
    valid_until TEXT NOT NULL,

    -- Usage Tracking
    first_accessed TEXT,
    last_accessed TEXT,
    access_count INTEGER DEFAULT 0,

    -- Status
    is_active INTEGER DEFAULT 1,
    notes TEXT,

    created_at TEXT DEFAULT (datetime('now')),
    created_by_id INTEGER NOT NULL,

    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE,
    FOREIGN KEY (booking_id) REFERENCES calendar_events(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_id) REFERENCES users(id)
);

CREATE INDEX idx_access_code_property ON guest_access_code(property_id);
CREATE INDEX idx_access_code_code ON guest_access_code(access_code);
CREATE INDEX idx_access_code_booking ON guest_access_code(booking_id);
CREATE INDEX idx_access_code_dates ON guest_access_code(valid_from, valid_until);
CREATE INDEX idx_access_code_active ON guest_access_code(is_active);

-- ================================================================
-- LOCAL RECOMMENDATIONS TABLE
-- Restaurants, attractions, services near property
-- ================================================================
CREATE TABLE IF NOT EXISTS local_recommendation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,

    -- Business Info
    name TEXT NOT NULL,
    category TEXT NOT NULL, -- restaurant, attraction, grocery, pharmacy, hospital, etc.
    description TEXT,

    -- Contact
    phone TEXT,
    website TEXT,
    address TEXT,

    -- Details
    distance_miles REAL,
    price_range TEXT, -- $, $$, $$$, $$$$
    rating REAL, -- 0-5

    -- Host Notes
    notes TEXT,
    is_favorite INTEGER DEFAULT 0,

    -- Display
    display_order INTEGER DEFAULT 0,
    is_visible INTEGER DEFAULT 1,

    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE
);

CREATE INDEX idx_recommendation_property ON local_recommendation(property_id);
CREATE INDEX idx_recommendation_category ON local_recommendation(category);
CREATE INDEX idx_recommendation_visible ON local_recommendation(is_visible);
CREATE INDEX idx_recommendation_favorite ON local_recommendation(is_favorite);

-- ================================================================
-- SAMPLE DATA
-- Default guidebook templates
-- ================================================================

-- Note: Guidebooks will be created when property owners set them up
-- Access codes generated per booking

-- ================================================================
-- VIEWS FOR GUEST PORTAL
-- ================================================================

-- Active access codes view
CREATE VIEW IF NOT EXISTS active_access_codes AS
SELECT
    gac.id,
    gac.access_code,
    gac.guest_name,
    gac.property_id,
    p.name as property_name,
    p.address as property_address,
    gac.valid_from,
    gac.valid_until,
    gac.access_count,
    gac.last_accessed,
    CASE
        WHEN date('now') < gac.valid_from THEN 'future'
        WHEN date('now') > gac.valid_until THEN 'expired'
        WHEN gac.is_active = 0 THEN 'disabled'
        ELSE 'active'
    END as status
FROM guest_access_code gac
LEFT JOIN property p ON gac.property_id = p.id
WHERE gac.is_active = 1;

-- Published guidebooks view
CREATE VIEW IF NOT EXISTS published_guidebooks AS
SELECT
    pg.id,
    pg.property_id,
    p.name as property_name,
    p.address as property_address,
    p.image_url as property_image,
    pg.welcome_message,
    pg.checkin_time,
    pg.checkout_time,
    pg.wifi_network,
    pg.emergency_contact,
    pg.emergency_phone,
    pg.last_updated,
    (SELECT COUNT(*) FROM guidebook_section WHERE guidebook_id = pg.id AND is_visible = 1) as section_count,
    (SELECT COUNT(*) FROM local_recommendation WHERE property_id = p.id AND is_visible = 1) as recommendation_count
FROM property_guidebook pg
LEFT JOIN property p ON pg.property_id = p.id
WHERE pg.is_published = 1;
