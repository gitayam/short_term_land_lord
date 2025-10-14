/**
 * Amenities Display Component
 * Shows property amenities with icons in a grid layout
 */

interface AmenitiesDisplayProps {
  amenities: string[];
  compact?: boolean;
}

const amenityConfig: Record<string, { icon: string; label: string }> = {
  wifi: { icon: '📶', label: 'WiFi' },
  kitchen: { icon: '🍳', label: 'Kitchen' },
  ac: { icon: '❄️', label: 'Air conditioning' },
  heating: { icon: '🔥', label: 'Heating' },
  tv: { icon: '📺', label: 'TV' },
  washer: { icon: '🧺', label: 'Washer' },
  dryer: { icon: '👕', label: 'Dryer' },
  parking: { icon: '🅿️', label: 'Free parking' },
  free_parking: { icon: '🅿️', label: 'Free parking' },
  pool: { icon: '🏊', label: 'Pool' },
  hot_tub: { icon: '🛁', label: 'Hot tub' },
  gym: { icon: '💪', label: 'Gym' },
  workspace: { icon: '💼', label: 'Dedicated workspace' },
  coffee_maker: { icon: '☕', label: 'Coffee maker' },
  dishwasher: { icon: '🍽️', label: 'Dishwasher' },
  microwave: { icon: '🔆', label: 'Microwave' },
  refrigerator: { icon: '🧊', label: 'Refrigerator' },
  oven: { icon: '🔥', label: 'Oven' },
  iron: { icon: '👔', label: 'Iron' },
  hair_dryer: { icon: '💨', label: 'Hair dryer' },
  hangers: { icon: '👗', label: 'Hangers' },
  shampoo: { icon: '🧴', label: 'Shampoo' },
  smoke_detector: { icon: '🚨', label: 'Smoke detector' },
  carbon_monoxide_detector: { icon: '⚠️', label: 'Carbon monoxide detector' },
  fire_extinguisher: { icon: '🧯', label: 'Fire extinguisher' },
  first_aid_kit: { icon: '⚕️', label: 'First aid kit' },
  essentials: { icon: '🧻', label: 'Essentials' },
  bed_linens: { icon: '🛏️', label: 'Bed linens' },
  extra_pillows: { icon: '🛋️', label: 'Extra pillows' },
  bbq_grill: { icon: '🍖', label: 'BBQ grill' },
  outdoor_furniture: { icon: '🪑', label: 'Outdoor furniture' },
  garden: { icon: '🌳', label: 'Garden' },
  balcony: { icon: '🏞️', label: 'Balcony' },
  patio: { icon: '🪴', label: 'Patio' },
  ev_charger: { icon: '🔌', label: 'EV charger' },
  elevator: { icon: '🛗', label: 'Elevator' },
  wheelchair_accessible: { icon: '♿', label: 'Wheelchair accessible' },
};

export function AmenitiesDisplay({ amenities, compact = false }: AmenitiesDisplayProps) {
  if (!amenities || amenities.length === 0) {
    return null;
  }

  const displayAmenities = compact ? amenities.slice(0, 6) : amenities;
  const hasMore = compact && amenities.length > 6;

  return (
    <div className="space-y-2">
      {!compact && (
        <h4 className="text-sm font-semibold text-gray-900">Amenities</h4>
      )}
      <div className={`grid ${compact ? 'grid-cols-2' : 'grid-cols-2 md:grid-cols-3'} gap-2`}>
        {displayAmenities.map((amenity) => {
          const config = amenityConfig[amenity] || { icon: '✓', label: amenity.replace(/_/g, ' ') };
          return (
            <div
              key={amenity}
              className="flex items-center gap-2 text-sm text-gray-700"
              title={config.label}
            >
              <span className="text-lg">{config.icon}</span>
              <span className="truncate">{config.label}</span>
            </div>
          );
        })}
      </div>
      {hasMore && (
        <p className="text-xs text-gray-500 mt-1">
          + {amenities.length - 6} more amenities
        </p>
      )}
    </div>
  );
}
