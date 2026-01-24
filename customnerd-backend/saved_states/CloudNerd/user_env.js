window.env = {
    "FRONTEND_FLOW": {
        "SITE_NAME": "CloudExpert Nerd",
        "SITE_LOGO": "assets/customnerd_logo.png",
        "LOGO_NAME": "",
        "SITE_ICON": "☁️",
        "SITE_TAGLINE": "We answer your cloud related questions based on Stack overflow",
        "DISCLAIMER": "<article class=\"text-token-text-primary w-full focus:outline-none scroll-mt-[calc(var(--header-height)+min(200px,max(70px,20svh)))]\" tabindex=\"-1\" dir=\"auto\" data-turn-id=\"d64a820a-a8bb-43dc-b4e2-43cd35161f72\" data-testid=\"conversation-turn-4\" data-scroll-anchor=\"true\" data-turn=\"assistant\"><div class=\"text-base my-auto mx-auto pb-10 [--thread-content-margin:--spacing(4)] thread-sm:[--thread-content-margin:--spacing(6)] thread-lg:[--thread-content-margin:--spacing(16)] px-(--thread-content-margin)\"><div class=\"[--thread-content-max-width:40rem] thread-sm:[--thread-content-max-width:40rem] thread-lg:[--thread-content-max-width:48rem] mx-auto max-w-(--thread-content-max-width) flex-1 group/turn-messages focus-visible:outline-hidden relative flex w-full min-w-0 flex-col agent-turn\" tabindex=\"-1\"><div class=\"flex max-w-full flex-col grow\"><div data-message-author-role=\"assistant\" data-message-id=\"193fcb03-d021-49d8-b4f4-3a4074d180b1\" dir=\"auto\" class=\"min-h-8 text-message relative flex w-full flex-col items-end gap-2 text-start break-words whitespace-normal [.text-message+&amp;]:mt-5\" data-message-model-slug=\"gpt-5\"><div class=\"flex w-full flex-col gap-1 empty:hidden first:pt-[3px]\"><div class=\"streaming-animation markdown prose dark:prose-invert w-full break-words dark markdown-new-styling\"><p data-start=\"219\" data-end=\"833\"><b><u>Everything on this website is for educational and informational purposes only</u></b>. The content is based on publicly available information, including community discussions and third-party sources, and may not always reflect the most current practices or official guidance. It is not intended to replace professional consultation, official cloud provider documentation, or vendor-specific support. Always review the official documentation from your cloud service provider and seek advice from a qualified professional before making technical, architectural, or security decisions for your environment.</p></div></div></div></div></div></div></article><div aria-hidden=\"true\" data-edge=\"true\" class=\"pointer-events-none h-px w-px\"></div>",
        "QUESTION_PLACEHOLDER": "Enter your cloud-related question here....",
        "STYLES": {
            "BACKGROUND_COLOR": "#fafafa",
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
                "label": "Search using Stack Exchange Articles",
                "tooltip": "Automatically search Stack Overflow for relevant articles and discussion",
                "type": "checkbox",
                "visible": true,
                "defaultChecked": true
            }
        ],
        "reference_section": {
            "visible": true
        },
        "chat_history": {
            "visible": true
        },
        "query_cleaning": {
            "visible": true
        }
    }
};