// Configuration
const BACKEND_URL = 'http://localhost:8000';

const baseURL = 'http://127.0.0.1:8000';  // Adjust the base URL as needed

let initialConfig;  // Variable to store the initial frontend configuration
let initialBackendConfig;  // Variable to store the initial backend configuration
let initialEnvConfig;  // Variable to store the initial environment configuration
let initialBackendFilesConfig;  // Variable to store the initial backend files configuration
let hardBackupPrompts;  // Variable to store the hard backup prompts
let customApiKeys = [];  // Array to store custom API keys

// Dynamic Color Detection and Page Transitions
function updateGlassElementColors() {
    const bodyBgColor = window.getComputedStyle(document.body).backgroundColor;
    const container = document.querySelector('.container');
    const containerBgColor = container ? window.getComputedStyle(container).backgroundColor : null;
    const root = document.documentElement;
    
    console.log('Config theme detection - Body background:', bodyBgColor);
    console.log('Config theme detection - Container background:', containerBgColor);
    console.log('Config theme detection - Expected background from user_env.js:', window.env?.FRONTEND_FLOW?.STYLES?.BACKGROUND_COLOR);
    
    // Check if the expected background color from user_env.js is dark
    const expectedBgColor = window.env?.FRONTEND_FLOW?.STYLES?.BACKGROUND_COLOR;
    let isDarkTheme = false;
    
    if (expectedBgColor) {
        // Parse the expected background color to determine if it's dark
        if (expectedBgColor.toLowerCase() === '#000000' || expectedBgColor.toLowerCase() === 'black') {
            isDarkTheme = true;
            console.log('Config theme detection - Expected background is black, forcing dark theme');
        } else if (expectedBgColor.startsWith('#')) {
            // Parse hex color
            const hex = expectedBgColor.replace('#', '');
            const r = parseInt(hex.substr(0, 2), 16);
            const g = parseInt(hex.substr(2, 2), 16);
            const b = parseInt(hex.substr(4, 2), 16);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
            isDarkTheme = luminance < 0.5;
            console.log('Config theme detection - Expected background luminance:', luminance, 'isDark:', isDarkTheme);
        }
    }
    
    // Use container background if available, otherwise use body background
    const bgColor = containerBgColor && containerBgColor !== 'rgba(0, 0, 0, 0)' ? containerBgColor : bodyBgColor;
    console.log('Config theme detection - Using background:', bgColor);
    
    // Use the expected background color to determine theme, not the actual detected background
    if (isDarkTheme) {
        console.log('Config theme detection - Using expected dark background, applying dark theme');
        const submitButtonColor = window.env?.FRONTEND_FLOW?.STYLES?.SUBMIT_BUTTON_BG || '#007bff';
        
        // Apply dark theme (light text)
        root.style.setProperty('--text-color', '#ffffff');
        root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.3)');
        root.style.setProperty('--accent-text-color', submitButtonColor);
        root.style.setProperty('--accent-border-color', submitButtonColor + '66');
        
        // Update toggle button colors for dark theme
        root.style.setProperty('--active', '#ffffff');
        root.style.setProperty('--inactive', '#ffffff');
        root.style.setProperty('--pill', 'rgba(255, 255, 255, 0.1)');
        root.style.setProperty('--pill-border', 'rgba(255, 255, 255, 0.3)');
        
        // Add CSS rule to force dark text on light background sections
        const style = document.createElement('style');
        style.textContent = `
            .predefined-api-keys h5,
            .predefined-api-keys p,
            .predefined-api-keys span,
            .predefined-api-keys div,
            .predefined-api-keys strong,
            .predefined-api-keys small,
            .custom-api-keys-section h4,
            .custom-api-keys-section h5,
            .custom-api-keys-section p,
            .custom-api-keys-section span,
            .custom-api-keys-section div,
            .custom-api-keys-section strong,
            .custom-api-keys-section small,
            .modern-key-btn,
            .predefined-key-btn {
                color: #1a202c !important;
            }
            
            /* More specific targeting for stubborn elements */
            .custom-api-keys-section h4[style*="color"],
            .predefined-api-keys h5[style*="color"],
            .predefined-api-keys p[style*="color"],
            .custom-api-keys-section p[style*="color"] {
                color: #1a202c !important;
            }
        `;
        document.head.appendChild(style);
        
        // Also add a delayed application to catch any dynamically loaded content
        setTimeout(() => {
            const stubbornElements = document.querySelectorAll('.custom-api-keys-section h4, .predefined-api-keys h5, .predefined-api-keys p, .custom-api-keys-section p');
            stubbornElements.forEach(el => {
                el.style.setProperty('color', '#1a202c', 'important');
            });
        }, 100);
        
        // Add an even more aggressive CSS rule that targets everything
        const aggressiveStyle = document.createElement('style');
        aggressiveStyle.textContent = `
            .predefined-api-keys *,
            .custom-api-keys-section *,
            .backend-files-tab *,
            .tab-content *,
            .code-note * {
                color: #1a202c !important;
            }
        `;
        document.head.appendChild(aggressiveStyle);
        
        // Force apply to all elements in these sections
        setTimeout(() => {
            const allElements = document.querySelectorAll('.predefined-api-keys *, .custom-api-keys-section *, .backend-files-tab *, .tab-content *, .code-note *');
            console.log('Config theme detection - Found all elements in API sections:', allElements.length);
            allElements.forEach(el => {
                el.style.setProperty('color', '#1a202c', 'important');
            });
        }, 200);
        
        // Also set text color directly on elements as fallback
        document.body.style.color = '#ffffff';
        const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, a, span, label, button');
        console.log('Config theme detection - Found text elements:', textElements.length);
        textElements.forEach(el => {
            if (!el.classList.contains('config-link')) {
                el.style.color = '#ffffff';
            }
        });
        
        // Keep input fields and textareas with dark text for readability
        const inputElements = document.querySelectorAll('input, textarea');
        console.log('Config theme detection - Found input elements:', inputElements.length);
        inputElements.forEach(el => {
            el.style.color = '#1a202c'; // Dark text for inputs
            el.style.backgroundColor = 'rgba(255, 255, 255, 0.9)'; // Light background for inputs
        });
        
        // Handle predefined API key buttons - they have light backgrounds so need dark text
        const predefinedKeyButtons = document.querySelectorAll('.predefined-key-btn, .modern-key-btn');
        console.log('Config theme detection - Found predefined API key buttons:', predefinedKeyButtons.length);
        predefinedKeyButtons.forEach(el => {
            el.style.color = '#1a202c'; // Dark text for light background buttons
        });
        
        // Handle custom API key sections - they have light backgrounds so need dark text
        const customApiSections = document.querySelectorAll('.custom-api-keys-section, .predefined-api-keys');
        console.log('Config theme detection - Found custom API sections:', customApiSections.length);
        customApiSections.forEach(section => {
            // Set dark text for all text elements within these sections
            const textElements = section.querySelectorAll('h4, h5, h6, p, span, div, strong, small');
            textElements.forEach(el => {
                el.style.color = '#1a202c !important'; // Dark text for light background sections with !important
            });
        });
        
        // Specifically target the "Common Publisher API Keys" heading and other predefined elements
        const predefinedHeadings = document.querySelectorAll('.predefined-api-keys h5, .predefined-api-keys p');
        console.log('Config theme detection - Found predefined headings:', predefinedHeadings.length);
        predefinedHeadings.forEach(el => {
            el.style.color = '#1a202c !important'; // Force dark text with !important
        });
        
        // Target all elements with inline color styles that might be overriding our theme
        const allElementsWithInlineStyles = document.querySelectorAll('[style*="color"]');
        console.log('Config theme detection - Found elements with inline color styles:', allElementsWithInlineStyles.length);
        allElementsWithInlineStyles.forEach(el => {
            // Check if this element is within a light background section
            const isInLightSection = el.closest('.predefined-api-keys, .custom-api-keys-section, .modern-key-btn, .predefined-key-btn');
            if (isInLightSection) {
                el.style.color = '#1a202c !important'; // Dark text for light background sections
            }
        });
        
        // Handle custom API key form elements
        const customApiFormElements = document.querySelectorAll('#custom_key_name, #custom_key_value, .custom-api-keys-section input, .custom-api-keys-section label');
        console.log('Config theme detection - Found custom API form elements:', customApiFormElements.length);
        customApiFormElements.forEach(el => {
            el.style.color = '#1a202c'; // Dark text for form elements
        });
    } else {
        // Parse RGB values from computed style (handles both rgb and rgba) for fallback
        const rgbMatch = bgColor.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)/);
        if (rgbMatch) {
            const r = parseInt(rgbMatch[1]);
            const g = parseInt(rgbMatch[2]);
            const b = parseInt(rgbMatch[3]);
            
            console.log('Config theme detection - RGB values:', r, g, b);
            
            // Calculate luminance to determine if background is dark or light
            const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
            console.log('Config theme detection - Luminance:', luminance);
            console.log('Config theme detection - Is dark background?', luminance < 0.5);
        
        // Get submit button color from user_env.js
            const submitButtonColor = window.env?.FRONTEND_FLOW?.STYLES?.SUBMIT_BUTTON_BG || '#007bff';
            
            if (luminance < 0.5) {
                console.log('Config theme detection - Applying dark theme (light text)');
                // Dark background - use light colors
                root.style.setProperty('--text-color', '#ffffff');
                root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.3)');
                root.style.setProperty('--accent-text-color', submitButtonColor);
                root.style.setProperty('--accent-border-color', submitButtonColor + '66'); // Add transparency
                
                // Update toggle button colors for dark theme
                root.style.setProperty('--active', '#ffffff');
                root.style.setProperty('--inactive', '#ffffff');
                root.style.setProperty('--pill', 'rgba(255, 255, 255, 0.1)');
                root.style.setProperty('--pill-border', 'rgba(255, 255, 255, 0.3)');
                
                // Add CSS rule to force dark text on light background sections
                const style = document.createElement('style');
                style.textContent = `
                    .predefined-api-keys h5,
                    .predefined-api-keys p,
                    .predefined-api-keys span,
                    .predefined-api-keys div,
                    .predefined-api-keys strong,
                    .predefined-api-keys small,
                    .custom-api-keys-section h4,
                    .custom-api-keys-section h5,
                    .custom-api-keys-section p,
                    .custom-api-keys-section span,
                    .custom-api-keys-section div,
                    .custom-api-keys-section strong,
                    .custom-api-keys-section small,
                    .modern-key-btn,
                    .predefined-key-btn {
                        color: #1a202c !important;
                    }
                    
                    /* More specific targeting for stubborn elements */
                    .custom-api-keys-section h4[style*="color"],
                    .predefined-api-keys h5[style*="color"],
                    .predefined-api-keys p[style*="color"],
                    .custom-api-keys-section p[style*="color"] {
                        color: #1a202c !important;
                    }
                `;
                document.head.appendChild(style);
                
                // Also add a delayed application to catch any dynamically loaded content
                setTimeout(() => {
                    const stubbornElements = document.querySelectorAll('.custom-api-keys-section h4, .predefined-api-keys h5, .predefined-api-keys p, .custom-api-keys-section p');
                    stubbornElements.forEach(el => {
                        el.style.setProperty('color', '#1a202c', 'important');
                    });
                }, 100);
                
                // Add an even more aggressive CSS rule that targets everything
                const aggressiveStyle = document.createElement('style');
                aggressiveStyle.textContent = `
                    .predefined-api-keys *,
                    .custom-api-keys-section *,
                    .backend-files-tab *,
                    .tab-content *,
                    .code-note * {
                        color: #1a202c !important;
                    }
                `;
                document.head.appendChild(aggressiveStyle);
                
                // Force apply to all elements in these sections
                setTimeout(() => {
                    const allElements = document.querySelectorAll('.predefined-api-keys *, .custom-api-keys-section *, .backend-files-tab *, .tab-content *, .code-note *');
                    console.log('Config theme detection - Found all elements in API sections:', allElements.length);
                    allElements.forEach(el => {
                        el.style.setProperty('color', '#1a202c', 'important');
                    });
                }, 200);
                
                // Also set text color directly on elements as fallback
                document.body.style.color = '#ffffff';
                const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, a, span, label, button');
                console.log('Config theme detection - Found text elements:', textElements.length);
                textElements.forEach(el => {
                    if (!el.classList.contains('config-link')) {
                        el.style.color = '#ffffff';
                    }
                });
                
                // Keep input fields and textareas with dark text for readability
                const inputElements = document.querySelectorAll('input, textarea');
                console.log('Config theme detection - Found input elements:', inputElements.length);
                inputElements.forEach(el => {
                    el.style.color = '#1a202c'; // Dark text for inputs
                    el.style.backgroundColor = 'rgba(255, 255, 255, 0.9)'; // Light background for inputs
                });
                
                // Handle predefined API key buttons - they have light backgrounds so need dark text
                const predefinedKeyButtons = document.querySelectorAll('.predefined-key-btn, .modern-key-btn');
                console.log('Config theme detection - Found predefined API key buttons:', predefinedKeyButtons.length);
                predefinedKeyButtons.forEach(el => {
                    el.style.color = '#1a202c'; // Dark text for light background buttons
                });
                
                // Handle custom API key sections - they have light backgrounds so need dark text
                const customApiSections = document.querySelectorAll('.custom-api-keys-section, .predefined-api-keys');
                console.log('Config theme detection - Found custom API sections:', customApiSections.length);
                customApiSections.forEach(section => {
                    // Set dark text for all text elements within these sections
                    const textElements = section.querySelectorAll('h4, h5, h6, p, span, div, strong, small');
                    textElements.forEach(el => {
                        el.style.color = '#1a202c !important'; // Dark text for light background sections with !important
                    });
                });
                
                // Specifically target the "Common Publisher API Keys" heading and other predefined elements
                const predefinedHeadings = document.querySelectorAll('.predefined-api-keys h5, .predefined-api-keys p');
                console.log('Config theme detection - Found predefined headings:', predefinedHeadings.length);
                predefinedHeadings.forEach(el => {
                    el.style.color = '#1a202c !important'; // Force dark text with !important
                });
                
                // Target all elements with inline color styles that might be overriding our theme
                const allElementsWithInlineStyles = document.querySelectorAll('[style*="color"]');
                console.log('Config theme detection - Found elements with inline color styles:', allElementsWithInlineStyles.length);
                allElementsWithInlineStyles.forEach(el => {
                    // Check if this element is within a light background section
                    const isInLightSection = el.closest('.predefined-api-keys, .custom-api-keys-section, .modern-key-btn, .predefined-key-btn');
                    if (isInLightSection) {
                        el.style.color = '#1a202c !important'; // Dark text for light background sections
                    }
                });
                
                // Handle custom API key form elements
                const customApiFormElements = document.querySelectorAll('#custom_key_name, #custom_key_value, .custom-api-keys-section input, .custom-api-keys-section label');
                console.log('Config theme detection - Found custom API form elements:', customApiFormElements.length);
                customApiFormElements.forEach(el => {
                    el.style.color = '#1a202c'; // Dark text for form elements
                });
        } else {
                console.log('Config theme detection - Applying light theme (dark text)');
                // Light background - use dark colors
                root.style.setProperty('--text-color', '#1a202c');
                root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.2)');
                root.style.setProperty('--accent-text-color', submitButtonColor);
                root.style.setProperty('--accent-border-color', submitButtonColor + '4D'); // Add transparency
                
                // Also set text color directly on elements as fallback
                document.body.style.color = '#1a202c';
                const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, a, span, input, textarea, label, button');
                console.log('Config theme detection - Found text elements:', textElements.length);
                textElements.forEach(el => {
                    if (!el.classList.contains('config-link')) {
                        el.style.color = '#1a202c';
                    }
                });
            }
        } else {
            console.log('Config theme detection - No RGB match found, using fallback');
        // Fallback: check if background color is set to black
        if (bgColor.includes('rgb(0, 0, 0)') || bgColor.includes('rgba(0, 0, 0') || bgColor.includes('black')) {
            console.log('Config theme detection - Fallback: Black background detected, applying light text');
            root.style.setProperty('--text-color', '#ffffff');
            root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.3)');
            root.style.setProperty('--accent-text-color', window.env?.FRONTEND_FLOW?.STYLES?.SUBMIT_BUTTON_BG || '#007bff');
            root.style.setProperty('--accent-border-color', (window.env?.FRONTEND_FLOW?.STYLES?.SUBMIT_BUTTON_BG || '#007bff') + '66');
            
            // Update toggle button colors for dark theme
            root.style.setProperty('--active', '#ffffff');
            root.style.setProperty('--inactive', '#ffffff');
            root.style.setProperty('--pill', 'rgba(255, 255, 255, 0.1)');
            root.style.setProperty('--pill-border', 'rgba(255, 255, 255, 0.3)');
            
            // Add CSS rule to force dark text on light background sections
            const style = document.createElement('style');
            style.textContent = `
                .predefined-api-keys h5,
                .predefined-api-keys p,
                .predefined-api-keys span,
                .predefined-api-keys div,
                .predefined-api-keys strong,
                .predefined-api-keys small,
                .custom-api-keys-section h4,
                .custom-api-keys-section h5,
                .custom-api-keys-section p,
                .custom-api-keys-section span,
                .custom-api-keys-section div,
                .custom-api-keys-section strong,
                .custom-api-keys-section small,
                .modern-key-btn,
                .predefined-key-btn {
                    color: #1a202c !important;
                }
                
                /* More specific targeting for stubborn elements */
                .custom-api-keys-section h4[style*="color"],
                .predefined-api-keys h5[style*="color"],
                .predefined-api-keys p[style*="color"],
                .custom-api-keys-section p[style*="color"] {
                    color: #1a202c !important;
                }
            `;
            document.head.appendChild(style);
            
            // Also add a delayed application to catch any dynamically loaded content
            setTimeout(() => {
                const stubbornElements = document.querySelectorAll('.custom-api-keys-section h4, .predefined-api-keys h5, .predefined-api-keys p, .custom-api-keys-section p');
                stubbornElements.forEach(el => {
                    el.style.setProperty('color', '#1a202c', 'important');
                });
            }, 100);
            
            // Add an even more aggressive CSS rule that targets everything
            const aggressiveStyle = document.createElement('style');
            aggressiveStyle.textContent = `
                .predefined-api-keys *,
                .custom-api-keys-section *,
                .backend-files-tab *,
                .tab-content *,
                .code-note * {
                    color: #1a202c !important;
                }
            `;
            document.head.appendChild(aggressiveStyle);
            
            // Force apply to all elements in these sections
            setTimeout(() => {
                const allElements = document.querySelectorAll('.predefined-api-keys *, .custom-api-keys-section *, .backend-files-tab *, .tab-content *, .code-note *');
                console.log('Config theme detection - Fallback: Found all elements in API sections:', allElements.length);
                allElements.forEach(el => {
                    el.style.setProperty('color', '#1a202c', 'important');
                });
            }, 200);
            
            // Also set text color directly on elements as fallback
            document.body.style.color = '#ffffff';
            const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, a, span, label, button');
            console.log('Config theme detection - Fallback: Found text elements:', textElements.length);
            textElements.forEach(el => {
                if (!el.classList.contains('config-link')) {
                    el.style.color = '#ffffff';
                }
            });
            
            // Keep input fields and textareas with dark text for readability
            const inputElements = document.querySelectorAll('input, textarea');
            console.log('Config theme detection - Fallback: Found input elements:', inputElements.length);
            inputElements.forEach(el => {
                el.style.color = '#1a202c'; // Dark text for inputs
                el.style.backgroundColor = 'rgba(255, 255, 255, 0.9)'; // Light background for inputs
            });
            
            // Handle predefined API key buttons - they have light backgrounds so need dark text
            const predefinedKeyButtons = document.querySelectorAll('.predefined-key-btn, .modern-key-btn');
            console.log('Config theme detection - Fallback: Found predefined API key buttons:', predefinedKeyButtons.length);
            predefinedKeyButtons.forEach(el => {
                el.style.color = '#1a202c'; // Dark text for light background buttons
            });
            
            // Handle custom API key sections - they have light backgrounds so need dark text
            const customApiSections = document.querySelectorAll('.custom-api-keys-section, .predefined-api-keys');
            console.log('Config theme detection - Fallback: Found custom API sections:', customApiSections.length);
            customApiSections.forEach(section => {
                // Set dark text for all text elements within these sections
                const textElements = section.querySelectorAll('h4, h5, h6, p, span, div, strong, small');
                textElements.forEach(el => {
                    el.style.color = '#1a202c !important'; // Dark text for light background sections with !important
                });
            });
            
            // Specifically target the "Common Publisher API Keys" heading and other predefined elements
            const predefinedHeadings = document.querySelectorAll('.predefined-api-keys h5, .predefined-api-keys p');
            console.log('Config theme detection - Fallback: Found predefined headings:', predefinedHeadings.length);
            predefinedHeadings.forEach(el => {
                el.style.color = '#1a202c !important'; // Force dark text with !important
            });
            
            // Target all elements with inline color styles that might be overriding our theme
            const allElementsWithInlineStyles = document.querySelectorAll('[style*="color"]');
            console.log('Config theme detection - Fallback: Found elements with inline color styles:', allElementsWithInlineStyles.length);
            allElementsWithInlineStyles.forEach(el => {
                // Check if this element is within a light background section
                const isInLightSection = el.closest('.predefined-api-keys, .custom-api-keys-section, .modern-key-btn, .predefined-key-btn');
                if (isInLightSection) {
                    el.style.color = '#1a202c !important'; // Dark text for light background sections
                }
            });
            
            // Handle custom API key form elements
            const customApiFormElements = document.querySelectorAll('#custom_key_name, #custom_key_value, .custom-api-keys-section input, .custom-api-keys-section label');
            console.log('Config theme detection - Fallback: Found custom API form elements:', customApiFormElements.length);
            customApiFormElements.forEach(el => {
                el.style.color = '#1a202c'; // Dark text for form elements
            });
        } else {
            console.log('Config theme detection - Fallback: No black background detected');
        }
    }
    }
}

