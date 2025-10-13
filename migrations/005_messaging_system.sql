-- Messaging System Migration
-- Created: 2025-10-11
-- Purpose: Add messaging, SMS, and message templates functionality

-- Message Templates Table
CREATE TABLE IF NOT EXISTS message_template (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  name TEXT NOT NULL,
  category TEXT NOT NULL, -- welcome, reminder, confirmation, alert, custom
  subject TEXT,
  body TEXT NOT NULL,
  variables TEXT, -- JSON array of variable placeholders
  channel TEXT DEFAULT 'email', -- email, sms, both
  is_active INTEGER DEFAULT 1,
  created_by_id TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  last_updated TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (created_by_id) REFERENCES users(id)
);

CREATE INDEX idx_message_template_category ON message_template(category);
CREATE INDEX idx_message_template_active ON message_template(is_active);

-- Messages Table (Internal messaging)
CREATE TABLE IF NOT EXISTS message (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  sender_id TEXT NOT NULL,
  recipient_id TEXT NOT NULL,
  subject TEXT,
  body TEXT NOT NULL,
  message_type TEXT DEFAULT 'direct', -- direct, broadcast, system
  priority TEXT DEFAULT 'normal', -- low, normal, high, urgent
  is_read INTEGER DEFAULT 0,
  read_at TEXT,
  parent_message_id TEXT, -- for threading
  property_id TEXT, -- optional property context
  booking_id TEXT, -- optional booking context
  task_id TEXT, -- optional task context
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (sender_id) REFERENCES users(id),
  FOREIGN KEY (recipient_id) REFERENCES users(id),
  FOREIGN KEY (parent_message_id) REFERENCES message(id),
  FOREIGN KEY (property_id) REFERENCES property(id),
  FOREIGN KEY (task_id) REFERENCES task(id)
);

CREATE INDEX idx_message_recipient ON message(recipient_id);
CREATE INDEX idx_message_sender ON message(sender_id);
CREATE INDEX idx_message_created ON message(created_at);
CREATE INDEX idx_message_read ON message(is_read);
CREATE INDEX idx_message_property ON message(property_id);

-- SMS Log Table
CREATE TABLE IF NOT EXISTS sms_log (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  recipient_phone TEXT NOT NULL,
  recipient_name TEXT,
  recipient_user_id TEXT, -- if recipient is a user
  message_body TEXT NOT NULL,
  template_id TEXT, -- if sent from template
  status TEXT DEFAULT 'pending', -- pending, sent, delivered, failed, bounced
  twilio_sid TEXT, -- Twilio message SID
  twilio_status TEXT, -- Twilio status
  error_message TEXT,
  segments INTEGER DEFAULT 1, -- number of SMS segments
  cost REAL, -- cost in dollars
  sent_by_id TEXT NOT NULL,
  sent_at TEXT DEFAULT (datetime('now')),
  delivered_at TEXT,
  property_id TEXT, -- optional property context
  booking_id TEXT, -- optional booking context
  FOREIGN KEY (sent_by_id) REFERENCES users(id),
  FOREIGN KEY (recipient_user_id) REFERENCES users(id),
  FOREIGN KEY (template_id) REFERENCES message_template(id),
  FOREIGN KEY (property_id) REFERENCES property(id)
);

CREATE INDEX idx_sms_log_recipient ON sms_log(recipient_phone);
CREATE INDEX idx_sms_log_status ON sms_log(status);
CREATE INDEX idx_sms_log_sent_at ON sms_log(sent_at);
CREATE INDEX idx_sms_log_property ON sms_log(property_id);

-- Email Log Table (for tracking sent emails)
CREATE TABLE IF NOT EXISTS email_log (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  recipient_email TEXT NOT NULL,
  recipient_name TEXT,
  recipient_user_id TEXT,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  template_id TEXT,
  status TEXT DEFAULT 'pending', -- pending, sent, delivered, failed, bounced
  ses_message_id TEXT, -- AWS SES message ID
  error_message TEXT,
  sent_by_id TEXT NOT NULL,
  sent_at TEXT DEFAULT (datetime('now')),
  opened_at TEXT,
  clicked_at TEXT,
  property_id TEXT,
  booking_id TEXT,
  FOREIGN KEY (sent_by_id) REFERENCES users(id),
  FOREIGN KEY (recipient_user_id) REFERENCES users(id),
  FOREIGN KEY (template_id) REFERENCES message_template(id),
  FOREIGN KEY (property_id) REFERENCES property(id)
);

