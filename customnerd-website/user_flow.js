/**
 * Search strategy configuration for DietNerd
 * This file contains the functions for handling search strategies
 * that can be used to find articles for answering user queries.
 */

// Get search strategies from user_env.js
const searchStrategies = window.env.USER_FLOW.searchStrategies;
const referenceSection = window.env.USER_FLOW.reference_section;

/**
 * Generates HTML for the search strategy selection UI
 * @param {string} question - The user's question
 * @returns {string} HTML string for the search strategy selection UI
 */
function generateSearchStrategyHTML(question) {
  let html = `
    <h3>Choose an article search strategy:</h3>
    <h4>Choose all that apply:</h4>
  `;
  
  // Add each search strategy
  searchStrategies.forEach(strategy => {
    if (!strategy.visible) return;

    html += `
      <div class="strategy-option">
        <div class="strategy-checkbox">
          <input type="checkbox" id="${strategy.id}" name="search-strategy" ${strategy.defaultChecked ? 'checked' : ''}>
        </div>
        <label for="${strategy.id}" class="strategy-label">${strategy.label}</label>
        ${strategy.tooltip ? `
          <span class="strategy-tooltip" data-tooltip="${strategy.tooltip}">?</span>
        ` : ''}
      </div>
    `;

    // Add additional UI elements based on strategy type
    if (strategy.type === 'file-upload') {
      html += `
        <div id="${strategy.id}-area" style="display: none; margin-bottom: 20px;">
          <p style="font-size: 14px; margin-bottom: 10px; color: var(--text-color, #1a202c); opacity: 0.8;">(Only PDF files allowed)</p>
          <input type="file" id="${strategy.id}-file-input" accept="${strategy.accept}" style="display: none;" ${strategy.multiple ? 'multiple' : ''}>
          <div style="display: flex; justify-content: center; align-items: flex-start; gap: 24px; margin-top: 16px;">
            <div id="${strategy.id}-drop-area" class="file-upload-area" style="width: 280px; height: 180px;">
                <div class="file-upload-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style="color: white;">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <polyline points="10,9 9,9 8,9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <button type="button" onclick="document.getElementById('${strategy.id}-file-input').click()" class="file-upload-button">
                    Choose Files
                </button>
                <p style="margin: 0; color: var(--text-color, #1a202c); font-size: 13px; font-weight: 500; opacity: 0.8;">or drag & drop here</p>
            </div>
            <div id="${strategy.id}-file-list" 
                style="display: flex; flex-wrap: wrap; justify-content: flex-start; align-items: flex-start; 
                gap: 12px; max-width: 400px; max-height: 180px; overflow-y: auto; padding: 8px;
                background: transparent; backdrop-filter: blur(20px); border-radius: 12px; 
                border: 1px solid var(--border-color, rgba(255, 255, 255, 0.2));
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.3);"></div>
          </div>
        </div>
      `;
    } else if (strategy.type === 'text-input') {
      html += `
        <div id="${strategy.id}-input-container" style="display: none; margin-top: 10px; max-width: 450px; margin-left: auto; margin-right: auto;">
          <input type="text" id="${strategy.id}-input" placeholder="${strategy.tooltip}" class="strategy-text-input">
        </div>
      `;
    }
  });

  // Add submit button
  html += `
    <div style="display: flex; justify-content: center; margin-top: 20px;">
      <button id="confirm-submit" class="search-strategy-submit">Submit</button>
    </div>
  `;


  return html;
}

/**
 * Sets up event listeners for the search strategy UI
 * @param {string} question - The user's question
 */
function setupSearchStrategyEventListeners(question) {
  // Event Listeners for dynamic elements
  searchStrategies.forEach(strategy => {
    if (!strategy.visible) return;

    const checkbox = document.getElementById(strategy.id);
    if (!checkbox) return;

    checkbox.addEventListener('change', (e) => {
      if (strategy.type === 'file-upload') {
        document.getElementById(`${strategy.id}-area`).style.display = e.target.checked ? 'block' : 'none';
      } else if (strategy.type === 'text-input') {
        document.getElementById(`${strategy.id}-input-container`).style.display = e.target.checked ? 'block' : 'none';
      }
    });

    // Set initial visibility based on default checked state
    if (strategy.type === 'file-upload' && strategy.defaultChecked) {
      document.getElementById(`${strategy.id}-area`).style.display = 'block';
    } else if (strategy.type === 'text-input' && strategy.defaultChecked) {
      document.getElementById(`${strategy.id}-input-container`).style.display = 'block';
    }
  });

  // Submit button event listener
  document.getElementById('confirm-submit').addEventListener('click', async () => {
    // Trigger submit animation
    const submitButton = document.getElementById('confirm-submit');
    submitButton.classList.add('submitting');
    setTimeout(() => {
      submitButton.classList.remove('submitting');
    }, 600);
    
    handleProcessQuery(question);
  });

  // Set up file upload functionality
  setupFileUploadHandlers();
}

