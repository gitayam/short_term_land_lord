-- Property Reviews and Ratings System
-- Allows guests to leave reviews after their stay

CREATE TABLE IF NOT EXISTS property_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  property_id INTEGER NOT NULL,
  booking_id INTEGER,
  guest_name TEXT NOT NULL,
  guest_email TEXT,
  rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
  title TEXT,
  comment TEXT,

  -- Category ratings (optional, 1-5 scale)
  cleanliness_rating INTEGER CHECK (cleanliness_rating >= 1 AND cleanliness_rating <= 5),
  communication_rating INTEGER CHECK (communication_rating >= 1 AND communication_rating <= 5),
  accuracy_rating INTEGER CHECK (accuracy_rating >= 1 AND accuracy_rating <= 5),
  location_rating INTEGER CHECK (location_rating >= 1 AND location_rating <= 5),
  value_rating INTEGER CHECK (value_rating >= 1 AND value_rating <= 5),

  -- Management
  is_verified BOOLEAN DEFAULT 0,
  is_published BOOLEAN DEFAULT 1,
  host_response TEXT,
  host_response_date TEXT,

  -- Metadata
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),

  FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reviews_property ON property_reviews(property_id, is_published);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON property_reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_created ON property_reviews(created_at DESC);

-- Add average rating column to property table
ALTER TABLE property ADD COLUMN average_rating REAL;
ALTER TABLE property ADD COLUMN total_reviews INTEGER DEFAULT 0;
