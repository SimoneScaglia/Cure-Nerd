// Contact Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Apply site branding and theming
    applySiteBranding();
    
    // Initialize page transitions
    initializePageTransitions();
    
    // Add form animations
    addFormAnimations();
    
    // Set up form submission handling
    setupFormSubmission();
});

// Function to apply site branding and dynamic theming
function applySiteBranding() {
    // Set page title and favicon
    document.title = 'Contact Us - CustomNerd';
    
    // Set favicon
    const favicon = document.querySelector('link[rel="icon"]') || document.createElement('link');
    favicon.rel = 'icon';
    favicon.href = 'assets/custom_nerd_default_logo.png';
    if (!document.querySelector('link[rel="icon"]')) {
        document.head.appendChild(favicon);
    }
    
    // Set logo with fallback
    setLogoWithFallback();
    
    // Apply background color from user_env.js
    if (window.env && window.env.FRONTEND_FLOW && window.env.FRONTEND_FLOW.STYLES) {
        const backgroundColor = window.env.FRONTEND_FLOW.STYLES.BACKGROUND_COLOR;
        if (backgroundColor) {
            document.body.style.backgroundColor = backgroundColor;
            document.documentElement.style.setProperty('--background-color', backgroundColor);
            
            // Apply background color to container
            let container = document.getElementById("container");
            if (container) {
                container.style.backgroundColor = backgroundColor;
            }
            
            // Force override any existing background colors with !important via CSS
            const style = document.createElement('style');
            style.textContent = `
                body { background-color: ${backgroundColor} !important; }
                #container { background-color: ${backgroundColor} !important; }
            `;
            document.head.appendChild(style);
        }
    }
    
    // Update glass element colors with delay to ensure background is applied
    setTimeout(() => {
        updateGlassElementColors();
    }, 200);
}

// Function to set logo with fallback
function setLogoWithFallback() {
    const logoElement = document.getElementById('site-logo');
    if (logoElement) {
        // Always use the default logo
        logoElement.src = 'assets/custom_nerd_default_logo.png';
        logoElement.alt = 'Custom Nerd Logo';
        logoElement.style.maxWidth = '250px';
        logoElement.style.height = 'auto';
    }
}

// Function to update glass element colors based on background
function updateGlassElementColors() {
    const bodyBgColor = window.getComputedStyle(document.body).backgroundColor;
    const container = document.getElementById('container');
    const containerBgColor = container ? window.getComputedStyle(container).backgroundColor : null;
    const root = document.documentElement;
    
    // Use container background if available, otherwise use body background
    const bgColor = containerBgColor && containerBgColor !== 'rgba(0, 0, 0, 0)' ? containerBgColor : bodyBgColor;
    
    // Parse RGB values from computed style (handles both rgb and rgba)
    const rgbMatch = bgColor.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)/);
    if (rgbMatch) {
        const r = parseInt(rgbMatch[1]);
        const g = parseInt(rgbMatch[2]);
        const b = parseInt(rgbMatch[3]);
        
        // Calculate luminance to determine if background is dark or light
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        
        // Get submit button color from user_env.js
        const submitButtonColor = window.env?.FRONTEND_FLOW?.STYLES?.SUBMIT_BUTTON_BG || '#007bff';
        
        if (luminance < 0.5) {
            // Dark background - use light colors
            root.style.setProperty('--text-color', '#ffffff');
            root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.3)');
            root.style.setProperty('--accent-text-color', submitButtonColor);
            root.style.setProperty('--accent-border-color', submitButtonColor + '66'); // Add transparency
            
            // Also set text color directly on elements as fallback
            document.body.style.color = '#ffffff';
            const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, a, span, input, textarea');
            textElements.forEach(el => {
                if (!el.classList.contains('contact-link')) {
                    el.style.color = '#ffffff';
                }
            });
        } else {
            // Light background - use dark colors
            root.style.setProperty('--text-color', '#1a202c');
            root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.2)');
            root.style.setProperty('--accent-text-color', submitButtonColor);
            root.style.setProperty('--accent-border-color', submitButtonColor + '4D'); // Add transparency
            
            // Also set text color directly on elements as fallback
            document.body.style.color = '#1a202c';
            const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, a, span, input, textarea');
            textElements.forEach(el => {
                if (!el.classList.contains('contact-link')) {
                    el.style.color = '#1a202c';
                }
            });
        }
    } else {
        // Fallback: check if background color is set to black
        if (bgColor.includes('rgb(0, 0, 0)') || bgColor.includes('rgba(0, 0, 0') || bgColor.includes('black')) {
            root.style.setProperty('--text-color', '#ffffff');
            root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.3)');
            root.style.setProperty('--accent-text-color', window.env?.FRONTEND_FLOW?.STYLES?.SUBMIT_BUTTON_BG || '#007bff');
            root.style.setProperty('--accent-border-color', (window.env?.FRONTEND_FLOW?.STYLES?.SUBMIT_BUTTON_BG || '#007bff') + '66');
            
            // Also set text color directly on elements as fallback
            document.body.style.color = '#ffffff';
            const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, a, span, input, textarea');
            textElements.forEach(el => {
                if (!el.classList.contains('contact-link')) {
                    el.style.color = '#ffffff';
                }
            });
        }
    }
}