/**
 * Sets up file upload handlers for all file upload strategies
 */
function setupFileUploadHandlers() {
  searchStrategies.forEach(strategy => {
    if (strategy.type !== 'file-upload' || !strategy.visible) return;

    const fileInput = document.getElementById(`${strategy.id}-file-input`);
    const dropArea = document.getElementById(`${strategy.id}-drop-area`);
    const fileList = document.getElementById(`${strategy.id}-file-list`);

    if (!fileInput || !dropArea || !fileList) return;

    fileInput.addEventListener('change', (e) => handleFileSelect(e, strategy, fileList));

    dropArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropArea.style.borderColor = 'var(--accent-text-color, #007bff)';
      dropArea.style.boxShadow = '0 8px 24px rgba(0, 123, 255, 0.2), 0 0 0 1px var(--accent-text-color, #007bff), inset 0 1px 0 rgba(255, 255, 255, 0.4)';
    });

    dropArea.addEventListener('dragleave', (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropArea.style.borderColor = 'var(--accent-border-color, rgba(0, 123, 255, 0.3))';
      dropArea.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(255, 255, 255, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.3)';
    });

    dropArea.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropArea.style.borderColor = 'var(--accent-border-color, rgba(0, 123, 255, 0.3))';
      dropArea.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(255, 255, 255, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.3)';
      handleFileSelect(e, strategy, fileList);
    });
  });
}

/**
 * Handles file selection for file upload strategies
 * @param {Event} e - The event object
 * @param {Object} strategy - The search strategy object
 * @param {HTMLElement} fileList - The file list element
 */
function handleFileSelect(e, strategy, fileList) {
  const files = e.target.files || e.dataTransfer.files;
  for (let file of files) {
    if (file.type === 'application/pdf') {
      const fileElement = document.createElement('div');
      fileElement.className = 'pdf-file';
      fileElement.style.margin = '5px';
      fileElement.style.padding = '8px 12px';
      fileElement.style.display = 'flex';
      fileElement.style.alignItems = 'center';
      fileElement.style.maxWidth = '140px';
      fileElement.style.background = 'transparent';
      fileElement.style.backdropFilter = 'blur(20px)';
      fileElement.style.border = '1px solid var(--border-color, rgba(255, 255, 255, 0.2))';
      fileElement.style.borderRadius = '8px';
      fileElement.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.3)';
      fileElement.style.transition = 'all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
      fileElement.innerHTML = `
        <i class="fas fa-file-pdf" style="color: #dc3545; margin-right: 8px; font-size: 16px;"></i>
        <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-right: 8px; color: var(--text-color, #1a202c); font-size: 13px; font-weight: 500;">${file.name}</span>
        <span class="delete-file" style="margin-left: auto; cursor: pointer; padding: 4px; border-radius: 4px; transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);">
          <i class="fas fa-trash" style="color: #dc3545; font-size: 12px;"></i>
        </span>
      `;
      fileElement.file = file;
      fileList.appendChild(fileElement);

      // Add hover effects
      fileElement.addEventListener('mouseenter', () => {
        fileElement.style.transform = 'translateY(-2px)';
        fileElement.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.4)';
        fileElement.style.borderColor = 'var(--accent-border-color, rgba(0, 123, 255, 0.4))';
      });
      
      fileElement.addEventListener('mouseleave', () => {
        fileElement.style.transform = 'translateY(0)';
        fileElement.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.3)';
        fileElement.style.borderColor = 'var(--border-color, rgba(255, 255, 255, 0.2))';
      });

      fileElement.querySelector('.delete-file').addEventListener('click', () => {
        fileList.removeChild(fileElement);
      });
    }
  }
}

/**
 * Gets the selected search strategies and their values
 * @returns {Object} Object containing the selected search strategies and their values
 */
function getSelectedSearchStrategies() {
  const result = {};
  
  searchStrategies.forEach(strategy => {
    if (!strategy.visible) return;
    
    const checkbox = document.getElementById(strategy.id);
    if (!checkbox) return;
    
    result[strategy.id] = {
      selected: checkbox.checked,
      value: null
    };
    
    if (strategy.type === 'text-input' && checkbox.checked) {
      const input = document.getElementById(`${strategy.id}-input`);
      if (input) {
        result[strategy.id].value = input.value;
      }
    } else if (strategy.type === 'file-upload' && checkbox.checked) {
      const fileList = document.getElementById(`${strategy.id}-file-list`);
      if (fileList) {
        result[strategy.id].files = Array.from(fileList.children).map(el => el.file);
      }
    }
  });
  
  return result;
}

// Export functions and objects
window.searchStrategies = searchStrategies;
window.generateSearchStrategyHTML = generateSearchStrategyHTML;
window.setupSearchStrategyEventListeners = setupSearchStrategyEventListeners;
window.getSelectedSearchStrategies = getSelectedSearchStrategies; 
window.referenceSection = referenceSection;