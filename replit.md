# Cantonese Learning Tool - Han Character & Word Frequency Analysis

## Overview

This is a Streamlit-based web application designed for Cantonese language learners to analyze both Han character and word frequency in documents. The tool supports multiple file formats (PDF, EPUB, TXT) and provides statistical analysis and visualization of character and word usage patterns to help users focus their learning efforts on the most commonly used elements.

## System Architecture

The application follows a modular, single-page web application architecture with the following key characteristics:

- **Frontend**: Streamlit-based web interface providing interactive file upload, analysis controls, and data visualization
- **Backend**: Python-based processing modules for file parsing and character analysis
- **Architecture Pattern**: Modular separation of concerns with dedicated classes for file parsing and character analysis
- **Deployment**: Designed for single-instance deployment (suitable for Replit environment)

## Key Components

### 1. Main Application (`app.py`)
- **Purpose**: Primary Streamlit interface and application orchestration
- **Responsibilities**: 
  - User interface rendering
  - File upload handling
  - Session state management
  - Data visualization using Plotly
- **Key Features**: Wide layout, sidebar controls, interactive charts

### 2. File Parser Module (`file_parsers.py`)
- **Purpose**: Handles extraction of text content from various file formats
- **Supported Formats**: PDF, EPUB, TXT
- **Architecture**: Strategy pattern with format-specific parsing methods
- **Dependencies**: PyPDF2 for PDF processing
- **Error Handling**: Graceful fallback to extension-based detection

### 3. Character Analyzer Module (`character_analyzer.py`)
- **Purpose**: Analyzes text for Han character frequency and statistics
- **Unicode Support**: Comprehensive CJK Unified Ideographs coverage
- **Analysis Features**:
  - Character frequency counting
  - Text statistics (total chars, unique chars, ratios)
  - Text cleaning and normalization
- **Output**: Structured dictionary with analysis results

### 4. Word Analyzer Module (`word_analyzer.py`)
- **Purpose**: Analyzes text for word frequency using Chinese word segmentation
- **Segmentation Engine**: Jieba Chinese word segmentation library
- **Analysis Features**:
  - Word frequency counting with focus on Han character words
  - Word length distribution analysis
  - Word difficulty categorization
  - Statistics on total words, unique words, and Han words
- **Output**: Structured dictionary with word analysis results

### 5. Pronunciation Analyzer Module (`pronunciation_analyzer.py`)
- **Purpose**: Provides Jyutping pronunciation analysis for Chinese characters and words
- **Pronunciation Engine**: PyCantonese library for authentic Jyutping conversion
- **Analysis Features**:
  - Character-to-Jyutping pronunciation mapping
  - Word-to-Jyutping pronunciation mapping
  - Pronunciation availability tracking
  - Tone distribution analysis
- **Output**: Structured dictionary with pronunciation data for characters and words

## Data Flow

1. **File Upload**: User uploads document through Streamlit interface
2. **Format Detection**: System identifies file type via MIME type or extension
3. **Text Extraction**: FileParser extracts plain text from uploaded document
4. **Character Analysis**: CharacterAnalyzer processes text for Han character statistics
5. **Visualization**: Results displayed through Plotly charts and Streamlit components
6. **Session Persistence**: Analysis results stored in Streamlit session state

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework and UI components
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive data visualization (Express and Graph Objects)
- **PyPDF2**: PDF text extraction
- **Jieba**: Chinese word segmentation and natural language processing
- **PyCantonese**: Jyutping pronunciation conversion and Cantonese linguistics

### Python Standard Library
- **collections.Counter**: Character frequency counting
- **re**: Regular expression processing for Unicode character matching
- **io, tempfile, os**: File handling and temporary storage
- **typing**: Type hints for better code documentation

## Deployment Strategy

The application is designed for straightforward deployment in containerized or cloud environments:

- **Target Platform**: Replit (based on file structure and dependencies)
- **Entry Point**: `app.py` as main Streamlit application
- **Requirements**: Standard Python package management (likely requirements.txt)
- **Scaling**: Single-instance design suitable for personal or small-group usage
- **Storage**: Temporary file processing with no persistent data storage

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- July 08, 2025. Initial setup
- July 08, 2025. Added Chinese word segmentation analysis using Jieba library alongside existing character analysis
- July 08, 2025. Added Jyutping pronunciation support using PyCantonese library for both characters and words