-- Migration: Add guest capacity, pet policy, and pricing fields
-- Version: 2.2.0
-- Date: 2025-10-13

-- Add guest capacity fields
ALTER TABLE property ADD COLUMN max_guests INTEGER DEFAULT 4;
ALTER TABLE property ADD COLUMN min_guests INTEGER DEFAULT 1;

-- Add pet policy fields
ALTER TABLE property ADD COLUMN pets_allowed INTEGER DEFAULT 0; -- boolean
ALTER TABLE property ADD COLUMN max_pets INTEGER DEFAULT 0;
ALTER TABLE property ADD COLUMN pet_fee REAL DEFAULT 0.00;
ALTER TABLE property ADD COLUMN pet_fee_per_pet INTEGER DEFAULT 1; -- boolean: charge per pet or flat fee

-- Add early/late checkin options
ALTER TABLE property ADD COLUMN allow_early_checkin INTEGER DEFAULT 1; -- boolean
ALTER TABLE property ADD COLUMN allow_late_checkout INTEGER DEFAULT 1; -- boolean
ALTER TABLE property ADD COLUMN early_checkin_fee REAL DEFAULT 20.00;
ALTER TABLE property ADD COLUMN late_checkout_fee REAL DEFAULT 20.00;
ALTER TABLE property ADD COLUMN early_checkin_hours INTEGER DEFAULT 2; -- how many hours early
ALTER TABLE property ADD COLUMN late_checkout_hours INTEGER DEFAULT 2; -- how many hours late

-- Add pricing fields if they don't exist
ALTER TABLE property ADD COLUMN nightly_rate REAL DEFAULT 100.00;
ALTER TABLE property ADD COLUMN cleaning_fee REAL DEFAULT 75.00;
ALTER TABLE property ADD COLUMN security_deposit REAL DEFAULT 0.00;
ALTER TABLE property ADD COLUMN weekend_rate REAL DEFAULT NULL; -- optional weekend override
ALTER TABLE property ADD COLUMN min_nights INTEGER DEFAULT 1;
ALTER TABLE property ADD COLUMN max_nights INTEGER DEFAULT 30;

-- Add location display fields
ALTER TABLE property ADD COLUMN display_address TEXT DEFAULT NULL; -- approximate address for public display
ALTER TABLE property ADD COLUMN neighborhood TEXT DEFAULT NULL;
ALTER TABLE property ADD COLUMN approximate_latitude REAL DEFAULT NULL; -- rounded for privacy
ALTER TABLE property ADD COLUMN approximate_longitude REAL DEFAULT NULL; -- rounded for privacy

-- Comments for clarity:
-- max_guests: Maximum number of guests allowed
-- pets_allowed: Whether pets are allowed (0=no, 1=yes)
-- max_pets: Maximum number of pets if allowed
-- pet_fee: Fee for bringing pets (flat or per pet based on pet_fee_per_pet)
-- early_checkin_fee/late_checkout_fee: Add-on fees (not guaranteed)
-- nightly_rate: Base nightly rate
-- cleaning_fee: One-time cleaning fee per stay
-- display_address: Approximate address shown to guests (e.g., "Downtown Fayetteville")
-- approximate_lat/lon: Rounded coordinates for map display (not exact location)
