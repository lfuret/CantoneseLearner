"""
Refactored analysis page with improved user interface and modular components.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import io
import tempfile
import os

from file_parsers import FileParser
from character_analyzer import CharacterAnalyzer
from word_analyzer import WordAnalyzer
from pronunciation_analyzer import PronunciationAnalyzer
from user_database import UserDatabase


def display_analysis_header(user_data):
    """Display the main header with user info and navigation."""
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title("🈯 Cantonese Learning Tool")
        st.markdown("**Han Character & Word Frequency Analysis**")
    
    with col2:
        st.markdown(f"**Welcome, {user_data['username']}!**")
        
    with col3:
        col3a, col3b = st.columns(2)
        with col3a:
            if st.button("📊 Progress", use_container_width=True):
                st.session_state.show_progress = True
                st.rerun()
        with col3b:
            if st.button("🚪 Sign Out", use_container_width=True):
                st.session_state.current_user = None
                st.rerun()


def display_file_upload_section():
    """Display the file upload section."""
    st.header("📁 Upload Document")
    
    uploaded_file = st.file_uploader(
        "Choose a file to analyze",
        type=['pdf', 'epub', 'txt'],
        help="Supported formats: PDF, EPUB, TXT files"
    )
    
    if uploaded_file:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size:,} bytes")
        with col3:
            st.metric("File Type", uploaded_file.type or "Unknown")
    
    return uploaded_file


def display_analysis_settings(user_prefs):
    """Display analysis settings with user preferences."""
    st.header("⚙️ Analysis Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Frequency Settings")
        
        min_frequency = st.slider(
            "Minimum frequency",
            min_value=1,
            max_value=50,
            value=user_prefs.get('min_frequency', 5),
            help="Only show items that appear at least this many times"
        )
        
        show_all_results = st.checkbox(
            "Show all results",
            value=user_prefs.get('max_chars_display') is None,
            help="Show all items or limit the display"
        )
        
        if not show_all_results:
            max_items_display = st.slider(
                "Maximum items to display",
                min_value=10,
                max_value=200,
                value=user_prefs.get('max_chars_display', 50),
                help="Limit the number of items shown"
            )
        else:
            max_items_display = None
    
    with col2:
        st.subheader("Display Settings")
        
        # Chart type selection
        chart_options = ["Bar Chart", "Pie Chart", "Treemap"]
        chart_mapping = {"bar chart": "Bar Chart", "pie chart": "Pie Chart", "treemap": "Treemap"}
        default_chart = chart_mapping.get(user_prefs.get('show_chart_type', 'bar chart'), "Bar Chart")
        
        chart_type = st.selectbox(
            "Chart type",
            chart_options,
            index=chart_options.index(default_chart),
            help="Choose visualization style"
        )
        
        # Analysis type selection
        analysis_options = ["Characters", "Words", "Both"]
        analysis_mapping = {"characters": "Characters", "words": "Words", "both": "Both"}
        default_analysis = analysis_mapping.get(user_prefs.get('preferred_analysis_type', 'both'), "Both")
        
        analysis_type = st.selectbox(
            "Analysis type",
            analysis_options,
            index=analysis_options.index(default_analysis),
            help="Choose what to analyze"
        )
    
    return {
        'min_frequency': min_frequency,
        'max_items_display': max_items_display,
        'chart_type': chart_type,
        'analysis_type': analysis_type
    }


def process_uploaded_file(uploaded_file, settings, user_data, db):
    """Process the uploaded file and perform analysis."""
    
    # Check if this is a new file
    if st.session_state.get('uploaded_filename') != uploaded_file.name:
        st.session_state.uploaded_filename = uploaded_file.name
        st.session_state.analysis_results = None
        st.session_state.word_analysis_results = None
        st.session_state.pronunciation_data = None
        
        # Create progress container
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Parse file
                status_text.text("📄 Parsing file...")
                progress_bar.progress(20)
                
                parser = FileParser()
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                try:
                    # Extract text
                    text_content = parser.parse_file(tmp_file_path, uploaded_file.type)
                    
                    if not text_content.strip():
                        st.error("❌ No text content found in the uploaded file.")
                        return False
                    
                    # Step 2: Character analysis
                    status_text.text("🔤 Analyzing characters...")
                    progress_bar.progress(40)
                    
                    analyzer = CharacterAnalyzer()
                    analysis_results = analyzer.analyze_text(text_content)
                    st.session_state.analysis_results = analysis_results
                    
                    # Step 3: Word analysis
                    status_text.text("📝 Analyzing words...")
                    progress_bar.progress(60)
                    
                    word_analyzer = WordAnalyzer()
                    word_analysis_results = word_analyzer.analyze_text(text_content)
                    st.session_state.word_analysis_results = word_analysis_results
                    
                    # Step 4: Pronunciation analysis
                    status_text.text("🗣️ Analyzing pronunciations...")
                    progress_bar.progress(80)
                    
                    pronunciation_analyzer = PronunciationAnalyzer()
                    character_pronunciations = pronunciation_analyzer.get_character_pronunciations(
                        analysis_results['character_frequency']
                    )
                    word_pronunciations = pronunciation_analyzer.get_word_pronunciations(
                        word_analysis_results['han_words']
                    )
                    
                    st.session_state.pronunciation_data = {
                        'characters': character_pronunciations,
                        'words': word_pronunciations
                    }
                    
                    # Step 5: Save to database
                    status_text.text("💾 Saving analysis...")
                    progress_bar.progress(100)
                    
                    # Save analysis results
                    analysis_data = {
                        'filename': uploaded_file.name,
                        'file_size': uploaded_file.size,
                        'analysis_type': settings['analysis_type'].lower(),
                        'character_stats': analysis_results,
                        'word_stats': word_analysis_results,
                        'top_characters': dict(analysis_results['character_frequency'].most_common(10)),
                        'top_words': dict(word_analysis_results['han_words'].most_common(10)),
                        'settings_used': {
                            'preferred_analysis_type': settings['analysis_type'].lower(),
                            'min_frequency': settings['min_frequency'],
                            'max_chars_display': settings['max_items_display'],
                            'show_chart_type': settings['chart_type'].lower()
                        }
                    }
                    
                    db.save_analysis_result(user_data['user_id'], analysis_data)
                    
                    # Update user preferences
                    db.update_user_preferences(user_data['user_id'], analysis_data['settings_used'])
                    
                    status_text.text("✅ Analysis complete!")
                    
                    # Clear progress after a moment
                    import time
                    time.sleep(1)
                    progress_container.empty()
                    
                    st.success("🎉 Analysis completed successfully! Results saved to your progress.")
                    
                finally:
                    # Clean up temporary file
                    os.unlink(tmp_file_path)
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                return False
    
    return True


def display_analysis_results(settings):
    """Display the analysis results based on current settings."""
    
    if not all([
        st.session_state.get('analysis_results'),
        st.session_state.get('word_analysis_results'),
        st.session_state.get('pronunciation_data')
    ]):
        st.info("👆 Upload a document above to start analyzing!")
        return
    
    char_results = st.session_state.analysis_results
    word_results = st.session_state.word_analysis_results
    pronunciation_data = st.session_state.pronunciation_data
    
    # Create tabs for different analysis views
    if settings['analysis_type'] == "Both":
        tab1, tab2, tab3 = st.tabs(["📊 Overview", "🔤 Characters", "📝 Words"])
        
        with tab1:
            display_overview_analysis(char_results, word_results, pronunciation_data, settings)
        
        with tab2:
            display_character_analysis(char_results, pronunciation_data['characters'], settings)
        
        with tab3:
            display_word_analysis(word_results, pronunciation_data['words'], settings)
    
    elif settings['analysis_type'] == "Characters":
        display_character_analysis(char_results, pronunciation_data['characters'], settings)
    
    else:  # Words
        display_word_analysis(word_results, pronunciation_data['words'], settings)


def display_overview_analysis(char_results, word_results, pronunciation_data, settings):
    """Display overview of both character and word analysis."""
    st.header("📊 Analysis Overview")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Characters", 
            f"{char_results['total_chars']:,}",
            help="Total Han characters found in the document"
        )
    
    with col2:
        st.metric(
            "Unique Characters", 
            f"{char_results['unique_han_chars']:,}",
            help="Number of different Han characters"
        )
    
    with col3:
        st.metric(
            "Total Words", 
            f"{word_results['total_words']:,}",
            help="Total words found in the document"
        )
    
    with col4:
        st.metric(
            "Han Words", 
            f"{len(word_results['han_words']):,}",
            help="Words containing Han characters"
        )
    
    # Side-by-side comparison charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔤 Top Characters")
        top_chars = dict(char_results['character_frequency'].most_common(10))
        if top_chars:
            fig = px.bar(
                x=list(top_chars.keys()),
                y=list(top_chars.values()),
                title="Most Frequent Characters"
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📝 Top Words")
        top_words = dict(word_results['han_words'].most_common(10))
        if top_words:
            fig = px.bar(
                x=list(top_words.keys()),
                y=list(top_words.values()),
                title="Most Frequent Words"
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)


def display_character_analysis(char_results, pronunciation_data, settings):
    """Display detailed character analysis."""
    st.header("🔤 Character Analysis")
    
    # Filter and limit results
    filtered_chars = {
        char: count for char, count in char_results['character_frequency'].items()
        if count >= settings['min_frequency']
    }
    
    if settings['max_items_display']:
        top_chars = dict(sorted(filtered_chars.items(), key=lambda x: x[1], reverse=True)[:settings['max_items_display']])
    else:
        top_chars = dict(sorted(filtered_chars.items(), key=lambda x: x[1], reverse=True))
    
    if not top_chars:
        st.warning(f"No characters found with frequency >= {settings['min_frequency']}. Try lowering the minimum frequency.")
        return
    
    # Display chart
    display_frequency_chart(top_chars, settings['chart_type'], "Characters", pronunciation_data)
    
    # Display table with pronunciations
    display_frequency_table(top_chars, pronunciation_data, "Character")


def display_word_analysis(word_results, pronunciation_data, settings):
    """Display detailed word analysis."""
    st.header("📝 Word Analysis")
    
    # Filter and limit results
    filtered_words = {
        word: count for word, count in word_results['han_words'].items()
        if count >= settings['min_frequency']
    }
    
    if settings['max_items_display']:
        top_words = dict(sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:settings['max_items_display']])
    else:
        top_words = dict(sorted(filtered_words.items(), key=lambda x: x[1], reverse=True))
    
    if not top_words:
        st.warning(f"No words found with frequency >= {settings['min_frequency']}. Try lowering the minimum frequency.")
        return
    
    # Display chart
    display_frequency_chart(top_words, settings['chart_type'], "Words", pronunciation_data)
    
    # Display table with pronunciations
    display_frequency_table(top_words, pronunciation_data, "Word")


def display_frequency_chart(data, chart_type, title, pronunciation_data):
    """Display frequency chart based on selected type."""
    st.subheader(f"📊 {title} Frequency Visualization")
    
    if chart_type == "Bar Chart":
        fig = px.bar(
            x=list(data.keys()),
            y=list(data.values()),
            title=f"Most Frequent {title}",
            labels={'x': title, 'y': 'Frequency'}
        )
        fig.update_layout(showlegend=False)
        
    elif chart_type == "Pie Chart":
        fig = px.pie(
            values=list(data.values()),
            names=list(data.keys()),
            title=f"Most Frequent {title}"
        )
        
    else:  # Treemap
        fig = px.treemap(
            values=list(data.values()),
            names=list(data.keys()),
            title=f"Most Frequent {title}"
        )
    
    st.plotly_chart(fig, use_container_width=True)


def display_frequency_table(data, pronunciation_data, item_type):
    """Display frequency table with pronunciations."""
    st.subheader(f"📋 {item_type} Frequency Table")
    
    # Prepare table data
    table_data = []
    total_count = sum(data.values())
    
    for item, frequency in data.items():
        pronunciation = pronunciation_data.get(item, {}).get('jyutping', 'N/A')
        percentage = (frequency / total_count) * 100
        
        table_data.append({
            item_type: item,
            'Frequency': frequency,
            'Percentage': f"{percentage:.2f}%",
            'Jyutping': pronunciation
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Download CSV option
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    
    st.download_button(
        label=f"📄 Download {item_type} Data (CSV)",
        data=csv_buffer.getvalue(),
        file_name=f"{item_type.lower()}_frequency_{st.session_state.uploaded_filename}.csv",
        mime="text/csv"
    )


def main_analysis_page():
    """Main analysis page function."""
    # Check if user is authenticated
    if 'current_user' not in st.session_state or st.session_state.current_user is None:
        return False
    
    user_data = st.session_state.current_user
    db = UserDatabase()
    
    # Load user preferences
    user_prefs = db.get_user_preferences(user_data['user_id'])
    
    # Display header
    display_analysis_header(user_data)
    
    # Main content in columns
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # File upload section
        uploaded_file = display_file_upload_section()
        
        # Analysis settings
        settings = display_analysis_settings(user_prefs)
    
    with col2:
        # Process file if uploaded
        if uploaded_file:
            if process_uploaded_file(uploaded_file, settings, user_data, db):
                # Display results
                display_analysis_results(settings)
        else:
            st.info("👈 Choose a file from the left panel to start analyzing!")
    
    return True