// Color validation and formatting
function validateAndFormatColor(color) {
    if (!color) return '#007bff'; // Default color
    
    // Remove any whitespace
    color = color.trim();
    
    // If it doesn't start with #, add it
    if (!color.startsWith('#')) {
        color = '#' + color;
    }
    
    // Validate hex color format
    const hexPattern = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
    if (!hexPattern.test(color)) {
        return '#007bff'; // Return default if invalid
    }
    
    return color;
}

// Validate color format for typing (more lenient)
function validateColorFormat(color) {
    if (!color) return { isValid: false, message: 'Color is required' };
    
    // Remove any whitespace
    color = color.trim();
    
    // Must start with #
    if (!color.startsWith('#')) {
        return { isValid: false, message: 'Color must start with #' };
    }
    
    // Check if it's a valid hex format (3 or 6 characters after #)
    const hexPattern = /^#([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})$/;
    if (!hexPattern.test(color)) {
        return { isValid: false, message: 'Invalid hex color format (use #RGB or #RRGGBB)' };
    }
    
    return { isValid: true, message: '' };
}

// Show error message below input
function showColorError(input, message) {
    // Find the input-group container (parent of the input)
    const inputGroup = input.closest('.input-group');
    if (!inputGroup) return;
    
    // Remove existing error (check both inside input group and after it)
    const existingError = inputGroup.querySelector('.color-error') || 
                        inputGroup.nextSibling?.classList?.contains('color-error') ? inputGroup.nextSibling : null;
    if (existingError) {
        existingError.remove();
    }
    
    if (message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'color-error';
        errorDiv.textContent = message;
        
        // Append error after the input group, not inside it
        inputGroup.parentNode.insertBefore(errorDiv, inputGroup.nextSibling);
    }
}

// Initialize color pickers with values from user_env.js
function initializeColorPickers() {
    try {
        // Get colors from user_env.js
        const backgroundColor = window.env?.FRONTEND_FLOW?.STYLES?.BACKGROUND_COLOR || '#f0f8ff';
        const submitButtonBg = window.env?.FRONTEND_FLOW?.STYLES?.SUBMIT_BUTTON_BG || '#007bff';
        
        // Validate and format colors
        const validBgColor = validateAndFormatColor(backgroundColor);
        const validSubmitColor = validateAndFormatColor(submitButtonBg);
        
        // Set background color picker (after validation is set up)
        setTimeout(() => {
            const bgColorInput = document.getElementById('background_color');
            const bgColorPicker = document.getElementById('background_color_picker');
            if (bgColorInput) {
                bgColorInput.value = validBgColor;
            }
            if (bgColorPicker) {
                bgColorPicker.value = validBgColor;
            }
            
            // Set submit button color picker
            const submitColorInput = document.getElementById('submit_button_bg');
            const submitColorPicker = document.getElementById('submit_button_bg_picker');
            if (submitColorInput) {
                submitColorInput.value = validSubmitColor;
            }
            if (submitColorPicker) {
                submitColorPicker.value = validSubmitColor;
            }
        }, 100);
        
        console.log('Color pickers initialized:', { validBgColor, validSubmitColor });
        
    } catch (error) {
        console.error('Error initializing color pickers:', error);
    }
}

// Add color picker validation
function addColorPickerValidation() {
    // Background color text input validation
    const bgColorInput = document.getElementById('background_color');
    const bgColorPicker = document.getElementById('background_color_picker');
    
    if (bgColorInput) {
        // Ensure input starts with #
        bgColorInput.value = '#';
        
        bgColorInput.addEventListener('input', function() {
            // Prevent deletion of #
            if (!this.value.startsWith('#')) {
                this.value = '#' + this.value;
            }
            
            const validation = validateColorFormat(this.value);
            
            if (validation.isValid) {
                showColorError(this, '');
                // Update the background color immediately
                document.body.style.backgroundColor = this.value;
                updateGlassElementColors();
                // Sync with color picker
                if (bgColorPicker) {
                    bgColorPicker.value = this.value;
                }
            } else {
                showColorError(this, validation.message);
            }
        });
        
        bgColorInput.addEventListener('change', function() {
            const validatedColor = validateAndFormatColor(this.value);
            this.value = validatedColor;
            showColorError(this, '');
            
            // Update the background color immediately
            document.body.style.backgroundColor = validatedColor;
            updateGlassElementColors();
            // Sync with color picker
            if (bgColorPicker) {
                bgColorPicker.value = validatedColor;
            }
        });
    }
    
    // Submit button color text input validation
    const submitColorInput = document.getElementById('submit_button_bg');
    const submitColorPicker = document.getElementById('submit_button_bg_picker');
    
    if (submitColorInput) {
        // Ensure input starts with #
        submitColorInput.value = '#';
        
        submitColorInput.addEventListener('input', function() {
            // Prevent deletion of #
            if (!this.value.startsWith('#')) {
                this.value = '#' + this.value;
            }
            
            const validation = validateColorFormat(this.value);
            
            if (validation.isValid) {
                showColorError(this, '');
                // Update glass element colors to reflect the new submit button color
                updateGlassElementColors();
                // Sync with color picker
                if (submitColorPicker) {
                    submitColorPicker.value = this.value;
                }
            } else {
                showColorError(this, validation.message);
            }
        });
        
        submitColorInput.addEventListener('change', function() {
            const validatedColor = validateAndFormatColor(this.value);
            this.value = validatedColor;
            showColorError(this, '');
            
            // Update glass element colors to reflect the new submit button color
            updateGlassElementColors();
            // Sync with color picker
            if (submitColorPicker) {
                submitColorPicker.value = validatedColor;
            }
        });
    }
}

function applySiteBranding() {
    try {
        // Set page title
        const siteName = window.env?.FRONTEND_FLOW?.SITE_NAME || 'Custom Nerd';
        document.title = `Configuration — ${siteName}`;
        
        // Set favicon
        const favicon = document.querySelector('link[rel="icon"]') || document.createElement('link');
        favicon.rel = 'icon';
        favicon.href = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">⚙️</text></svg>';
        document.head.appendChild(favicon);
        
        // Set background color
        const backgroundColor = window.env?.FRONTEND_FLOW?.STYLES?.BACKGROUND_COLOR || '#f0f8ff';
        console.log('Config background setting - Setting background to:', backgroundColor);
        
        // Force override any existing background colors with !important via CSS FIRST
        const style = document.createElement('style');
        style.textContent = `
            html { 
                background-color: ${backgroundColor} !important; 
                background: ${backgroundColor} !important;
            }
            body { 
                background-color: ${backgroundColor} !important; 
                background: ${backgroundColor} !important;
            }
            .container { 
                background-color: ${backgroundColor} !important; 
                background: ${backgroundColor} !important;
            }
            .config-content { 
                background-color: ${backgroundColor} !important; 
                background: ${backgroundColor} !important;
            }
            .tab-content { 
                background-color: ${backgroundColor} !important; 
                background: ${backgroundColor} !important;
            }
        `;
        document.head.appendChild(style);
        
        // Also set via JavaScript
        document.documentElement.style.backgroundColor = backgroundColor;
        document.body.style.backgroundColor = backgroundColor;
        document.documentElement.style.setProperty('--background-color', backgroundColor);
        
        // Apply background color to all major containers
        const containers = document.querySelectorAll('.container, .config-content, .tab-content, .config-section');
        containers.forEach(container => {
            container.style.backgroundColor = backgroundColor;
            container.style.background = backgroundColor;
        });
        
        // Update glass element colors with longer delay to ensure background is fully applied
        setTimeout(() => {
            console.log('Config background setting - Calling updateGlassElementColors after delay');
            
            // Force refresh the background color one more time before theme detection
            const currentBgColor = window.env?.FRONTEND_FLOW?.STYLES?.BACKGROUND_COLOR;
            if (currentBgColor) {
                // Apply to all major elements
                document.documentElement.style.backgroundColor = currentBgColor;
                document.body.style.backgroundColor = currentBgColor;
                
                // Apply to all containers
                const allContainers = document.querySelectorAll('.container, .config-content, .tab-content, .config-section, .save-state-section, .load-state-section, .delete-state-section');
                allContainers.forEach(container => {
                    container.style.backgroundColor = currentBgColor;
                    container.style.background = currentBgColor;
                });
                
                console.log('Config background setting - Force refreshed background to:', currentBgColor);
                console.log('Config background setting - Applied to', allContainers.length, 'containers');
            }
            
        updateGlassElementColors();
        }, 500);
        
        // Set logo
        const logoElement = document.getElementById('site-logo');
        if (logoElement) {
            logoElement.src = 'assets/custom_nerd_default_logo.png';
            logoElement.alt = 'Custom Nerd Logo';
        }
        
        // Initialize color pickers with values from user_env.js
        initializeColorPickers();
        
    } catch (error) {
        console.error('Error applying site branding:', error);
    }
}

function initializePageTransitions() {
    // Add page entry animation
    document.body.classList.add('page-transition');
    
    // Add navigation link loading states
    const navLinks = document.querySelectorAll('.toolbar a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.href && !this.href.includes('#')) {
                this.classList.add('nav-loading');
                document.body.classList.add('page-exit');
            }
        });
    });
}

function addButtonAnimations() {
    // Add clicking animation to all buttons
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            this.classList.add('clicking');
            setTimeout(() => {
                this.classList.remove('clicking');
            }, 200);
        });
    });
}

// Frontend Configuration Functions
async function loadConfig() {
    try {
        const response = await fetch(`${baseURL}/fetch_frontend_config`);
        initialConfig = await response.json();  // Store the initial config
        document.getElementById('site_name').value = initialConfig.FRONTEND_FLOW.SITE_NAME;
        // document.getElementById('site_logo').value = initialConfig.SITE_LOGO;
        document.getElementById('site_icon').value = initialConfig.FRONTEND_FLOW.SITE_ICON;
        document.getElementById('site_tagline').value = initialConfig.FRONTEND_FLOW.SITE_TAGLINE;
        
        // Set disclaimer content in the rich text editor
        const editor = document.getElementById('disclaimer-editor');
        const hiddenTextarea = document.getElementById('disclaimer');
        if (editor && hiddenTextarea) {
            hiddenTextarea.value = initialConfig.FRONTEND_FLOW.DISCLAIMER;
            editor.innerHTML = initialConfig.FRONTEND_FLOW.DISCLAIMER;
        }
        
        document.getElementById('question_placeholder').value = initialConfig.FRONTEND_FLOW.QUESTION_PLACEHOLDER;
        document.getElementById('background_color').value = initialConfig.FRONTEND_FLOW.STYLES.BACKGROUND_COLOR;
        document.getElementById('font_family').value = initialConfig.FRONTEND_FLOW.STYLES.FONT_FAMILY;
        document.getElementById('submit_button_bg').value = initialConfig.FRONTEND_FLOW.STYLES.SUBMIT_BUTTON_BG;
        // document.getElementById('example_question_bg').value = initialConfig.STYLES.EXAMPLE_QUESTION_BG;
        // document.getElementById('similar_question_bg').value = initialConfig.STYLES.SIMILAR_QUESTION_BG;
        // document.getElementById('API_URL').value = initialConfig.API_URL;
    } catch (error) {
        console.error('Error loading config:', error);
        showNotification('error', 'Error loading frontend configuration.');
    }
}

async function updateConfig() {
    const emojiValue = document.getElementById('site_icon').value;
    
    const response = await fetch(`${baseURL}/fetch_frontend_config`);
    const frontendConfig = await response.json();
    const userFlow = frontendConfig.USER_FLOW;

    // Create FormData for file upload
    const formData = new FormData();
    
    // Get the logo file if one is selected
    const logoFile = document.getElementById('site_logo').files[0];
    if (logoFile) {
        formData.append('logo_file', logoFile);
    }

    // Create the config object
    const updatedConfig = {
        FRONTEND_FLOW: {
            SITE_NAME: document.getElementById('site_name').value,
            SITE_LOGO: document.getElementById('site_logo').value,
            LOGO_NAME: document.getElementById('logo_name').value,
            SITE_ICON: emojiValue,
            SITE_TAGLINE: document.getElementById('site_tagline').value,
            DISCLAIMER: document.getElementById('disclaimer').value,
            QUESTION_PLACEHOLDER: document.getElementById('question_placeholder').value,
            STYLES: {
                BACKGROUND_COLOR: document.getElementById('background_color').value,
                FONT_FAMILY: document.getElementById('font_family').value,
                SUBMIT_BUTTON_BG: document.getElementById('submit_button_bg').value,
            },
            API_URL: "http://127.0.0.1:8000",
        },
        USER_FLOW: userFlow
    };

    // If no new logo is uploaded, keep the existing logo path
    if (!logoFile && frontendConfig.FRONTEND_FLOW.SITE_LOGO) {
        updatedConfig.FRONTEND_FLOW.SITE_LOGO = frontendConfig.FRONTEND_FLOW.SITE_LOGO;
    }

    // Add the config JSON as a string
    formData.append('config', JSON.stringify(updatedConfig));
    try {
        const response = await fetch(`${baseURL}/update_frontend_config`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            showNotification('success', 'Frontend Configuration updated successfully!');
        } else {
            showNotification('error', 'Error updating configuration.');
        }
    } catch (error) {
        console.error('Error updating config:', error);
        showNotification('error', 'Error connecting to server.');
    }
}

function resetFrontendToDefault() {
    if (initialConfig) {
        document.getElementById('site_name').value = initialConfig.SITE_NAME;
        // document.getElementById('site_logo').value = initialConfig.SITE_LOGO;
        document.getElementById('site_icon').value = initialConfig.SITE_ICON;
        document.getElementById('site_tagline').value = initialConfig.SITE_TAGLINE;
        document.getElementById('disclaimer').value = initialConfig.DISCLAIMER;
        document.getElementById('question_placeholder').value = initialConfig.QUESTION_PLACEHOLDER;
        document.getElementById('background_color').value = initialConfig.STYLES.BACKGROUND_COLOR;
        document.getElementById('font_family').value = initialConfig.STYLES.FONT_FAMILY;
        document.getElementById('submit_button_bg').value = initialConfig.STYLES.SUBMIT_BUTTON_BG;
        // document.getElementById('example_question_bg').value = initialConfig.STYLES.EXAMPLE_QUESTION_BG;
        // document.getElementById('similar_question_bg').value = initialConfig.STYLES.SIMILAR_QUESTION_BG;
        // document.getElementById('API_URL').value = initialConfig.API_URL;
        showNotification('info', 'Reset to original frontend configuration.');
    } else {
        showNotification('error', 'Cannot reset: original frontend configuration not loaded.');
    }
}



// Backend Configuration Functions
async function loadPromptsConfig() {
    try {
        const response = await fetch(`${baseURL}/fetch_prompts_config`);
        initialBackendConfig = await response.json();  // Store the initial config
        
        // Populate form fields with the loaded configuration
        document.getElementById('DETERMINE_QUESTION_VALIDITY_PROMPT').value = initialBackendConfig.DETERMINE_QUESTION_VALIDITY_PROMPT;
        document.getElementById('GENERAL_QUERY_PROMPT').value = initialBackendConfig.GENERAL_QUERY_PROMPT;
        document.getElementById('QUERY_CONTENTION_PROMPT').value = initialBackendConfig.QUERY_CONTENTION_PROMPT;
        document.getElementById('RELEVANCE_CLASSIFIER_PROMPT').value = initialBackendConfig.RELEVANCE_CLASSIFIER_PROMPT;
        document.getElementById('ARTICLE_TYPE_PROMPT').value = initialBackendConfig.ARTICLE_TYPE_PROMPT;
        document.getElementById('ABSTRACT_EXTRACTION_PROMPT').value = initialBackendConfig.ABSTRACT_EXTRACTION_PROMPT;
        document.getElementById('REVIEW_SUMMARY_PROMPT').value = initialBackendConfig.REVIEW_SUMMARY_PROMPT;
        document.getElementById('STUDY_SUMMARY_PROMPT').value = initialBackendConfig.STUDY_SUMMARY_PROMPT;
        document.getElementById('RELEVANT_SECTIONS_PROMPT').value = initialBackendConfig.RELEVANT_SECTIONS_PROMPT;
        document.getElementById('FINAL_RESPONSE_PROMPT').value = initialBackendConfig.FINAL_RESPONSE_PROMPT;
        document.getElementById('DISCLAIMER_TEXT').value = initialBackendConfig.DISCLAIMER_TEXT;
        document.getElementById('backend_disclaimer').value = initialBackendConfig.disclaimer;
        
        // Handle query contention toggle
        const queryContentionEnabled = initialBackendConfig.QUERY_CONTENTION_ENABLED !== undefined ? initialBackendConfig.QUERY_CONTENTION_ENABLED : true;
        document.getElementById('query_contention_enabled').checked = queryContentionEnabled;
        toggleQueryContentionFields(queryContentionEnabled);
    } catch (error) {
        console.error('Error loading backend config:', error);
        showNotification('error', 'Error loading backend configuration.');
    }
}

