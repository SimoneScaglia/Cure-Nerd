const baseURL = window.env.FRONTEND_FLOW.API_URL;  // Adjust the base URL as needed
const disclaimer = `
DietNerd is an exploratory tool designed to enrich your conversations with a registered dietitian or registered dietitian nutritionist, who can then review your profile before providing recommendations.
Please be aware that the insights provided by DietNerd may not fully take into consideration all potential medication interactions or pre-existing conditions.
To find a local expert near you, use this website: https://www.eatright.org/find-a-nutrition-expert
`

/**
 * Asynchronously checks if a given user query is valid.
 *
 * @param {string} userQuery - The user query to be checked.
 * @return {Promise<Object>} A Promise that resolves to the response object.
 * @throws {Error} If the network response is not ok.
 */
async function check_valid(userQuery) {
    try {
        const response = await fetch(`${baseURL}/check_valid/${userQuery}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            mode: 'cors'
        });
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error in query_generation:', error);
    }
}


/**
 * Generates an answer based on the given question.
 *
 * @param {string} question - The question to generate an answer for.
 * @return {Promise<Object>} A Promise that resolves to the generated answer.
 * @throws {Error} If the network response is not ok.
 */
const generate = async (question) => {
    try {
        const queryUrl = `${baseURL}/generate/${encodeURIComponent(question)}`;
        const response = await fetch(queryUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            mode: 'cors'
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const result = await response.json();
        return result;
    } catch (err) {
        console.error('Fetch error:', err);
        throw err;
    }
};

/**
 * Retrieves a similarity search result from the server based on the provided question.
 *
 * @param {string} question - The question to be searched.
 * @return {Promise<Object>} A promise that resolves to the similarity search result object.
 * @throws {Error} If the network response is not ok.
 */
const get_sim = async (question) => {
    try {
        const queryUrl = `${baseURL}/db_sim_search/${encodeURIComponent(question)}`;
        const response = await fetch(queryUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            mode: 'cors'
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const result = await response.json();
        return result;
    } catch (err) {
        console.error('Fetch error:', err);
        throw err;
    }
};

/**
 * Split the citation into its components using regex
 *
 * @param {string} citation - The citation to be parsed
 * @return {Array} An array containing the authors, title, and journal of the citation
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
 * Formats raw reference text by converting URLs to hyperlinks and improving formatting
 *
 * @param {string} rawText - The raw reference text to format
 * @return {string} The formatted reference text with hyperlinks
 */
const formatRawReferences = (rawText) => {
    if (!rawText || !rawText.trim()) {
        return '';
    }
    
    let formattedText = rawText.trim();
    
    // Convert URLs to hyperlinks - matches http/https URLs
    formattedText = formattedText.replace(
        /(https?:\/\/[^\s<>"]+)/gi,
        '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
    );
    
    // Format reference numbers [1], [2], etc. to be bold
    formattedText = formattedText.replace(
        /(\[\d+\])/g,
        '<strong>$1</strong>'
    );
    
    // Format numbered references like "1.", "2.", etc. to be bold
    formattedText = formattedText.replace(
        /^(\d+\.)\s/gm,
        '<strong>$1</strong> '
    );
    
    // Add proper line breaks between different references
    // Split by newlines and process each line
    const lines = formattedText.split(/\r?\n/);
    const processedLines = lines.map(line => {
        line = line.trim();
        if (!line) return '';
        
        // If line starts with a reference number, add extra spacing
        if (/^(\[\d+\]|\d+\.)/.test(line)) {
            return line;
        }
        
        return line;
    }).filter(line => line !== '');
    
    // Join lines with proper spacing
    formattedText = processedLines.join('<br><br>');
    
    // Format quoted titles to be italic
    formattedText = formattedText.replace(
        /"([^"]+)"/g,
        '<em>"$1"</em>'
    );
    
    // Clean up multiple spaces
    formattedText = formattedText.replace(/\s+/g, ' ');
    
    return formattedText;
};

/**
 * Formats references from the stored references content as clickable links.
 *
 * @return {string} The formatted references as a string.
 */
const formatReferences = () => {
    // Get the stored references content
    const referencesContent = localStorage.getItem('referencesContent');
    if (!referencesContent) {
        return 'No references available.';
    }

    // Check if referencesContent is our fallback message
    if (referencesContent === "No references to be shown.") {
        return 'No references to be shown.';
    }

    // Safely parse JSON with null checks
    const citationsData = localStorage.getItem('citations');
    const referenceData = localStorage.getItem('referenceObject');
    
    if (!citationsData || !referenceData) {
        // Check if we have any content in referencesContent that we can display
        if (referencesContent.trim()) {
            // Remove reference headers and see if there's any meaningful content
            const contentWithoutHeaders = referencesContent
                .replace(/^(References?:?|### References?:?|#### References?:?|\*\*References?\*\*:?)\s*/i, '')
                .trim();
            
            if (contentWithoutHeaders) {
                return `<b>References:</b><br><br>${formatRawReferences(contentWithoutHeaders)}`;
            }
        }
        return 'No references available.';
    }

    let citations, citationObj;
    try {
        citations = JSON.parse(citationsData);
        citationObj = JSON.parse(referenceData);
    } catch (e) {
        console.error('Error parsing citation data:', e);
        // Fallback: try to display raw referencesContent if it exists and has meaningful content
        if (referencesContent && referencesContent.trim()) {
            const contentWithoutHeaders = referencesContent
                .replace(/^(References?:?|### References?:?|#### References?:?|\*\*References?\*\*:?)\s*/i, '')
                .trim();
            
            if (contentWithoutHeaders) {
                return `<b>References:</b><br><br>${formatRawReferences(contentWithoutHeaders)}`;
            }
        }
        return 'Error loading references.';
    }

    const references = extractReferences(referencesContent);
    if (references.length === 0) {
        // Check if referencesContent has any meaningful content to display
        if (referencesContent && referencesContent.trim()) {
            const contentWithoutHeaders = referencesContent
                .replace(/^(References?:?|### References?:?|#### References?:?|\*\*References?\*\*:?)\s*/i, '')
                .trim();
            
            if (contentWithoutHeaders && contentWithoutHeaders.length > 5) {
                return `<b>References:</b><br><br>${formatRawReferences(contentWithoutHeaders)}`;
            }
        }
        return 'No references available.';
    }

    // Ensure citationObj is an array
    if (!Array.isArray(citationObj)) {
        console.error('Citation object is not an array:', citationObj);
        // Try to display raw references content if available
        if (referencesContent && referencesContent.trim()) {
            const contentWithoutHeaders = referencesContent
                .replace(/^(References?:?|### References?:?|#### References?:?|\*\*References?\*\*:?)\s*/i, '')
                .trim();
            
            if (contentWithoutHeaders) {
                return `<b>References:</b><br><br>${formatRawReferences(contentWithoutHeaders)}`;
            }
        }
        return 'Error loading references.';
    }

    const seenReferences = new Set();
    const referenceList = references
        .map((ref) => {
            // Normalize the reference number
            const normalizedRef = normalizeReference(ref);

            // Skip if we've already seen this normalized reference
            if (seenReferences.has(normalizedRef)) {
                return null;
            }
            seenReferences.add(normalizedRef);

            // Since citations_obj is an array, find the citation by index
            const refIndex = normalizedRef - 1; // Convert to 0-based index
            if (refIndex < 0 || refIndex >= citationObj.length) {
                return null;
            }

            const citation = citationObj[refIndex];
            if (!citation) {
                return null;
            }

            const citationToDisplay = `<strong>${ref} ${citation.title}</br>${citation.author_name}<br>${citation.journal}</strong>`;

            // Pass the array index instead of the reference number for proper mapping
            return `<a href="reference.html?ref=${refIndex}" target="_blank">${citationToDisplay}</a>`;
        })
        .filter(Boolean)
        .join('<br><br>');

    if (!referenceList || referenceList.trim() === '') {
        // Final fallback: try to display the raw referencesContent
        if (referencesContent && referencesContent.trim()) {
            const contentWithoutHeaders = referencesContent
                .replace(/^(References?:?|### References?:?|#### References?:?|\*\*References?\*\*:?)\s*/i, '')
                .trim();
            
            if (contentWithoutHeaders) {
                return `<b>References:</b><br><br>${formatRawReferences(contentWithoutHeaders)}`;
            }
        }
        return 'No references available.';
    }

    return `<b>References:</b><br><br> ${referenceList}`;
};
  
  // Function to normalize reference numbers
  const normalizeReference = (ref) => {
    // Remove any non-digit characters and convert to a number
    return parseInt(ref.replace(/\D/g, ''), 10);
  };

/**
 * Extracts references from the given output.
 *
 * @param {string} output - The output containing references.
 * @return {Array} An array of references.
 */
const extractReferences = (output) => {
    const referenceMarkers = [
        "References:", 
        "References", 
        "Reference:", 
        "### References", 
        "### References:", 
        "#### References", 
        "#### References:", 
        "**References:**", 
        "**References**:", 
        "**References**", 
        "Reference"
      ];
      
      // Initialize referencePart as undefined
      let referencePart = undefined;
      
      // Loop through each marker and try to find a match
      for (const marker of referenceMarkers) {
        if (output.includes(marker)) {
          // Split using the first matching marker and break the loop
          referencePart = output.split(marker)[1];
          break;
        }
      }
    
    if (!referencePart) return [];
  
    // Use a regex that matches both [n] and n. formats
    const referenceRegex = /(\[\d+\]|\d+\.)/g;
    
    // Find all matches
    const matches = referencePart.match(referenceRegex) || [];
    
    // Normalize and deduplicate the matches
    const uniqueReferences = [...new Set(matches.map(normalizeReference))];
    
    // Convert back to original format, preferring [n] over n.
    return uniqueReferences.map(num => matches.find(ref => normalizeReference(ref) === num) || `[${num}]`);
  };

/**
 * Finds the citation corresponding to the given reference.
 *
 * @param {string} ref - The reference.
 * @param {Array} citations - The array of citations.
 * @return {string|undefined} The citation corresponding to the reference, or undefined if not found.
 */
const findCitation = (ref, citations) => {
  const refNumber = ref.match(/\d+/)[0];
  return citations.find((citation) => citation.startsWith(`[${refNumber}]`) || citation.startsWith(`${refNumber}.`));
};


/**
 * Returns the analysis text based on whether the citation has full text or not.
 *
 * @param {boolean} fullText - Indicates whether the citation has full text.
 * @return {string} The analysis text.
 */
const getAnalysisText = (fullText) => {
  const iconStyle = 'width: 16px; height: 16px; vertical-align: middle; margin-right: 4px;';
  const analysisText = fullText ? 'Full Text Analysis' : 'Abstract Only Analysis';
  const imageUrl = fullText ? 'assets/full_text.png' : 'assets/abstract.png';
  return `<span style="color: black; font-weight: bold; border: 1px solid ${fullText ? 'green' : 'yellow'}; padding: 2px 4px; background-color: rgba(${fullText ? '0, 128, 0' : '255, 255, 0'}, 0.1); display: inline-flex; align-items: center;"><img src="${imageUrl}" alt="${analysisText}" style="${iconStyle}"><img src="${imageUrl}" alt="${analysisText}" style="${iconStyle}">${analysisText}</span>`;
};


/**
 * Formats the input text by replacing newline characters with `<br>`,
 * double asterisks with `<strong>`, triple hashes with `<strong>`,
 * and hyphens or asterisks with `<li>`.
 *
 * @param {string} input - The input text to be formatted.
 * @param {string} disclaimer - The disclaimer to be appended to the formatted text.
 * @return {string} The formatted text.
 */
const formatText = (input,disclaimer) => {
    // Replace \n with <br>
    let formattedText = input.replace(/\n/g, '<br>');
    // Replace **text** with <strong>text</strong>
    formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Replace ###
    formattedText = formattedText.replace(/### (.*?)(<br>|$)/g, '<strong>$1</strong>$2');
    // Replace "-" with <li> 
    formattedText = formattedText.replace(/[-*] (.*?)(<br>|$)/g, '<li>$1</li>');
    return formattedText;
}

/**
 * Generates a PDF document based on the formatted text content.
 */
const generatePDF = () => {
    try {
        // Check if jsPDF is available
        if (typeof window.jspdf === 'undefined') {
            console.error('jsPDF library not loaded');
            alert('PDF generation library not loaded. Please refresh the page and try again.');
            return;
        }

        const { jsPDF } = window.jspdf;
        
        // Get the current answer and question
        const question = document.getElementById('question').value.trim();
        const rawOutput = localStorage.getItem("rawOutput");
        
        if (!rawOutput) {
            alert('No answer available to download. Please generate an answer first.');
            return;
        }

        // Create PDF document
        const doc = new jsPDF();
        
        // Set up document properties
        const lineHeight = 7;
        let y = 20;
        const listItemIndent = 10;
        const maxWidth = 180;
        const pageHeight = doc.internal.pageSize.height;
        const margin = 15;

        // Function to add formatted text with word wrap
        const addFormattedText = (text, startX, fontSize = 12) => {
            let x = startX;
            const lines = text.split('\n');

            lines.forEach(line => {
                x = startX;
                const isListItem = line.trim().startsWith('-');
                if (isListItem) {
                    x += listItemIndent;
                    line = line.substring(line.indexOf('-') + 1).trim();
                    doc.setFont("helvetica", "normal");
                    doc.setFontSize(fontSize);
                    doc.text('•', startX, y);
                }

                const parts = line.split(/(\*\*.*?\*\*)/);

                parts.forEach(part => {
                    if (part.startsWith('**') && part.endsWith('**')) {
                        doc.setFont("helvetica", "bold");
                        part = part.slice(2, -2);
                    } else {
                        doc.setFont("helvetica", "normal");
                    }

                    doc.setFontSize(fontSize);
                    const words = part.split(' ');
                    let currentLine = '';

                    words.forEach(word => {
                        const testLine = currentLine + (currentLine ? ' ' : '') + word;
                        const testWidth = doc.getTextWidth(testLine);

                        if (testWidth > maxWidth - x + margin) {
                            if (y > pageHeight - 20) {
                                doc.addPage();
                                y = 20;
                            }
                            doc.text(currentLine, x, y);
                            y += lineHeight;
                            currentLine = word;
                            x = isListItem ? startX + listItemIndent : startX;
                        } else {
                            currentLine = testLine;
                        }
                    });

                    if (currentLine) {
                        if (y > pageHeight - 20) {
                            doc.addPage();
                            y = 20;
                        }
                        doc.text(currentLine, x, y);
                        x += doc.getTextWidth(currentLine) + 1;
                    }
                });

                y += lineHeight;
                if (y > pageHeight - 20) {
                    doc.addPage();
                    y = 20;
                }
            });
        };

        // Add header with site information
        doc.setFontSize(14);
        doc.setFont("helvetica", "bold");
        doc.text(window.env.FRONTEND_FLOW.SITE_NAME || "Custom Nerd", margin, y);
        y += 10;
        
        // Add current date and time
        const now = new Date();
        const dateStr = now.toLocaleDateString();
        const timeStr = now.toLocaleTimeString();
        doc.setFontSize(10);
        doc.setFont("helvetica", "normal");
        doc.text(`Generated on: ${dateStr} at ${timeStr}`, margin, y);
        y += 15;

        // Add the question as a title
        doc.setFontSize(16);
        doc.setFont("helvetica", "bold");
        doc.text("Question:", margin, y);
        y += 10;
        doc.setFontSize(12);
        doc.setFont("helvetica", "normal");
        const titleLines = doc.splitTextToSize(question, maxWidth);
        titleLines.forEach(line => {
            doc.text(line, margin, y);
            y += 8;
        });
        y += 10;

        // Add separator line
        doc.setDrawColor(200, 200, 200);
        doc.line(margin, y, margin + maxWidth, y);
        y += 15;

        // Add the main content
        doc.setFontSize(12);
        doc.setFont("helvetica", "bold");
        doc.text("Answer:", margin, y);
        y += 10;
        doc.setFont("helvetica", "normal");
        addFormattedText(rawOutput, margin);



        // Generate filename with date and time
        const timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const filename = `${window.env.FRONTEND_FLOW.SITE_NAME || 'CustomNerd'}_${timestamp}.pdf`;

        // Save the PDF
        doc.save(filename);
        
    } catch (error) {
        console.error('Error generating PDF:', error);
        alert('Error generating PDF. Please try again.');
    }
};

async function runGeneration(userQuery, uploadArticles, insertPMIDs, searchPubmed, pmids, pdfFiles) {
    const answerElement = document.getElementById('output');
    answerElement.innerText = 'Connecting...\n';

    const cleanedPmids = pmids.map(pmid => pmid.trim()).filter(pmid => pmid !== '');
    const formData = new FormData();
    formData.append('user_query', userQuery);
    formData.append('search_pubmed', searchPubmed);
    formData.append('search_pmid', insertPMIDs);
    formData.append('search_pdf', uploadArticles);
    formData.append('pmids', JSON.stringify(cleanedPmids));
    pdfFiles.forEach((file) => formData.append('files', file));
    return new Promise(async (resolve, reject) => {
        try {
            const response = await fetch(`${baseURL}/process_detailed_combined_query`, {
                method: 'POST',
                body: formData,
                mode: 'cors'
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            const sessionId = data.session_id;

            answerElement.innerText += `Got session_id: ${sessionId}\nAnalyzing the user question...\n`;
            const eventSource = new EventSource(`${baseURL}/sse?session_id=${sessionId}`);
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.update) {
                    answerElement.innerText += `${data.update}\n`;
                    if (data.update.end_output) {
                        localStorage.setItem('generatedAnswer', JSON.stringify(data.update)); // Store answer
                        eventSource.close();
                        resolve();
                    }
                }
            };

            eventSource.onerror = (error) => {
                console.error('EventSource failed:', error);
                answerElement.innerText += 'Error: EventSource failed\n';
                eventSource.close();
                reject(error);
            };

        } catch (error) {
            console.error('Error:', error);
            answerElement.innerText += `Error: ${error.message}\n`;
            reject(error);
        }
    });
}

/**
 * Retrieves an answer, either from stored generation results or from the database.
 *
 * @param {string} question - The question to retrieve an answer for.
 * @return {Promise<string>} The answer.
 */
const getAnswer = async (question) => {
    // **Check if an answer was already generated and stored**
    const storedAnswer = localStorage.getItem('generatedAnswer');
    if (storedAnswer) {
        const parsedAnswer = JSON.parse(storedAnswer);
        let output = parsedAnswer.end_output;
        
        // Split the output at "References:" to separate main content from references
        const referenceMarkers = [
            "References:", 
            "References", 
            "Reference:", 
            "### References", 
            "### References:", 
            "#### References", 
            "#### References:", 
            "**References:**", 
            "**References**:", 
            "**References**", 
            "Reference"
        ];
        
        let mainContent = output;
        let referencesContent = '';
        
        // Find the first matching reference marker and split there
        for (const marker of referenceMarkers) {
            if (output.includes(marker)) {
                const splitIndex = output.indexOf(marker);
                mainContent = output.substring(0, splitIndex).trim();
                referencesContent = output.substring(splitIndex).trim();
                break;
            }
        }
        
        // Check if referencesContent actually contains meaningful references
        let hasActualReferences = false;
        if (referencesContent) {
            // Extract references to see if there are any actual numbered references
            const extractedRefs = extractReferences(referencesContent);
            hasActualReferences = extractedRefs && extractedRefs.length > 0;
            
            // If no actual references found, check if we just have headers/text without numbers
            if (!hasActualReferences) {
                // Check if referencesContent has any substantial content beyond just headers
                const contentWithoutHeaders = referencesContent
                    .replace(/^(References?:?|### References?:?|#### References?:?|\*\*References?\*\*:?)\s*/i, '')
                    .trim();
                
                // If there's meaningful content even without numbered references, keep it
                if (contentWithoutHeaders && contentWithoutHeaders.length > 10) {
                    hasActualReferences = true;
                }
            }
        }
        
        // If no meaningful references found, set referencesContent to indicate no references
        if (!hasActualReferences) {
            referencesContent = "No references to be shown.";
        }
        
        // Extract disclaimer from references content and add it back to main content
        let disclaimer = '';
        if (referencesContent) {
            // Look for disclaimer patterns
            const disclaimerPatterns = [
                /\*\*Disclaimer:\*\*.*$/m,
                /Disclaimer:.*$/m,
                /\*\*Disclaimer\*\*.*$/m,
                /Note:.*$/m
            ];
            
            for (const pattern of disclaimerPatterns) {
                const disclaimerMatch = referencesContent.match(pattern);
                if (disclaimerMatch) {
                    disclaimer = disclaimerMatch[0];
                    // Remove disclaimer from references content
                    referencesContent = referencesContent.replace(pattern, '').trim();
                    break;
                }
            }
        }
        
        // Apply formatting to main content
        mainContent = mainContent.replace(/(^|\n)(\d+)\.\s/g, '\n\n$2. ');
        
        // Add disclaimer back to main content if found
        if (disclaimer) {
            mainContent += '\n\n' + disclaimer;
        }
        
        // Store the raw output for PDF generation (full content)
        localStorage.setItem('rawOutput', output);
        
        // Store the references content separately
        localStorage.setItem('referencesContent', referencesContent);
        
        // Store the citations and reference data
        const citations_obj = parsedAnswer.citations_obj;
        
        // Since the structure only has end_output and citations_obj, we need to handle this properly
        localStorage.setItem('referenceObject', JSON.stringify(citations_obj));
        localStorage.setItem('citations', JSON.stringify(citations_obj));
        localStorage.setItem('allArticles', JSON.stringify(citations_obj));
        
        return mainContent;
    }

    return 'No stored answer found';
};

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
 * Triggers the smooth color change animation for the submit button
 */
function triggerSubmitAnimation() {
    const submitButton = document.getElementById('submit');
    
    // Add smooth color change animation
    submitButton.classList.add('submitting');
    
    // Remove animation class after animation completes
    setTimeout(() => {
        submitButton.classList.remove('submitting');
        submitButton.style.backgroundColor = "#ccc";  // Grey out button
        submitButton.style.cursor = "not-allowed";
    }, 600);
}

/**
 * Handles the click event of the submit button.
 * 
 * @returns {Promise<void>} A Promise that resolves when the function completes.
 */
document.getElementById('submit').addEventListener('click', async () => {
    const submitButton = document.getElementById('submit');
    
    // Trigger smooth color change animation
    triggerSubmitAnimation();

    const question = document.getElementById('question').value.trim();

    const answerElement = document.getElementById('output');
    const referencesElement = document.getElementById('references');
    const resultsElement = document.getElementById('results');
    const hintElement = document.querySelector('.hint');
    const generatePdfButton = document.getElementById('generate-pdf-button');
    const exampleQuestions = document.getElementById('example-questions');
    
    // Hide example questions and show "Did you know" section
    // exampleQuestions.classList.add('hidden');
    // let currentFactIndex = Math.floor(Math.random() * facts.length);
    
    // Set initial content
    // exampleQuestions.innerHTML = `
    //     <h3>Did You Know?</h3>
    //     <div style="text-align: center">
    //         <div class="fact-display">${facts[currentFactIndex]}</div>
    //         <div style="padding: 20px"></div>
    //     </div>
    // `;
    
    // Update fact every second
    // setInterval(() => {
    //     currentFactIndex = (currentFactIndex + 1) % facts.length;
    //     const factElement = exampleQuestions.querySelector('.fact-display');
    //     if (factElement) {
    //         factElement.textContent = facts[currentFactIndex];
    //     }
    // }, 2000);

    // Reset UI
    resultsElement.style.display = 'none';
    generatePdfButton.classList.add("hidden");

    if (!question) {
        answerElement.innerHTML = '<textarea readonly placeholder="Please enter a question."></textarea>';
        return;
    }

    answerElement.innerHTML = '';
    referencesElement.innerHTML = '';

    // Remove any existing similar suggestions
    const similarCard = document.getElementById('similar-suggestions');
    if (similarCard) {
        similarCard.classList.add('hidden');
        similarCard.innerHTML = '';
        try { similarCard.style.display = 'none'; } catch (e) {}
    }

    // Hide recent questions row on submit
    const recent = document.getElementById('recent-questions');
    if (recent) {
        recent.classList.add('hidden');
    }

    // If chat history is enabled, try similar-question suggestions first
    const chatHistoryEnabled = (window.env && window.env.USER_FLOW && window.env.USER_FLOW.chat_history && window.env.USER_FLOW.chat_history.visible) || false;
    if (chatHistoryEnabled) {
        const suggestions = await fetchSimilarQuestions(question, 0.8, 3);
        if (suggestions.length > 0) {
            renderSimilarSuggestions(suggestions, question);
            return; // Stop here; only proceed if user chooses generate
        }
    }

    // **Fallback: Show Search Strategy Selection (PMID, PDF, PubMed)**
    displaySearchStrategy(question);
});

async function fetchRecentQuestions(limit = 3, first = true) {
    try {
        const res = await fetch(`${baseURL}/history_recent?limit=${limit}&first=${first ? 'true' : 'false'}`);
        if (!res.ok) return [];
        const data = await res.json();
        return Array.isArray(data.items) ? data.items : [];
    } catch (e) {
        console.error('Failed to fetch recent history', e);
        return [];
    }
}

async function renderRecentQuestions() {
    const container = document.getElementById('recent-questions');
    if (!container) return;
    const items = await fetchRecentQuestions(3, true);
    if (!items.length) {
        container.classList.add('hidden');
        return;
    }
    container.classList.remove('hidden');
    container.innerHTML = '';
    items.forEach((item, idx) => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'recent-question-chip';
        chip.textContent = item.input_text || `Previous Question ${idx+1}`;
        chip.title = 'Click to view the saved answer';
        chip.addEventListener('click', () => {
            if (item && item.result) {
                try {
                    localStorage.setItem('generatedAnswer', JSON.stringify(item.result));
                    // Directly display the stored answer without re-generating
                    displayStoredAnswer(item.input_text || '');
                } catch (e) { console.error('Error loading historical answer', e); }
            }
        });
        container.appendChild(chip);
    });
}

