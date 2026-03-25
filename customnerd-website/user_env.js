window.env = {
    "FRONTEND_FLOW": {
        "SITE_NAME": "Cure Nerd",
        "SITE_LOGO": "assets/customnerd_logo.png",
        "LOGO_NAME": "",
        "SITE_ICON": "⚕",
        "SITE_TAGLINE": "We answer your cure and treatment questions using evidence from PubMed, arXiv, and Mayo Clinic",
        "DISCLAIMER": "Everything on this website is for educational purposes only. It is not intended to be a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.",
        "QUESTION_PLACEHOLDER": "Enter your treatment-related question here....",
        "STYLES": {
            "BACKGROUND_COLOR": "#EFF8FF",
            "FONT_FAMILY": "'Roboto', sans-serif",
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
                "visible": true,
                "defaultChecked": false
            },
            {
                "id": "search-pubmed",
                "label": "Search using PubMed, arXiv, and Mayo Clinic",
                "tooltip": "Automatically search PubMed, arXiv, and Mayo Clinic for relevant content",
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