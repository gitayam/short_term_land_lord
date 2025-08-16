/**
 * Smart Form Helpers for Property Creation
 * Provides auto-complete, validation, and intelligent suggestions
 */

class PropertyFormHelpers {
    constructor() {
        this.initializeAddressAutocomplete();
        this.initializeSmartDefaults();
        this.initializeFormPersistence();
    }

    /**
     * Initialize Google Places Autocomplete for address field
     */
    initializeAddressAutocomplete() {
        if (typeof google !== 'undefined' && google.maps && google.maps.places) {
            const addressInput = document.getElementById('street_address');
            if (addressInput) {
                const autocomplete = new google.maps.places.Autocomplete(addressInput, {
                    types: ['address'],
                    componentRestrictions: { country: 'us' }
                });

                autocomplete.addListener('place_changed', () => {
                    const place = autocomplete.getPlace();
                    this.fillAddressFields(place);
                });
            }
        }
    }

    /**
     * Fill address fields from Google Places result
     */
    fillAddressFields(place) {
        if (!place.address_components) return;

        const addressComponents = {};
        place.address_components.forEach(component => {
            const type = component.types[0];
            addressComponents[type] = component.long_name;
        });

        // Fill form fields
        if (addressComponents.locality) {
            document.getElementById('city').value = addressComponents.locality;
        }
        if (addressComponents.administrative_area_level_1) {
            document.getElementById('state').value = addressComponents.administrative_area_level_1;
        }
        if (addressComponents.postal_code) {
            document.getElementById('zip_code').value = addressComponents.postal_code;
        }
        if (addressComponents.country) {
            document.getElementById('country').value = addressComponents.country;
        }

        // Suggest property name if not filled
        const nameField = document.getElementById('name');
        if (!nameField.value && addressComponents.street_number && addressComponents.route) {
            const suggestedName = `${addressComponents.street_number} ${addressComponents.route}`;
            nameField.placeholder = `e.g., "${suggestedName} Property"`;
        }

        // Auto-detect timezone and suggest check-in/out times
        this.suggestTimesFromLocation(place.geometry?.location);
    }

    /**
     * Suggest check-in/out times based on location timezone
     */
    suggestTimesFromLocation(location) {
        if (!location) return;

        // This would typically use a timezone API
        // For now, we'll use common defaults for US regions
        const checkinField = document.getElementById('checkin_time');
        const checkoutField = document.getElementById('checkout_time');

        if (!checkinField.value) {
            checkinField.value = '15:00';
            this.showSuggestionTooltip(checkinField, 'Standard 3:00 PM check-in suggested');
        }

        if (!checkoutField.value) {
            checkoutField.value = '11:00';
            this.showSuggestionTooltip(checkoutField, 'Standard 11:00 AM check-out suggested');
        }
    }

    /**
     * Initialize smart defaults based on property type
     */
    initializeSmartDefaults() {
        const propertyTypeField = document.getElementById('property_type');
        if (propertyTypeField) {
            propertyTypeField.addEventListener('change', (e) => {
                this.applyPropertyTypeDefaults(e.target.value);
            });
        }
    }

