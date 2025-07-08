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

# Configure page
st.set_page_config(
    page_title="Cantonese Learning - Han Character Frequency Analysis",
    page_icon="🈯",
    layout="wide",
    initial_sidebar_state="expanded"
)

def display_character_analysis(results, min_frequency, max_chars_display, show_chart_type):
    """Display character frequency analysis results."""
    # Filter results based on settings
    filtered_chars = {
        char: count for char, count in results['character_frequency'].items()
        if count >= min_frequency
    }
    
    # Limit the number of characters displayed
    top_chars = dict(sorted(filtered_chars.items(), key=lambda x: x[1], reverse=True)[:max_chars_display])
    
    if not top_chars:
        st.warning(f"No characters found with frequency >= {min_frequency}. Try lowering the minimum frequency.")
        return
    
    # Display summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Characters", results['total_chars'])
    
    with col2:
        st.metric("Unique Han Characters", results['unique_han_chars'])
    
    with col3:
        st.metric("Text Length", results['text_length'])
    
    with col4:
        st.metric("Displayed Characters", len(top_chars))
    
    st.divider()
    
    # Create visualization and table
    display_frequency_chart_and_table(top_chars, results['total_chars'], show_chart_type, "Character", "Characters")

def display_word_analysis(word_results, min_frequency, max_chars_display, show_chart_type):
    """Display word frequency analysis results."""
    # Filter Han words based on settings
    filtered_words = {
        word: count for word, count in word_results['han_words'].items()
        if count >= min_frequency
    }
    
    # Limit the number of words displayed
    top_words = dict(sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:max_chars_display])
    
    if not top_words:
        st.warning(f"No words found with frequency >= {min_frequency}. Try lowering the minimum frequency.")
        return
    
    # Display summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Words", word_results['total_words'])
    
    with col2:
        st.metric("Unique Words", word_results['unique_words'])
    
    with col3:
        st.metric("Han Words", len(word_results['han_words']))
    
    with col4:
        st.metric("Displayed Words", len(top_words))
    
    st.divider()
    
    # Create visualization and table
    display_frequency_chart_and_table(top_words, word_results['total_words'], show_chart_type, "Word", "Words")

def display_combined_analysis(char_results, word_results, min_frequency, max_chars_display, show_chart_type):
    """Display both character and word analysis results."""
    # Create tabs for different analysis types
    tab1, tab2 = st.tabs(["📝 Characters", "🔤 Words"])
    
    with tab1:
        display_character_analysis(char_results, min_frequency, max_chars_display, show_chart_type)
    
    with tab2:
        display_word_analysis(word_results, min_frequency, max_chars_display, show_chart_type)

def display_frequency_chart_and_table(top_items, total_count, show_chart_type, item_type, item_type_plural):
    """Display frequency chart and table for either characters or words."""
    # Create two columns for visualization and table
    col_chart, col_table = st.columns([2, 1])
    
    with col_chart:
        st.subheader(f"📊 {item_type} Frequency Visualization")
        
        # Prepare data for plotting
        items = list(top_items.keys())
        frequencies = list(top_items.values())
        
        # Create DataFrame for plotly
        df_plot = pd.DataFrame({
            item_type: items,
            'Frequency': frequencies,
            'Percentage': [f"{(freq/total_count*100):.1f}%" for freq in frequencies]
        })
        
        if show_chart_type == "Bar Chart":
            fig = px.bar(
                df_plot, 
                x=item_type, 
                y='Frequency',
                title=f"Top {len(top_items)} Most Frequent {item_type_plural}",
                hover_data=['Percentage']
            )
            fig.update_layout(xaxis_tickangle=-45)
            
        elif show_chart_type == "Pie Chart":
            # Show only top 20 for pie chart to avoid clutter
            df_pie = df_plot.head(20)
            fig = px.pie(
                df_pie, 
                values='Frequency', 
                names=item_type,
                title=f"Top {len(df_pie)} Most Frequent {item_type_plural}"
            )
            
        else:  # Treemap
            fig = px.treemap(
                df_plot, 
                path=[item_type], 
                values='Frequency',
                title=f"{item_type} Frequency Treemap"
            )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_table:
        st.subheader("📋 Frequency Table")
        
        # Create detailed table
        table_data = []
        for item, freq in top_items.items():
            percentage = (freq / total_count) * 100
            table_data.append({
                item_type: item,
                'Frequency': freq,
                'Percentage': f"{percentage:.1f}%"
            })
        
        df_table = pd.DataFrame(table_data)
        
        # Display table with styling
        st.dataframe(
            df_table,
            use_container_width=True,
            height=500,
            hide_index=True
        )

