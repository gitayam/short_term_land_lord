# Property Type Icons

This directory contains icons for different property types supported in the system.

## Icon Files
- `house.svg` - Icon for houses 🏠
- `suite.svg` - Icon for suites 🏢
- `apartment.svg` - Icon for apartments 🏢
- `condo.svg` - Icon for condominiums 🏙️
- `townhouse.svg` - Icon for townhouses 🏘️
- `duplex.svg` - Icon for duplexes 🏠🏠
- `cabin.svg` - Icon for cabins 🌲
- `cottage.svg` - Icon for cottages 🏡
- `villa.svg` - Icon for villas 🏛️
- `other.svg` - Icon for other property types 🏗️

## Usage
These icons are used throughout the application to visually represent different property types. They are referenced in templates using the following path:

```html
<img src="{{ url_for('static', filename='img/property_types/[type].svg') }}" alt="[Type] Icon">
```

## Icon Design Guidelines
- All icons should be in SVG format for scalability
- Icons should be monochromatic for consistent styling
- Recommended size: 24x24px
- Use consistent stroke width
- Keep file size optimized 