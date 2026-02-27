# Custom-Nerd/Nerd-Engine: Architecture Summary & Key Insights

## Executive Summary

Custom-Nerd/Nerd-Engine is a modular, configurable academic research assistant that demonstrates several advanced architectural patterns:

### 🏗️ **Architecture Highlights**

1. **Microservice-Inspired Modular Design**
   - Clear separation between frontend, backend, and configuration layers
   - Pluggable components for different academic databases
   - AI-assisted code generation for extensibility

2. **Real-Time Processing Pipeline**
   - 9-stage processing workflow with live progress updates
   - Server-Sent Events (SSE) for non-blocking user experience
   - Concurrent processing for performance optimization

3. **Multi-Level Configuration System**
   - Frontend appearance and behavior configuration
   - Backend LLM prompt customization
   - Environment and API key management
   - Complete state save/restore functionality

4. **Local LLM Support via Ollama**
   - Run the full pipeline without any cloud API key using locally hosted models
   - Automated install → serve → pull lifecycle managed entirely from the config UI
   - Per-platform multi-method installation fallback ensures maximum compatibility
   - Interactive Model Guide with Basic/Advanced toggle and live installed-model detection

### 🔄 **Processing Workflow Overview**

```
User Question → Validation → Query Generation → Query Cleaning → Article Collection → 
Relevance Classification → Content Processing → Response Synthesis → 
Citation Extraction → Formatted Output
```

**Key Stages:**
- **Question Validation**: LLM-powered filtering for domain appropriateness
- **Query Generation**: Creates 5 specialized academic search queries
- **Query Cleaning**: Advanced preprocessing and refinement of search queries (optional)
- **Multi-Database Collection**: Parallel searches across PubMed, Springer, Wiley, etc.
- **AI-Powered Relevance Filtering**: Eliminates irrelevant content
- **Evidence Synthesis**: Generates comprehensive, cited responses

### 📊 **Data Flow Architecture**

1. **Frontend Layer**: Dynamic UI with configurable search strategies
2. **API Layer**: FastAPI server with 15+ endpoints
3. **Processing Layer**: Concurrent article processing and LLM integration
4. **Data Sources**: 5+ academic databases + PDF upload capability
5. **Configuration Layer**: 4-tier configuration management system

### 🔧 **Key Technical Features**

#### **Modularity & Extensibility**
- Configurable search implementations (`user_search_apis.py`)
- AI-assisted code generation for new database integrations
- Plugin-like architecture for different research domains
- **Query Cleaning System**: Advanced query preprocessing and refinement (`clean_query.py`)
- **Similarity Search**: Multi-algorithm question matching using TF-IDF, Jaccard, and fuzzy matching
- **Chat History Management**: Automatic conversation storage and retrieval with configurable visibility

#### **Performance Optimization**
- Multi-threaded article collection and processing
- Token-efficient LLM interactions
- Connection pooling and caching strategies
- Graceful error handling with exponential backoff

#### **Configuration Management**
- Complete system state persistence
- Domain-specific configurations (DietNerd, NewsNerd, Space Nerd, SciNer)
- Hot-swappable UI themes and search strategies
- AI-powered prompt optimization

##### Saved State Templates

Prebuilt templates live in `customnerd-backend/saved_states/`:
- `DietNerd/`: PubMed nutrition research (prompts, UI, search, env)
- `NewsNerd/`: News aggregation via GNews, NewsAPI, Guardian
- `Space Nerd/`: Space research via arXiv, NASA Images, optional NASA ADS; includes `clean_query.py`
- `SciNer/`: QASPER-based scientific QA setup
- `CloudNerd/`: Stack Overflow-based cloud technology research

Templates include `openai_prompts.py`, `user_env.js`, `user_search_apis.py`, `user_list_search.py`, `variables.env`, and `historical_answer.json` (plus domain extras). Load via Configuration UI (Load/Save State) or copy files into place and restart.

#### **Real-Time User Experience**
- Live progress tracking via Server-Sent Events
- Non-blocking query processing
- Dynamic UI updates based on configuration
- Instant feedback on all operations

### 🎯 **Design Patterns Implemented**

1. **Strategy Pattern**: Configurable search strategies for different use cases
2. **Observer Pattern**: Real-time updates via SSE
3. **Factory Pattern**: Dynamic configuration loading and application
4. **Template Method Pattern**: Consistent processing pipeline with customizable steps
5. **Facade Pattern**: Simplified API interface hiding complex processing