async function displayStoredAnswer(questionText) {
    try {
        // Ensure results container is visible
        const resultsElement = document.getElementById('results');
        const answerElement = document.getElementById('output');
        const referencesElement = document.getElementById('references');
        const generatePdfButton = document.getElementById('generate-pdf-button');

        // Remove any hidden state enforced via CSS and show results
        resultsElement.classList.remove('hidden');
        resultsElement.style.display = 'flex';

        // Leverage getAnswer to parse and prepare localStorage artifacts from stored answer
        const answer = await getAnswer(questionText || '');

        if (answer) {
            const formattedAnswer = formatText(answer);
            const formattedReferences = formatReferences();
            function decodeHTML(html) {
                const txt = document.createElement('textarea');
                txt.innerHTML = html;
                return txt.value;
            }
            answerElement.innerHTML = decodeHTML(formattedAnswer);

            if (window.referenceSection && window.referenceSection.visible) {
                referencesElement.classList.remove('hidden');
                referencesElement.style.display = 'block';
                referencesElement.innerHTML = decodeHTML(formattedReferences);
            } else {
                referencesElement.style.display = 'none';
                referencesElement.innerHTML = '';
            }

            generatePdfButton.classList.remove('hidden');
        }
    } catch (e) {
        console.error('Error displaying stored answer', e);
    }
}

