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

# Configure page
st.set_page_config(
    page_title="Cantonese Learning - Han Character Frequency Analysis",
    page_icon="🈯",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Header
    st.title("🈯 Cantonese Learning Tool")
    st.markdown("### Han Character Frequency Analysis")
    st.markdown("Upload documents in various formats to analyze Han character frequency and improve your Cantonese learning experience.")
    
    # Initialize session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
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
    
    # Main content area
    if uploaded_file is not None:
        # Check if this is a new file
        if st.session_state.uploaded_filename != uploaded_file.name:
            st.session_state.uploaded_filename = uploaded_file.name
            st.session_state.analysis_results = None
            
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
                        
                    finally:
                        # Clean up temporary file
                        os.unlink(tmp_file_path)
                        
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
                    return
    
    # Display results if available
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
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
        
        # Create two columns for visualization and table
        col_chart, col_table = st.columns([2, 1])
        
        with col_chart:
            st.subheader("📊 Character Frequency Visualization")
            
            # Prepare data for plotting
            chars = list(top_chars.keys())
            frequencies = list(top_chars.values())
            
            # Create DataFrame for plotly
            df_plot = pd.DataFrame({
                'Character': chars,
                'Frequency': frequencies,
                'Percentage': [f"{(freq/results['total_chars']*100):.1f}%" for freq in frequencies]
            })
            
            if show_chart_type == "Bar Chart":
                fig = px.bar(
                    df_plot, 
                    x='Character', 
                    y='Frequency',
                    title=f"Top {len(top_chars)} Most Frequent Han Characters",
                    hover_data=['Percentage']
                )
                fig.update_layout(xaxis_tickangle=-45)
                
            elif show_chart_type == "Pie Chart":
                # Show only top 20 for pie chart to avoid clutter
                df_pie = df_plot.head(20)
                fig = px.pie(
                    df_pie, 
                    values='Frequency', 
                    names='Character',
                    title=f"Top {len(df_pie)} Most Frequent Han Characters"
                )
                
            else:  # Treemap
                fig = px.treemap(
                    df_plot, 
                    path=['Character'], 
                    values='Frequency',
                    title=f"Han Character Frequency Treemap"
                )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_table:
            st.subheader("📋 Frequency Table")
            
            # Create detailed table
            table_data = []
            for char, freq in top_chars.items():
                percentage = (freq / results['total_chars']) * 100
                table_data.append({
                    'Character': char,
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
        
        # Download section
        st.divider()
        st.subheader("💾 Download Results")
        
        col_download1, col_download2 = st.columns(2)
        
        with col_download1:
            # CSV download
            csv_data = pd.DataFrame(list(top_chars.items()), columns=['Character', 'Frequency'])
            csv_data['Percentage'] = (csv_data['Frequency'] / results['total_chars'] * 100).round(1)
            
            csv_buffer = io.StringIO()
            csv_data.to_csv(csv_buffer, index=False, encoding='utf-8')
            
            st.download_button(
                label="📄 Download as CSV",
                data=csv_buffer.getvalue(),
                file_name=f"han_character_frequency_{st.session_state.uploaded_filename}.csv",
                mime="text/csv"
            )
        
        with col_download2:
            # Text summary download
            summary_text = f"""Han Character Frequency Analysis
File: {st.session_state.uploaded_filename}
Total Characters: {results['total_chars']}
Unique Han Characters: {results['unique_han_chars']}
Text Length: {results['text_length']}

Top {len(top_chars)} Most Frequent Characters:
{'='*50}
"""
            for i, (char, freq) in enumerate(top_chars.items(), 1):
                percentage = (freq / results['total_chars']) * 100
                summary_text += f"{i:3d}. {char} - {freq:4d} times ({percentage:5.1f}%)\n"
            
            st.download_button(
                label="📝 Download Summary",
                data=summary_text,
                file_name=f"han_character_summary_{st.session_state.uploaded_filename}.txt",
                mime="text/plain"
            )
    
    else:
        # Welcome screen when no file is uploaded
        st.info("👆 Please upload a file using the sidebar to begin Han character frequency analysis.")
        
        # Instructions
        with st.expander("📖 How to use this tool", expanded=True):
            st.markdown("""
            1. **Upload a file**: Use the sidebar to upload PDF, EPUB, or TXT files
            2. **Adjust settings**: Configure minimum frequency and display limits
            3. **View results**: Analyze character frequency through interactive charts and tables
            4. **Download data**: Export your results as CSV or text summary
            
            **Supported file formats:**
            - **PDF**: Extract text from PDF documents
            - **EPUB**: Parse e-book content 
            - **TXT**: Plain text files with UTF-8 encoding
            
            **Perfect for:**
            - Analyzing Chinese text difficulty
            - Identifying common characters for study
            - Understanding character frequency patterns
            - Preparing vocabulary lists for Cantonese learning
            """)
        
        # Sample usage tips
        with st.expander("💡 Tips for Cantonese Learning"):
            st.markdown("""
            - Focus on the most frequent characters first - they appear in many words
            - Use frequency analysis to gauge text difficulty level
            - Compare character frequencies across different text types
            - Create study lists based on character frequency rankings
            - Track your progress by analyzing texts of increasing complexity
            """)

if __name__ == "__main__":
    main()