### 🔗 **Integration Architecture**

#### **Academic Database APIs (DietNerd)**
- **PubMed**: Primary source via Bio.Entrez (current DietNerd `user_search_apis.py`)
- **Elsevier**: Full-text retrieval for open access
- **Springer**: Article metadata and content
- **Wiley**: PDF full-text access
- **Oxford Academic**: Supplementary content

#### **News APIs (NewsNerd)**
- **GNews API**: News search and aggregation
- **NewsAPI**: Broad news source coverage
- **The Guardian Open Platform**: First‑party Guardian articles

#### **Space/Astronomy APIs (SpaceNerd)**
- **arXiv API**: Preprints in astrophysics and related categories
- **NASA ADS**: Peer-reviewed astronomy literature (token-based)
- **Query Cleaning**: Advanced query preprocessing for complex astronomy terminology

#### **LLM Integration (OpenAI, Gemini, Claude, Ollama)**
- **OpenAI**: GPT-4-turbo primary; **Gemini**: Gemini-2.5-flash; **Claude**: claude-sonnet-4-5; **Ollama**: any locally hosted model (e.g., `llama3.2`, `phi3:mini`, `llama3.1:8b`, `qwen3:8b`, `codellama:7b`). Provider set via `LLM` in variables.env.
- **Ollama (local)**: Uses OpenAI-compatible REST API at `http://localhost:11434/v1/`. No cloud key needed. Automated install/pull/serve lifecycle managed by `/ollama_setup` SSE endpoint with per-platform multi-method fallback (macOS: curl script → Homebrew → binary; Linux: curl script → arch binary; Windows: PowerShell script → winget).
- **Prompt Engineering**: 10+ specialized prompts for different tasks
- **Token Management**: Dynamic limiting and optimization
- **Error Handling**: Robust retry mechanisms; Ollama errors (`NotFoundError`, `APIConnectionError`) converted to descriptive user-facing messages via `_safe_create()` wrapper

### 📱 **Frontend Architecture**

#### **Component Structure**
```
User Interface (index.html/js) →
Configuration Panel (config.html/js) →
User Flow Manager (user_flow.js) →
Environment Configuration (user_env.js) →
Dynamic UI Application (user_based.js)
```

#### **Configuration Flow**
1. **Static Configuration**: Base environment and API settings
2. **Dynamic Configuration**: User-specific UI and behavior settings
3. **Real-Time Application**: DOM manipulation based on configuration
4. **State Persistence**: Save/restore complete system states

### 🚀 **Deployment & Scalability**

#### **Environment Management**
- Automated setup scripts with dependency management
- Environment-specific configuration (dev/production)
- API key management with secure storage
- Comprehensive error handling and logging

#### **Performance Characteristics**
- **Concurrent Processing**: Multi-threaded article collection
- **Resource Efficiency**: Memory-optimized article processing
- **Scalability**: Modular architecture supports horizontal scaling
- **Reliability**: Comprehensive error handling and recovery

### 💡 **Innovation Highlights**

1. **AI-Assisted Configuration**: Automated code generation for new integrations
2. **Domain Adaptability**: Single codebase serves multiple research domains
3. **Real-Time Academic Research**: Live progress tracking for complex queries
4. **Evidence-Based AI**: LLM responses backed by peer-reviewed sources
5. **Zero-Code Customization**: Complete system customization via web interface
6. **Local LLM with Zero Cloud Dependency**: Full Ollama integration with automated setup — users can run the entire system locally with no external API calls

### 🎯 **Use Case Adaptability**

The architecture supports rapid adaptation to new domains:
- **Diet & Nutrition (DietNerd)**: PubMed-focused medical research with full academic features
- **News & Current Events (NewsNerd)**: Multi-source news aggregation with simplified interface
- **Space & Astronomy (SpaceNerd)**: arXiv/ADS research with advanced query cleaning
- **Medical Research**: Enhanced with medical database integrations
- **Technology Research**: Adapted for IEEE and ACM databases
- **Legal Research**: Configurable for legal databases and case law

This modular design makes Custom-Nerd/Nerd-Engine a powerful platform for building domain-specific research assistants with minimal code changes and maximum configuration flexibility. 