async function fetchSimilarQuestions(query, threshold = 0.7, limit = 3) {
    try {
        const res = await fetch(`${baseURL}/similar_questions?` + new URLSearchParams({ query, threshold, limit }).toString());
        if (!res.ok) return [];
        const data = await res.json();
        return Array.isArray(data.items) ? data.items : [];
    } catch (e) {
        console.error('Failed to fetch similar questions', e);
        return [];
    }
}

function renderSimilarSuggestions(items, originalQuestion) {
    const card = document.getElementById('similar-suggestions');
    if (!card) return;

    // Build strict block layout with inline styles to override any conflicting CSS
    const btnBaseStyle = 'display:block !important;width:600px;max-width:90%;margin:8px auto;text-align:center;white-space:normal;word-break:break-word;overflow-wrap:anywhere;border-radius:999px;padding:12px 18px;font-size:14px;cursor:pointer;';
    const chipStyle = `${btnBaseStyle}background:linear-gradient(180deg,#f8f9fa,#eef2f7);border:1px solid #dfe3e8;color:#333;`;
    const genStyle = `${btnBaseStyle}background:linear-gradient(135deg,#007bff 0%,#0056b3 100%);border:none;color:#fff;text-align:center;`;

    const chips = items.slice(0, 3).map((it, idx) => {
        const label = (it.input_text || `Similar Question ${idx+1}`).replace(/\n/g, ' ').trim();
        return `<button type="button" data-idx="${idx}" title="Show saved answer" style="${chipStyle}">${label}</button>`;
    }).join('');

    const generateBtn = `<button type="button" id="proceed-generate" style="${genStyle}">Generate answer to my question</button>`;

    // Ensure container is block and stacked
    card.style.cssText = 'width:80%;max-width:800px;margin:16px auto 0 auto;display:block !important;';
    card.innerHTML = `${chips}${generateBtn}`;
    card.classList.remove('hidden');

    // Wire chips (each acts as show)
    const chipButtons = card.querySelectorAll('button[data-idx]');
    chipButtons.forEach((btn) => {
        const i = parseInt(btn.getAttribute('data-idx'));
        btn.addEventListener('click', () => {
            const chosen = items[i];
            if (chosen && chosen.result) {
                try {
                    localStorage.setItem('generatedAnswer', JSON.stringify(chosen.result));
                    card.classList.add('hidden');
                    card.innerHTML = '';
                    displayStoredAnswer(chosen.input_text || '');
                } catch (e) { console.error('Error displaying chosen similar answer', e); }
            }
        });
    });

    // Proceed to generate flow
    const proceed = document.getElementById('proceed-generate');
    if (proceed) proceed.addEventListener('click', () => {
        card.classList.add('hidden');
        card.innerHTML = '';
        displaySearchStrategy(originalQuestion);
    });
}