async function updateBackendConfig() {
    const updatedBackendConfig = {
        DETERMINE_QUESTION_VALIDITY_PROMPT: document.getElementById('DETERMINE_QUESTION_VALIDITY_PROMPT').value,
        GENERAL_QUERY_PROMPT: document.getElementById('GENERAL_QUERY_PROMPT').value,
        QUERY_CONTENTION_PROMPT: document.getElementById('QUERY_CONTENTION_PROMPT').value,
        RELEVANCE_CLASSIFIER_PROMPT: document.getElementById('RELEVANCE_CLASSIFIER_PROMPT').value,
        ARTICLE_TYPE_PROMPT: document.getElementById('ARTICLE_TYPE_PROMPT').value,
        ABSTRACT_EXTRACTION_PROMPT: document.getElementById('ABSTRACT_EXTRACTION_PROMPT').value,
        REVIEW_SUMMARY_PROMPT: document.getElementById('REVIEW_SUMMARY_PROMPT').value,
        STUDY_SUMMARY_PROMPT: document.getElementById('STUDY_SUMMARY_PROMPT').value,
        RELEVANT_SECTIONS_PROMPT: document.getElementById('RELEVANT_SECTIONS_PROMPT').value,
        FINAL_RESPONSE_PROMPT: document.getElementById('FINAL_RESPONSE_PROMPT').value,
        DISCLAIMER_TEXT: document.getElementById('DISCLAIMER_TEXT').value,
        disclaimer: document.getElementById('backend_disclaimer').value,
        QUERY_CONTENTION_ENABLED: document.getElementById('query_contention_enabled').checked
    };

    try {
        const response = await fetch(`${baseURL}/update_prompts_config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedBackendConfig)
        });
        
        if (response.ok) {
            showNotification('success', 'Prompts configuration updated successfully!');
        } else {
            showNotification('error', 'Error updating prompts configuration.');
        }
    } catch (error) {
        console.error('Error updating prompts config:', error);
        showNotification('error', 'Error connecting to server.');
    }
}

function resetBackendToDefault() {
    if (initialBackendConfig) {
        document.getElementById('DETERMINE_QUESTION_VALIDITY_PROMPT').value = initialBackendConfig.DETERMINE_QUESTION_VALIDITY_PROMPT;
        document.getElementById('GENERAL_QUERY_PROMPT').value = initialBackendConfig.GENERAL_QUERY_PROMPT;
        document.getElementById('QUERY_CONTENTION_PROMPT').value = initialBackendConfig.QUERY_CONTENTION_PROMPT;
        document.getElementById('RELEVANCE_CLASSIFIER_PROMPT').value = initialBackendConfig.RELEVANCE_CLASSIFIER_PROMPT;
        document.getElementById('ARTICLE_TYPE_PROMPT').value = initialBackendConfig.ARTICLE_TYPE_PROMPT;
        document.getElementById('ABSTRACT_EXTRACTION_PROMPT').value = initialBackendConfig.ABSTRACT_EXTRACTION_PROMPT;
        document.getElementById('REVIEW_SUMMARY_PROMPT').value = initialBackendConfig.REVIEW_SUMMARY_PROMPT;
        document.getElementById('STUDY_SUMMARY_PROMPT').value = initialBackendConfig.STUDY_SUMMARY_PROMPT;
        document.getElementById('RELEVANT_SECTIONS_PROMPT').value = initialBackendConfig.RELEVANT_SECTIONS_PROMPT;
        document.getElementById('FINAL_RESPONSE_PROMPT').value = initialBackendConfig.FINAL_RESPONSE_PROMPT;
        document.getElementById('DISCLAIMER_TEXT').value = initialBackendConfig.DISCLAIMER_TEXT;
        document.getElementById('backend_disclaimer').value = initialBackendConfig.disclaimer;
        
        // Reset query contention toggle
        const queryContentionEnabled = initialBackendConfig.QUERY_CONTENTION_ENABLED !== undefined ? initialBackendConfig.QUERY_CONTENTION_ENABLED : true;
        document.getElementById('query_contention_enabled').checked = queryContentionEnabled;
        toggleQueryContentionFields(queryContentionEnabled);
        
        showNotification('info', 'Reset to original backend configuration.');
    } else {
        showNotification('error', 'Cannot reset: original backend configuration not loaded.');
    }
}

// Backend Files Configuration Functions
async function loadBackendFilesConfig() {
    try {
        const response = await fetch(`${baseURL}/fetch_backend_config`);
        initialBackendFilesConfig = await response.json();  // Store the initial config
        const frontendResponse = await fetch(`${baseURL}/fetch_frontend_config`);
        initialConfig = await frontendResponse.json();  // Store the initial config

        // Populate form fields with the loaded configuration
        // Normal Search Section
        document.getElementById('normal_search').value = initialBackendFilesConfig.normal_search || '';
        document.getElementById('normal_search_hint_text_area').value = initialConfig.USER_FLOW.searchStrategies[2].tooltip ?? '';
        document.getElementById('normal_search_text').value = initialConfig.USER_FLOW.searchStrategies[2].label ?? '';
        document.getElementById('edit_normal_search').checked = initialConfig.USER_FLOW.searchStrategies[2].visible;
        // ID Specific Search Section
        document.getElementById('id_specific_search').value = initialBackendFilesConfig.id_specific_search || '';
        document.getElementById('id_specific_search_hint_text_area').value = initialConfig.USER_FLOW.searchStrategies[1].tooltip ?? '';
        document.getElementById('id_specific_search_text').value = initialConfig.USER_FLOW.searchStrategies[1].label ?? '';
        document.getElementById('edit_id_specific_search').checked = initialConfig.USER_FLOW.searchStrategies[1].visible;

        // Query Cleaning Section
        document.getElementById('query_cleaning').value = initialBackendFilesConfig.query_cleaning || '';
        document.getElementById('edit_query_cleaning').checked = initialConfig.USER_FLOW.query_cleaning?.visible ?? false;
        
        // The query cleaning visibility is already handled by the existing edit_query_cleaning toggle
        // which controls the query_cleaning.visible setting in the frontend config
        
        // Load clean_query.py content
        loadCleanQueryContent();
        
        // No auto-save for query_cleaning - it will be saved when Update User Flow is clicked

        // Local Document Search Section
        document.getElementById('local_document_search_hint_text_area').value = initialConfig.USER_FLOW.searchStrategies[0].tooltip ?? '';
        document.getElementById('local_document_search_text').value = initialConfig.USER_FLOW.searchStrategies[0].label ?? '';
        document.getElementById('edit_local_document_search').checked = initialConfig.USER_FLOW.searchStrategies[0].visible;

        // Reference Section
        document.getElementById('edit_reference_section_visible').checked = initialConfig.USER_FLOW.reference_section.visible ?? '';
        // Chat History Section
        const chatHistoryVisible = initialConfig.USER_FLOW.chat_history?.visible ?? false;
        const chatToggle = document.getElementById('edit_chat_history_visible');
        if (chatToggle) chatToggle.checked = chatHistoryVisible;
        // Update line numbers for code editors
        updateLineNumbers('normal_search');
        updateLineNumbers('id_specific_search');
        updateLineNumbers('query_cleaning');
        toggleEdit('normal_search', 'edit_normal_search');
        toggleEdit('id_specific_search', 'edit_id_specific_search');
        toggleEdit('query_cleaning', 'edit_query_cleaning');
        toggleEdit('local_document_search', 'edit_local_document_search');
        toggleEdit('reference_section_visible', 'edit_reference_section_visible');
        // showNotification('success', 'Backend files configuration loaded successfully.');

    } catch (error) {
        console.error('Error loading backend files config:', error);
        showNotification('error', 'Error loading backend files configuration.');
    }
}
// # End of Selection

async function updateBackendFilesConfig() {
    // Create FormData for file upload
    const formData = new FormData();
    
    // Create the backend config object
    const updatedBackendFilesConfig = {
        normal_search: document.getElementById('normal_search').value,
        id_specific_search: document.getElementById('id_specific_search').value,
        query_cleaning: document.getElementById('query_cleaning').value
    };

    // Get current frontend config
    const frontendResponse = await fetch(`${baseURL}/fetch_frontend_config`);
    const frontendConfig = await frontendResponse.json();
    const userFlow = frontendConfig.USER_FLOW;

    // Update user flow configuration
    userFlow.searchStrategies[0].label = document.getElementById('local_document_search_text').value;
    userFlow.searchStrategies[0].tooltip = document.getElementById('local_document_search_hint_text_area').value;
    userFlow.searchStrategies[0].visible = document.getElementById('edit_local_document_search').checked;

    userFlow.searchStrategies[1].label = document.getElementById('id_specific_search_text').value;
    userFlow.searchStrategies[1].tooltip = document.getElementById('id_specific_search_hint_text_area').value;
    userFlow.searchStrategies[1].visible = document.getElementById('edit_id_specific_search').checked;

    userFlow.searchStrategies[2].label = document.getElementById('normal_search_text').value;
    userFlow.searchStrategies[2].tooltip = document.getElementById('normal_search_hint_text_area').value;
    userFlow.searchStrategies[2].visible = document.getElementById('edit_normal_search').checked;

    // Query Cleaning Section
    if (!userFlow.query_cleaning) {
        userFlow.query_cleaning = {};
    }
    userFlow.query_cleaning.visible = document.getElementById('edit_query_cleaning').checked;

    userFlow.reference_section.visible = document.getElementById('edit_reference_section_visible').checked;
    // Chat History Section
    if (!userFlow.chat_history) {
        userFlow.chat_history = {};
    }
    userFlow.chat_history.visible = document.getElementById('edit_chat_history_visible').checked;

    // Create the updated frontend config object
    const updatedFrontendConfig = {
        ...frontendConfig,
        USER_FLOW: userFlow
    };

    // Add the config JSON as a string
    formData.append('config', JSON.stringify(updatedFrontendConfig));

    try {
        // Update backend config
        const backendResponse = await fetch(`${baseURL}/update_backend_config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedBackendFilesConfig)
        });

        // Update frontend config
        const frontendResponse = await fetch(`${baseURL}/update_frontend_config`, {
            method: 'POST',
            body: formData
        });
       
        if (backendResponse.ok && frontendResponse.ok) {
            const queryCleaningVisible = document.getElementById('edit_query_cleaning').checked;
            const refineStatus = queryCleaningVisible ? 'enabled' : 'disabled';
            showNotification('success', `User Flow updated successfully!`);
        } else {
            showNotification('error', 'Error updating configurations.');
        }
    } catch (error) {
        console.error('Error updating configurations:', error);
        showNotification('error', 'Error connecting to server.');
    }
}

async function clearChatHistory() {
    // Confirm dialog
    showModal(
        "Clear Chat History",
        "Are you sure you want to delete chat history?",
        async () => {
            try {
                const response = await fetch(`${BACKEND_URL}/clear_chat_history`, {
                    method: 'POST'
                });
                if (response.ok) {
                    showNotification('success', 'Chat history cleared successfully');
                } else {
                    const err = await response.json().catch(() => ({}));
                    showNotification('error', err.detail || 'Failed to clear chat history');
                }
            } catch (error) {
                console.error('Error clearing chat history:', error);
                showNotification('error', 'Error connecting to server.');
            }
        }
    );
}

function resetAllBackendFiles() {
    if (initialBackendFilesConfig) {
        document.getElementById('normal_search').value = initialBackendFilesConfig.normal_search;
        document.getElementById('id_specific_search').value = initialBackendFilesConfig.id_specific_search;
        document.getElementById('query_cleaning').value = initialBackendFilesConfig.query_cleaning;
        
        showNotification('info', 'Reset to original backend files configuration.');
    } else {
        showNotification('error', 'Cannot reset: original backend files configuration not loaded.');
    }
}

// Reset individual field to default
function resetToDefault(field) {
    // Check if this is a backend prompt field
    const backendPromptFields = [
        'DETERMINE_QUESTION_VALIDITY_PROMPT',
        'GENERAL_QUERY_PROMPT', 
        'QUERY_CONTENTION_PROMPT',
        'RELEVANCE_CLASSIFIER_PROMPT',
        'ARTICLE_TYPE_PROMPT',
        'ABSTRACT_EXTRACTION_PROMPT',
        'REVIEW_SUMMARY_PROMPT',
        'STUDY_SUMMARY_PROMPT',
        'RELEVANT_SECTIONS_PROMPT',
        'FINAL_RESPONSE_PROMPT',
        'DISCLAIMER_TEXT',
        'backend_disclaimer'
    ];
    
    if (backendPromptFields.includes(field)) {
        // Use hard backup prompts for backend fields
        if (hardBackupPrompts && hardBackupPrompts[field]) {
            const element = document.getElementById(field.toLowerCase());
            if (element) {
                element.value = hardBackupPrompts[field];
                showNotification('success', `Reset ${field} to hard backup default`);
            }
        } else {
            showNotification('error', 'Hard backup prompts not loaded. Please refresh the page.');
        }
        return;
    }
    
    // // Get the default configuration for frontend fields
    // const defaultConfig = {
    //     SITE_NAME: 'Custom Nerd',
    //     SITE_LOGO: '',
    //     LOGO_NAME: 'Custom Nerd Logo',
    //     SITE_ICON: '🍎',
    //     SITE_TAGLINE: 'Your AI-Powered Research Assistant',
    //     DISCLAIMER: 'This is an AI-powered research assistant. Please verify all information independently.',
    //     QUESTION_PLACEHOLDER: 'Ask your research question here...',
    //     'STYLES.BACKGROUND_COLOR': '#ffffff',
    //     'STYLES.FONT_FAMILY': "'Roboto', sans-serif",
    //     'STYLES.SUBMIT_BUTTON_BG': '#007bff',
    //     'OPENAI_API_KEY': '',
    //     'GEMINI_API_KEY': ''
    // };

    // If a specific field is provided, reset only that field
    if (field) {
        const element = document.getElementById(field.toLowerCase());
        if (element) {
            // Use fallback to empty string if field is not present
            element.value = defaultConfig[field] || '';
            
            // Special handling for logo preview
            if (field === 'SITE_LOGO') {
                const previewContainer = document.getElementById('logo_preview');
                const previewImage = document.getElementById('preview_image');
                const fileInput = document.getElementById('site_logo');
                
                // Clear the file input
                fileInput.value = '';
                
                // Hide the preview
                previewContainer.style.display = 'none';
                previewImage.src = '';
            }
            
            showNotification('success', `Reset ${field} to default value`);
        }
    } else {
        // Reset all fields
        Object.keys(defaultConfig).forEach(key => {
            const element = document.getElementById(key.toLowerCase());
            if (element) {
                // Use fallback to empty string if field is not present
                element.value = defaultConfig[key] || '';
                
                // Special handling for logo preview
                if (key === 'SITE_LOGO') {
                    const previewContainer = document.getElementById('logo_preview');
                    const previewImage = document.getElementById('preview_image');
                    const fileInput = document.getElementById('site_logo');
                    
                    // Clear the file input
                    fileInput.value = '';
                    
                    // Hide the preview
                    previewContainer.style.display = 'none';
                    previewImage.src = '';
                }
            }
        });
        showNotification('success', 'Reset all fields to default values');
    }
}

async function loadEnvConfig() {
    try {
        const response = await fetch(`${baseURL}/fetch_env_config`);
        initialEnvConfig = await response.json();  // Store the initial config
        
        // Clear custom API keys array
        customApiKeys = [];
        
        // Extract metadata about optional and required keys
        const optionalKeys = initialEnvConfig._optional_keys || [];
        const requiredKeys = initialEnvConfig._required_keys || [];
        
        // Remove metadata from the config
        delete initialEnvConfig._optional_keys;
        delete initialEnvConfig._required_keys;
        
        // Get LLM provider from config (default to OpenAI if not set)
        const llmProvider = initialEnvConfig['LLM'] || 'OpenAI';
        
        for (const key in initialEnvConfig) {
            if (initialEnvConfig.hasOwnProperty(key)) {
                const trimmedKey = key.trim();
                initialEnvConfig[trimmedKey] = initialEnvConfig[key];
                if (trimmedKey !== key) {
                    delete initialEnvConfig[key];
                }
                
                // Check if this is a predefined API key (not OpenAI or Gemini)
                const predefinedKeys = [
                    'NCBI_API_KEY', 'ELSEVIER_API_KEY', 'SPRINGER_API_KEY', 
                    'WILEY_API_KEY', 'OXFORD_API_KEY', 'OXFORD_APP_HEADER', 'ENTREZ_EMAIL'
                ];
                
                if (predefinedKeys.includes(trimmedKey)) {
                    // This is a predefined API key - add it to custom keys
                    customApiKeys.push({
                        name: trimmedKey,
                        value: initialEnvConfig[trimmedKey],
                        isPredefined: true
                    });
                } else if (trimmedKey !== 'OPENAI_API_KEY' && trimmedKey !== 'GEMINI_API_KEY' && trimmedKey !== 'ANTHROPIC_API_KEY' && trimmedKey !== 'LLM' && trimmedKey !== 'OLLAMA_MODEL' && trimmedKey !== 'OLLAMA_BASE_URL') {
                    // This is a custom API key
                    customApiKeys.push({
                        name: trimmedKey,
                        value: initialEnvConfig[trimmedKey],
                        isPredefined: false
                    });
                }
            }
        }
        
        // Set LLM provider based on config
        setLLMProvider(llmProvider);
        
        // Always set placeholders for all provider inputs first
        const openaiInput = document.getElementById('OPENAI_API_KEY');
        const geminiInput = document.getElementById('GEMINI_API_KEY');
        const claudeInput = document.getElementById('ANTHROPIC_API_KEY');
        
        if (openaiInput) {
            openaiInput.placeholder = 'Required - Please enter your OpenAI API key';
        }
        if (geminiInput) {
            geminiInput.placeholder = 'Required - Please enter your Gemini API key';
        }
        if (claudeInput) {
            claudeInput.placeholder = 'Required - Please enter your Anthropic API key';
        }
        
        // Load all provider API keys from the environment (preserve all)
        if (openaiInput) {
            openaiInput.value = initialEnvConfig['OPENAI_API_KEY'] || '';
        }
        if (geminiInput) {
            geminiInput.value = initialEnvConfig['GEMINI_API_KEY'] || '';
        }
        if (claudeInput) {
            claudeInput.value = initialEnvConfig['ANTHROPIC_API_KEY'] || '';
        }

        // Load Ollama settings
        const ollamaModelInput = document.getElementById('OLLAMA_MODEL');
        const ollamaBaseUrlInput = document.getElementById('OLLAMA_BASE_URL');
        if (ollamaModelInput) {
            const savedModel = initialEnvConfig['OLLAMA_MODEL'] || 'llama3.2';
            ollamaModelInput.value = savedModel;
            if (typeof syncOllamaModelSelect === 'function') syncOllamaModelSelect(savedModel);
            // Show/hide custom row based on whether loaded model is predefined or custom
            const ollamaSelect = document.getElementById('OLLAMA_MODEL_SELECT');
            if (ollamaSelect && typeof syncOllamaModelInput === 'function') {
                syncOllamaModelInput(ollamaSelect.value);
                // Restore the actual model name if the row ended up custom
                if (ollamaSelect.value === 'custom') ollamaModelInput.value = savedModel;
            }
        }
        if (ollamaBaseUrlInput) {
            ollamaBaseUrlInput.value = initialEnvConfig['OLLAMA_BASE_URL'] || 'http://localhost:11434';
        }

        // setLLMProvider already syncs hidden input and tab state
        // Render custom API keys (including predefined ones)
        renderCustomApiKeys();
    } catch (error) {
        console.error('Error loading environment config:', error);
        showNotification('error', 'Error loading environment configuration.');
    }
}

