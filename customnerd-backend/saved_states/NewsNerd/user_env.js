window.env = {
    "FRONTEND_FLOW": {
        "SITE_NAME": "News Nerds",
        "SITE_LOGO": "assets/customnerd_logo.png",
        "LOGO_NAME": "",
        "SITE_ICON": "📰",
        "SITE_TAGLINE": "We answer your news related questions",
        "DISCLAIMER": "Everything on this website is for educational purposes only.<u><b> Always watch news</b></u>",
        "QUESTION_PLACEHOLDER": "Enter your news-related question here....",
        "STYLES": {
            "BACKGROUND_COLOR": "#e9e2e2",
            "FONT_FAMILY": "'Nunito', sans-serif",
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
                "label": "Search using News Articles",
                "tooltip": "Automatically search for relevant news articles",
                "type": "checkbox",
                "visible": true,
                "defaultChecked": true
            }
        ],
        "chat_history": {
            "visible": true
        },
        "query_cleaning": {
            "visible": false
        },
        "reference_section": {
            "visible": true
        }
    }
};