def display_download_section(char_results, word_results, analysis_type):
    """Display download section with appropriate data based on analysis type."""
    st.divider()
    st.subheader("💾 Download Results")
    
    col_download1, col_download2 = st.columns(2)
    
    if analysis_type == "Characters":
        # Character analysis download
        top_chars = dict(sorted(char_results['character_frequency'].items(), key=lambda x: x[1], reverse=True)[:50])
        
        with col_download1:
            csv_data = pd.DataFrame(list(top_chars.items()), columns=['Character', 'Frequency'])
            csv_data['Percentage'] = (csv_data['Frequency'] / char_results['total_chars'] * 100).round(1)
            
            csv_buffer = io.StringIO()
            csv_data.to_csv(csv_buffer, index=False, encoding='utf-8')
            
            st.download_button(
                label="📄 Download Characters CSV",
                data=csv_buffer.getvalue(),
                file_name=f"han_character_frequency_{st.session_state.uploaded_filename}.csv",
                mime="text/csv"
            )
        
        with col_download2:
            summary_text = f"""Han Character Frequency Analysis
File: {st.session_state.uploaded_filename}
Total Characters: {char_results['total_chars']}
Unique Han Characters: {char_results['unique_han_chars']}
Text Length: {char_results['text_length']}

Top {len(top_chars)} Most Frequent Characters:
{'='*50}
"""
            for i, (char, freq) in enumerate(top_chars.items(), 1):
                percentage = (freq / char_results['total_chars']) * 100
                summary_text += f"{i:3d}. {char} - {freq:4d} times ({percentage:5.1f}%)\n"
            
            st.download_button(
                label="📝 Download Character Summary",
                data=summary_text,
                file_name=f"han_character_summary_{st.session_state.uploaded_filename}.txt",
                mime="text/plain"
            )
    
    elif analysis_type == "Words":
        # Word analysis download
        top_words = dict(sorted(word_results['han_words'].items(), key=lambda x: x[1], reverse=True)[:50])
        
        with col_download1:
            csv_data = pd.DataFrame(list(top_words.items()), columns=['Word', 'Frequency'])
            csv_data['Percentage'] = (csv_data['Frequency'] / word_results['total_words'] * 100).round(1)
            
            csv_buffer = io.StringIO()
            csv_data.to_csv(csv_buffer, index=False, encoding='utf-8')
            
            st.download_button(
                label="📄 Download Words CSV",
                data=csv_buffer.getvalue(),
                file_name=f"han_word_frequency_{st.session_state.uploaded_filename}.csv",
                mime="text/csv"
            )
        
        with col_download2:
            summary_text = f"""Han Word Frequency Analysis
File: {st.session_state.uploaded_filename}
Total Words: {word_results['total_words']}
Unique Words: {word_results['unique_words']}
Han Words: {len(word_results['han_words'])}

Top {len(top_words)} Most Frequent Words:
{'='*50}
"""
            for i, (word, freq) in enumerate(top_words.items(), 1):
                percentage = (freq / word_results['total_words']) * 100
                summary_text += f"{i:3d}. {word} - {freq:4d} times ({percentage:5.1f}%)\n"
            
            st.download_button(
                label="📝 Download Word Summary",
                data=summary_text,
                file_name=f"han_word_summary_{st.session_state.uploaded_filename}.txt",
                mime="text/plain"
            )
    
    else:  # Both
        # Combined analysis download
        col_download3, col_download4 = st.columns(2)
        
        with col_download1:
            # Character CSV
            top_chars = dict(sorted(char_results['character_frequency'].items(), key=lambda x: x[1], reverse=True)[:50])
            csv_data = pd.DataFrame(list(top_chars.items()), columns=['Character', 'Frequency'])
            csv_data['Percentage'] = (csv_data['Frequency'] / char_results['total_chars'] * 100).round(1)
            
            csv_buffer = io.StringIO()
            csv_data.to_csv(csv_buffer, index=False, encoding='utf-8')
            
            st.download_button(
                label="📄 Download Characters CSV",
                data=csv_buffer.getvalue(),
                file_name=f"han_character_frequency_{st.session_state.uploaded_filename}.csv",
                mime="text/csv"
            )
        
        with col_download2:
            # Word CSV
            top_words = dict(sorted(word_results['han_words'].items(), key=lambda x: x[1], reverse=True)[:50])
            csv_data = pd.DataFrame(list(top_words.items()), columns=['Word', 'Frequency'])
            csv_data['Percentage'] = (csv_data['Frequency'] / word_results['total_words'] * 100).round(1)
            
            csv_buffer = io.StringIO()
            csv_data.to_csv(csv_buffer, index=False, encoding='utf-8')
            
            st.download_button(
                label="📄 Download Words CSV",
                data=csv_buffer.getvalue(),
                file_name=f"han_word_frequency_{st.session_state.uploaded_filename}.csv",
                mime="text/csv"
            )