// Function to update UI indicators for optional fields
function updateOptionalFieldIndicators(optionalKeys, requiredKeys) {
    // Add optional indicator to optional API key fields
    optionalKeys.forEach(key => {
        const inputElement = document.getElementById(key);
        if (inputElement) {
            // Add optional indicator to the label
            const labelElement = inputElement.previousElementSibling?.previousElementSibling;
            if (labelElement && !labelElement.querySelector('.optional-indicator')) {
                const optionalSpan = document.createElement('span');
                optionalSpan.className = 'optional-indicator';
                optionalSpan.textContent = ' (Optional)';
                optionalSpan.style.color = '#6c757d';
                optionalSpan.style.fontSize = '0.9em';
                optionalSpan.style.fontWeight = 'normal';
                labelElement.appendChild(optionalSpan);
            }
            
            // Add placeholder text to indicate it's optional
            if (!inputElement.placeholder) {
                inputElement.placeholder = 'Optional - Leave empty if not needed';
            }
        }
    });
    
    // Add required indicator to required fields
    requiredKeys.forEach(key => {
        const inputElement = document.getElementById(key);
        if (inputElement) {
            // Add required indicator to the label
            const labelElement = inputElement.previousElementSibling?.previousElementSibling;
            if (labelElement && !labelElement.querySelector('.required-indicator')) {
                const requiredSpan = document.createElement('span');
                requiredSpan.className = 'required-indicator';
                requiredSpan.textContent = ' (Required)';
                requiredSpan.style.color = '#dc3545';
                requiredSpan.style.fontSize = '0.9em';
                requiredSpan.style.fontWeight = 'normal';
                labelElement.appendChild(requiredSpan);
            }
            
            // Add placeholder text to indicate it's required
            if (!inputElement.placeholder) {
                inputElement.placeholder = 'Required - Please enter your API key';
            }
        }
    });
}

// Function to render custom API keys in the container
function renderCustomApiKeys() {
    const container = document.getElementById('custom_api_keys_container');
    container.innerHTML = '';
    
    if (customApiKeys.length === 0) {
        container.innerHTML = '<p style="color: #666; font-style: italic;">No custom API keys added yet. Use the buttons above to add predefined keys or create your own.</p>';
        return;
    }
    
    // Separate predefined and custom keys
    const predefinedKeys = customApiKeys.filter(key => key.isPredefined);
    const customKeys = customApiKeys.filter(key => !key.isPredefined);
    
    // Render predefined keys first
    if (predefinedKeys.length > 0) {
        const predefinedSection = document.createElement('div');
        predefinedSection.style.marginBottom = '20px';
        predefinedSection.innerHTML = '<h6 style="margin-bottom: 10px; color: #495057; border-bottom: 1px solid #dee2e6; padding-bottom: 5px;">Predefined API Keys</h6>';
        
        predefinedKeys.forEach((key) => {
            // Find the actual index in the customApiKeys array
            const actualIndex = customApiKeys.findIndex(k => k.name === key.name);
            const keyElement = createApiKeyElement(key, actualIndex, true);
            predefinedSection.appendChild(keyElement);
        });
        
        container.appendChild(predefinedSection);
    }
    
    // Render custom keys
    if (customKeys.length > 0) {
        const customSection = document.createElement('div');
        customSection.innerHTML = '<h6 style="margin-bottom: 10px; color: #495057; border-bottom: 1px solid #dee2e6; padding-bottom: 5px;">Custom API Keys</h6>';
        
        customKeys.forEach((key) => {
            // Find the actual index in the customApiKeys array
            const actualIndex = customApiKeys.findIndex(k => k.name === key.name);
            const keyElement = createApiKeyElement(key, actualIndex, false);
            customSection.appendChild(keyElement);
        });
        
        container.appendChild(customSection);
    }
}

// Function to create an API key element
function createApiKeyElement(key, index, isPredefined) {
    const keyElement = document.createElement('div');
    keyElement.className = 'custom-api-key-item';
    keyElement.style.display = 'flex';
    keyElement.style.alignItems = 'center';
    keyElement.style.marginBottom = '12px';
    keyElement.style.padding = '16px 20px';
    keyElement.style.background = 'rgba(255, 255, 255, 0.08)';
    keyElement.style.backdropFilter = 'blur(20px)';
    keyElement.style.borderRadius = '12px';
    keyElement.style.border = '1px solid rgba(255, 255, 255, 0.15)';
    keyElement.style.transition = 'all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
    keyElement.style.position = 'relative';
    keyElement.style.overflow = 'hidden';
    
    const displayName = key.displayName || key.name;
    const keyType = isPredefined ? 'predefined' : 'custom';
    
    // Define tooltips and links for predefined keys
    const tooltipsAndLinks = {
        'NCBI_API_KEY': {
            tooltip: 'NCBI API Key for PubMed/NCBI services',
            link: 'https://support.nlm.nih.gov/kbArticle/?pn=KA-05317',
            linkText: 'Get API Key'
        },
        'ELSEVIER_API_KEY': {
            tooltip: 'Elsevier API Key for Elsevier publications',
            link: 'https://dev.elsevier.com/apikey/manage',
            linkText: 'Get API Key'
        },
        'SPRINGER_API_KEY': {
            tooltip: 'Springer API Key for Springer publications',
            link: 'https://dev.springernature.com/docs/quick-start/api-access/',
            linkText: 'Get API Key'
        },
        'WILEY_API_KEY': {
            tooltip: 'Wiley API Key for Wiley publications',
            link: 'https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining',
            linkText: 'Get API Key'
        },
        'OXFORD_API_KEY': {
            tooltip: 'Oxford API Key for Oxford publications',
            link: '',
            linkText: ''
        },
        'OXFORD_APP_HEADER': {
            tooltip: 'Oxford App Header for Oxford services',
            link: '',
            linkText: ''
        },
        'ENTREZ_EMAIL': {
            tooltip: 'Just enter your email address - no need to register for PubMed searches',
            link: '',
            linkText: ''
        }
    };
    
    const tooltipInfo = tooltipsAndLinks[key.name] || { tooltip: '', link: '', linkText: '' };
    
    keyElement.innerHTML = `
        <div style="flex: 8;">
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <label style="font-weight: 600; color: #2d3748; margin-right: 12px; font-size: 15px; letter-spacing: -0.01em;">
                    ${displayName}
                    ${isPredefined ? '<span style="color: #6c757d; font-size: 0.8em; font-weight: normal;"> (Predefined)</span>' : ''}
                </label>
                ${tooltipInfo.link ? `<a href="${tooltipInfo.link}" target="_blank" style="font-family: Arial, sans-serif; color: blue; text-decoration: underline; margin-right: 10px;">${tooltipInfo.linkText}</a>` : ''}
                ${tooltipInfo.tooltip ? `
                    <span style="font-family: Arial, sans-serif; color: gray; position: relative;">
                        <i class="fas fa-question-circle" style="cursor: pointer;" onmouseover="showTooltip(this, '${tooltipInfo.tooltip}')" onmouseout="hideTooltip(this)"></i>
                    </span>
                ` : ''}
            </div>
            <div class="password-input-wrapper" style="position: relative; width: 100%;">
                <input type="password" id="custom_key_${index}" value="${key.value || ''}"
                       placeholder="${isPredefined ? 'Enter your ' + displayName : 'Enter your API key'}"
                       style="width: 100%; padding: 16px 20px; background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.25); border-radius: 12px; color: #2d3748; font-size: 14px; transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94); box-sizing: border-box;">
                            <button type="button" class="visibility-toggle" onclick="toggleVisibilityById('custom_key_${index}', this)" aria-label="Show API key" style="position: absolute; right: 12px; top: 50%; transform: translateY(-80%); background: transparent !important; border: none !important; padding: 0 !important; margin: 0 !important; color: #6b7280 !important; cursor: pointer; z-index: 2; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; box-shadow: none !important; outline: none !important; border-radius: 0 !important; transition: none !important;">
                    <i class="fas fa-eye"></i>
                </button>
            </div>
        </div>
        <button type="button" onclick="removeCustomApiKey(${index})" 
                style="flex: 1; margin-left: 12px; background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(20px); border: 1px solid rgba(239, 68, 68, 0.2); color: rgba(220, 38, 38, 0.8); padding: 12px 16px; border-radius: 8px; cursor: pointer; transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94); display: flex; align-items: center; justify-content: center; min-width: 40px; height: 40px;">
            <i class="fas fa-trash"></i>
        </button>
    `;
    
    // Add hover effects for modern glass morphism
    keyElement.addEventListener('mouseenter', function() {
        this.style.background = 'rgba(255, 255, 255, 0.12)';
        this.style.borderColor = 'rgba(255, 255, 255, 0.25)';
        this.style.transform = 'translateY(-2px)';
        this.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.1)';
    });
    
    keyElement.addEventListener('mouseleave', function() {
        this.style.background = 'rgba(255, 255, 255, 0.08)';
        this.style.borderColor = 'rgba(255, 255, 255, 0.15)';
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = 'none';
    });
    
    // Add focus effects for input
    const input = keyElement.querySelector('input');
    if (input) {
        input.addEventListener('focus', function() {
            this.style.background = 'rgba(255, 255, 255, 0.18)';
            this.style.borderColor = 'rgba(59, 130, 246, 0.5)';
            this.style.boxShadow = '0 0 0 4px rgba(59, 130, 246, 0.1), 0 8px 32px rgba(59, 130, 246, 0.1)';
            this.style.transform = 'translateY(-1px)';
        });
        
        input.addEventListener('blur', function() {
            this.style.background = 'rgba(255, 255, 255, 0.12)';
            this.style.borderColor = 'rgba(255, 255, 255, 0.25)';
            this.style.boxShadow = 'none';
            this.style.transform = 'translateY(0)';
        });
    }
    
    // Add hover effects for delete button
    const deleteButton = keyElement.querySelector('button[onclick*="removeCustomApiKey"]');
    if (deleteButton) {
        deleteButton.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(255, 255, 255, 0.12)';
            this.style.borderColor = 'rgba(239, 68, 68, 0.3)';
            this.style.color = 'rgba(185, 28, 28, 0.9)';
            this.style.transform = 'translateY(-1px)';
            this.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.1)';
        });
        
        deleteButton.addEventListener('mouseleave', function() {
            this.style.background = 'rgba(255, 255, 255, 0.08)';
            this.style.borderColor = 'rgba(239, 68, 68, 0.2)';
            this.style.color = 'rgba(220, 38, 38, 0.8)';
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
        });
    }
    
    return keyElement;
}

// Function to show tooltip
function showTooltip(element, text) {
    // Remove any existing tooltip
    const existingTooltip = document.querySelector('.custom-tooltip');
    if (existingTooltip) {
        existingTooltip.remove();
    }
    
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background-color: black;
        color: white;
        text-align: center;
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 12px;
        z-index: 1000;
        max-width: 200px;
        word-wrap: break-word;
        opacity: 0;
        transition: opacity 0.3s;
    `;
    
    document.body.appendChild(tooltip);
    
    // Position the tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
    
    // Show the tooltip
    setTimeout(() => {
        tooltip.style.opacity = '1';
    }, 10);
}

// Function to hide tooltip
function hideTooltip(element) {
    const tooltip = document.querySelector('.custom-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Function to add a new custom API key
function addCustomApiKey() {
    const keyName = document.getElementById('custom_key_name').value.trim();
    const keyValue = document.getElementById('custom_key_value').value.trim();
    
    if (!keyName) {
        showNotification('error', 'Please enter a key name.');
        return;
    }
    
    if (!keyValue) {
        showNotification('error', 'Please enter a key value.');
        return;
    }
    
    // Check if key name already exists
    if (customApiKeys.some(key => key.name === keyName)) {
        showNotification('error', 'A key with this name already exists.');
        return;
    }
    
    // Add the new key to the array
    customApiKeys.push({
        name: keyName,
        value: keyValue
    });
    
    // Clear the input fields
    document.getElementById('custom_key_name').value = '';
    document.getElementById('custom_key_value').value = '';
    
    // Re-render the custom API keys
    renderCustomApiKeys();
    
    showNotification('success', 'Custom API key added successfully.');
}

// Function to remove a custom API key
function removeCustomApiKey(index) {
    if (index >= 0 && index < customApiKeys.length) {
        customApiKeys.splice(index, 1);
        renderCustomApiKeys();
        showNotification('info', 'Custom API key removed.');
    }
}

async function updateEnvConfig() {
    // Get the current LLM provider from the dropdown
    const llmSelect = document.getElementById('llm_provider');
    const currentProvider = llmSelect ? (llmSelect.value || 'OpenAI') : 'OpenAI';
    
    // Create the base config object with LLM provider
    const updatedEnvConfig = {
        LLM: currentProvider
    };
    
    // Always add all provider API keys to preserve them (never delete existing keys)
    const openaiInput = document.getElementById('OPENAI_API_KEY');
    const geminiInput = document.getElementById('GEMINI_API_KEY');
    const claudeInput = document.getElementById('ANTHROPIC_API_KEY');
    
    updatedEnvConfig.OPENAI_API_KEY = openaiInput ? (openaiInput.value || '') : '';
    updatedEnvConfig.GEMINI_API_KEY = geminiInput ? (geminiInput.value || '') : '';
    updatedEnvConfig.ANTHROPIC_API_KEY = claudeInput ? (claudeInput.value || '') : '';

    // Collect Ollama settings
    const ollamaModelInput = document.getElementById('OLLAMA_MODEL');
    const ollamaBaseUrlInput = document.getElementById('OLLAMA_BASE_URL');
    updatedEnvConfig.OLLAMA_MODEL = ollamaModelInput ? (ollamaModelInput.value.trim() || 'llama3.2') : 'llama3.2';
    updatedEnvConfig.OLLAMA_BASE_URL = ollamaBaseUrlInput ? (ollamaBaseUrlInput.value.trim() || 'http://localhost:11434') : 'http://localhost:11434';

    // Update custom API keys from the DOM
    customApiKeys.forEach((key, index) => {
        const valueElement = document.getElementById(`custom_key_${index}`);
        if (valueElement) {
            key.value = valueElement.value;
        }
    });
    
    // Add all custom API keys (including predefined ones) to the config object
    customApiKeys.forEach(key => {
        updatedEnvConfig[key.name] = key.value;
    });

    // Validate required fields based on current provider (Ollama requires no API key)
    if (currentProvider !== 'Ollama') {
        const requiredFields = currentProvider === 'Gemini' ? ['GEMINI_API_KEY'] : (currentProvider === 'Claude' ? ['ANTHROPIC_API_KEY'] : ['OPENAI_API_KEY']);
        const missingFields = requiredFields.filter(field => !updatedEnvConfig[field] || updatedEnvConfig[field].trim() === '');
        if (missingFields.length > 0) {
            const providerName = currentProvider === 'Gemini' ? 'Gemini' : (currentProvider === 'Claude' ? 'Claude (Anthropic)' : 'OpenAI');
            showNotification('error', `Required ${providerName} API key is missing. Please enter your ${providerName} API key.`);
            return;
        }
    } else {
        // For Ollama, validate that a model name is provided
        if (!updatedEnvConfig.OLLAMA_MODEL) {
            showNotification('error', 'Please enter an Ollama model name (e.g. llama3.2).');
            return;
        }
    }

    try {
        const response = await fetch(`${baseURL}/update_env_config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedEnvConfig)
        });

        if (response.ok) {
            showNotification('success', 'Environment Configuration saved successfully!');
            // If Ollama is the selected provider, automatically run setup
            if (currentProvider === 'Ollama') {
                setupOllama(updatedEnvConfig.OLLAMA_MODEL || 'llama3.2');
            }
        } else {
            showNotification('error', 'Error updating environment configuration.');
        }
    } catch (error) {
        console.error('Error updating environment config:', error);
        showNotification('error', 'Error connecting to server.');
    }
}

/**
 * Connect to /ollama_setup via SSE and stream progress into the setup panel.
 * Called automatically after saving config when Ollama provider is selected.
 */
// ── API key / connection tester ──────────────────────────────────────────────

const _PROVIDER_KEY_ID = {
    openai: 'OPENAI_API_KEY',
    gemini: 'GEMINI_API_KEY',
    claude: 'ANTHROPIC_API_KEY',
    ollama: null,
};

async function testApiKey(provider) {
    const btnEl   = document.getElementById('test_btn_' + provider);
    const resultEl = document.getElementById(provider + '_test_result');
    const keyInputId = _PROVIDER_KEY_ID[provider];
    const apiKey = keyInputId ? ((document.getElementById(keyInputId) || {}).value || '').trim() : '';

    if (provider !== 'ollama' && !apiKey) {
        _showTestResult(resultEl, false, 'Enter your API key first.');
        return;
    }

    // Loading state
    if (btnEl) {
        btnEl.disabled = true;
        btnEl.innerHTML = '<span style="display:inline-block;width:12px;height:12px;border:2px solid currentColor;border-top-color:transparent;border-radius:50%;animation:ollama_spin 0.7s linear infinite;vertical-align:middle;margin-right:4px;"></span>Testing…';
    }
    if (resultEl) resultEl.style.display = 'none';

    try {
        const resp = await fetch(baseURL + '/test_api_key/' + provider, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey }),
        });
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const data = await resp.json();
        _showTestResult(resultEl, data.ok, data.message);
    } catch (e) {
        _showTestResult(resultEl, false, 'Could not reach backend — make sure the server is running.');
    } finally {
        if (btnEl) {
            btnEl.disabled = false;
            btnEl.innerHTML = '<i class="fas fa-plug"></i> ' + (provider === 'ollama' ? 'Test Connection' : 'Test');
        }
    }
}

