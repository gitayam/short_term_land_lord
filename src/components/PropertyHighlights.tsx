/**
 * Property Highlights Component
 * Displays top 3-4 key features as badges
 */

interface Property {
  pets_allowed?: boolean;
  allow_early_checkin?: boolean;
  allow_late_checkout?: boolean;
  amenities?: string[];
  max_guests?: number;
  property_type?: string;
  city?: string;
}

interface PropertyHighlightsProps {
  property: Property;
}

export function PropertyHighlights({ property }: PropertyHighlightsProps) {
  const highlights: Array<{ icon: string; text: string }> = [];

  // Pet-friendly
  if (property.pets_allowed) {
    highlights.push({ icon: '🐾', text: 'Pet-Friendly' });
  }

  // Free parking
  if (property.amenities?.includes('parking') || property.amenities?.includes('free_parking')) {
    highlights.push({ icon: '🅿️', text: 'Free Parking' });
  }

  // WiFi
  if (property.amenities?.includes('wifi')) {
    highlights.push({ icon: '📶', text: 'High-Speed WiFi' });
  }

  // Early check-in / Late checkout
  if (property.allow_early_checkin || property.allow_late_checkout) {
    highlights.push({ icon: '🕐', text: 'Flexible Check Times' });
  }

  // Full kitchen
  if (property.amenities?.includes('kitchen')) {
    highlights.push({ icon: '🍳', text: 'Full Kitchen' });
  }

  // Workspace
  if (property.amenities?.includes('workspace')) {
    highlights.push({ icon: '💼', text: 'Workspace' });
  }

  // Self check-in (if we add this feature later)
  // highlights.push({ icon: '🔑', text: 'Self Check-In' });

  // Near downtown (if city is known)
  if (property.city?.toLowerCase() === 'fayetteville') {
    highlights.push({ icon: '🏙️', text: 'Near Downtown' });
  }

  // Limit to top 4 highlights
  const displayHighlights = highlights.slice(0, 4);

  if (displayHighlights.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {displayHighlights.map((highlight, index) => (
        <span
          key={index}
          className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full"
        >
          <span>{highlight.icon}</span>
          <span>{highlight.text}</span>
        </span>
      ))}
    </div>
  );
}