CREATE INDEX idx_email_log_recipient ON email_log(recipient_email);
CREATE INDEX idx_email_log_status ON email_log(status);
CREATE INDEX idx_email_log_sent_at ON email_log(sent_at);

-- Message Attachments Table
CREATE TABLE IF NOT EXISTS message_attachment (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  message_id TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_size INTEGER NOT NULL, -- bytes
  r2_key TEXT NOT NULL, -- R2 storage key
  uploaded_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (message_id) REFERENCES message(id) ON DELETE CASCADE
);

CREATE INDEX idx_message_attachment_message ON message_attachment(message_id);

-- Default Message Templates
INSERT INTO message_template (id, name, category, subject, body, variables, channel, created_by_id) VALUES
  ('welcome-guest', 'Welcome Guest', 'welcome', 'Welcome to {{property_name}}!',
   'Hi {{guest_name}},\n\nWelcome to {{property_name}}! We''re excited to host you.\n\nYour check-in is on {{checkin_date}} at {{checkin_time}}.\nCheck-out is on {{checkout_date}} at {{checkout_time}}.\n\nYour access code: {{access_code}}\n\nIf you have any questions, feel free to reach out!\n\nBest regards,\n{{host_name}}',
   '["property_name", "guest_name", "checkin_date", "checkin_time", "checkout_date", "checkout_time", "access_code", "host_name"]',
   'email', 'system'),

  ('checkin-reminder', 'Check-in Reminder', 'reminder', 'Check-in Tomorrow at {{property_name}}',
   'Hi {{guest_name}},\n\nThis is a friendly reminder that your check-in is tomorrow at {{checkin_time}}.\n\nProperty: {{property_name}}\nAddress: {{property_address}}\nAccess Code: {{access_code}}\n\nWe look forward to hosting you!\n\nBest regards,\n{{host_name}}',
   '["property_name", "property_address", "guest_name", "checkin_time", "access_code", "host_name"]',
   'both', 'system'),

  ('checkout-reminder', 'Check-out Reminder', 'reminder', 'Check-out Today at {{checkout_time}}',
   'Hi {{guest_name}},\n\nThank you for staying with us! This is a reminder that check-out is today at {{checkout_time}}.\n\nPlease remember to:\n- Lock all doors and windows\n- Turn off lights and appliances\n- Leave keys as instructed\n\nWe hope you enjoyed your stay!\n\nBest regards,\n{{host_name}}',
   '["guest_name", "checkout_time", "host_name"]',
   'both', 'system'),

  ('cleaning-assigned', 'Cleaning Task Assigned', 'alert', 'New Cleaning Assignment',
   'Hi {{cleaner_name}},\n\nYou have been assigned a cleaning task:\n\nProperty: {{property_name}}\nAddress: {{property_address}}\nScheduled: {{cleaning_date}} at {{cleaning_time}}\n\nPlease confirm receipt of this message.\n\nThank you!',
   '["cleaner_name", "property_name", "property_address", "cleaning_date", "cleaning_time"]',
   'sms', 'system'),

  ('booking-confirmation', 'Booking Confirmation', 'confirmation', 'Booking Confirmed for {{property_name}}',
   'Hi {{guest_name}},\n\nYour booking has been confirmed!\n\nProperty: {{property_name}}\nCheck-in: {{checkin_date}} at {{checkin_time}}\nCheck-out: {{checkout_date}} at {{checkout_time}}\nGuests: {{guest_count}}\nTotal: ${{booking_amount}}\n\nWe''ll send you the access code and additional details closer to your check-in date.\n\nLooking forward to hosting you!\n\nBest regards,\n{{host_name}}',
   '["property_name", "guest_name", "checkin_date", "checkin_time", "checkout_date", "checkout_time", "guest_count", "booking_amount", "host_name"]',
   'email', 'system');
