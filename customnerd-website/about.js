/**
 * Sets logo with fallback mechanism
 * @param {HTMLElement} logoElement - The logo image element
 * @param {string} primaryLogoPath - The primary logo path
 * @param {string} altText - Alt text for the logo
 */
function setLogoWithFallback(logoElement, primaryLogoPath, altText) {
    logoElement.alt = altText;
    
    // Try to load the primary logo first
    const primaryImg = new Image();
    primaryImg.onload = function() {
        logoElement.src = primaryLogoPath;
    };
    primaryImg.onerror = function() {
        // If primary logo fails to load, use the default fallback logo
        logoElement.src = "assets/custom_nerd_default_logo.png";
    };
    primaryImg.src = primaryLogoPath;
}

/**
 * Detects background color and sets appropriate text colors for glass elements
 */
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
            const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, a, span');
            textElements.forEach(el => {
                if (!el.classList.contains('team-icon') && !el.classList.contains('contact-link')) {
                    el.style.color = '#ffffff';
                }
            });
            
            // Special handling for features list - they have light background so need dark text
            const featuresListItems = document.querySelectorAll('.features-list li');
            featuresListItems.forEach(el => {
                el.style.color = '#1a202c'; // Dark text for light background
            });
        } else {
            // Light background - use dark colors
            root.style.setProperty('--text-color', '#1a202c');
            root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.2)');
            root.style.setProperty('--accent-text-color', submitButtonColor);
            root.style.setProperty('--accent-border-color', submitButtonColor + '4D'); // Add transparency
            
            // Also set text color directly on elements as fallback
            document.body.style.color = '#1a202c';
            const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, a, span');
            textElements.forEach(el => {
                if (!el.classList.contains('team-icon') && !el.classList.contains('contact-link')) {
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
            const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, a, span');
            textElements.forEach(el => {
                if (!el.classList.contains('team-icon') && !el.classList.contains('contact-link')) {
                    el.style.color = '#ffffff';
                }
            });
        }
    }
}

/**
 * Apply site branding and styling from user_env.js configuration
 * This ensures consistent styling with the main site
 */
function applySiteBranding() {
    console.log("Applying site settings from user_env.js to about page...");

    // Set Page Title
    document.title = `${window.env.FRONTEND_FLOW.SITE_NAME} - About`;

    // Set Favicon (Emoji-based)
    let favicon = document.createElement("link");
    favicon.rel = "icon";
    favicon.href = `data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>${window.env.FRONTEND_FLOW.SITE_ICON}</text></svg>`;
    document.head.appendChild(favicon);

    // Set Logo with fixed default logo
    let logoElement = document.getElementById("site-logo");
    if (logoElement) {
        logoElement.src = "assets/custom_nerd_default_logo.png";
        logoElement.alt = "Custom Nerd Logo";
        logoElement.style.maxWidth = "250px";
        logoElement.style.height = "auto";
    }

    // Apply Global Styles
    document.body.style.backgroundColor = window.env.FRONTEND_FLOW.STYLES.BACKGROUND_COLOR;
    document.body.style.fontFamily = window.env.FRONTEND_FLOW.STYLES.FONT_FAMILY;
    
    // Apply background color to container
    let container = document.getElementById("container");
    if (container) {
        container.style.backgroundColor = window.env.FRONTEND_FLOW.STYLES.BACKGROUND_COLOR;
    }
    
    // Set CSS custom property for background color
    document.documentElement.style.setProperty('--background-color', window.env.FRONTEND_FLOW.STYLES.BACKGROUND_COLOR);
    
    // Force override any existing background colors with !important via CSS
    const style = document.createElement('style');
    style.textContent = `
        body { background-color: ${window.env.FRONTEND_FLOW.STYLES.BACKGROUND_COLOR} !important; }
        #container { background-color: ${window.env.FRONTEND_FLOW.STYLES.BACKGROUND_COLOR} !important; }
    `;
    document.head.appendChild(style);

    // Update glass element colors based on new background
    // Add a delay to ensure background color is applied
    setTimeout(() => {
        updateGlassElementColors();
    }, 200);

    // Apply Button Styles to contact link
    let contactLink = document.querySelector('.contact-link');
    if (contactLink) {
        contactLink.style.backgroundColor = window.env.FRONTEND_FLOW.STYLES.SUBMIT_BUTTON_BG;
    }
}

/**
 * Initialize page transitions and modern interactions
 */
function initializePageTransitions() {
    document.body.classList.add('page-transition');
    setTimeout(() => {
        document.body.classList.add('loaded');
    }, 100);
    
    // Add navigation link transitions
    const navLinks = document.querySelectorAll('.toolbar a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            const href = this.getAttribute('href');
            if (href && (href.endsWith('.html') || href === 'index.html' || href === '/')) {
                event.preventDefault();
                this.classList.add('nav-loading');
                document.body.classList.add('page-exit');
                setTimeout(() => {
                    window.location.href = href;
                }, 300);
            }
        });
    });
}

/**
 * Add modern button animations
 */
function addButtonAnimations() {
    const contactLink = document.querySelector('.contact-link');
    if (contactLink) {
        contactLink.addEventListener('click', function() {
            this.classList.add('clicking');
            setTimeout(() => {
                this.classList.remove('clicking');
            }, 200);
        });
    }
}

/**
 * Add team member hover effects
 */
function addTeamMemberEffects() {
    const teamMembers = document.querySelectorAll('.team-member');
    teamMembers.forEach((member, index) => {
        member.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        member.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

/**
 * Add scroll animations for team members
 */
function addScrollAnimations() {
    const teamMembers = document.querySelectorAll('.team-member');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    teamMembers.forEach((member, index) => {
        member.style.opacity = '0';
        member.style.transform = 'translateY(30px)';
        member.style.transition = `all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) ${index * 0.1}s`;
        observer.observe(member);
    });
}

/**
 * Executes when the window has finished loading.
 * Calls the functions to apply branding and set up interactions.
 *
 * @return {void} No return value.
 */
window.onload = () => {
    applySiteBranding(); // Apply branding on load
    initializePageTransitions();
    addButtonAnimations();
    addTeamMemberEffects();
    addScrollAnimations();
};
