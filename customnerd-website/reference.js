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
    const root = document.documentElement;
    
    // Parse RGB values from computed style
    const rgbMatch = bodyBgColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
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
        } else {
            // Light background - use dark colors
            root.style.setProperty('--text-color', '#1a202c');
            root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.2)');
            root.style.setProperty('--accent-text-color', submitButtonColor);
            root.style.setProperty('--accent-border-color', submitButtonColor + '4D'); // Add transparency
        }
    }
}

/**
 * Apply site branding and styling from user_env.js configuration
 * This ensures consistent styling with the main site
 */
function applySiteBranding() {
    console.log("Applying site settings from user_env.js to reference page...");

    // Set Page Title
    document.title = `${window.env.FRONTEND_FLOW.SITE_NAME} - Reference`;

    // Set Favicon (Emoji-based)
    let favicon = document.createElement("link");
    favicon.rel = "icon";
    favicon.href = `data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>${window.env.FRONTEND_FLOW.SITE_ICON}</text></svg>`;
    document.head.appendChild(favicon);

    // Set Logo with fallback
    let logoElement = document.querySelector(".logo");
    if (logoElement) {
        setLogoWithFallback(logoElement, window.env.FRONTEND_FLOW.SITE_LOGO, `${window.env.FRONTEND_FLOW.SITE_NAME} Logo`);
    }

    // Apply Global Styles
    document.body.style.backgroundColor = window.env.FRONTEND_FLOW.STYLES.BACKGROUND_COLOR;
    document.body.style.fontFamily = window.env.FRONTEND_FLOW.STYLES.FONT_FAMILY;
    
    // Apply background color to container
    let container = document.getElementById("container");
    if (container) {
        container.style.backgroundColor = window.env.FRONTEND_FLOW.STYLES.BACKGROUND_COLOR;
    }

    // Apply Button Styles to redirect button
    let redirectButton = document.getElementById("redirect-button");
    if (redirectButton) {
        redirectButton.style.backgroundColor = window.env.FRONTEND_FLOW.STYLES.SUBMIT_BUTTON_BG;
    }

    // Update glass element colors based on new background
    updateGlassElementColors();
}

/**
 * Checks if a field is valid (not null, undefined, empty, or whitespace only)
 *
 * @param {any} field - The field to validate
 * @return {boolean} True if the field is valid, false otherwise
 */
function isValidField(field) {
    return field !== null && 
           field !== undefined && 
           typeof field === 'string' && 
           field.trim() !== '';
}

/**
 * Checks if an author field is valid (contains at least one alphabetic character)
 *
 * @param {any} field - The author field to validate
 * @return {boolean} True if the field is valid and contains alphabetic characters, false otherwise
 */
function isValidAuthorField(field) {
    return isValidField(field) && /[a-zA-Z]/.test(field);
}

/**
 * Retrieves the value of the specified query parameter from the URL.
 *
 * @param {string} name - The name of the query parameter to retrieve.
 * @return {string} The value of the specified query parameter.
 */
function getQueryParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

/**
 * Replaces specific text patterns in the input text and returns the formatted text.
 *
 * @param {string} input - The input text to be formatted.
 * @return {string} The formatted text after replacing specific patterns.
 */
