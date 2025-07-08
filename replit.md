# Cantonese Learning Tool - Han Character & Word Frequency Analysis

## Overview

This is a Streamlit-based web application designed for Cantonese language learners to analyze both Han character and word frequency in documents. The tool supports multiple file formats (PDF, EPUB, TXT) and provides statistical analysis and visualization of character and word usage patterns to help users focus their learning efforts on the most commonly used elements.

## System Architecture

The application follows a modular, single-page web application architecture with the following key characteristics:

- **Frontend**: Streamlit-based web interface providing interactive file upload, analysis controls, and data visualization
- **Backend**: Python-based processing modules for file parsing, character analysis, and user management
- **Database**: MongoDB with automatic JSON fallback for development environments
- **Architecture Pattern**: Modular separation of concerns with dedicated classes for file parsing, character analysis, and user management
- **Authentication**: Simple username-based authentication with user progress tracking
- **Deployment**: Designed for single-instance deployment with cloud database support (suitable for Replit environment)
- **Data Persistence**: Hybrid storage system ensuring functionality in both production (MongoDB) and development (JSON) environments

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

### 6. User Database Module (`user_database.py`)
- **Purpose**: Manages user authentication, preferences, and progress tracking
- **Storage**: JSON-based NoSQL database for simplicity and portability
- **User Management Features**:
  - User account creation and authentication
  - Analysis history tracking (last 50 analyses per user)
  - User preferences persistence (analysis settings)
  - Progress statistics (total analyses, characters/words processed)
  - User session management
- **Data Structure**: Hierarchical JSON with user profiles and analysis records

### 7. File Tracker Module (`file_tracker.py`)
- **Purpose**: Tracks uploaded files and maintains detailed analysis history
- **File Management Features**:
  - File deduplication using content hashing
  - Multiple user access tracking per file
  - Detailed file metadata (size, type, upload date)
  - Analysis history per file with timestamps
  - User access patterns and frequency tracking
- **Storage**: JSON-based file registry with comprehensive metadata

### 8. Learning Tracker Module (`learning_tracker.py`)
- **Purpose**: Tracks individual character and word learning progress
- **Learning Features**:
  - Character exposure frequency across multiple files
  - Word exposure tracking with context
  - Mastery level categorization (beginner, learning, familiar, mastered)
  - Learning session history with progress metrics
  - Personalized learning recommendations
  - Cross-file learning pattern analysis
- **Mastery System**: Dynamic leveling based on exposure frequency and file diversity

## Data Flow

1. **User Authentication**: User signs in or creates account through authentication interface
2. **Preference Loading**: System loads user's saved analysis preferences
3. **File Upload**: User uploads document through Streamlit interface
4. **Format Detection**: System identifies file type via MIME type or extension
5. **Text Extraction**: FileParser extracts plain text from uploaded document
6. **Character & Word Analysis**: Analyzers process text for statistics and pronunciation
7. **Progress Saving**: Analysis results automatically saved to user's history
8. **Visualization**: Results displayed through Plotly charts and Streamlit components
9. **Session Persistence**: Analysis results and user state maintained across interactions

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

## Recent Changes

- July 08, 2025: Successfully migrated from Replit Agent to Replit environment
- July 08, 2025: Configured Streamlit server settings for proper deployment (port 5000, headless mode)
- July 08, 2025: Installed all required dependencies and verified application functionality
- July 08, 2025: Added user authentication and progress tracking system with JSON-based NoSQL database
- July 08, 2025: Implemented user preferences persistence and analysis history tracking
- July 08, 2025: Enhanced UI with progress dashboard and user session management
- July 08, 2025: Refactored analysis page with improved modular design and better error handling
- July 08, 2025: Fixed preference mapping issues and created cleaner UI layout with progress indicators
- July 08, 2025: Added comprehensive file tracking and learning progress system
- July 08, 2025: Implemented mastery-based learning recommendations and detailed exposure tracking
- July 08, 2025: Added file reload capability for previously analyzed documents
- July 08, 2025: Implemented duplicate file detection and comparison features
- July 08, 2025: Added re-analysis functionality for stored files with content preservation
- July 08, 2025: Migrated from JSON-only storage to MongoDB with JSON fallback for development
- July 08, 2025: Added database management interface with migration tools and performance monitoring

## Changelog

Changelog:
- July 08, 2025. Initial setup
- July 08, 2025. Added Chinese word segmentation analysis using Jieba library alongside existing character analysis
- July 08, 2025. Added Jyutping pronunciation support using PyCantonese library for both characters and words
- July 08, 2025. Completed migration to Replit environment with proper security configuration