    /**
     * Apply smart defaults based on property type
     */
    applyPropertyTypeDefaults(propertyType) {
        const suggestions = {
            'house': {
                bedrooms: 3,
                bathrooms: 2,
                description: 'Beautiful house perfect for families and groups'
            },
            'suite': {
                bedrooms: 1,
                bathrooms: 1,
                description: 'Comfortable suite with hotel-style amenities'
            },
            'apartment': {
                bedrooms: 2,
                bathrooms: 1,
                description: 'Modern apartment in convenient location'
            },
            'condo': {
                bedrooms: 2,
                bathrooms: 2,
                description: 'Stylish condominium with great amenities'
            },
            'townhouse': {
                bedrooms: 3,
                bathrooms: 2.5,
                description: 'Spacious townhouse with multiple levels'
            },
            'duplex': {
                bedrooms: 2,
                bathrooms: 1.5,
                description: 'Duplex unit offering privacy and space'
            },
            'cabin': {
                bedrooms: 2,
                bathrooms: 1,
                description: 'Cozy cabin retreat perfect for getaways'
            },
            'cottage': {
                bedrooms: 2,
                bathrooms: 1,
                description: 'Charming cottage with rustic appeal'
            },
            'villa': {
                bedrooms: 4,
                bathrooms: 3,
                description: 'Luxurious villa with premium amenities'
            },
            'loft': {
                bedrooms: 1,
                bathrooms: 1,
                description: 'Urban loft with open floor plan and high ceilings'
            },
            'studio': {
                bedrooms: 0,
                bathrooms: 1,
                description: 'Efficient studio perfect for solo travelers'
            },
            'guesthouse': {
                bedrooms: 1,
                bathrooms: 1,
                description: 'Private guesthouse offering independence'
            },
            'tiny_house': {
                bedrooms: 1,
                bathrooms: 1,
                description: 'Unique tiny house experience with everything you need'
            },
            'boat': {
                bedrooms: 2,
                bathrooms: 1,
                description: 'Unique waterfront accommodation on a boat'
            },
            'rv': {
                bedrooms: 1,
                bathrooms: 1,
                description: 'Mobile home experience with all amenities'
            },
            'tree_house': {
                bedrooms: 1,
                bathrooms: 1,
                description: 'Magical tree house escape in nature'
            },
            'farm_stay': {
                bedrooms: 2,
                bathrooms: 1,
                description: 'Authentic farm experience with rural charm'
            },
            'castle': {
                bedrooms: 5,
                bathrooms: 4,
                description: 'Historic castle offering a royal experience'
            }
        };

        const defaults = suggestions[propertyType];
        if (!defaults) return;

        // Suggest values only if fields are empty
        const bedroomsField = document.getElementById('bedrooms');
        if (bedroomsField && !bedroomsField.value) {
            bedroomsField.placeholder = `Typical: ${defaults.bedrooms}`;
            this.showQuickFillButton(bedroomsField, defaults.bedrooms);
        }

        const bathroomsField = document.getElementById('bathrooms');
        if (bathroomsField && !bathroomsField.value) {
            bathroomsField.placeholder = `Typical: ${defaults.bathrooms}`;
            this.showQuickFillButton(bathroomsField, defaults.bathrooms);
        }

        const descriptionField = document.getElementById('description');
        if (descriptionField && !descriptionField.value) {
            descriptionField.placeholder = defaults.description;
        }
    }