/**
 * Show search strategy selection (PMID, PDF, PubMed)
 */
function displaySearchStrategy(question) {
    // Remove existing search strategy container if any
    const existingContainer = document.getElementById('search-strategy-container');
    if (existingContainer) existingContainer.remove();

    // Create search strategy container directly
    const searchStrategyContainer = document.createElement('div');
    searchStrategyContainer.id = 'search-strategy-container';
    searchStrategyContainer.className = 'search-strategy-container';

    // Use the generateSearchStrategyHTML function from user_flow.js
    searchStrategyContainer.innerHTML = window.generateSearchStrategyHTML(question);

    document.getElementById('container').appendChild(searchStrategyContainer);

    // Set up event listeners using the function from user_flow.js
    window.setupSearchStrategyEventListeners(question);
}


/**
 * Process the query after selecting the search strategy
 */
async function handleProcessQuery(question) {
    // Hide search strategy selection
    document.getElementById('search-strategy-container').style.display = 'none';

    // Show results section
    const resultsElement = document.getElementById('results');
    resultsElement.classList.remove('hidden');
    resultsElement.style.display = 'flex';

    const answerElement = document.getElementById('output');
    const referencesElement = document.getElementById('references');
    const hintElement = document.querySelector('.hint');

    // Show loading message
    answerElement.innerHTML = `<textarea readonly placeholder="Answer will load here, please wait. This may take a minute..."></textarea>`;
    if (window.referenceSection.visible) {
        referencesElement.classList.remove('hidden');
        referencesElement.style.display = 'block';
        referencesElement.innerHTML = `<textarea readonly placeholder="References will appear here..."></textarea>`;
    } else {
        referencesElement.classList.add('hidden');
        referencesElement.style.display = 'none';
        referencesElement.innerHTML = '';
    }
    try {
        // Check if the question is valid
        const checkValid = await check_valid(question);
        if (checkValid["response"] !== "good") {
            answerElement.innerText = checkValid["response"];
            return;
        }

        // Get selected search strategies using the function from user_flow.js
        const selectedStrategies = window.getSelectedSearchStrategies();
        
        // Extract values from selected strategies
        const uploadArticles = selectedStrategies['upload-articles']?.selected || false;
        const insertPMIDs = selectedStrategies['insert-pmids']?.selected || false;
        const searchPubmed = selectedStrategies['search-pubmed']?.selected || false;
        const pmids = insertPMIDs ? selectedStrategies['insert-pmids'].value.split(';').map(pmid => pmid.trim()) : [];
        const pdfFiles = uploadArticles ? selectedStrategies['upload-articles'].files || [] : [];

        // Run the generation process
        await runGeneration(question, uploadArticles, insertPMIDs, searchPubmed, pmids, pdfFiles);

        // Fetch the answer
        const answer = await getAnswer(question);

        if (answer) {

            // **Update the UI with the answer**
            resultsElement.classList.remove('hidden');
            resultsElement.style.display = 'flex';
            const formattedAnswer = formatText(answer);
            const formattedReferences = formatReferences();
            function decodeHTML(html) {
                const txt = document.createElement("textarea");
                txt.innerHTML = html;
                return txt.value;
            }
            answerElement.innerHTML = decodeHTML(formattedAnswer);
            
            // Show/hide references based on referenceSection.visible setting
            if (window.referenceSection.visible) {
                referencesElement.classList.remove('hidden');
                referencesElement.style.display = 'block';
                referencesElement.innerHTML = decodeHTML(formattedReferences);
            } else {
                referencesElement.classList.add('hidden');
                referencesElement.style.display = 'none';
                referencesElement.innerHTML = '';
            }
            
            // Ensure PDF button appears
            const generatePdfButton = document.getElementById('generate-pdf-button');
            generatePdfButton.classList.remove("hidden");

        } else {
            answerElement.innerHTML = `<textarea readonly>Sorry, we couldn't retrieve an answer at this time.</textarea>`;
        }

    } catch (error) {
        console.error("Error processing query:", error);
        answerElement.innerHTML = `<textarea readonly>Error generating the answer. Please try again.</textarea>`;
    }
}



