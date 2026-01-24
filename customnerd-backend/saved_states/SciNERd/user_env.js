window.env = {
    "FRONTEND_FLOW": {
        "SITE_NAME": "SciNERd",
        "SITE_LOGO": "assets/customnerd_logo.png",
        "LOGO_NAME": "",
        "SITE_ICON": "🧠",
        "SITE_TAGLINE": "We answer your NLP and ML questions based on the strongest scientific evidence from our Qasper PDF",
        "DISCLAIMER": "<b>SciNERd is for educational and informational purposes only.</b>",
        "QUESTION_PLACEHOLDER": "Enter your ML-related question here....",
        "STYLES": {
            "BACKGROUND_COLOR": "#F0F2F5",
            "FONT_FAMILY": "'Rubik', sans-serif",
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
                "visible": true,
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
                "label": "Search using Pubmed Articles",
                "tooltip": "Automatically search PubMed for relevant articles",
                "type": "checkbox",
                "visible": false,
                "defaultChecked": true
            }
        ],
        "reference_section": {
            "visible": false
        },
        "chat_history": {
            "visible": false
        },
        "query_cleaning": {
            "visible": false
        }
    }
};