def main():
    # Header
    st.title("🈯 Cantonese Learning Tool")
    st.markdown("### Han Character & Word Frequency Analysis")
    st.markdown("Upload documents in various formats to analyze Han character and word frequency to improve your Cantonese learning experience.")
    
    # Initialize session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'word_analysis_results' not in st.session_state:
        st.session_state.word_analysis_results = None
    if 'uploaded_filename' not in st.session_state:
        st.session_state.uploaded_filename = None
    
    # Sidebar for file upload and settings
    with st.sidebar:
        st.header("📁 File Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'epub', 'txt'],
            help="Supported formats: PDF, EPUB, TXT"
        )
        
        st.header("⚙️ Analysis Settings")
        
        min_frequency = st.slider(
            "Minimum character frequency",
            min_value=1,
            max_value=50,
            value=5,
            help="Only show characters that appear at least this many times"
        )
        
        max_chars_display = st.slider(
            "Maximum characters to display",
            min_value=10,
            max_value=200,
            value=50,
            help="Limit the number of characters shown in results"
        )
        
        show_chart_type = st.selectbox(
            "Chart type",
            ["Bar Chart", "Pie Chart", "Treemap"],
            help="Choose how to visualize the frequency data"
        )
        
        analysis_type = st.selectbox(
            "Analysis type",
            ["Characters", "Words", "Both"],
            help="Choose to analyze characters, words, or both"
        )
    
    # Main content area
    if uploaded_file is not None:
        # Check if this is a new file
        if st.session_state.uploaded_filename != uploaded_file.name:
            st.session_state.uploaded_filename = uploaded_file.name
            st.session_state.analysis_results = None
            st.session_state.word_analysis_results = None
            
            with st.spinner(f"Processing {uploaded_file.name}..."):
                try:
                    # Parse the file
                    parser = FileParser()
                    
                    # Create temporary file to save uploaded content
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # Extract text from file
                        text_content = parser.parse_file(tmp_file_path, uploaded_file.type)
                        
                        if not text_content.strip():
                            st.error("No text content found in the uploaded file.")
                            return
                        
                        # Analyze characters
                        analyzer = CharacterAnalyzer()
                        analysis_results = analyzer.analyze_text(text_content)
                        st.session_state.analysis_results = analysis_results
                        
                        # Analyze words
                        word_analyzer = WordAnalyzer()
                        word_analysis_results = word_analyzer.analyze_text(text_content)
                        st.session_state.word_analysis_results = word_analysis_results
                        
                    finally:
                        # Clean up temporary file
                        os.unlink(tmp_file_path)
                        
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
                    return
    
    # Display results if available
    if st.session_state.analysis_results and st.session_state.word_analysis_results:
        char_results = st.session_state.analysis_results
        word_results = st.session_state.word_analysis_results
        
        # Display different analysis types based on selection
        if analysis_type == "Characters":
            display_character_analysis(char_results, min_frequency, max_chars_display, show_chart_type)
        elif analysis_type == "Words":
            display_word_analysis(word_results, min_frequency, max_chars_display, show_chart_type)
        else:  # Both
            display_combined_analysis(char_results, word_results, min_frequency, max_chars_display, show_chart_type)
        
        
        # Download section
        display_download_section(char_results, word_results, analysis_type)
    
    else:
        # Welcome screen when no file is uploaded
        st.info("👆 Please upload a file using the sidebar to begin Han character and word frequency analysis.")
        
        # Instructions
        with st.expander("📖 How to use this tool", expanded=True):
            st.markdown("""
            1. **Upload a file**: Use the sidebar to upload PDF, EPUB, or TXT files
            2. **Choose analysis type**: Select Characters, Words, or Both
            3. **Adjust settings**: Configure minimum frequency and display limits
            4. **View results**: Analyze frequency through interactive charts and tables
            5. **Download data**: Export your results as CSV or text summary
            
            **Supported file formats:**
            - **PDF**: Extract text from PDF documents
            - **EPUB**: Parse e-book content 
            - **TXT**: Plain text files with UTF-8 encoding
            
            **Analysis types:**
            - **Characters**: Analyze individual Han character frequency
            - **Words**: Analyze word frequency using Chinese word segmentation
            - **Both**: View both character and word analysis in separate tabs
            
            **Perfect for:**
            - Analyzing Chinese text difficulty
            - Identifying common characters and words for study
            - Understanding frequency patterns in Chinese text
            - Preparing vocabulary lists for Cantonese learning
            """)
        
        # Sample usage tips
        with st.expander("💡 Tips for Cantonese Learning"):
            st.markdown("""
            - **Characters**: Focus on the most frequent characters first - they appear in many words
            - **Words**: Learn high-frequency words to build vocabulary faster
            - **Difficulty**: Use frequency analysis to gauge text difficulty level
            - **Progression**: Start with character analysis, then move to word analysis
            - **Comparison**: Compare frequencies across different text types
            - **Study lists**: Create targeted study lists based on frequency rankings
            """)

if __name__ == "__main__":
    main()