function _showTestResult(el, ok, message) {
    if (!el) return;
    el.style.display = 'flex';
    if (ok) {
        el.style.background = 'rgba(40, 167, 69, 0.08)';
        el.innerHTML = '<i class="fas fa-check-circle" style="color:#28a745;flex-shrink:0;"></i> <span style="color:#28a745;">' + message + '</span>';
    } else {
        el.style.background = 'rgba(220, 53, 69, 0.08)';
        el.innerHTML = '<i class="fas fa-times-circle" style="color:#dc3545;flex-shrink:0;"></i> <span style="color:#dc3545;">' + message + '</span>';
    }
}

// ── End API key tester ───────────────────────────────────────────────────────

// ── Ollama pre-flight status check ──────────────────────────────────────────

/**
 * Polls /ollama_status and updates the three indicator dots + banner text.
 * Safe to call at any time; does nothing if the status card is not in the DOM.
 */
async function checkOllamaStatus() {
    var checkingEl = document.getElementById('ollama_status_checking');
    if (checkingEl) { checkingEl.style.display = 'inline'; }

    // Reset all dots to pending while we wait
    ['installed', 'running', 'model'].forEach(function(k) {
        var dot = document.getElementById('ollama_ind_' + k);
        if (dot) { dot.className = 'ollama-status-dot ollama-dot-pending'; }
        var noteEl = document.getElementById('ollama_ind_' + k + '_note');
        if (noteEl) noteEl.textContent = 'checking…';
    });

    try {
        var resp = await fetch(baseURL + '/ollama_status');
        if (!resp.ok) throw new Error('status ' + resp.status);
        var data = await resp.json();

        // Installed
        _setStatusDot(
            'installed',
            data.is_installed,
            data.is_installed ? 'Found on this machine' : 'Not installed — will be installed automatically'
        );

        // Running
        _setStatusDot(
            'running',
            data.is_running,
            data.is_running ? 'Listening on port 11434' : 'Not running — will be started automatically'
        );

        // Model available
        var modelInput = document.getElementById('OLLAMA_MODEL');
        var currentModel = (modelInput && modelInput.value) ? modelInput.value.trim() : 'llama3.2';
        var baseName = currentModel.split(':')[0];
        var installedModels = data.installed_models || [];
        var modelPulled = installedModels.some(function(m) {
            return m === currentModel || m.startsWith(baseName + ':') || m.startsWith(baseName + ' ');
        });

        var modelLabelEl = document.getElementById('ollama_ind_model_label');
        if (modelLabelEl) modelLabelEl.textContent = 'Model \u2018' + currentModel + '\u2019';

        _setStatusDot(
            'model',
            modelPulled,
            modelPulled ? 'Already pulled \u2714' : 'Not downloaded — will be pulled automatically'
        );

        // Cache for other functions to use
        window._ollamaStatusCache = { data: data, modelPulled: modelPulled, currentModel: currentModel };

        // Update dynamic banner
        _updateOllamaBanner(data.is_installed, data.is_running, modelPulled);

    } catch (e) {
        ['installed', 'running', 'model'].forEach(function(k) {
            var dot = document.getElementById('ollama_ind_' + k);
            if (dot) { dot.className = 'ollama-status-dot ollama-dot-pending'; }
            var noteEl = document.getElementById('ollama_ind_' + k + '_note');
            if (noteEl) noteEl.textContent = '';
        });
        var checkingTxt = document.getElementById('ollama_status_checking');
        if (checkingTxt) { checkingTxt.textContent = '(backend offline — start backend first)'; }
        return;
    }

    if (checkingEl) { checkingEl.style.display = 'none'; }
}

function _setStatusDot(key, ok, noteText) {
    var dot = document.getElementById('ollama_ind_' + key);
    var noteEl = document.getElementById('ollama_ind_' + key + '_note');
    if (!dot) return;
    if (ok) {
        dot.className = 'ollama-status-dot ollama-dot-ok';
    } else {
        dot.className = 'ollama-status-dot ollama-dot-missing';
    }
    if (noteEl) noteEl.textContent = noteText || '';
}

function _updateOllamaBanner(isInstalled, isRunning, modelPulled) {
    var banner = document.getElementById('ollama_status_banner_text');
    if (!banner) return;
    var allReady = isInstalled && isRunning && modelPulled;
    if (allReady) {
        banner.innerHTML = '<i class="fas fa-check-circle" style="color:#28a745;margin-right:6px;"></i>' +
            '<strong>Ollama is ready!</strong> All systems are running. You can save and start using it now.';
    } else {
        var missing = [];
        if (!isInstalled) missing.push('install Ollama');
        if (!isRunning)   missing.push('start the server');
        if (!modelPulled) missing.push('pull the selected model');
        banner.innerHTML = '<i class="fas fa-magic" style="color:#7c3aed;margin-right:6px;"></i>' +
            'Click <strong>Update Environment Configuration</strong> to automatically: ' +
            missing.join(' \u2192 ') + '.';
    }
}

// ── End Ollama pre-flight ────────────────────────────────────────────────────

function setupOllama(model) {
    if (!model) model = (document.getElementById('OLLAMA_MODEL') || {}).value || 'llama3.2';
    model = model.trim();

    const panel = document.getElementById('ollama_setup_panel');
    const log   = document.getElementById('ollama_setup_log');
    const title = document.getElementById('ollama_panel_title');
    const spinner = document.getElementById('ollama_panel_spinner');

    if (!panel) return;

    // Reset & show panel
    panel.style.display = 'block';
    if (log) log.textContent = '';
    if (title) { title.textContent = `Setting up Ollama with model '${model}'…`; title.style.color = '#7c3aed'; }
    if (spinner) spinner.style.display = 'inline-block';

    // Reset step icons
    for (var s = 1; s <= 4; s++) {
        var icon = document.getElementById('ollama_step_' + s + '_icon');
        if (icon) { icon.textContent = '○'; icon.className = 'ollama-step-icon ollama-step-pending'; }
    }

    function appendLog(msg) {
        if (!log) return;
        log.textContent += msg + '\n';
        log.scrollTop = log.scrollHeight;
    }

    function setStep(step, state) {
        // state: 'active' | 'done' | 'error' | 'warn'
        var icon = document.getElementById('ollama_step_' + step + '_icon');
        if (!icon) return;
        var map = { active: ['●', 'ollama-step-active'], done: ['✓', 'ollama-step-done'], error: ['✗', 'ollama-step-error'], warn: ['⚠', 'ollama-step-warn'] };
        var entry = map[state] || ['○', 'ollama-step-pending'];
        icon.textContent = entry[0];
        icon.className = 'ollama-step-icon ' + entry[1];
    }

    var url = baseURL + '/ollama_setup?model=' + encodeURIComponent(model);
    var es = new EventSource(url);

    es.onmessage = function(e) {
        try {
            var data = JSON.parse(e.data);
            var step = data.step || 0;
            var type = data.type || 'progress';
            var msg  = data.message || '';

            if (step > 0) setStep(step, 'active');

            switch (type) {
                case 'success':
                    if (step > 0) setStep(step, 'done');
                    appendLog('✓ ' + msg);
                    break;
                case 'warning':
                    if (step > 0) setStep(step, 'warn');
                    appendLog('⚠ ' + msg);
                    break;
                case 'error':
                    if (step > 0) setStep(step, 'error');
                    appendLog('✗ ' + msg);
                    break;
                case 'fatal':
                    appendLog('✗ FATAL: ' + msg);
                    if (title) { title.textContent = 'Setup failed'; title.style.color = '#dc3545'; }
                    if (spinner) spinner.style.display = 'none';
                    es.close();
                    break;
                case 'complete':
                    if (step > 0) setStep(step, 'done');
                    appendLog('✓ ' + msg);
                    if (title) { title.textContent = 'Ollama is ready!'; title.style.color = '#28a745'; }
                    if (spinner) spinner.style.display = 'none';
                    showNotification('success', 'Ollama setup complete — model is ready to use!');
                    es.close();
                    break;
                default:
                    // install_log / pull_log / progress
                    appendLog(msg);
            }
        } catch(err) {
            appendLog(e.data);
        }
    };

    es.onerror = function() {
        appendLog('Connection to setup stream lost. Check the backend console for details.');
        if (title) { title.textContent = 'Setup stream ended'; title.style.color = '#6c757d'; }
        if (spinner) spinner.style.display = 'none';
        es.close();
    };
}

function resetAllEnv() {
    if (initialEnvConfig) {
        // Get the original LLM provider
        const originalProvider = initialEnvConfig['LLM'] || 'OpenAI';
        
        // Set the LLM provider
        setLLMProvider(originalProvider);
        
        // Always set placeholders for all provider inputs first
        const openaiInput = document.getElementById('OPENAI_API_KEY');
        const geminiInput = document.getElementById('GEMINI_API_KEY');
        const claudeInput = document.getElementById('ANTHROPIC_API_KEY');
        
        if (openaiInput) {
            openaiInput.placeholder = 'Required - Please enter your OpenAI API key';
        }
        if (geminiInput) {
            geminiInput.placeholder = 'Required - Please enter your Gemini API key';
        }
        if (claudeInput) {
            claudeInput.placeholder = 'Required - Please enter your Anthropic API key';
        }
        
        // Reset all provider API keys
        if (openaiInput) {
            openaiInput.value = initialEnvConfig.OPENAI_API_KEY || '';
        }
        if (geminiInput) {
            geminiInput.value = initialEnvConfig.GEMINI_API_KEY || '';
        }
        if (claudeInput) {
            claudeInput.value = initialEnvConfig.ANTHROPIC_API_KEY || '';
        }

        // Reset Ollama settings
        const ollamaModelInput = document.getElementById('OLLAMA_MODEL');
        const ollamaBaseUrlInput = document.getElementById('OLLAMA_BASE_URL');
        if (ollamaModelInput) {
            const savedModel = initialEnvConfig.OLLAMA_MODEL || 'llama3.2';
            ollamaModelInput.value = savedModel;
            if (typeof syncOllamaModelSelect === 'function') syncOllamaModelSelect(savedModel);
            const ollamaSelect = document.getElementById('OLLAMA_MODEL_SELECT');
            if (ollamaSelect && typeof syncOllamaModelInput === 'function') {
                syncOllamaModelInput(ollamaSelect.value);
                if (ollamaSelect.value === 'custom') ollamaModelInput.value = savedModel;
            }
        }
        if (ollamaBaseUrlInput) {
            ollamaBaseUrlInput.value = initialEnvConfig.OLLAMA_BASE_URL || 'http://localhost:11434';
        }

        // Reset custom API keys (including predefined ones)
        customApiKeys = [];
        const predefinedKeys = [
            'NCBI_API_KEY', 'ELSEVIER_API_KEY', 'SPRINGER_API_KEY', 
            'WILEY_API_KEY', 'OXFORD_API_KEY', 'OXFORD_APP_HEADER', 'ENTREZ_EMAIL'
        ];
        
        for (const key in initialEnvConfig) {
            if (key !== 'OPENAI_API_KEY' && key !== 'GEMINI_API_KEY' && key !== 'ANTHROPIC_API_KEY' && key !== 'LLM'
                && key !== 'OLLAMA_MODEL' && key !== 'OLLAMA_BASE_URL' && initialEnvConfig.hasOwnProperty(key)) {
                const isPredefined = predefinedKeys.includes(key);
                customApiKeys.push({
                    name: key,
                    value: initialEnvConfig[key],
                    isPredefined: isPredefined,
                    displayName: isPredefined ? key.replace('_', ' ').replace('API KEY', 'API Key').replace('APP HEADER', 'App Header') : key
                });
            }
        }
        
        // Re-render custom API keys
        renderCustomApiKeys();
        
        showNotification('info', 'Reset to original environment configuration.');
    } else {
        showNotification('error', 'Cannot reset: original environment configuration not loaded.');
    }
}

// Function to add a predefined API key
function addPredefinedApiKey(keyName, displayName) {
    // Check if this key already exists
    const existingKey = customApiKeys.find(key => key.name === keyName);
    if (existingKey) {
        showNotification('info', `${displayName} is already added.`);
        return;
    }
    
    // Add the predefined key
    customApiKeys.push({
        name: keyName,
        value: '',
        isPredefined: true,
        displayName: displayName
    });
    
    // Re-render the custom API keys
    renderCustomApiKeys();
    
    showNotification('success', `${displayName} added successfully.`);
}

// Function to show a pretty notification
function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Add a unique ID for stacking
    const notificationId = `notification-${Date.now()}`;
    notification.id = notificationId;
    
    // Calculate position based on existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    const topPosition = existingNotifications.length * 80; // 80px spacing between notifications
    
    notification.style.top = `${topPosition}px`;
    
    // Check if this is the refresh message and add refresh button
    const isRefreshMessage = message.includes('refresh the page manually');
    const refreshButton = isRefreshMessage ? `
        <button class="notification-refresh-btn" onclick="location.reload()">
            <i class="fas fa-sync-alt"></i> Refresh
        </button>
    ` : '';
    
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-icon">
                ${type === 'success' ? '<i class="fas fa-check-circle"></i>' : 
                  type === 'error' ? '<i class="fas fa-exclamation-circle"></i>' : 
                  '<i class="fas fa-info-circle"></i>'}
            </div>
            <div class="notification-text">
                <div class="notification-message">${message}</div>
                ${refreshButton}
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Trigger slide-in animation
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Set different durations based on notification type
    const duration = type === 'info' ? 8000 : 3000; // 8 seconds for info, 3 seconds for others
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 500);
    }, duration);
}

// Tab functionality
function openTab(tabId) {
    // Hide all tab contents
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }
    
    // Deactivate all tab buttons
    const tabButtons = document.getElementsByClassName('tab-button');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }
    
    // Show the selected tab content and activate the button
    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');
    
    // Load appropriate configuration based on the tab
    if (tabId === 'frontend-tab') {
        loadConfig();
    } else if (tabId === 'backend-tab') {
        console.log("CHeck")
        loadPromptsConfig();
    } else if (tabId === 'env-tab') {
        loadEnvConfig();
    } else if (tabId === 'backend-files-tab') {
        loadBackendFilesConfig();
    }
}



// Function to update line numbers for code editors
function updateLineNumbers(textareaId) {
    const textarea = document.getElementById(textareaId);
    const lineNumbersContainer = textarea.parentElement.querySelector('.line-numbers');
    
    // Count the number of lines
    const lineCount = textarea.value.split('\n').length;
    
    // Generate line numbers HTML
    let lineNumbersHTML = '';
    for (let i = 1; i <= lineCount; i++) {
        lineNumbersHTML += `<div>${i}</div>`;
    }
    
    // Update the line numbers container
    lineNumbersContainer.innerHTML = lineNumbersHTML;
}

// Function to initialize code editors
function initCodeEditors() {
    const codeTextareas = ['normal_search', 'id_specific_search'];
    
    codeTextareas.forEach(textareaId => {
        const textarea = document.getElementById(textareaId);
        if (textarea) {
            // Update line numbers on load
            updateLineNumbers(textareaId);
            
            // Update line numbers when content changes
            textarea.addEventListener('input', () => {
                updateLineNumbers(textareaId);
            });
            
            // Handle tab key for indentation
            textarea.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    e.preventDefault();
                    
                    // Get cursor position
                    const start = textarea.selectionStart;
                    const end = textarea.selectionEnd;
                    
                    // Insert 4 spaces at cursor position
                    textarea.value = textarea.value.substring(0, start) + '    ' + textarea.value.substring(end);
                    
                    // Move cursor after the inserted spaces
                    textarea.selectionStart = textarea.selectionEnd = start + 4;
                }
            });
        }
    });
}

// Rich Text Editor Functions
function initRichTextEditor() {
    const editor = document.getElementById('disclaimer-editor');
    const hiddenTextarea = document.getElementById('disclaimer');
    const formatButtons = document.querySelectorAll('.format-btn');
    
    if (editor && hiddenTextarea) {
        // Initialize editor with content from hidden textarea
        editor.innerHTML = hiddenTextarea.value;
        
        // Update hidden textarea when editor content changes
        editor.addEventListener('input', () => {
            updateHiddenTextarea();
        });
        
        // Handle format buttons
        formatButtons.forEach(button => {
            button.addEventListener('click', () => {
                const format = button.getAttribute('data-format');
                applyFormat(format);
            });
        });
    }
}

function applyFormat(format) {
    const editor = document.getElementById('disclaimer-editor');
    
    // Save current selection
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);
    
    // Apply formatting
    document.execCommand(format, false, null);
    
    // Restore focus
    editor.focus();
    
    // Update hidden textarea
    updateHiddenTextarea();
}

function updateHiddenTextarea() {
    const editor = document.getElementById('disclaimer-editor');
    const hiddenTextarea = document.getElementById('disclaimer');
    
    if (editor && hiddenTextarea) {
        // Convert editor content to HTML and store in hidden textarea
        hiddenTextarea.value = editor.innerHTML;
    }
}

