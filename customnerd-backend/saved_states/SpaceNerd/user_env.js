window.env = {
    "FRONTEND_FLOW": {
        "SITE_NAME": "Space Nerd",
        "SITE_LOGO": "assets/customnerd_logo.png",
        "LOGO_NAME": "",
        "SITE_ICON": "⋆⁺₊⋆ ☾⋆⁺₊⋆",
        "SITE_TAGLINE": "We answer your space related questions based on Nasa",
        "DISCLAIMER": "<b>Everything on this website is for educational purposes only</b>",
        "QUESTION_PLACEHOLDER": "Enter your space-related question here....",
        "STYLES": {
            "BACKGROUND_COLOR": "#f5f4f4",
            "FONT_FAMILY": "'Open Sans', sans-serif",
            "SUBMIT_BUTTON_BG": "#007bff"
        },
        "API_URL": "http://127.0.0.1:8000"
    },
    "USER_FLOW": {
        "searchStrategies": [
            {
                "id": "upload-articles",
                "label": "Include articles from your computer",
                "tooltip": "Only accepts PDF file formats.",
                "type": "file-upload",
                "visible": false,
                "defaultChecked": false
            },
            {
                "id": "insert-pmids",
                "label": "Serach using PMIDs",
                "tooltip": "Enter PMIDs separated by semicolons",
                "type": "text-input",
                "visible": false,
                "defaultChecked": false
            },
            {
                "id": "search-pubmed",
                "label": "Search using NASA, Wikipedia and other Articles",
                "tooltip": "Automatically search for relevant articles",
                "type": "checkbox",
                "visible": true,
                "defaultChecked": true
            }
        ],
        "query_cleaning": {
            "visible": true
        },
        "chat_history": {
            "visible": true
        },
        "reference_section": {
            "visible": true
        }
    }
};