const formatText = (input) => {
    // Replace \n with <br>
    let formattedText = input.replace(/\n/g, '<br>');

    // Replace **text** with <strong>text</strong>
    formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    //Replace ### text with bold
    formattedText = formattedText.replace(/### (.*?)(<br>|$)/g, '<strong>$1</strong>$2');


    // Replace "-" with <li> and wrap in <ul>
    formattedText = formattedText.replace(/- (.*?)(<br>|$)/g, '<li>$1</li>');

    return formattedText;
}

/**
 * Parses a citation string into its components.
 *
 * @param {string} citation - The citation string to be parsed.
 * @return {Array} An array containing the authors, title, and journal of the citation.
 */
function parseCitation(citation) {
    // Split the citation into its components using regex
    citation = citation.slice(1);
    const firstDotIndex = citation.indexOf('.');
    const secondDotIndex = citation.indexOf('.', firstDotIndex + 1);
    const authors = citation.substring(3, firstDotIndex).trim();
    const title = citation.substring(firstDotIndex + 1, secondDotIndex).trim();
    const journal = citation.substring(secondDotIndex + 1).trim();
    return [authors, title, journal];
}


/**
 * Loads the content of a reference based on the reference index provided in the query parameter.
 *
 * @return {void} This function does not return anything.
 */
function loadReferenceContent() {
    const refIndex = getQueryParameter('ref');
    const referenceObject = JSON.parse(localStorage.getItem('referenceObject'));
    
    if (!referenceObject || !Array.isArray(referenceObject)) {
        document.getElementById('reference-content').innerText = 'No reference data found.';
        return;
    }

    // Convert refIndex to integer
    const index = parseInt(refIndex, 10);
    
    if (isNaN(index) || index < 0 || index >= referenceObject.length) {
        document.getElementById('reference-content').innerText = 'Reference not found.';
        return;
    }

    // Get the citation object from the array
    const citation = referenceObject[index];
    
    if (!citation) {
        document.getElementById('reference-content').innerText = 'Reference content not found.';
        return;
    }

    // Extract data from the citation object
    const title = citation.title;
    const authors = citation.author_name;
    const doi = citation.doi;
    const journal = citation.journal;
    const abstract = citation.abstract;
    const summary = citation.summary;
    const url = citation.url;
    
    console.log('Citation data:', citation);
    console.log('URL:', url);
    localStorage.setItem('url', url || '');

    // Build content sections only if they exist and are valid
    let contentParts = [];
    
    // Title section
    if (isValidField(title)) {
        if (isValidField(url)) {
            contentParts.push(`<strong><a href="${url}" target="_blank">${title}</a></strong>`);
        } else {
            contentParts.push(`<strong>${title}</strong>`);
        }
    }
    
    // Author section
    if (isValidAuthorField(authors)) {
        contentParts.push(`<strong>Authors:</strong> ${authors}`);
    }
    
    // DOI section
    if (isValidField(doi)) {
        contentParts.push(`<strong>DOI:</strong> ${doi}`);
    }
    
    // Journal section
    if (isValidField(journal)) {
        contentParts.push(`<strong>Journal:</strong> ${journal}`);
    }
    
    // Abstract section
    if (isValidField(abstract)) {
        contentParts.push(`<strong>Abstract:</strong><br>${abstract}`);
    }
    
    // Summary section
    if (isValidField(summary)) {
        contentParts.push(`<strong>Summary:</strong><br>${summary}`);
    }
    
    // Join all parts with double line breaks
    const fullContent = contentParts.join('<br><br>');
    document.getElementById('reference-content').innerHTML = formatText(fullContent);
}


/**
 * Extracts the citation number from the citation string.
 *
 * @param {string} citation - The citation string to extract the number from.
 * @return {number|null} The extracted citation number or null if not found.
 */
function extractCitationNumber(citation) {
    const match = citation.match(/^\[?(\d+)\]?\.?/);
    if (match) {
        return parseInt(match[1], 10);
    }
    return null;
}


/**
 * Sets up the redirect button functionality.
 */
 function setupRedirectButton() {
    const redirectButton = document.getElementById('redirect-button');
    const redirectUrl = localStorage.getItem("url"); // Retrieve the stored URL
    console.log('Redirect URL:', redirectUrl);

    // Check if URL exists and is valid
    if (!redirectUrl || redirectUrl === "" || redirectUrl === "nil" || redirectUrl === "None") {
        // Disable the button if no valid URL
        redirectButton.disabled = true;
        redirectButton.style.backgroundColor = '#ccc';
        redirectButton.style.cursor = 'not-allowed';
        redirectButton.style.opacity = '0.6';
        redirectButton.title = 'Article URL not available';
        
        redirectButton.addEventListener('click', (e) => {
            e.preventDefault();
            alert("Article URL is not available for this reference.");
        });
    } else {
        // Enable the button if valid URL exists and apply consistent styling
        redirectButton.disabled = false;
        redirectButton.style.backgroundColor = window.env.FRONTEND_FLOW.STYLES.SUBMIT_BUTTON_BG;
        redirectButton.style.cursor = 'pointer';
        redirectButton.style.opacity = '1';
        redirectButton.title = 'Read the full article';
        
        redirectButton.addEventListener('click', () => {
            window.open(redirectUrl, '_blank'); // Open in new tab
        });
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
    const redirectButton = document.getElementById('redirect-button');
    if (redirectButton) {
        redirectButton.addEventListener('click', function() {
            this.classList.add('clicking');
            setTimeout(() => {
                this.classList.remove('clicking');
            }, 200);
        });
    }
}

/**
 * Executes when the window has finished loading.
 * Calls the functions to load reference content and set up the redirect button.
 *
 * @return {void} No return value.
 */
window.onload = () => {
    applySiteBranding(); // Apply branding on load
    loadReferenceContent();
    setupRedirectButton();
    initializePageTransitions();
    addButtonAnimations();
};