// Function to generate code using AI
async function generateAICode(textareaId, type) {
    try {
        // Show loading notification
        showNotification('info', 'Generating code with AI...');
        
        // Get the content from the textarea
        const textarea = document.getElementById(textareaId);
        const content = textarea.value;
        
        // Add loading animation to the button
        const button = document.querySelector(`button[onclick="generateAICode('${textareaId}', '${type}')"]`);
        button.classList.add('ai-button-loading');
        
        // Show the spinner
        const spinner = button.querySelector('.ai-button-spinner');
        if (spinner) {
            spinner.style.display = 'block';
        }
        
        // Create particle effect
        createParticleEffect(button);
        
        // Send the content to the backend API
        const response = await fetch(`${baseURL}/generate_code_endpoint?type=${type}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ article_content: content })
        });
        
        // Parse the response
        const data = await response.json();
        
        // Remove loading animation
        button.classList.remove('ai-button-loading');
        
        // Hide the spinner
        if (spinner) {
            spinner.style.display = 'none';
        }
        
        if (data.status === 'success') {
            // Update the textarea with the generated code
            textarea.value = data.summary;
            
            // Update line numbers
            updateLineNumbers(textareaId);
            
            // Show success notification
            showNotification('success', 'Code generated successfully!');
            
            // Add success animation
            button.classList.add('ai-button-success');
            setTimeout(() => {
                button.classList.remove('ai-button-success');
            }, 2000);
            
            // Show temporary message below the button
            showTemporaryMessage(button, 'Your code has been generated and pasted in below code area');
            
            // Highlight important notes and scroll to them
            highlightImportantNotes(textareaId);
        } else {
            // Show error notification
            showNotification('error', 'Failed to generate code: ' + data.detail);
            
            // Add error animation
            button.classList.add('ai-button-error');
            setTimeout(() => {
                button.classList.remove('ai-button-error');
            }, 2000);
        }
    } catch (error) {
        console.error('Error generating code:', error);
        showNotification('error', 'Error connecting to the server.');
        
        // Remove loading animation and add error animation
        const button = document.querySelector(`button[onclick="generateAICode('${textareaId}')"]`);
        button.classList.remove('ai-button-loading');
        
        // Hide the spinner
        const spinner = button.querySelector('.ai-button-spinner');
        if (spinner) {
            spinner.style.display = 'none';
        }
        
        button.classList.add('ai-button-error');
        setTimeout(() => {
            button.classList.remove('ai-button-error');
        }, 2000);
    }
}

// Function to highlight important notes and scroll to them
function highlightImportantNotes(textareaId) {
    // Find the search section containing the textarea
    const textarea = document.getElementById(textareaId);
    const searchSection = textarea.closest('.search-section');
    
    if (searchSection) {
        // Find all code-note elements within this search section
        const codeNotes = searchSection.querySelectorAll('.code-note');
        
        if (codeNotes.length > 0) {
            // Add highlighting animation to each code note
            codeNotes.forEach((note, index) => {
                // Add highlight class
                note.classList.add('highlight-note');
                
                // Add pulsing animation
                note.style.animation = 'pulseHighlight 2s ease-in-out';
                
                // Remove highlight after animation
                setTimeout(() => {
                    note.classList.remove('highlight-note');
                    note.style.animation = '';
                }, 2000);
            });
            
            // Scroll to the first code note
            setTimeout(() => {
                codeNotes[0].scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
            }, 500);
            
            // Show a temporary notification about the notes
            setTimeout(() => {
                showNotification('info', 'Please review the highlighted notes below for important configuration details!');
            }, 1000);
        }
    }
}

// Function to show a temporary message below an element
function showTemporaryMessage(element, message) {
    // Remove any existing temporary message
    const existingMessage = document.querySelector('.temporary-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create message element with modern glass morphism
    const messageElement = document.createElement('div');
    messageElement.className = 'temporary-message modern-temp-message';
    messageElement.innerHTML = `
        <div class="temp-message-content">
            <div class="temp-message-icon">
                <i class="fas fa-check-circle"></i>
            </div>
            <span class="temp-message-text">${message}</span>
        </div>
    `;
    
    // Add the message after the button
    element.parentNode.appendChild(messageElement);
    
    // Remove the message after 5 seconds
    setTimeout(() => {
        if (messageElement.parentNode) {
        messageElement.remove();
        }
    }, 5000);
}

// Function to create particle effect
function createParticleEffect(element) {
    // Create particles container
    const particlesContainer = document.createElement('div');
    particlesContainer.style.position = 'absolute';
    particlesContainer.style.top = '0';
    particlesContainer.style.left = '0';
    particlesContainer.style.width = '100%';
    particlesContainer.style.height = '100%';
    particlesContainer.style.pointerEvents = 'none';
    particlesContainer.style.zIndex = '1000';
    particlesContainer.style.overflow = 'hidden';
    
    // Add to the element
    element.style.position = 'relative';
    element.appendChild(particlesContainer);
    
    // Create particles
    for (let i = 0; i < 8; i++) {
        const particle = document.createElement('div');
        particle.style.position = 'absolute';
        particle.style.width = '4px';
        particle.style.height = '4px';
        particle.style.backgroundColor = '#ffffff';
        particle.style.borderRadius = '50%';
        particle.style.pointerEvents = 'none';
        
        // Random position around the button
        const angle = (i / 8) * 2 * Math.PI;
        const distance = 30;
        const startX = 50 + Math.cos(angle) * distance;
        const startY = 50 + Math.sin(angle) * distance;
        
        particle.style.left = startX + '%';
        particle.style.top = startY + '%';
        
        // Add to container
        particlesContainer.appendChild(particle);
        
        // Animate particle
        setTimeout(() => {
            particle.style.transition = 'all 0.8s ease-out';
            particle.style.transform = `translate(${Math.cos(angle) * 100}px, ${Math.sin(angle) * 100}px)`;
            particle.style.opacity = '0';
            
            // Remove particle after animation
            setTimeout(() => {
                if (particle.parentNode) {
                    particle.parentNode.removeChild(particle);
                }
            }, 800);
        }, i * 50);
    }
    
    // Remove particles container after all animations
    setTimeout(() => {
        if (particlesContainer.parentNode) {
            particlesContainer.parentNode.removeChild(particlesContainer);
        }
    }, 1200);
}

// Add CSS styles for the AI button animations
function addAIButtonStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .ai-prompt-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
            border: none;
            color: white;
            padding: 12px 32px !important;
            min-width: 180px !important;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.2);
        }

        .ai-prompt-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.3);
            background: linear-gradient(135deg, #FF8E53 0%, #FF6B6B 100%);
        }

        .ai-prompt-btn:active {
            transform: translateY(0);
            box-shadow: 0 2px 10px rgba(255, 107, 107, 0.2);
        }

        .ai-prompt-btn .ai-button-glow {
            position: absolute;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transform: translateX(-100%);
            transition: transform 0.6s ease;
        }

        .ai-prompt-btn:hover .ai-button-glow {
            transform: translateX(100%);
        }

        .ai-prompt-btn .ai-button-spinner {
            display: none;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-left: 8px;
        }

        .ai-prompt-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .ai-info-icon {
            position: relative;
            display: flex;
            align-items: center;
        }

        .ai-info-icon .fa-info-circle {
            color: #666;
            font-size: 18px;
            cursor: pointer;
            transition: color 0.3s ease;
            margin-top: 15px;
        }

        .ai-info-icon:hover .fa-info-circle {
            color: #FF6B6B;
        }

        .ai-info-tooltip {
            visibility: hidden;
            width: 250px;
            background-color: rgba(0, 0, 0, 0.9);
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 10px 15px;
            position: absolute;
            z-index: 1;
            left: 50%;
            margin-left: -125px;
            opacity: 0;
            transition: all 0.3s ease;
            font-size: 13px;
            line-height: 1.4;
            bottom: 100%;
            margin-bottom: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            pointer-events: none;
        }

        .ai-info-icon:hover .ai-info-tooltip {
            visibility: visible;
            opacity: 1;
        }

        .ai-info-tooltip .tooltip-arrow {
            position: absolute;
            bottom: -5px;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: rgba(0, 0, 0, 0.9) transparent transparent transparent;
        }

        /* Highlight animation for code notes */
        .highlight-note {
            text-decoration: underline;
            text-decoration-color: #007bff;
            text-decoration-thickness: 2px;
            text-underline-offset: 2px;
            transition: all 0.3s ease;
        }

        @keyframes pulseHighlight {
            0% {
                text-decoration-color: #007bff;
            }
            50% {
                text-decoration-color: #0056b3;
            }
            100% {
                text-decoration-color: #007bff;
            }
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @keyframes fadeInOut {
            0% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
            10% { opacity: 1; transform: translateX(-50%) translateY(0); }
            90% { opacity: 1; transform: translateX(-50%) translateY(0); }
            100% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
        }
    `;
    document.head.appendChild(style);
}

// Initialize tooltips for AI info icons
function initAITooltips() {
    // Initialize tooltips for AI Code Generator
    const aiInfoIcons = document.querySelectorAll('.ai-info-icon');
    aiInfoIcons.forEach(icon => {
        const tooltip = icon.querySelector('.ai-info-tooltip');
        icon.addEventListener('mouseover', () => {
            tooltip.style.visibility = 'visible';
            tooltip.style.opacity = '1';
        });
        icon.addEventListener('mouseout', () => {
            tooltip.style.visibility = 'hidden';
            tooltip.style.opacity = '0';
        });
    });
}

// Function to show custom modal
function showModal(title, message, onConfirm) {
    // Create modal elements
    const modalOverlay = document.createElement('div');
    modalOverlay.className = 'modal-overlay';
    
    modalOverlay.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <i class="fas fa-exclamation-triangle"></i>
                <h3 class="modal-title">${title}</h3>
            </div>
            <div class="modal-body">
                ${message}
            </div>
            <div class="modal-footer">
                <button class="modal-button cancel">
                    <i class="fas fa-times"></i> Cancel
                </button>
                <button class="modal-button confirm">
                    <i class="fas fa-check"></i> Confirm Reset
                </button>
            </div>
        </div>
    `;
    
    // Add to document
    document.body.appendChild(modalOverlay);
    
    // Show modal with smooth animation
    requestAnimationFrame(() => {
        modalOverlay.classList.add('active');
    });
    
    // Handle button clicks with enhanced animations
    const cancelButton = modalOverlay.querySelector('.cancel');
    const confirmButton = modalOverlay.querySelector('.confirm');
    
    const closeModal = () => {
        modalOverlay.classList.add('closing');
        setTimeout(() => {
            modalOverlay.remove();
        }, 400);
    };
    
    cancelButton.addEventListener('click', (e) => {
        e.target.style.transform = 'scale(0.95)';
        setTimeout(() => {
            closeModal();
        }, 150);
    });
    
    confirmButton.addEventListener('click', (e) => {
        e.target.style.transform = 'scale(0.95)';
        setTimeout(() => {
            closeModal();
            onConfirm();
        }, 150);
    });
    
    // Close on overlay click
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) {
            closeModal();
        }
    });
    
    // Close on Escape key
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', handleEscape);
        }
    };
    document.addEventListener('keydown', handleEscape);
}

// Function to perform hard reset of configuration
async function hardResetConfig() {
    showModal(
        "Hard Reset Configuration",
        "Are you sure you want to reset all configurations to their default values? This action cannot be undone.",
        async () => {
            try {
                const response = await fetch(`${BACKEND_URL}/fetch_hard_backup_config`, {
                    method: 'GET'
                });
                
                if (response.ok) {
                    showNotification('success', 'Configuration reset successfully');
                    // Show a second notification about manual refresh with longer duration
                    setTimeout(() => {
                        showNotification('info', 'If you don\'t see the changes, please refresh the page manually.');
                    }, 500);
                } else {
                    const error = await response.json();
                    showNotification('error', error.detail || 'Failed to reset configuration');
                }
            } catch (error) {
                showNotification('error', 'An error occurred while resetting configuration');
                console.error('Error resetting configuration:', error);
            }
        }
    );
}

function previewLogo(event) {
    const file = event.target.files[0];
    const previewContainer = document.getElementById('logo_preview');
    const previewImage = document.getElementById('preview_image');
    const fileNameElement = document.getElementById('file_name');
    const fileSizeElement = document.getElementById('file_size');
    
    console.log('previewLogo called with file:', file);
    console.log('Elements found:', {
        previewContainer: !!previewContainer,
        previewImage: !!previewImage,
        fileNameElement: !!fileNameElement,
        fileSizeElement: !!fileSizeElement
    });
    
    if (file) {
        // Check if file is an image
        if (!file.type.startsWith('image/')) {
            showNotification('error', 'Please select an image file');
            event.target.value = ''; // Clear the file input
            previewContainer.style.display = 'none';
            return;
        }

        // Check file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showNotification('error', 'Image size should be less than 5MB');
            event.target.value = ''; // Clear the file input
            previewContainer.style.display = 'none';
            return;
        }

        // Display file information immediately
        console.log('Setting file name:', file.name);
        console.log('Setting file size:', formatFileSize(file.size));
        
        if (fileNameElement) {
            fileNameElement.textContent = file.name;
            fileNameElement.style.color = '#1a202c';
            fileNameElement.style.fontSize = '14px';
            fileNameElement.style.fontWeight = '500';
            fileNameElement.style.backgroundColor = 'transparent';
            console.log('File name set successfully');
        } else {
            console.error('fileNameElement not found');
        }
        
        if (fileSizeElement) {
            fileSizeElement.textContent = formatFileSize(file.size);
            fileSizeElement.style.color = '#4a5568';
            fileSizeElement.style.fontSize = '12px';
            fileSizeElement.style.fontWeight = '400';
            fileSizeElement.style.backgroundColor = 'transparent';
            console.log('File size set successfully');
        } else {
            console.error('fileSizeElement not found');
        }
        
        // Show the preview container immediately to display file info
        if (previewContainer) {
            previewContainer.style.display = 'block';
            previewContainer.style.visibility = 'visible';
            previewContainer.style.opacity = '1';
            previewContainer.style.position = 'relative';
            previewContainer.style.zIndex = '999';
            previewContainer.classList.add('logo-preview-visible');
            console.log('Preview container shown');
            console.log('Preview container display:', previewContainer.style.display);
            console.log('Preview container visibility:', previewContainer.style.visibility);
            console.log('Preview container classes:', previewContainer.className);
            console.log('Preview container computed style:', window.getComputedStyle(previewContainer).display);
            console.log('Preview container offsetHeight:', previewContainer.offsetHeight);
            console.log('Preview container offsetWidth:', previewContainer.offsetWidth);
        } else {
            console.error('previewContainer not found');
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            previewImage.src = e.target.result;
        };
        reader.readAsDataURL(file);
    } else {
        previewContainer.style.display = 'none';
    }
}

// Helper function to format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function removeLogo() {
    const fileInput = document.getElementById('site_logo');
    const previewContainer = document.getElementById('logo_preview');
    const previewImage = document.getElementById('preview_image');
    const fileNameElement = document.getElementById('file_name');
    const fileSizeElement = document.getElementById('file_size');
    
    // Clear the file input
    fileInput.value = '';
    
    // Clear file info
    if (fileNameElement) {
        fileNameElement.textContent = '';
    }
    if (fileSizeElement) {
        fileSizeElement.textContent = '';
    }
    
    // Clear and hide the preview
    previewImage.src = '';
    previewContainer.style.display = 'none';
    previewContainer.style.visibility = 'hidden';
    previewContainer.style.opacity = '0';
    previewContainer.classList.remove('logo-preview-visible');
    
    showNotification('info', 'Logo removed successfully');
}

// Initialize emoji picker
function initEmojiHandling() {
    const siteIconInput = document.getElementById('site_icon');
    const emojiPickerBtn = document.getElementById('emoji-picker-btn');
    const emojiPicker = document.getElementById('emoji-picker');
    const emojiGrid = document.getElementById('emoji-grid');
    
    // Emoji categories and their emojis
    const emojiCategories = {
        recent: [],
        smileys: ['😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙', '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🤫', '🤔', '🤐', '🤨', '😐', '😑', '😶', '😏', '😒', '🙄', '😬', '🤥', '😔', '😪', '🤤', '😴', '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '🥵', '🥶', '🥴', '😵', '🤯', '🤠', '🥳', '😎', '🤓', '🧐'],
        people: ['👶', '🧒', '👦', '👧', '🧑', '👨', '👩', '🧓', '👴', '👵', '👤', '👥', '🫂', '👪', '👨‍👩‍👧', '👨‍👩‍👧‍👦', '👨‍👨‍👦', '👩‍👩‍👦', '👨‍👦', '👨‍👦‍👦', '👨‍👧', '👨‍👧‍👦', '👩‍👦', '👩‍👦‍👦', '👩‍👧', '👩‍👧‍👦', '👨‍👨‍👧', '👩‍👩‍👧', '👨‍👨‍👧‍👦', '👩‍👩‍👧‍👦'],
        animals: ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', '🐷', '🐸', '🐵', '🙈', '🙉', '🙊', '🐒', '🦍', '🦧', '🐕', '🐩', '🦮', '🐕‍🦺', '🐈', '🐈‍⬛', '🦄', '🐎', '🦓', '🦌', '🐂', '🐃', '🐄', '🐷', '🐖', '🐗', '🐏', '🐑', '🐐', '🐪', '🐫', '🦙', '🦒', '🐘', '🦏', '🦛', '🐘', '🦏', '🦛', '🐭', '🐁', '🐀', '🐹', '🐰', '🦝', '🦨', '🦡', '🦫', '🦦', '🦥', '🐿️', '🦔'],
        food: ['🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🫐', '🍈', '🍒', '🍑', '🥭', '🍍', '🥥', '🥝', '🍅', '🍆', '🥑', '🥦', '🥬', '🥒', '🌶️', '🫑', '🌽', '🥕', '🫒', '🧄', '🧅', '🥔', '🍠', '🥐', '🥖', '🍞', '🥨', '🥯', '🧀', '🥚', '🍳', '🧈', '🥞', '🧇', '🥓', '🥩', '🍗', '🍖', '🦴', '🌭', '🍔', '🍟', '🍕'],
        travel: ['🚗', '🚕', '🚙', '🚌', '🚎', '🏎️', '🚓', '🚑', '🚒', '🚐', '🛻', '🚚', '🚛', '🚜', '🏍️', '🛵', '🚲', '🛴', '🛹', '🛼', '🚁', '✈️', '🛩️', '🛫', '🛬', '🪂', '💺', '🚀', '🛸', '🚉', '🚊', '🚝', '🚞', '🚋', '🚃', '🚋', '🚞', '🚝', '🚄', '🚅', '🚈', '🚂', '🚆', '🚇', '🚊', '🚉', '✈️', '🛫', '🛬', '🪂', '💺', '🚀', '🛸'],
        activities: ['⚽', '🏀', '🏈', '⚾', '🥎', '🎾', '🏐', '🏉', '🎱', '🪀', '🏓', '🏸', '🏒', '🏑', '🥍', '🏏', '🪃', '🥅', '⛳', '🪁', '🏹', '🎣', '🤿', '🥊', '🥋', '🎽', '🛹', '🛷', '⛸️', '🥌', '🎿', '⛷️', '🏂', '🪂', '🏋️‍♀️', '🏋️', '🏋️‍♂️', '🤼‍♀️', '🤼', '🤼‍♂️', '🤸‍♀️', '🤸', '🤸‍♂️', '⛹️‍♀️', '⛹️', '⛹️‍♂️', '🤺', '🤾‍♀️', '🤾', '🤾‍♂️', '🏌️‍♀️', '🏌️', '🏌️‍♂️', '🏇', '🧘‍♀️', '🧘', '🧘‍♂️', '🏄‍♀️', '🏄', '🏄‍♂️', '🏊‍♀️', '🏊', '🏊‍♂️', '🤽‍♀️', '🤽', '🤽‍♂️', '🚣‍♀️', '🚣', '🚣‍♂️', '🧗‍♀️', '🧗', '🧗‍♂️', '🚵‍♀️', '🚵', '🚵‍♂️', '🚴‍♀️', '🚴', '🚴‍♂️', '🏆', '🥇', '🥈', '🥉', '🏅', '🎖️', '🏵️', '🎗️', '🎫', '🎟️', '🎪', '🤹', '🤹‍♀️', '🤹‍♂️', '🎭', '🩰', '🎨', '🎬', '🎤', '🎧', '🎼', '🎵', '🎶', '🪘', '🥁', '🎸', '🪕', '🎺', '🎷', '🪗', '🎹', '🎻', '🪈', '🎲', '♠️', '♥️', '♦️', '♣️', '🃏', '🀄', '🎴', '🎯', '🎳', '🎮', '🕹️', '🎰', '🧩'],
        objects: ['📱', '📲', '☎️', '📞', '📟', '📠', '🔋', '🔌', '💻', '🖥️', '🖨️', '⌨️', '🖱️', '🖲️', '💽', '💾', '💿', '📀', '🧮', '🎥', '📷', '📸', '📹', '🎞️', '📽️', '🎬', '📺', '📻', '🎙️', '🎚️', '🎛️', '🧭', '⏱️', '⏲️', '⏰', '🕰️', '⌛', '⏳', '📡', '🔋', '🔌', '💡', '🔦', '🕯️', '🪔', '🧯', '🛢️', '💸', '💵', '💴', '💶', '💷', '🪙', '💰', '💳', '💎', '⚖️', '🧰', '🔧', '🔨', '⚒️', '🛠️', '⛏️', '🪓', '🪚', '🔩', '⚙️', '🪤', '🧱', '⛓️', '🧲', '🔫', '💣', '🧨', '🪓', '🔪', '🗡️', '⚔️', '🛡️', '🚬', '⚰️', '🪦', '⚱️', '🏺', '🔮', '📿', '🧿', '💈', '⚗️', '🔭', '🔬', '🕳️', '🩹', '🩺', '💊', '💉', '🧬', '🦠', '🧫', '🧪', '🌡️', '🧹', '🧺', '🧻', '🚽', '🚰', '🚿', '🛁', '🛀', '🧴', '🧷', '🧸', '🧵', '🧶', '🪡', '🪢', '🧽', '🪣', '🧼', '🪥', '🪒', '🧴', '🧷', '🧸', '🧵', '🧶', '🪡', '🪢', '🧽', '🪣', '🧼', '🪥', '🪒'],
        symbols: ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️', '✝️', '☪️', '🕉️', '☸️', '✡️', '🔯', '🕎', '☯️', '☦️', '🛐', '⛎', '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓', '🆔', '⚛️', '🉑', '☢️', '☣️', '📴', '📳', '🈶', '🈚', '🈸', '🈺', '🈷️', '✴️', '🆚', '💮', '🉐', '㊙️', '㊗️', '🈴', '🈵', '🈹', '🈲', '🅰️', '🅱️', '🆎', '🆑', '🅾️', '🆘', '❌', '⭕', '🛑', '⛔', '📛', '🚫', '💯', '💢', '♨️', '🚷', '🚯', '🚳', '🚱', '🔞', '📵', '🚭', '❗', '❕', '❓', '❔', '‼️', '⁉️', '🔅', '🔆', '〽️', '⚠️', '🚸', '🔱', '⚜️', '🔰', '♻️', '✅', '🈯', '💹', '❇️', '✳️', '❎', '🌐', '💠', 'Ⓜ️', '🌀', '💤', '🏧', '🚾', '♿', '🅿️', '🈳', '🈂️', '🛂', '🛃', '🛄', '🛅', '🚹', '🚺', '🚼', '🚻', '🚮', '🎦', '📶', '🈁', '🔣', '🔤', 'ℹ️', '🔡', '🔠', '🆖', '🆗', '🆙', '🆒', '🆕', '🆓', '0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'],
        flags: ['🏳️', '🏴', '🏁', '🚩', '🏳️‍🌈', '🏳️‍⚧️', '🏴‍☠️', '🇦🇨', '🇦🇩', '🇦🇪', '🇦🇫', '🇦🇬', '🇦🇮', '🇦🇱', '🇦🇲', '🇦🇴', '🇦🇶', '🇦🇷', '🇦🇸', '🇦🇹', '🇦🇺', '🇦🇼', '🇦🇽', '🇦🇿', '🇧🇦', '🇧🇧', '🇧🇩', '🇧🇪', '🇧🇫', '🇧🇬', '🇧🇭', '🇧🇮', '🇧🇯', '🇧🇱', '🇧🇲', '🇧🇳', '🇧🇴', '🇧🇶', '🇧🇷', '🇧🇸', '🇧🇹', '🇧🇻', '🇧🇼', '🇧🇾', '🇧🇿', '🇨🇦', '🇨🇨', '🇨🇩', '🇨🇫', '🇨🇬', '🇨🇭', '🇨🇮', '🇨🇰', '🇨🇱', '🇨🇲', '🇨🇳', '🇨🇴', '🇨🇵', '🇨🇷', '🇨🇺', '🇨🇻', '🇨🇼', '🇨🇽', '🇨🇾', '🇨🇿', '🇩🇪', '🇩🇬', '🇩🇯', '🇩🇰', '🇩🇲', '🇩🇴', '🇩🇿', '🇪🇦', '🇪🇨', '🇪🇪', '🇪🇬', '🇪🇭', '🇪🇷', '🇪🇸', '🇪🇹', '🇪🇺', '🇫🇮', '🇫🇯', '🇫🇰', '🇫🇲', '🇫🇴', '🇫🇷', '🇬🇦', '🇬🇧', '🇬🇩', '🇬🇪', '🇬🇫', '🇬🇬', '🇬🇭', '🇬🇮', '🇬🇱', '🇬🇲', '🇬🇳', '🇬🇵', '🇬🇶', '🇬🇷', '🇬🇸', '🇬🇹', '🇬🇺', '🇬🇼', '🇬🇾', '🇭🇰', '🇭🇲', '🇭🇳', '🇭🇷', '🇭🇹', '🇭🇺', '🇮🇨', '🇮🇩', '🇮🇪', '🇮🇱', '🇮🇲', '🇮🇳', '🇮🇴', '🇮🇶', '🇮🇷', '🇮🇸', '🇮🇹', '🇯🇪', '🇯🇲', '🇯🇴', '🇯🇵', '🇰🇪', '🇰🇬', '🇰🇭', '🇰🇮', '🇰🇲', '🇰🇳', '🇰🇵', '🇰🇷', '🇰🇼', '🇰🇾', '🇰🇿', '🇱🇦', '🇱🇧', '🇱🇨', '🇱🇮', '🇱🇰', '🇱🇷', '🇱🇸', '🇱🇹', '🇱🇺', '🇱🇻', '🇱🇾', '🇲🇦', '🇲🇨', '🇲🇩', '🇲🇪', '🇲🇫', '🇲🇬', '🇲🇭', '🇲🇰', '🇲🇱', '🇲🇲', '🇲🇳', '🇲🇴', '🇲🇵', '🇲🇶', '🇲🇷', '🇲🇸', '🇲🇹', '🇲🇺', '🇲🇻', '🇲🇼', '🇲🇽', '🇲🇾', '🇲🇿', '🇳🇦', '🇳🇨', '🇳🇪', '🇳🇫', '🇳🇬', '🇳🇮', '🇳🇱', '🇳🇴', '🇳🇵', '🇳🇷', '🇳🇺', '🇳🇿', '🇴🇲', '🇵🇦', '🇵🇪', '🇵🇫', '🇵🇬', '🇵🇭', '🇵🇰', '🇵🇱', '🇵🇲', '🇵🇳', '🇵🇷', '🇵🇸', '🇵🇹', '🇵🇼', '🇵🇾', '🇶🇦', '🇷🇪', '🇷🇴', '🇷🇸', '🇷🇺', '🇷🇼', '🇸🇦', '🇸🇧', '🇸🇨', '🇸🇩', '🇸🇪', '🇸🇬', '🇸🇭', '🇸🇮', '🇸🇯', '🇸🇰', '🇸🇱', '🇸🇲', '🇸🇳', '🇸🇴', '🇸🇷', '🇸🇸', '🇸🇹', '🇸🇻', '🇸🇽', '🇸🇾', '🇸🇿', '🇹🇦', '🇹🇨', '🇹🇩', '🇹🇫', '🇹🇬', '🇹🇭', '🇹🇯', '🇹🇰', '🇹🇱', '🇹🇲', '🇹🇳', '🇹🇴', '🇹🇷', '🇹🇹', '🇹🇻', '🇹🇼', '🇹🇿', '🇺🇦', '🇺🇬', '🇺🇲', '🇺🇳', '🇺🇸', '🇺🇾', '🇺🇿', '🇻🇦', '🇻🇨', '🇻🇪', '🇻🇬', '🇻🇮', '🇻🇳', '🇻🇺', '🇼🇫', '🇼🇸', '🇽🇰', '🇾🇪', '🇾🇹', '🇿🇦', '🇿🇲', '🇿🇼']
    };
    
    let currentCategory = 'recent';
    
    // Toggle emoji picker
    emojiPickerBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        emojiPicker.classList.toggle('show');
        if (emojiPicker.classList.contains('show')) {
            loadEmojis(currentCategory);
        }
    });
    
    // Close emoji picker when clicking outside
    document.addEventListener('click', function(e) {
        if (!emojiPicker.contains(e.target) && !emojiPickerBtn.contains(e.target)) {
            emojiPicker.classList.remove('show');
        }
    });
    
    // Category switching
    document.querySelectorAll('.emoji-category').forEach(category => {
        category.addEventListener('click', function() {
            document.querySelectorAll('.emoji-category').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            currentCategory = this.dataset.category;
            loadEmojis(currentCategory);
        });
    });
    
    // Load emojis for a category
    function loadEmojis(category) {
        emojiGrid.innerHTML = '';
        const emojis = emojiCategories[category] || [];
        
        emojis.forEach(emoji => {
            const emojiItem = document.createElement('div');
            emojiItem.className = 'emoji-item';
            emojiItem.textContent = emoji;
            emojiItem.addEventListener('click', function() {
                siteIconInput.value = emoji;
                emojiPicker.classList.remove('show');
                
                // Add to recent emojis
                if (category !== 'recent') {
                    if (!emojiCategories.recent.includes(emoji)) {
                        emojiCategories.recent.unshift(emoji);
                        if (emojiCategories.recent.length > 20) {
                            emojiCategories.recent.pop();
                        }
                    }
                }
            });
            emojiGrid.appendChild(emojiItem);
        });
    }
    
    // Initialize with recent emojis
    loadEmojis('recent');
}

// Modern UI Enhancements
function addModernUIEnhancements() {
    // Add loading states to all buttons
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        if (!button.classList.contains('ai-prompt-btn')) {
            button.addEventListener('click', function() {
                if (this.type === 'submit' || this.onclick) {
                    this.classList.add('loading');
                    setTimeout(() => {
                        this.classList.remove('loading');
                    }, 2000);
                }
            });
        }
    });
    
    // Add smooth transitions to form elements
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
    
    // Add hover effects to cards
    const cards = document.querySelectorAll('.card, .section');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.transition = 'transform 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Enhanced notification system
function showEnhancedNotification(type, message, duration = 3000) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.enhanced-notification');
    existingNotifications.forEach(notification => notification.remove());
    
    const notification = document.createElement('div');
    notification.className = `enhanced-notification ${type}`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 
                 type === 'error' ? 'fa-exclamation-circle' : 
                 type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
    
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-icon">
                <i class="fas ${icon}"></i>
            </div>
            <div class="notification-text">
                <div class="notification-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="notification-progress"></div>
    `;
    
    // Use CSS classes instead of inline styles for glass morphism
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        transform: translateX(100%);
        transition: transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    `;
    
    // CSS styles are now handled by config.css
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto remove after duration
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 400);
    }, duration);
}

// Override the original showNotification function
const originalShowNotification = showNotification;
showNotification = function(type, message) {
    showEnhancedNotification(type, message);
};

// Add keyboard shortcuts
function addKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + S to save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const activeTab = document.querySelector('.tab-button.active');
            if (activeTab) {
                const tabId = activeTab.getAttribute('onclick').match(/openTab\('([^']+)'\)/);
                if (tabId) {
                    if (tabId[1] === 'frontend-tab') {
                        updateConfig();
                    } else if (tabId[1] === 'backend-tab') {
                        updateBackendConfig();
                    } else if (tabId[1] === 'env-tab') {
                        updateEnvConfig();
                    } else if (tabId[1] === 'backend-files-tab') {
                        updateBackendFilesConfig();
                    }
                }
            }
        }
        
        // Ctrl/Cmd + R to reset
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            const activeTab = document.querySelector('.tab-button.active');
            if (activeTab) {
                const tabId = activeTab.getAttribute('onclick').match(/openTab\('([^']+)'\)/);
                if (tabId) {
                    if (tabId[1] === 'frontend-tab') {
                        resetFrontendToDefault();
                    } else if (tabId[1] === 'backend-tab') {
                        resetBackendToDefault();
                    } else if (tabId[1] === 'env-tab') {
                        resetAllEnv();
                    } else if (tabId[1] === 'backend-files-tab') {
                        resetAllBackendFiles();
                    }
                }
            }
        }
    });
}

// Add font preview functionality
function addFontPreview() {
    const fontSelect = document.getElementById('font_family');
    const fontPreview = document.getElementById('font-preview');
    const fontPreviewText = document.getElementById('font-preview-text');
    
    if (fontSelect && fontPreview && fontPreviewText) {
        // Show preview on change
        fontSelect.addEventListener('change', function() {
            const selectedFont = this.value;
            fontPreviewText.style.fontFamily = selectedFont;
            fontPreview.style.display = 'block';
            
            // Add smooth transition
            fontPreviewText.style.transition = 'all 0.3s ease';
        });
        
        // Show preview on focus
        fontSelect.addEventListener('focus', function() {
            const selectedFont = this.value;
            fontPreviewText.style.fontFamily = selectedFont;
            fontPreview.style.display = 'block';
        });
        
        // Hide preview on blur (with delay)
        fontSelect.addEventListener('blur', function() {
            setTimeout(() => {
                if (document.activeElement !== fontSelect) {
                    fontPreview.style.display = 'none';
                }
            }, 200);
        });
        
        // Initialize with current font
        const currentFont = fontSelect.value;
        if (currentFont) {
            fontPreviewText.style.fontFamily = currentFont;
        }
    }
}

// Initialize all enhancements
document.addEventListener('DOMContentLoaded', function() {
    addModernUIEnhancements();
    addKeyboardShortcuts();
    addColorPickerValidation();
    addFontPreview();
});

// Load the frontend configuration when the page loads
loadConfig();
loadPromptsConfig();
loadEnvConfig();
loadBackendFilesConfig();
initCodeEditors();  // Initialize code editors
initRichTextEditor();  // Initialize rich text editor
addAIButtonStyles();  // Add AI button styles
initAITooltips();  // Initialize AI tooltips
initEmojiHandling();  // Initialize emoji handling
ensurePlaceholders();  // Ensure placeholders are set correctly

// Add event listeners to maintain placeholders
document.addEventListener('DOMContentLoaded', function() {
    const llmSelect = document.getElementById('llm_provider');
    if (llmSelect) {
        llmSelect.addEventListener('change', function() {
            setTimeout(() => ensurePlaceholders(), 200);
        });
    }
    
    const openaiInput = document.getElementById('OPENAI_API_KEY');
    const geminiInput = document.getElementById('GEMINI_API_KEY');
    const claudeInput = document.getElementById('ANTHROPIC_API_KEY');
    
    if (openaiInput) {
        openaiInput.addEventListener('focus', function() {
            if (!this.value || this.value === '') {
                this.placeholder = 'Required - Please enter your OpenAI API key';
            }
        });
        openaiInput.addEventListener('blur', function() {
            if (!this.value || this.value === '') {
                this.placeholder = 'Required - Please enter your OpenAI API key';
            }
        });
    }
    
    if (geminiInput) {
        geminiInput.addEventListener('focus', function() {
            if (!this.value || this.value === '') {
                this.placeholder = 'Required - Please enter your Gemini API key';
            }
        });
        geminiInput.addEventListener('blur', function() {
            if (!this.value || this.value === '') {
                this.placeholder = 'Required - Please enter your Gemini API key';
            }
        });
    }
    
    if (claudeInput) {
        claudeInput.addEventListener('focus', function() {
            if (!this.value || this.value === '') {
                this.placeholder = 'Required - Please enter your Anthropic API key';
            }
        });
        claudeInput.addEventListener('blur', function() {
            if (!this.value || this.value === '') {
                this.placeholder = 'Required - Please enter your Anthropic API key';
            }
        });
    }
});

// Toggle password visibility for a given input id
function toggleVisibilityById(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (input.type === 'password') {
        input.type = 'text';
        if (btn && btn.querySelector('i')) {
            btn.querySelector('i').classList.remove('fa-eye');
            btn.querySelector('i').classList.add('fa-eye-slash');
        }
    } else {
        input.type = 'password';
        if (btn && btn.querySelector('i')) {
            btn.querySelector('i').classList.remove('fa-eye-slash');
            btn.querySelector('i').classList.add('fa-eye');
        }
    }
}

// Toggle Normal Search section
function toggleNormalSearchSection() {
    const content = document.getElementById('normal_search_content');
    const chevron = document.getElementById('normal_search_chevron');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        chevron.style.transform = 'rotate(0deg)';
    }
}

// Toggle ID Specific Search section
function toggleIdSpecificSearchSection() {
    const content = document.getElementById('id_specific_search_content');
    const chevron = document.getElementById('id_specific_search_chevron');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        chevron.style.transform = 'rotate(0deg)';
    }
}

// Toggle Local Document Search section
function toggleLocalDocumentSearchSection() {
    const content = document.getElementById('local_document_search_content');
    const chevron = document.getElementById('local_document_search_chevron');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        chevron.style.transform = 'rotate(0deg)';
    }
}

// Toggle Query Cleaning section
function toggleQueryCleaningSection() {
    const content = document.getElementById('query_cleaning_content');
    const chevron = document.getElementById('query_cleaning_chevron');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        chevron.style.transform = 'rotate(0deg)';
    }
}

// Toggle Show References section
function toggleShowReferencesSection() {
    const content = document.getElementById('show_references_content');
    const chevron = document.getElementById('show_references_chevron');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        chevron.style.transform = 'rotate(0deg)';
    }
}

// Load clean_query.py content
async function loadCleanQueryContent() {
    try {
        const response = await fetch(`${baseURL}/fetch_clean_query`);
        if (response.ok) {
            const content = await response.text();
            document.getElementById('query_cleaning').value = content;
        } else {
            // If file doesn't exist, show instructions
            const instructions = `def clean_query(query):
    """
    Cleans and refines a query based on user needs.
    
    Parameters:
    - query (str): The query to clean and refine
    
    Returns:
    - str: The cleaned and refined query
    """
    if not query or not isinstance(query, str):
        return query
    
    # Basic cleaning - remove extra whitespace and normalize
    cleaned_query = query.strip()
    
    # Remove common query artifacts
    cleaned_query = cleaned_query.replace('"', '"').replace('"', '"')
    cleaned_query = cleaned_query.replace(''', "'").replace(''', "'")
    
    # Remove excessive punctuation
    import re
    cleaned_query = re.sub(r'[^\\w\\s\\-\\(\\)\\[\\]\\/\\:\\.\\,\\?]', ' ', cleaned_query)
    cleaned_query = re.sub(r'\\s+', ' ', cleaned_query)
    
    return cleaned_query.strip()`;
            
            document.getElementById('query_cleaning').value = instructions;
        }
    } catch (error) {
        console.error('Error loading clean_query.py:', error);
        // Show instructions if there's an error
        const instructions = `def clean_query(query):
    """
    Cleans and refines a query based on user needs.
    
    Parameters:
    - query (str): The query to clean and refine
    
    Returns:
    - str: The cleaned and refined query
    """
    if not query or not isinstance(query, str):
        return query
    
    # Basic cleaning - remove extra whitespace and normalize
    cleaned_query = query.strip()
    
    # Remove common query artifacts
    cleaned_query = cleaned_query.replace('"', '"').replace('"', '"')
    cleaned_query = cleaned_query.replace(''', "'").replace(''', "'")
    
    # Remove excessive punctuation
    import re
    cleaned_query = re.sub(r'[^\\w\\s\\-\\(\\)\\[\\]\\/\\:\\.\\,\\?]', ' ', cleaned_query)
    cleaned_query = re.sub(r'\\s+', ' ', cleaned_query)
    
    return cleaned_query.strip()`;
        
        document.getElementById('query_cleaning').value = instructions;
    }
}

// Save clean_query.py content
async function saveCleanQueryContent() {
    try {
        const content = document.getElementById('query_cleaning').value;
        const formData = new FormData();
        formData.append('content', content);
        
        const response = await fetch(`${baseURL}/save_clean_query`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            console.log('clean_query.py saved successfully');
        } else {
            console.error('Error saving clean_query.py:', result.message);
        }
    } catch (error) {
        console.error('Error saving clean_query.py:', error);
    }
}

async function saveState() {
    const stateName = document.getElementById('state_name').value.trim();
    
    if (!stateName) {
        showNotification('error', 'Please enter a state name');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('state_name', stateName);

        const response = await fetch(`${BACKEND_URL}/save_state`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showNotification('success', result.message);
            document.getElementById('state_name').value = '';
        } else {
            showNotification('error', result.detail || 'Failed to save state');
        }
    } catch (error) {
        showNotification('error', 'An error occurred while saving the state');
        console.error('Error saving state:', error);
    }
}

async function loadSavedStates() {
    try {
        const response = await fetch(`${BACKEND_URL}/list_saved_states`);
        const data = await response.json();
        
        const select = document.getElementById('state_select');
        const deleteSelect = document.getElementById('delete_state_select');
        
        select.innerHTML = '<option value="">Select a state...</option>';
        deleteSelect.innerHTML = '<option value="">Select a state...</option>';
        
        data.states.forEach(state => {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = state;
            select.appendChild(option);
            
            const deleteOption = document.createElement('option');
            deleteOption.value = state;
            deleteOption.textContent = state;
            deleteSelect.appendChild(deleteOption);
        });
    } catch (error) {
        showNotification('error', 'Failed to load saved states');
        console.error('Error loading saved states:', error);
    }
}

async function loadState() {
    const stateName = document.getElementById('state_select').value;
    
    if (!stateName) {
        showNotification('error', 'Please select a state to load');
        return;
    }

    showModal(
        "Load Saved State",
        `Are you sure you want to load the state "${stateName}"? This will replace your current configuration.`,
        async () => {
            try {
                const formData = new FormData();
                formData.append('state_name', stateName);

                const response = await fetch(`${BACKEND_URL}/load_state`, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    showNotification('success', result.message);
                    // Reload clean_query.py content after state load
                    loadCleanQueryContent();
                    // Show a second notification about manual refresh with longer duration
                    setTimeout(() => {
                        showNotification('info', 'If you don\'t see the changes, please refresh the page manually.');
                    }, 500);
                } else {
                    showNotification('error', result.detail || 'Failed to load state');
                }
            } catch (error) {
                showNotification('error', 'An error occurred while loading the state');
                console.error('Error loading state:', error);
            }
        }
    );
}

async function deleteState() {
    const stateName = document.getElementById('delete_state_select').value;
    
    if (!stateName) {
        showNotification('error', 'Please select a state to delete');
        return;
    }

    showModal(
        "Delete Saved State",
        `Are you sure you want to delete the state "${stateName}"? This action cannot be undone.`,
        async () => {
            try {
                const formData = new FormData();
                formData.append('state_name', stateName);

                const response = await fetch(`${BACKEND_URL}/delete_state`, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    showNotification('success', result.message);
                    // Reload the saved states to update both dropdowns
                    await loadSavedStates();
                    // Hide the delete section after successful deletion
                    toggleDeleteSection();
                } else {
                    showNotification('error', result.detail || 'Failed to delete state');
                }
            } catch (error) {
                showNotification('error', 'An error occurred while deleting the state');
                console.error('Error deleting state:', error);
            }
        }
    );
}

function toggleDeleteSection() {
    const deleteContainer = document.getElementById('delete_state_container');
    const toggleBtn = document.getElementById('toggle_delete_btn');
    const toggleIcon = document.getElementById('toggle_delete_icon');
    const toggleText = document.getElementById('toggle_delete_text');
    
    if (deleteContainer.style.display === 'none') {
        // Show delete section
        deleteContainer.style.display = 'block';
        toggleText.textContent = 'Hide Delete Options';
        toggleIcon.className = 'fas fa-eye-slash';
        toggleBtn.style.background = 'linear-gradient(135deg, #dc3545, #c82333)';
        toggleBtn.onmouseover = function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 12px rgba(220, 53, 69, 0.3)';
        };
        toggleBtn.onmouseout = function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 8px rgba(220, 53, 69, 0.2)';
        };
        
        // Add slide-down animation
        deleteContainer.style.animation = 'slideDown 0.3s ease-out';
    } else {
        // Hide delete section
        deleteContainer.style.display = 'none';
        toggleText.textContent = 'Show Delete Options';
        toggleIcon.className = 'fas fa-trash';
        toggleBtn.style.background = 'linear-gradient(135deg, #6c757d, #495057)';
        toggleBtn.onmouseover = function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 12px rgba(108, 117, 125, 0.3)';
        };
        toggleBtn.onmouseout = function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 8px rgba(108, 117, 125, 0.2)';
        };
    }
}

// Function to toggle query contention fields visibility and state
function toggleQueryContentionFields(enabled) {
    console.log('toggleQueryContentionFields called with enabled:', enabled);
    const queryContentionTextarea = document.getElementById('QUERY_CONTENTION_PROMPT');
    const queryContentionLabel = document.querySelector('label[for="QUERY_CONTENTION_PROMPT"]');
    const queryContentionResetBtn = document.querySelector('button[data-target="QUERY_CONTENTION_PROMPT"]');
    const checkbox = document.getElementById('query_contention_enabled');
    const checkboxLabel = document.querySelector('label[for="query_contention_enabled"]');
    const icon = document.getElementById('query_contention_icon');
    const aiButtonContainer = queryContentionTextarea?.closest('.input-group')?.querySelector('.ai-button-container');
    
    console.log('Elements found:', {
        textarea: !!queryContentionTextarea,
        label: !!queryContentionLabel,
        resetBtn: !!queryContentionResetBtn,
        icon: !!icon
    });
    
    if (queryContentionTextarea && queryContentionLabel) {
        if (enabled) {
            // Enable the field - show tick
            queryContentionTextarea.disabled = false;
            queryContentionTextarea.readOnly = false;
            queryContentionTextarea.style.opacity = '1';
            queryContentionTextarea.style.backgroundColor = '';
            queryContentionTextarea.style.filter = '';
            queryContentionTextarea.style.color = '';
            queryContentionTextarea.style.cursor = '';
            queryContentionLabel.style.opacity = '1';
            queryContentionLabel.style.color = '';
            if (queryContentionResetBtn) {
            queryContentionResetBtn.disabled = false;
            queryContentionResetBtn.style.opacity = '1';
            }
            
            // Update icon to white tick
            if (icon) {
                icon.textContent = '✓';
                console.log('Icon updated to tick:', icon.textContent);
                console.log('Icon element:', icon);
            } else {
                console.log('Icon element not found!');
            }
            
            // CSS will handle the checkbox label styling
            
            // Remove disabled class from container
            const container = queryContentionTextarea.closest('.input-group');
            if (container) {
                container.classList.remove('query-contention-disabled');
            }
            
            // Enable AI button
            if (aiButtonContainer) {
                const aiButton = aiButtonContainer.querySelector('.ai-prompt-btn');
                if (aiButton) {
                    aiButton.disabled = false;
                    aiButton.style.opacity = '1';
                    aiButton.style.cursor = '';
                }
            }
        } else {
            // Disable the field - show red cross
            queryContentionTextarea.disabled = true;
            queryContentionTextarea.readOnly = true;
            queryContentionLabel.style.opacity = '0.4';
            if (queryContentionResetBtn) {
            queryContentionResetBtn.disabled = true;
            }
            
            // Update icon to red cross
            if (icon) {
                icon.textContent = '✗';
                console.log('Icon updated to cross:', icon.textContent);
                console.log('Icon element:', icon);
            } else {
                console.log('Icon element not found for cross!');
            }
            
            // CSS will handle the checkbox label styling
            
            // Add disabled class to the entire section container
            const sectionContainer = queryContentionTextarea.closest('.input-group');
            if (sectionContainer) {
                sectionContainer.classList.add('query-contention-disabled');
            }
            
            // Disable AI button
            if (aiButtonContainer) {
                const aiButton = aiButtonContainer.querySelector('.ai-prompt-btn');
                if (aiButton) {
                    aiButton.disabled = true;
                }
            }
        }
    }
}

// Function to handle query contention toggle change
function onQueryContentionToggle() {
    console.log('Query contention toggle called');
    const checkbox = document.getElementById('query_contention_enabled');
    const isEnabled = checkbox.checked;
    console.log('Is enabled:', isEnabled);
    console.log('Checkbox element:', checkbox);
    console.log('Checkbox checked state:', checkbox.checked);
    
    // Force a small delay to ensure the checkbox state is updated
    setTimeout(() => {
    toggleQueryContentionFields(isEnabled);
    }, 10);
}

// Add event listener for direct testing
document.addEventListener('DOMContentLoaded', function() {
    const checkbox = document.getElementById('query_contention_enabled');
    if (checkbox) {
        console.log('Checkbox found, adding click listener');
        checkbox.addEventListener('click', function(e) {
            console.log('Checkbox clicked directly');
            setTimeout(() => {
                onQueryContentionToggle();
            }, 10);
        });
        
        // Test CSS selectors
        const label = document.querySelector('label[for="query_contention_enabled"]');
        const icon = document.getElementById('query_contention_icon');
        console.log('CSS Test - Label found:', !!label);
        console.log('CSS Test - Icon found:', !!icon);
        console.log('CSS Test - Checkbox checked:', checkbox.checked);
        
        // Test CSS selector manually
        if (label) {
            console.log('CSS Test - Label styles:', {
                backgroundColor: getComputedStyle(label).backgroundColor,
                borderColor: getComputedStyle(label).borderColor
            });
        }
        if (icon) {
            console.log('CSS Test - Icon styles:', {
                color: getComputedStyle(icon).color,
                content: icon.textContent
            });
        }
    }
});

// Function to toggle LLM provider (no-op: provider is now set via dropdown; kept for compatibility)
function toggleLLMProvider(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const llmSelect = document.getElementById('llm_provider');
    if (llmSelect) {
        setLLMProvider(llmSelect.value || 'OpenAI');
    }
}

// Helper function to ensure placeholder text is set correctly
function ensurePlaceholders() {
    const openaiInput = document.getElementById('OPENAI_API_KEY');
    const geminiInput = document.getElementById('GEMINI_API_KEY');
    const claudeInput = document.getElementById('ANTHROPIC_API_KEY');
    
    if (openaiInput) {
        openaiInput.placeholder = 'Required - Please enter your OpenAI API key';
        if (!openaiInput.value || openaiInput.value === '') {
            openaiInput.focus();
            openaiInput.blur();
        }
    }
    if (geminiInput) {
        geminiInput.placeholder = 'Required - Please enter your Gemini API key';
        if (!geminiInput.value || geminiInput.value === '') {
            geminiInput.focus();
            geminiInput.blur();
        }
    }
    if (claudeInput) {
        claudeInput.placeholder = 'Required - Please enter your Anthropic API key';
        if (!claudeInput.value || claudeInput.value === '') {
            claudeInput.focus();
            claudeInput.blur();
        }
    }
}

// Function to force placeholder visibility
function forcePlaceholderVisibility(inputElement) {
    if (inputElement && (!inputElement.value || inputElement.value === '')) {
        inputElement.focus();
        inputElement.blur();
    }
}

// Map data-side (4-segment pill) to provider name and back
var LLM_SIDE_TO_PROVIDER = { left: 'OpenAI', center: 'Gemini', right: 'Claude', 'far-right': 'Ollama' };
var LLM_PROVIDER_TO_SIDE = { OpenAI: 'left', Gemini: 'center', Claude: 'right', Ollama: 'far-right' };

// Function to set LLM provider based on value (OpenAI, Gemini, Claude, or Ollama)
function setLLMProvider(provider) {
    const validProviders = ['OpenAI', 'Gemini', 'Claude', 'Ollama'];
    const norm = validProviders.includes(provider) ? provider : 'OpenAI';
    const side = LLM_PROVIDER_TO_SIDE[norm];
    const openaiSection = document.getElementById('openai_section');
    const geminiSection = document.getElementById('gemini_section');
    const claudeSection = document.getElementById('claude_section');
    const ollamaSection = document.getElementById('ollama_section');
    const openaiInput = document.getElementById('OPENAI_API_KEY');
    const geminiInput = document.getElementById('GEMINI_API_KEY');
    const claudeInput = document.getElementById('ANTHROPIC_API_KEY');
    const hiddenInput = document.getElementById('llm_provider');
    const modelSwitch = document.getElementById('modelSwitch');

    if (hiddenInput) hiddenInput.value = norm;
    if (modelSwitch && side) modelSwitch.setAttribute('data-side', side);

    if (openaiInput) openaiInput.placeholder = 'Required - Please enter your OpenAI API key';
    if (geminiInput) geminiInput.placeholder = 'Required - Please enter your Gemini API key';
    if (claudeInput) claudeInput.placeholder = 'Required - Please enter your Anthropic API key';

    if (openaiSection) openaiSection.style.display = (norm === 'OpenAI') ? 'block' : 'none';
    if (geminiSection) geminiSection.style.display = (norm === 'Gemini') ? 'block' : 'none';
    if (claudeSection) claudeSection.style.display = (norm === 'Claude') ? 'block' : 'none';
    if (ollamaSection) ollamaSection.style.display = (norm === 'Ollama') ? 'block' : 'none';

    if (norm !== 'Ollama') {
        const focusInput = norm === 'OpenAI' ? openaiInput : (norm === 'Gemini' ? geminiInput : claudeInput);
        setTimeout(function() {
            if (focusInput && (!focusInput.value || focusInput.value === '')) {
                focusInput.focus();
                focusInput.blur();
            }
        }, 100);
    } else {
        // Auto-check Ollama status whenever the section becomes visible
        setTimeout(checkOllamaStatus, 200);
    }
}



// Initialize 4-segment AI provider pill
function initModernToggle() {
    var modelSwitch = document.getElementById('modelSwitch');
    if (!modelSwitch) return;

    // Attach a JS click listener to every label — belt-and-suspenders on top of
    // the inline onclick attributes, so no parent element can swallow the event.
    modelSwitch.querySelectorAll('[data-provider]').forEach(function(lbl) {
        lbl.style.cursor = 'pointer';
        lbl.addEventListener('click', function(e) {
            e.stopPropagation();
            var provider = lbl.getAttribute('data-provider');
            if (provider) setLLMProvider(provider);
        });
    });

    // Keyboard: Arrow keys cycle through providers
    modelSwitch.addEventListener('keydown', function(e) {
        var sides     = ['left', 'center', 'right', 'far-right'];
        var providers = sides.map(function(s) { return LLM_SIDE_TO_PROVIDER[s]; });
        var current   = modelSwitch.getAttribute('data-side') || 'left';
        var idx       = sides.indexOf(current);
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
            e.preventDefault();
            setLLMProvider(providers[(idx + 1) % providers.length]);
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            e.preventDefault();
            setLLMProvider(providers[(idx - 1 + providers.length) % providers.length]);
        }
    });
}

// Load saved states when the page loads
document.addEventListener('DOMContentLoaded', () => {
    loadSavedStates();
    initModernToggle();
});



async function generateAIPrompt(promptType) {
    const button = event.currentTarget;
    const spinner = button.querySelector('.ai-button-spinner');
    const icon = button.querySelector('i');
    const originalText = button.querySelector('span').textContent;
    const originalIcon = icon.className;
    
    // Fun icon animation sequence
    const iconSequence = [
        'fas fa-robot',
        'fas fa-brain',
        'fas fa-magic',
        'fas fa-sparkles',
        'fas fa-wand-magic-sparkles',
        'fas fa-crystal-ball',
        'fas fa-lightbulb',
        'fas fa-rocket',
        'fas fa-star',
        'fas fa-robot'
    ];
    
    let iconIndex = 0;
    const iconInterval = setInterval(() => {
        icon.className = iconSequence[iconIndex];
        iconIndex = (iconIndex + 1) % iconSequence.length;
    }, 600);
    
    try {
        // Show loading state
        button.disabled = true;
        button.classList.add('generating');
        spinner.style.display = 'block';
        button.querySelector('span').textContent = 'Generating...';
        
        // Get the current prompt text
        // Map prompt types to their corresponding textarea IDs
        const promptTypeToId = {
            'question_validity': 'DETERMINE_QUESTION_VALIDITY_PROMPT',
            'general_query': 'GENERAL_QUERY_PROMPT',
            'query_contention': 'QUERY_CONTENTION_PROMPT',
            'relevance': 'RELEVANCE_CLASSIFIER_PROMPT',
            'article_type': 'ARTICLE_TYPE_PROMPT',
            'abstract': 'ABSTRACT_EXTRACTION_PROMPT',
            'review_summary': 'REVIEW_SUMMARY_PROMPT',
            'study_summary': 'STUDY_SUMMARY_PROMPT',
            'relevant_sections': 'RELEVANT_SECTIONS_PROMPT',
            'final_response': 'FINAL_RESPONSE_PROMPT'
        };
        
        const textareaId = promptTypeToId[promptType];
        if (!textareaId) {
            throw new Error(`Invalid prompt type: ${promptType}`);
        }
        
        const promptTextarea = document.getElementById(textareaId);
        if (!promptTextarea) {
            throw new Error(`Could not find textarea with ID: ${textareaId}`);
        }
        
        const currentPrompt = promptTextarea.value;
        console.log(currentPrompt);
        console.log(promptType);
        // Call the backend endpoint
        const response = await fetch(`${BACKEND_URL}/generate_prompt_endpoint`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                article_content: currentPrompt,
                prompt_type: promptType
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate prompt');
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Update the textarea with the generated prompt
            promptTextarea.value = data.prompt;
            
            // Show success message
            showTemporaryMessage(button, 'Prompt generated successfully!');
            createParticleEffect(button);
        } else {
            throw new Error(data.detail || 'Failed to generate prompt');
        }
    } catch (error) {
        console.error('Error generating prompt:', error);
        showTemporaryMessage(button, 'Failed to generate prompt. Please try again.');
    } finally {
        // Stop icon animation and restore original icon
        clearInterval(iconInterval);
        icon.className = originalIcon;
        
        // Reset button state
        button.disabled = false;
        button.classList.remove('generating');
        spinner.style.display = 'none';
        button.querySelector('span').textContent = originalText;
    }
}