document.getElementById('generate-pdf-button').addEventListener('click', async(event) => {
    const button = event.target;
    const originalHTML = button.innerHTML;
    
    try {
        // Trigger download animation
        button.classList.add('downloading');
        
        // Show loading state
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating PDF...';
        button.disabled = true;
        button.style.backgroundColor = '#ccc';
        
        // Generate the PDF
        generatePDF();
        
        // Reset button after a short delay
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.disabled = false;
            button.style.backgroundColor = '';
            button.classList.remove('downloading');
        }, 2000);
        
    } catch (error) {
        console.error('Error in PDF generation:', error);
        button.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error - Try Again';
        button.style.backgroundColor = '#dc3545';
        
        // Reset button after 3 seconds
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.disabled = false;
            button.style.backgroundColor = '';
            button.classList.remove('downloading');
        }, 3000);
    }
});

// Event listener for the enter key on the input field
document.getElementById('question').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        const submitBtn = document.getElementById('submit');
        const hasText = (event.target.value || '').trim().length > 0;
        if (!hasText || submitBtn.disabled) {
            event.preventDefault();
            return;
        }
        event.preventDefault();
        submitBtn.click();
    }
});

// Resize functionality for answer and references sections
let isResizing = false;
let startY = 0;
let startHeight = 0;
let minHeight = 200; // Minimum height for the sections
let maxHeight = 800; // Maximum height for the sections