    /**
     * Show a quick-fill button next to a field
     */
    showQuickFillButton(field, value) {
        // Remove existing quick-fill button
        const existingButton = field.parentNode.querySelector('.quick-fill-suggestion');
        if (existingButton) {
            existingButton.remove();
        }

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-sm btn-outline-primary quick-fill-suggestion mt-1';
        button.innerHTML = `<i class="fas fa-magic"></i> Use ${value}`;
        button.onclick = () => {
            field.value = value;
            button.remove();
            field.focus();
        };

        field.parentNode.appendChild(button);

        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (button.parentNode) {
                button.remove();
            }
        }, 10000);
    }

    /**
     * Show a temporary tooltip with suggestions
     */
    showSuggestionTooltip(field, message) {
        const tooltip = document.createElement('div');
        tooltip.className = 'alert alert-info alert-sm mt-1';
        tooltip.innerHTML = `<i class="fas fa-lightbulb"></i> ${message}`;
        tooltip.style.fontSize = '0.875rem';
        tooltip.style.padding = '0.5rem';

        field.parentNode.appendChild(tooltip);

        setTimeout(() => {
            if (tooltip.parentNode) {
                tooltip.remove();
            }
        }, 5000);
    }

    /**
     * Initialize form persistence to save progress
     */
    initializeFormPersistence() {
        const form = document.getElementById('propertyForm');
        if (!form) return;

        // Save form data on input
        form.addEventListener('input', this.debounce(() => {
            this.saveFormProgress();
        }, 2000));

        // Restore form data on load
        this.restoreFormProgress();
    }

    /**
     * Save current form progress to localStorage
     */
    saveFormProgress() {
        const formData = new FormData(document.getElementById('propertyForm'));
        const data = {};

        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }

        localStorage.setItem('propertyFormProgress', JSON.stringify(data));
        this.showProgressSavedIndicator();
    }

    /**
     * Restore form progress from localStorage
     */
    restoreFormProgress() {
        const saved = localStorage.getItem('propertyFormProgress');
        if (!saved) return;

        try {
            const data = JSON.parse(saved);
            let hasData = false;

            for (let [key, value] of Object.entries(data)) {
                const field = document.querySelector(`[name="${key}"]`);
                if (field && value) {
                    field.value = value;
                    hasData = true;
                }
            }

            if (hasData) {
                this.showProgressRestoredMessage();
            }
        } catch (e) {
            console.warn('Could not restore form progress:', e);
        }
    }

    /**
     * Show progress saved indicator
     */
    showProgressSavedIndicator() {
        const indicator = document.getElementById('progress-indicator') || this.createProgressIndicator();
        indicator.innerHTML = '<i class="fas fa-check text-success"></i> Progress saved';
        indicator.style.display = 'block';

        setTimeout(() => {
            indicator.style.display = 'none';
        }, 2000);
    }

    /**
     * Show progress restored message
     */
    showProgressRestoredMessage() {
        const alert = document.createElement('div');
        alert.className = 'alert alert-info alert-dismissible fade show';
        alert.innerHTML = `
            <i class="fas fa-history"></i> Your previous progress has been restored.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('.property-form-container');
        container.insertBefore(alert, container.firstChild);
    }

    /**
     * Create progress indicator element
     */
    createProgressIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'progress-indicator';
        indicator.className = 'position-fixed bottom-0 end-0 m-3 alert alert-light border';
        indicator.style.display = 'none';
        indicator.style.zIndex = '9999';

        document.body.appendChild(indicator);
        return indicator;
    }

    /**
     * Clear saved form progress
     */
    clearFormProgress() {
        localStorage.removeItem('propertyFormProgress');
    }

    /**
     * Debounce function to limit rapid calls
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Validate calendar URLs from known platforms
     */
    static validateCalendarUrl(url) {
        if (!url) return { valid: false, message: '' };

        const patterns = {
            airbnb: /airbnb\.com.*\.ics/i,
            vrbo: /vrbo\.com.*\.ics/i,
            booking: /booking\.com.*\.ics/i,
            generic: /\.ics$/i
        };

        for (let [platform, pattern] of Object.entries(patterns)) {
            if (pattern.test(url)) {
                return {
                    valid: true,
                    platform: platform === 'generic' ? 'iCal' : platform.toUpperCase(),
                    message: `Valid ${platform === 'generic' ? 'iCal' : platform.toUpperCase()} calendar URL`
                };
            }
        }

        return {
            valid: false,
            message: 'URL should be an iCal (.ics) file from Airbnb, VRBO, or Booking.com'
        };
    }

    /**
     * Get property suggestions based on address
     */
    static async getPropertySuggestions(address) {
        try {
            // This would typically call a real estate API
            const suggestions = {
                'North Carolina': {
                    propertyTypes: ['cabin', 'house', 'cottage'],
                    avgSize: 1200,
                    commonAmenities: ['fireplace', 'deck', 'mountain_view']
                },
                'Florida': {
                    propertyTypes: ['condo', 'house', 'villa'],
                    avgSize: 1500,
                    commonAmenities: ['pool', 'beach_access', 'balcony']
                },
                'California': {
                    propertyTypes: ['apartment', 'condo', 'house'],
                    avgSize: 1000,
                    commonAmenities: ['patio', 'parking', 'modern_kitchen']
                }
            };

            // Simple matching based on address
            for (let [state, data] of Object.entries(suggestions)) {
                if (address.toLowerCase().includes(state.toLowerCase())) {
                    return data;
                }
            }

            return null;
        } catch (error) {
            console.warn('Could not get property suggestions:', error);
            return null;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.propertyFormHelpers = new PropertyFormHelpers();
});

// Global functions for template use
window.PropertyFormHelpers = PropertyFormHelpers;