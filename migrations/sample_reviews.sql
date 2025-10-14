-- Sample Reviews for Property 4 (Elegant Suite)

INSERT INTO property_reviews (
  property_id, guest_name, guest_email, rating, title, comment,
  cleanliness_rating, communication_rating, accuracy_rating, location_rating, value_rating,
  is_verified, is_published, created_at
) VALUES
(
  4, 'Sarah Johnson', 'sarah.j@example.com', 5, 'Perfect Stay!',
  'The suite was absolutely beautiful and spotlessly clean. The host was very responsive and helpful. The location is perfect for exploring downtown Fayetteville. Would definitely stay again!',
  5, 5, 5, 5, 5,
  1, 1, '2025-10-01 14:30:00'
),
(
  4, 'Michael Chen', 'michael.chen@example.com', 5, 'Exceeded expectations',
  'This place is even better than the photos! Everything was immaculate and the amenities were top-notch. The guidebook with local recommendations was super helpful. Highly recommend!',
  5, 5, 5, 4, 5,
  1, 1, '2025-09-28 16:45:00'
),
(
  4, 'Emily Rodriguez', 'emily.r@example.com', 4, 'Great location and clean',
  'Really enjoyed our stay. The suite was clean and comfortable. Only minor issue was parking but that is understandable for downtown. The coffee maker was a nice touch!',
  5, 4, 5, 5, 4,
  1, 1, '2025-09-20 10:15:00'
),
(
  4, 'David Thompson', 'david.t@example.com', 5, 'Best Airbnb experience',
  'This was hands down the best Airbnb we have stayed at. The host thought of everything - from the welcome basket to the detailed check-in instructions. The space was beautiful and comfortable.',
  5, 5, 5, 5, 5,
  1, 1, '2025-09-15 19:20:00'
),
(
  4, 'Lisa Martinez', 'lisa.m@example.com', 5, 'Wonderful stay',
  'We had a wonderful time at this property. It was exactly as described, clean, and in a great location. The host was very accommodating with our late check-in. Thank you!',
  5, 5, 5, 5, 5,
  1, 1, '2025-09-08 12:00:00'
);

-- Update property average rating and total reviews
UPDATE property
SET average_rating = (
  SELECT AVG(rating) FROM property_reviews WHERE property_id = 4 AND is_published = 1
),
total_reviews = (
  SELECT COUNT(*) FROM property_reviews WHERE property_id = 4 AND is_published = 1
)
WHERE id = 4;
