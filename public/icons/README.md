# PWA App Icons

This directory should contain app icons for the Progressive Web App (PWA).

## Required Icons

The following icon sizes are required (as specified in manifest.json):

- `icon-72x72.png` - 72x72 pixels
- `icon-96x96.png` - 96x96 pixels
- `icon-128x128.png` - 128x128 pixels
- `icon-144x144.png` - 144x144 pixels
- `icon-152x152.png` - 152x152 pixels (Apple touch icon)
- `icon-192x192.png` - 192x192 pixels (Android)
- `icon-384x384.png` - 384x384 pixels
- `icon-512x512.png` - 512x512 pixels (Android splash screen)

## Icon Design Guidelines

- **Maskable**: Icons should work with the "maskable" safe zone (80% of the icon area)
- **Simple**: Keep the design simple and recognizable at small sizes
- **Consistent**: Use the app's brand colors (primary: #2563eb - blue)
- **Background**: Consider both light and dark backgrounds
- **Format**: PNG with transparency (where appropriate)

## Generating Icons

You can use online tools like:

1. **PWA Builder** - https://www.pwabuilder.com/imageGenerator
2. **Favicon Generator** - https://realfavicongenerator.net/
3. **PWA Icon Generator** - https://tools.crawlink.com/tools/pwa-icon-generator/

Or use a design tool like Figma/Sketch and export at the required sizes.

## Quick Icon Template

For quick testing, you can create a simple icon with:

1. Create a 512x512 canvas
2. Add a blue (#2563eb) background
3. Add a house icon (🏠) or "STLL" text in white
4. Export at all required sizes

## Testing

After adding icons, test them by:

1. Deploying the app
2. Opening in Chrome DevTools > Application > Manifest
3. Checking that all icons load correctly
4. Testing install prompt on mobile devices
