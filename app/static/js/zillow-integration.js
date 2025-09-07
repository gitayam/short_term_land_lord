/**
 * Zillow Integration for Property Creation
 * Enhanced property data collection with modern UX patterns
 */

class ZillowIntegration {
    constructor() {
        this.apiEndpoint = '/api/zillow/property-data';
        this.isLoading = false;
        this.cache = new Map();
        
        this.init();
    }
    
    init() {
        // Find the address/URL input field
        this.addressInput = document.querySelector('#address_or_url, #property_address, #zillow_url');
        this.setupEventListeners();
        this.setupUI();
    }
    
    setupEventListeners() {
        if (!this.addressInput) return;
        
        // Fetch data when user stops typing
        let timeout;
        this.addressInput.addEventListener('input', (e) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const value = e.target.value.trim();
                if (value.length > 10) { // Minimum length for meaningful address
                    this.fetchPropertyData(value);
                }
            }, 1000); // Wait 1 second after user stops typing
        });
        
        // Also fetch on blur
        this.addressInput.addEventListener('blur', (e) => {
            const value = e.target.value.trim();
            if (value.length > 10) {
                this.fetchPropertyData(value);
            }
        });
    }
    
    setupUI() {
        if (!this.addressInput) return;
        
        // Add loading indicator
        this.loadingIndicator = this.createLoadingIndicator();
        this.addressInput.parentNode.appendChild(this.loadingIndicator);
        
        // Add status display
        this.statusDisplay = this.createStatusDisplay();
        this.addressInput.parentNode.appendChild(this.statusDisplay);
        
        // Add help text
        this.helpText = this.createHelpText();
        this.addressInput.parentNode.appendChild(this.helpText);
    }
    
    createLoadingIndicator() {
        const div = document.createElement('div');
        div.className = 'zillow-loading d-none';
        div.innerHTML = `
            <div class="d-flex align-items-center mt-2">
                <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <small class="text-muted">Fetching property details from Zillow...</small>
            </div>
        `;
        return div;
    }
    
    createStatusDisplay() {
        const div = document.createElement('div');
        div.className = 'zillow-status mt-2';
        return div;
    }
    
    createHelpText() {
        const div = document.createElement('div');
        div.className = 'zillow-help mt-1';
        div.innerHTML = `
            <small class="text-muted">
                💡 Enter a full address or Zillow URL to automatically fill property details
            </small>
        `;
        return div;
    }
    
    showLoading(show = true) {
        if (!this.loadingIndicator) return;
        
        if (show) {
            this.loadingIndicator.classList.remove('d-none');
            this.hideStatus();
        } else {
            this.loadingIndicator.classList.add('d-none');
        }
    }
    
    showStatus(message, type = 'info') {
        if (!this.statusDisplay) return;
        
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        this.statusDisplay.innerHTML = `
            <div class="alert ${alertClass} py-2 small" role="alert">
                ${message}
            </div>
        `;
        
        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => this.hideStatus(), 5000);
        }
    }
    
    hideStatus() {
        if (this.statusDisplay) {
            this.statusDisplay.innerHTML = '';
        }
    }
    
    async fetchPropertyData(addressOrUrl) {
        // Check cache first
        if (this.cache.has(addressOrUrl)) {
            const cachedData = this.cache.get(addressOrUrl);
            this.populateForm(cachedData);
            this.showStatus('✅ Property details loaded from cache', 'success');
            return;
        }
        
        this.isLoading = true;
        this.showLoading(true);
        
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    address_or_url: addressOrUrl
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.data) {
                // Cache successful results
                this.cache.set(addressOrUrl, result.data);
                
                // Populate form with retrieved data
                this.populateForm(result.data);
                this.showStatus('✅ Property details loaded successfully!', 'success');
                
                // Show preview
                this.showPropertyPreview(result.data);
                
            } else {
                const errorMsg = result.error || 'Could not fetch property details';
                this.showStatus(`⚠️ ${errorMsg}`, 'warning');
                
                // Still show help for manual entry
                this.showManualEntryHelp();
            }
            
        } catch (error) {
            console.error('Zillow fetch error:', error);
            this.showStatus('❌ Network error. Please check your connection.', 'error');
            
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }
    
    populateForm(data) {
        const fieldMappings = {
            'name': data.address ? `Property at ${data.address.split(',')[0]}` : '',
            'address': data.address || '',
            'bedrooms': data.bedrooms || '',
            'bathrooms': data.bathrooms || '',
            'square_feet': data.square_feet || '',
            'year_built': data.year_built || '',
            'property_type': data.property_type || '',
            'estimated_value': data.price || '',
            'description': data.description || ''
        };
        
        // Populate fields that exist in the form
        Object.entries(fieldMappings).forEach(([fieldName, value]) => {
            if (value) {
                const field = document.querySelector(`#${fieldName}, [name="${fieldName}"]`);
                if (field && !field.value) { // Only populate if field is empty
                    field.value = value;
                    
                    // Trigger change event for any listeners
                    field.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    // Visual feedback
                    field.classList.add('zillow-populated');
                    setTimeout(() => field.classList.remove('zillow-populated'), 2000);
                }
            }
        });
        
        // Set max guests based on bedrooms
        if (data.bedrooms) {
            const maxGuestsField = document.querySelector('#max_guests, [name="max_guests"]');
            if (maxGuestsField && !maxGuestsField.value) {
                maxGuestsField.value = Math.max(2, parseInt(data.bedrooms) * 2);
                maxGuestsField.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    }
    
    showPropertyPreview(data) {
        // Create or update property preview
        let preview = document.querySelector('.zillow-preview');
        if (!preview) {
            preview = document.createElement('div');
            preview.className = 'zillow-preview mt-3';
            this.statusDisplay.parentNode.appendChild(preview);
        }
        
        const priceDisplay = data.price ? 
            `<strong class="text-success">$${parseInt(data.price).toLocaleString()}</strong>` : 
            '<span class="text-muted">Price not available</span>';
        
        preview.innerHTML = `
            <div class="card border-success">
                <div class="card-header bg-light">
                    <h6 class="mb-0">
                        <i class="fas fa-home text-success me-2"></i>
                        Property Details Retrieved
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <strong>Address:</strong><br>
                            <span class="text-muted">${data.address || 'Not available'}</span>
                        </div>
                        <div class="col-md-6">
                            <strong>Price:</strong><br>
                            ${priceDisplay}
                        </div>
                        <div class="col-md-3">
                            <strong>Beds:</strong><br>
                            <span class="badge bg-primary">${data.bedrooms || '?'}</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Baths:</strong><br>
                            <span class="badge bg-primary">${data.bathrooms || '?'}</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Sq Ft:</strong><br>
                            <span class="badge bg-info">${data.square_feet ? parseInt(data.square_feet).toLocaleString() : '?'}</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Built:</strong><br>
                            <span class="badge bg-secondary">${data.year_built || '?'}</span>
                        </div>
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">
                            ✨ Form fields have been automatically populated. You can edit any details before saving.
                        </small>
                    </div>
                </div>
            </div>
        `;
        
        // Smooth scroll to preview
        setTimeout(() => {
            preview.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }
    
    showManualEntryHelp() {
        let helpDiv = document.querySelector('.zillow-manual-help');
        if (!helpDiv) {
            helpDiv = document.createElement('div');
            helpDiv.className = 'zillow-manual-help mt-3';
            this.statusDisplay.parentNode.appendChild(helpDiv);
        }
        
        helpDiv.innerHTML = `
            <div class="card border-warning">
                <div class="card-body">
                    <h6 class="card-title">
                        <i class="fas fa-edit text-warning me-2"></i>
                        Manual Entry Required
                    </h6>
                    <p class="card-text small mb-2">
                        We couldn't automatically fetch the property details. Please fill in the form manually.
                    </p>
                    <div class="small text-muted">
                        <strong>Tips for better results:</strong>
                        <ul class="mb-0 ps-3">
                            <li>Use the full address: "123 Main St, City, State ZIP"</li>
                            <li>Try the direct Zillow URL if you have it</li>
                            <li>Check spelling and ensure the property exists on Zillow</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
    
    getCSRFToken() {
        // Try to get CSRF token from meta tag or form
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) return csrfMeta.getAttribute('content');
        
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        if (csrfInput) return csrfInput.value;
        
        return '';
    }
}

// CSS for visual feedback
const style = document.createElement('style');
style.textContent = `
    .zillow-populated {
        background-color: #d4edda !important;
        border-color: #c3e6cb !important;
        transition: all 0.3s ease;
    }
    
    .zillow-loading .spinner-border {
        width: 1rem;
        height: 1rem;
    }
    
    .zillow-preview .card {
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .zillow-manual-help .card {
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
`;
document.head.appendChild(style);

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on property creation/edit pages
    if (document.querySelector('#property-form, .property-form, form[action*="property"]')) {
        window.zillowIntegration = new ZillowIntegration();
    }
});

// Export for manual initialization
window.ZillowIntegration = ZillowIntegration;