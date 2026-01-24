

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

// Wait for the DOM to fully load before applying changes
document.addEventListener("DOMContentLoaded", function () {
    console.log("Applying site settings from user_env.js...");

    // Set Page Title
    document.title = window.env.FRONTEND_FLOW.SITE_NAME;

    // Set Favicon (Emoji-based)
    let favicon = document.createElement("link");
    favicon.rel = "icon";
    favicon.href = `data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>${window.env.FRONTEND_FLOW.SITE_ICON}</text></svg>`;
    document.head.appendChild(favicon);

    // Set Logo with fallback
    let logoElement = document.getElementById("site-logo");
    if (logoElement) {
        setLogoWithFallback(logoElement, window.env.FRONTEND_FLOW.SITE_LOGO, `${window.env.FRONTEND_FLOW.SITE_NAME} Logo`);
    }

    // Set Tagline
    let taglineElement = document.getElementById("site-tagline");
    if (taglineElement) {
        taglineElement.textContent = window.env.FRONTEND_FLOW.SITE_TAGLINE;
    }

    // Set Disclaimer
    let disclaimerElement = document.querySelector(".disclaimer");
    if (disclaimerElement) {
        disclaimerElement.innerHTML = formatText(window.env.FRONTEND_FLOW.DISCLAIMER);
    }

    // Set Input Placeholder
    let questionInput = document.getElementById("question");
    if (questionInput) {
        questionInput.placeholder = window.env.FRONTEND_FLOW.QUESTION_PLACEHOLDER;
    }

    // Apply Global Styles
    document.body.style.backgroundColor = window.env.FRONTEND_FLOW.STYLES.BACKGROUND_COLOR;
    // Load and apply selected font family
    (function applyConfiguredFont() {
        const configuredFont = window.env.FRONTEND_FLOW.STYLES.FONT_FAMILY || "'Lato', sans-serif";
        // Attempt to extract primary font name within quotes for Google Fonts
        const fontMatch = configuredFont.match(/'([^']+)'|"([^"]+)"/);
        const primaryFontName = fontMatch ? (fontMatch[1] || fontMatch[2]) : null;
        if (primaryFontName) {
            const existing = document.getElementById('dynamic-google-font');
            if (!existing) {
                const link = document.createElement('link');
                link.id = 'dynamic-google-font';
                link.rel = 'stylesheet';
                const googleHref = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(primaryFontName.replace(/\s+/g, '+'))}:wght@300;400;500;600;700&display=swap`;
                link.href = googleHref;
                document.head.appendChild(link);
            }
        }
        document.body.style.fontFamily = configuredFont;
    })();
    // Apply background color to container
    let container = document.getElementById("container");
    if (container) {
        container.style.backgroundColor = window.env.FRONTEND_FLOW.STYLES.BACKGROUND_COLOR;
    }

    // Apply Button Styles
    let submitButton = document.getElementById("submit");
    if (submitButton) {
        submitButton.style.backgroundColor = window.env.FRONTEND_FLOW.STYLES.SUBMIT_BUTTON_BG;
    }
    
    // Update glass element colors based on new background
    if (typeof updateGlassElementColors === 'function') {
        updateGlassElementColors();
    }

    // Load Example Questions
    // let exampleQuestionsContainer = document.getElementById("example-questions");
    // if (exampleQuestionsContainer) {
    //     exampleQuestionsContainer.innerHTML = "<h3>Example Questions:</h3>";
    //     window.env.EXAMPLE_QUESTIONS.forEach((question) => {
    //         let div = document.createElement("div");
    //         div.className = "example-question";
    //         div.textContent = question;
    //         div.style.backgroundColor = window.env.STYLES.EXAMPLE_QUESTION_BG;
    //         div.addEventListener("click", function () {
    //             questionInput.value = question;
    //             submitButton.click();
    //         });
    //         exampleQuestionsContainer.appendChild(div);
    //     });
    // }

    // Apply Styling to Similar Questions Section
    let similarQuestions = document.getElementById("similarQuestions");
    if (similarQuestions) {
        similarQuestions.style.backgroundColor = window.env.FRONTEND_FLOW.STYLES.SIMILAR_QUESTION_BG;
    }
});
