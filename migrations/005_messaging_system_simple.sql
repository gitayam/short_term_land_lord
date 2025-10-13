-- Messaging System Migration (Simplified without FK constraints)
-- Created: 2025-10-11

-- Message Templates Table
CREATE TABLE IF NOT EXISTS message_template (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  subject TEXT,
  body TEXT NOT NULL,
  variables TEXT,
  channel TEXT DEFAULT 'email',
  is_active INTEGER DEFAULT 1,
  created_by_id TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  last_updated TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_message_template_category ON message_template(category);
CREATE INDEX IF NOT EXISTS idx_message_template_active ON message_template(is_active);

-- Messages Table
CREATE TABLE IF NOT EXISTS message (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  sender_id TEXT NOT NULL,
  recipient_id TEXT NOT NULL,
  subject TEXT,
  body TEXT NOT NULL,
  message_type TEXT DEFAULT 'direct',
  priority TEXT DEFAULT 'normal',
  is_read INTEGER DEFAULT 0,
  read_at TEXT,
  parent_message_id TEXT,
  property_id TEXT,
  booking_id TEXT,
  task_id TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_message_recipient ON message(recipient_id);
CREATE INDEX IF NOT EXISTS idx_message_sender ON message(sender_id);
CREATE INDEX IF NOT EXISTS idx_message_created ON message(created_at);
CREATE INDEX IF NOT EXISTS idx_message_read ON message(is_read);

-- SMS Log Table
CREATE TABLE IF NOT EXISTS sms_log (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  recipient_phone TEXT NOT NULL,
  recipient_name TEXT,
  recipient_user_id TEXT,
  message_body TEXT NOT NULL,
  template_id TEXT,
  status TEXT DEFAULT 'pending',
  twilio_sid TEXT,
  twilio_status TEXT,
  error_message TEXT,
  segments INTEGER DEFAULT 1,
  cost REAL,
  sent_by_id TEXT NOT NULL,
  sent_at TEXT DEFAULT (datetime('now')),
  delivered_at TEXT,
  property_id TEXT,
  booking_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_sms_log_recipient ON sms_log(recipient_phone);
CREATE INDEX IF NOT EXISTS idx_sms_log_status ON sms_log(status);
CREATE INDEX IF NOT EXISTS idx_sms_log_sent_at ON sms_log(sent_at);

-- Email Log Table
CREATE TABLE IF NOT EXISTS email_log (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  recipient_email TEXT NOT NULL,
  recipient_name TEXT,
  recipient_user_id TEXT,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  template_id TEXT,
  status TEXT DEFAULT 'pending',
  ses_message_id TEXT,
  error_message TEXT,
  sent_by_id TEXT NOT NULL,
  sent_at TEXT DEFAULT (datetime('now')),
  opened_at TEXT,
  clicked_at TEXT,
  property_id TEXT,
  booking_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_email_log_recipient ON email_log(recipient_email);
CREATE INDEX IF NOT EXISTS idx_email_log_status ON email_log(status);
CREATE INDEX IF NOT EXISTS idx_email_log_sent_at ON email_log(sent_at);

-- Default Templates
INSERT OR IGNORE INTO message_template (id, name, category, subject, body, variables, channel, created_by_id) VALUES
  ('welcome-guest', 'Welcome Guest', 'welcome', 'Welcome to {{property_name}}!',
   'Hi {{guest_name}},

Welcome to {{property_name}}! We''re excited to host you.

Your check-in is on {{checkin_date}} at {{checkin_time}}.
Check-out is on {{checkout_date}} at {{checkout_time}}.

Your access code: {{access_code}}

If you have any questions, feel free to reach out!',
   '["property_name","guest_name","checkin_date","checkin_time","checkout_date","checkout_time","access_code"]',
   'email', 'system'),

  ('checkin-reminder', 'Check-in Reminder', 'reminder', 'Check-in Tomorrow',
   'Hi {{guest_name}},

This is a reminder that your check-in is tomorrow at {{checkin_time}}.

Property: {{property_name}}
Address: {{property_address}}
Access Code: {{access_code}}

We look forward to hosting you!',
   '["guest_name","checkin_time","property_name","property_address","access_code"]',
   'both', 'system'),

  ('checkout-reminder', 'Check-out Reminder', 'reminder', 'Check-out Today',
   'Hi {{guest_name}},

Thank you for staying with us! Check-out is today at {{checkout_time}}.

Please remember to:
- Lock all doors and windows
- Turn off lights and appliances
- Leave keys as instructed

We hope you enjoyed your stay!',
   '["guest_name","checkout_time"]',
   'both', 'system');