// Function to initialize page transitions
function initializePageTransitions() {
    // Add page entry animation
    document.body.classList.add('page-transition');
    
    // Handle navigation link clicks
    const navLinks = document.querySelectorAll('.toolbar a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // Don't animate if it's the current page
            if (href === 'contact.html' || href === '#') {
                return;
            }
            
            e.preventDefault();
            
            // Add loading state to clicked link
            this.classList.add('nav-loading');
            
            // Add page exit animation
            document.body.classList.add('page-exit');
            
            // Navigate after animation
            setTimeout(() => {
                window.location.href = href;
            }, 400);
        });
    });
}

// Function to add form animations
function addFormAnimations() {
    const form = document.getElementById('contactForm');
    const inputs = form.querySelectorAll('input, textarea');
    
    // Add focus animations to inputs
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'translateY(-2px)';
            this.parentElement.style.transition = 'transform 0.3s ease';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'translateY(0)';
        });
    });
}

// Function to setup form submission handling
function setupFormSubmission() {
    const form = document.getElementById('contactForm');
    const submitButton = document.getElementById('submit');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Add submitting animation
        submitButton.classList.add('submitting');
        submitButton.disabled = true;
        
        // Simulate form processing (replace with actual EmailJS logic)
        setTimeout(() => {
            // Remove submitting animation
            submitButton.classList.remove('submitting');
            submitButton.disabled = false;
            
            // Add success animation
            submitButton.classList.add('success');
            setTimeout(() => {
                submitButton.classList.remove('success');
            }, 600);
            
            // Show success message
            showNotification('success', 'Thank you for your message! We\'ll get back to you soon.');
            
            // Reset form
            form.reset();
        }, 2000);
    });
}

// Function to show notifications
function showNotification(type, message) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-icon">
                ${type === 'success' ? '<i class="fas fa-check-circle"></i>' : 
                  type === 'error' ? '<i class="fas fa-exclamation-circle"></i>' : 
                  '<i class="fas fa-info-circle"></i>'}
            </div>
            <div class="notification-text">
                <div class="notification-message">${message}</div>
            </div>
        </div>
    `;
    
    // Add notification styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? 'linear-gradient(135deg, #28a745, #20c997)' : 
                    type === 'error' ? 'linear-gradient(135deg, #dc3545, #c82333)' : 
                    'linear-gradient(135deg, #17a2b8, #138496)'};
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        z-index: 10000;
        transform: translateX(100%);
        transition: transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        max-width: 300px;
        font-family: 'Open Sans', sans-serif;
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 5000);
}

// Function to handle window resize
window.addEventListener('resize', function() {
    // Update glass element colors on resize
    updateGlassElementColors();
});

// Function to handle page visibility change
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        // Update colors when page becomes visible
        updateGlassElementColors();
    }
});
