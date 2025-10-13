-- Customer Ratings System Migration
-- Allows property owners to rate staff after work completion

-- Staff ratings table
CREATE TABLE IF NOT EXISTS staff_rating (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,
    rated_by_id INTEGER NOT NULL,
    property_id INTEGER,
    work_log_id INTEGER,
    repair_request_id INTEGER,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    quality_rating INTEGER CHECK (quality_rating >= 1 AND quality_rating <= 5),
    timeliness_rating INTEGER CHECK (timeliness_rating >= 1 AND timeliness_rating <= 5),
    communication_rating INTEGER CHECK (communication_rating >= 1 AND communication_rating <= 5),
    professionalism_rating INTEGER CHECK (professionalism_rating >= 1 AND professionalism_rating <= 5),
    comment TEXT,
    is_anonymous INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (rated_by_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE SET NULL,
    FOREIGN KEY (work_log_id) REFERENCES staff_work_log(id) ON DELETE SET NULL,
    FOREIGN KEY (repair_request_id) REFERENCES repair_request(id) ON DELETE SET NULL
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_staff_rating_worker ON staff_rating(worker_id);
CREATE INDEX IF NOT EXISTS idx_staff_rating_property ON staff_rating(property_id);
CREATE INDEX IF NOT EXISTS idx_staff_rating_created ON staff_rating(created_at);

-- Staff rating responses (optional - workers can respond to ratings)
CREATE TABLE IF NOT EXISTS staff_rating_response (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rating_id INTEGER NOT NULL,
    worker_id INTEGER NOT NULL,
    response_text TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (rating_id) REFERENCES staff_rating(id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rating_response_rating ON staff_rating_response(rating_id);