function initializeResizeHandle() {
    const resizeHandle = document.getElementById('resize-handle');
    const output = document.getElementById('output');
    const references = document.getElementById('references');
    const siteLogo = document.getElementById('site-logo');
    
    if (!resizeHandle || !output || !references) return;
    
    // Set initial height
    const initialHeight = 600;
    output.style.height = `${initialHeight}px`;
    references.style.height = `${initialHeight}px`;
    
    resizeHandle.addEventListener('mousedown', function(e) {
        isResizing = true;
        startY = e.clientY;
        startHeight = parseInt(output.style.height) || initialHeight;
        
        // Reset container height to allow proper expansion
        const container = document.getElementById('container');
        if (container) {
            container.style.minHeight = 'calc(100vh - 40px)';
        }
        
        document.body.style.cursor = 'ns-resize';
        document.body.style.userSelect = 'none';
        
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', function(e) {
        if (!isResizing) return;
        
        const deltaY = e.clientY - startY; // Positive because dragging down increases height
        let newHeight = startHeight + deltaY;
        
        // Constrain height within limits
        newHeight = Math.max(minHeight, Math.min(maxHeight, newHeight));
        
        // Update both sections
        output.style.height = `${newHeight}px`;
        references.style.height = `${newHeight}px`;
        
        // Ensure the page expands to accommodate the larger content
        const container = document.getElementById('container');
        if (container) {
            // Calculate the new minimum height needed
            const currentHeight = Math.max(newHeight, 600); // Use the new height or minimum
            const additionalHeight = currentHeight - 600; // Extra height beyond default
            container.style.minHeight = `calc(100vh + ${additionalHeight}px)`;
        }
        
        // Handle logo visibility based on height - subtle big tech style
        if (siteLogo) {
            const logoRect = siteLogo.getBoundingClientRect();
            const resultsRect = document.getElementById('results').getBoundingClientRect();
            
            // Subtle opacity changes for smooth blending
            if (resultsRect.top - logoRect.bottom < 50) {
                siteLogo.style.opacity = '0.2';
                siteLogo.style.transform = 'scale(0.95)';
            } else if (resultsRect.top - logoRect.bottom < 100) {
                siteLogo.style.opacity = '0.4';
                siteLogo.style.transform = 'scale(0.98)';
            } else {
                siteLogo.style.opacity = '0.85'; // Back to default subtle opacity
                siteLogo.style.transform = 'scale(1)';
            }
        }
    });
    
    document.addEventListener('mouseup', function() {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
    
    // Prevent text selection while dragging
    resizeHandle.addEventListener('selectstart', function(e) {
        e.preventDefault();
    });
}

/**
 * Handles smooth page transitions for navigation links
 */
function handleNavigationTransition(event) {
    const link = event.currentTarget;
    const href = link.getAttribute('href');
    
    // Only handle internal links
    if (href && (href.endsWith('.html') || href === 'index.html' || href === '/')) {
        event.preventDefault();
        
        // Add loading animation to the clicked link
        link.classList.add('nav-loading');
        
        // Add fade out effect to current page
        document.body.classList.add('page-exit');
        
        // Navigate after fade out completes
        setTimeout(() => {
            window.location.href = href;
        }, 300);
    }
}

/**
 * Initialize page transition effects
 */
function initializePageTransitions() {
    // Add transition class to body on page load
    document.body.classList.add('page-transition');
    
    // Remove transition class after page loads
    setTimeout(() => {
        document.body.classList.add('loaded');
    }, 100);
    
    // Add click handlers to navigation links
    const navLinks = document.querySelectorAll('.toolbar a');
    navLinks.forEach(link => {
        link.addEventListener('click', handleNavigationTransition);
    });
}

/**
 * Check for missing modules and display warning banner
 */
async function checkMissingModules() {
    try {
        const response = await fetch(`${baseURL}/check_missing_modules`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            mode: 'cors'
        });

        if (!response.ok) {
            // If endpoint fails, hide warning (backend might not be running)
            hideMissingModulesWarning();
            return;
        }

        const result = await response.json();
        const warningEl = document.getElementById('missing-modules-warning');
        const detailsEl = document.getElementById('warning-details');
        const closeBtn = document.getElementById('close-warning');

        if (!warningEl || !detailsEl || !closeBtn) {
            return; // Elements not found
        }

        // Get all warnings (modules + API keys)
        const allWarnings = result.warnings || {};
        
        // Check if user has dismissed warnings
        const dismissedWarnings = JSON.parse(localStorage.getItem('dismissedWarnings') || '[]');
        const currentWarningKeys = Object.keys(allWarnings);
        
        // Clear dismissed warnings that are no longer present (they've been fixed)
        const stillDismissed = dismissedWarnings.filter(key => currentWarningKeys.includes(key));
        if (stillDismissed.length !== dismissedWarnings.length) {
            localStorage.setItem('dismissedWarnings', JSON.stringify(stillDismissed));
        }
        
        // Filter out dismissed warnings
        const activeWarnings = {};
        for (const [key, value] of Object.entries(allWarnings)) {
            if (!stillDismissed.includes(key)) {
                activeWarnings[key] = value;
            }
        }

        if (Object.keys(activeWarnings).length === 0) {
            hideMissingModulesWarning();
            return;
        }

        // Build warning message in clean format
        let warningHTML = '';
        const warningEntries = Object.entries(activeWarnings);
        for (let i = 0; i < warningEntries.length; i++) {
            const [warningKey, warningInfo] = warningEntries[i];
            const description = warningInfo.description || warningKey;
            const solution = warningInfo.solution || '';
            
            if (warningInfo.type === 'missing_module') {
                // Extract module name from solution (pip install <module>)
                const moduleMatch = solution.match(/pip install (.+)/);
                const moduleName = moduleMatch ? moduleMatch[1] : warningKey.replace('module_', '');
                warningHTML += `${description}: Missing module <code>${moduleName}</code>. Install with: <code>${solution}</code>`;
            } else if (warningInfo.type === 'missing_api_key') {
                warningHTML += `${description}: ${warningInfo.message}. ${solution}`;
            } else {
                warningHTML += `${description}: ${warningInfo.message || ''}`;
            }
            
            if (i < warningEntries.length - 1) {
                warningHTML += '<br>';
            }
        }

        detailsEl.innerHTML = warningHTML;
        warningEl.classList.remove('hidden');
        document.body.classList.add('warning-visible');

        // Add close button handler
        closeBtn.onclick = function() {
            // Store dismissed warnings in localStorage
            const allWarningKeys = Object.keys(result.warnings || {});
            localStorage.setItem('dismissedWarnings', JSON.stringify(allWarningKeys));
            hideMissingModulesWarning();
        };

    } catch (error) {
        console.error('Error checking for missing modules:', error);
        // Hide warning on error (backend might not be available)
        hideMissingModulesWarning();
    }
}

/**
 * Hide the missing modules warning banner
 */
function hideMissingModulesWarning() {
    const warningEl = document.getElementById('missing-modules-warning');
    if (warningEl) {
        warningEl.classList.add('hidden');
        document.body.classList.remove('warning-visible');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const questionInput = document.getElementById('question');
    const submitButton = document.getElementById('submit');
    const exampleQuestions = document.querySelectorAll('.example-question');
    
    // Initialize resize handle
    initializeResizeHandle();
    
    // Update glass element colors based on background
    updateGlassElementColors();
    
    // Initialize page transitions
    initializePageTransitions();

    // Initialize submit button disabled state and keep it in sync with input
    const updateSubmitState = () => {
        const hasText = (questionInput.value || '').trim().length > 0;
        submitButton.disabled = !hasText;
        submitButton.style.opacity = hasText ? '1' : '0.6';
        submitButton.style.cursor = hasText ? 'pointer' : 'not-allowed';
        // Use custom tooltip because native title doesn't show on disabled buttons
        submitButton.setAttribute('aria-disabled', (!hasText).toString());
        if (hasText) hideTooltip();
    };
    updateSubmitState();
    questionInput.addEventListener('input', updateSubmitState);

    // Lightweight custom tooltip for disabled submit hover (works even when disabled)
    let tooltipEl = null;
    function ensureTooltip() {
        if (tooltipEl) return tooltipEl;
        tooltipEl = document.createElement('div');
        tooltipEl.id = 'submit-tooltip';
        tooltipEl.style.position = 'fixed';
        tooltipEl.style.background = 'rgba(0,0,0,0.85)';
        tooltipEl.style.color = '#fff';
        tooltipEl.style.padding = '6px 10px';
        tooltipEl.style.borderRadius = '6px';
        tooltipEl.style.fontSize = '12px';
        tooltipEl.style.pointerEvents = 'none';
        tooltipEl.style.zIndex = '9999';
        tooltipEl.style.whiteSpace = 'nowrap';
        tooltipEl.style.display = 'none';
        document.body.appendChild(tooltipEl);
        return tooltipEl;
    }
    function showTooltip(message) {
        const el = ensureTooltip();
        el.textContent = message;
        const rect = submitButton.getBoundingClientRect();
        const top = rect.top - 8; // above button
        const left = rect.left + rect.width / 2;
        el.style.display = 'block';
        el.style.transform = 'translate(-50%, -100%)';
        el.style.top = `${top}px`;
        el.style.left = `${left}px`;
    }
    function hideTooltip() {
        if (tooltipEl) tooltipEl.style.display = 'none';
    }
    const submitWrapper = submitButton.parentElement || submitButton;
    submitWrapper.addEventListener('mouseenter', () => {
        const hasText = (questionInput.value || '').trim().length > 0;
        if (!hasText) showTooltip('Please type to search');
    });
    submitWrapper.addEventListener('mouseleave', hideTooltip);
    submitWrapper.addEventListener('focusin', () => {
        const hasText = (questionInput.value || '').trim().length > 0;
        if (!hasText) showTooltip('Please type to search');
    });
    submitWrapper.addEventListener('focusout', hideTooltip);

    exampleQuestions.forEach(question => {
        question.addEventListener('click', function() {
            questionInput.value = this.textContent;
            updateSubmitState();
            submitButton.click();
        });
    });

    // Load recent questions if chat history is enabled
    try {
        const chatHistoryEnabled = (window.env && window.env.USER_FLOW && window.env.USER_FLOW.chat_history && window.env.USER_FLOW.chat_history.visible) || false;
        if (chatHistoryEnabled) {
            renderRecentQuestions();
        }
    } catch (e) { console.warn('Could not determine chat history setting', e); }

    // Check for missing modules and display warning
    checkMissingModules();
    
    // Check for missing modules periodically (every 30 seconds)
    setInterval(checkMissingModules, 30000);
});


/* TODO: Add facts to the website
// const facts = [
//     "Did you know that the average person should consume 2,000 calories per day?",
//     "Did you know that the average person should consume 2,000 calories per day?",
//     "Did you know that the average person should consume 2,000 calories per day?",
//     "Did you know that the average person should consume 2,000 calories per day?",
    
// ]
*/