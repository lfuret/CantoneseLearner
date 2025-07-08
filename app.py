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

# Configure page
st.set_page_config(
    page_title="Cantonese Learning - Han Character Frequency Analysis",
    page_icon="🈯",
    layout="wide",
    initial_sidebar_state="expanded"
)

def display_character_analysis(results, pronunciation_data, min_frequency, max_chars_display, show_chart_type):
    """Display character frequency analysis results."""
    # Filter results based on settings
    filtered_chars = {
        char: count for char, count in results['character_frequency'].items()
        if count >= min_frequency
    }
    
    # Limit the number of characters displayed if specified
    if max_chars_display is not None:
        top_chars = dict(sorted(filtered_chars.items(), key=lambda x: x[1], reverse=True)[:max_chars_display])
    else:
        top_chars = dict(sorted(filtered_chars.items(), key=lambda x: x[1], reverse=True))
    
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
    
    # Create visualization and table with pronunciation data
    display_frequency_chart_and_table_with_pronunciation(
        top_chars, pronunciation_data, results['total_chars'], show_chart_type, "Character", "Characters"
    )

def display_word_analysis(word_results, pronunciation_data, min_frequency, max_chars_display, show_chart_type):
    """Display word frequency analysis results."""
    # Filter Han words based on settings
    filtered_words = {
        word: count for word, count in word_results['han_words'].items()
        if count >= min_frequency
    }
    
    # Limit the number of words displayed if specified
    if max_chars_display is not None:
        top_words = dict(sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:max_chars_display])
    else:
        top_words = dict(sorted(filtered_words.items(), key=lambda x: x[1], reverse=True))
    
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
    
    # Create visualization and table with pronunciation data
    display_frequency_chart_and_table_with_pronunciation(
        top_words, pronunciation_data, word_results['total_words'], show_chart_type, "Word", "Words"
    )

def display_combined_analysis(char_results, word_results, pronunciation_data, min_frequency, max_chars_display, show_chart_type):
    """Display both character and word analysis results."""
    # Create tabs for different analysis types
    tab1, tab2 = st.tabs(["📝 Characters", "🔤 Words"])
    
    with tab1:
        display_character_analysis(char_results, pronunciation_data['characters'], min_frequency, max_chars_display, show_chart_type)
    
    with tab2:
        display_word_analysis(word_results, pronunciation_data['words'], min_frequency, max_chars_display, show_chart_type)

def display_frequency_chart_and_table_with_pronunciation(top_items, pronunciation_data, total_count, show_chart_type, item_type, item_type_plural):
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
            # Show only top 30 for pie chart to avoid clutter
            df_pie = df_plot.head(30)
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
        
        # Create detailed table with pronunciation data
        table_data = []
        for item, freq in top_items.items():
            percentage = (freq / total_count) * 100
            
            # Get pronunciation and type data if available
            if item in pronunciation_data:
                jyutping = pronunciation_data[item]['jyutping']
                char_type = pronunciation_data[item]['type']
            else:
                jyutping = "unknown"
                char_type = "unknown"
            
            table_data.append({
                item_type: item,
                'Type': char_type.capitalize(),
                'Jyutping': jyutping,
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

def display_download_section(char_results, word_results, pronunciation_data, analysis_type):
    """Display download section with appropriate data based on analysis type."""
    st.divider()
    st.subheader("💾 Download Results")
    
    col_download1, col_download2 = st.columns(2)
    
    if analysis_type == "Characters":
        # Character analysis download - all characters that meet minimum frequency
        all_chars = {
            char: count for char, count in char_results['character_frequency'].items()
            if count >= min_frequency
        }
        top_chars = dict(sorted(all_chars.items(), key=lambda x: x[1], reverse=True))
        
        with col_download1:
            # Create CSV with pronunciation data
            csv_data_list = []
            for char, freq in top_chars.items():
                char_data = pronunciation_data['characters'].get(char, {})
                jyutping = char_data.get('jyutping', 'unknown')
                char_type = char_data.get('type', 'unknown')
                percentage = (freq / char_results['total_chars'] * 100)
                csv_data_list.append({
                    'Character': char,
                    'Type': char_type.capitalize(),
                    'Jyutping': jyutping,
                    'Frequency': freq,
                    'Percentage': round(percentage, 1)
                })
            
            csv_data = pd.DataFrame(csv_data_list)
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
                char_data = pronunciation_data['characters'].get(char, {})
                jyutping = char_data.get('jyutping', 'unknown')
                char_type = char_data.get('type', 'unknown')
                summary_text += f"{i:3d}. {char} [{char_type}] ({jyutping}) - {freq:4d} times ({percentage:5.1f}%)\n"
            
            st.download_button(
                label="📝 Download Character Summary",
                data=summary_text,
                file_name=f"han_character_summary_{st.session_state.uploaded_filename}.txt",
                mime="text/plain"
            )
    
    elif analysis_type == "Words":
        # Word analysis download - all words that meet minimum frequency
        all_words = {
            word: count for word, count in word_results['han_words'].items()
            if count >= min_frequency
        }
        top_words = dict(sorted(all_words.items(), key=lambda x: x[1], reverse=True))
        
        with col_download1:
            # Create CSV with pronunciation data
            csv_data_list = []
            for word, freq in top_words.items():
                word_data = pronunciation_data['words'].get(word, {})
                jyutping = word_data.get('jyutping', 'unknown')
                word_type = word_data.get('type', 'unknown')
                percentage = (freq / word_results['total_words'] * 100)
                csv_data_list.append({
                    'Word': word,
                    'Type': word_type.capitalize(),
                    'Jyutping': jyutping,
                    'Frequency': freq,
                    'Percentage': round(percentage, 1)
                })
            
            csv_data = pd.DataFrame(csv_data_list)
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
                word_data = pronunciation_data['words'].get(word, {})
                jyutping = word_data.get('jyutping', 'unknown')
                word_type = word_data.get('type', 'unknown')
                summary_text += f"{i:3d}. {word} [{word_type}] ({jyutping}) - {freq:4d} times ({percentage:5.1f}%)\n"
            
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
            # Character CSV with pronunciation - all characters that meet minimum frequency
            all_chars = {
                char: count for char, count in char_results['character_frequency'].items()
                if count >= min_frequency
            }
            top_chars = dict(sorted(all_chars.items(), key=lambda x: x[1], reverse=True))
            csv_data_list = []
            for char, freq in top_chars.items():
                jyutping = pronunciation_data['characters'].get(char, {}).get('jyutping', 'unknown')
                percentage = (freq / char_results['total_chars'] * 100)
                csv_data_list.append({
                    'Character': char,
                    'Jyutping': jyutping,
                    'Frequency': freq,
                    'Percentage': round(percentage, 1)
                })
            
            csv_data = pd.DataFrame(csv_data_list)
            csv_buffer = io.StringIO()
            csv_data.to_csv(csv_buffer, index=False, encoding='utf-8')
            
            st.download_button(
                label="📄 Download Characters CSV",
                data=csv_buffer.getvalue(),
                file_name=f"han_character_frequency_{st.session_state.uploaded_filename}.csv",
                mime="text/csv"
            )
        
        with col_download2:
            # Word CSV with pronunciation - all words that meet minimum frequency
            all_words = {
                word: count for word, count in word_results['han_words'].items()
                if count >= min_frequency
            }
            top_words = dict(sorted(all_words.items(), key=lambda x: x[1], reverse=True))
            csv_data_list = []
            for word, freq in top_words.items():
                jyutping = pronunciation_data['words'].get(word, {}).get('jyutping', 'unknown')
                percentage = (freq / word_results['total_words'] * 100)
                csv_data_list.append({
                    'Word': word,
                    'Jyutping': jyutping,
                    'Frequency': freq,
                    'Percentage': round(percentage, 1)
                })
            
            csv_data = pd.DataFrame(csv_data_list)
            csv_buffer = io.StringIO()
            csv_data.to_csv(csv_buffer, index=False, encoding='utf-8')
            
            st.download_button(
                label="📄 Download Words CSV",
                data=csv_buffer.getvalue(),
                file_name=f"han_word_frequency_{st.session_state.uploaded_filename}.csv",
                mime="text/csv"
            )

def show_user_progress(user_data, db):
    """Display user progress dashboard."""
    st.header(f"📊 Progress Dashboard - {user_data['username']}")
    
    # User statistics
    stats = db.get_user_statistics(user_data['user_id'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Analyses", stats.get('total_analyses', 0))
    with col2:
        st.metric("Files Processed", stats.get('files_processed', 0))
    with col3:
        st.metric("Characters Analyzed", f"{stats.get('total_characters_analyzed', 0):,}")
    with col4:
        st.metric("Words Analyzed", f"{stats.get('total_words_analyzed', 0):,}")
    
    # Recent activity
    st.subheader("📈 Recent Analysis History")
    history = db.get_user_history(user_data['user_id'], limit=10)
    
    if history:
        history_df = pd.DataFrame([
            {
                'Date': record['timestamp'][:10],
                'Time': record['timestamp'][11:19],
                'File': record['filename'],
                'Type': record['analysis_type'],
                'Characters': record['character_stats'].get('total_chars', 'N/A'),
                'Words': record['word_stats'].get('total_words', 'N/A')
            }
            for record in history
        ])
        st.dataframe(history_df, use_container_width=True)
        
        # Analysis trends chart
        if len(history) > 1:
            st.subheader("📊 Analysis Trends")
            chart_data = pd.DataFrame([
                {
                    'Date': record['timestamp'][:10],
                    'Characters': record['character_stats'].get('total_chars', 0),
                    'Words': record['word_stats'].get('total_words', 0)
                }
                for record in reversed(history)
            ])
            
            fig = px.line(chart_data, x='Date', y=['Characters', 'Words'], 
                         title="Characters and Words Analyzed Over Time")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No analysis history yet. Start by uploading a document!")
    
    # User preferences section
    st.subheader("⚙️ Your Preferences")
    prefs = db.get_user_preferences(user_data['user_id'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Preferred Analysis Type:** {prefs.get('preferred_analysis_type', 'both').title()}")
        st.write(f"**Minimum Frequency:** {prefs.get('min_frequency', 1)}")
    with col2:
        st.write(f"**Max Items Display:** {prefs.get('max_chars_display', 50)}")
        st.write(f"**Chart Type:** {prefs.get('show_chart_type', 'bar').title()}")

def user_authentication():
    """Handle user authentication and registration."""
    db = UserDatabase()
    
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    if st.session_state.current_user is None:
        st.title("🈯 Welcome to Cantonese Learning Tool")
        st.markdown("**Please sign in or create an account to track your progress**")
        
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        with tab1:
            st.subheader("Sign In")
            username = st.text_input("Username", key="signin_username")
            if st.button("Sign In", key="signin_button"):
                if username:
                    user_data = db.get_user_by_username(username)
                    if user_data:
                        st.session_state.current_user = user_data
                        db.update_last_login(user_data['user_id'])
                        st.success(f"Welcome back, {username}!")
                        st.rerun()
                    else:
                        st.error("Username not found. Please create an account first.")
                else:
                    st.error("Please enter a username.")
        
        with tab2:
            st.subheader("Create New Account")
            new_username = st.text_input("Choose Username", key="new_username")
            new_email = st.text_input("Email (optional)", key="new_email")
            if st.button("Create Account", key="create_button"):
                if new_username:
                    try:
                        user_id = db.create_user(new_username, new_email)
                        user_data = db.get_user(user_id)
                        st.session_state.current_user = user_data
                        st.success(f"Account created successfully! Welcome, {new_username}!")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                else:
                    st.error("Please enter a username.")
        
        return False
    
    return True

def main():
    """Main application function."""
    # Handle user authentication first
    if not user_authentication():
        return
    
    # User is authenticated, show main app
    user_data = st.session_state.current_user
    db = UserDatabase()
    
    # Header with user info
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("🈯 Cantonese Learning Tool")
        st.markdown("**Han Character & Word Frequency Analysis for Language Learners**")
    with col2:
        st.markdown(f"**Welcome, {user_data['username']}!**")
    with col3:
        if st.button("📊 View Progress"):
            st.session_state.show_progress = True
        if st.button("Sign Out"):
            st.session_state.current_user = None
            st.rerun()
    
    # Initialize session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'word_analysis_results' not in st.session_state:
        st.session_state.word_analysis_results = None
    if 'pronunciation_data' not in st.session_state:
        st.session_state.pronunciation_data = None
    if 'uploaded_filename' not in st.session_state:
        st.session_state.uploaded_filename = None
    if 'show_progress' not in st.session_state:
        st.session_state.show_progress = False
    
    # Load user preferences
    user_prefs = db.get_user_preferences(user_data['user_id'])
    
    # Show progress dashboard if requested
    if st.session_state.show_progress:
        show_user_progress(user_data, db)
        if st.button("← Back to Analysis"):
            st.session_state.show_progress = False
            st.rerun()
        return
    
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
            value=user_prefs.get('min_frequency', 5),
            help="Only show characters that appear at least this many times"
        )
        
        show_all_results = st.checkbox(
            "Show all results",
            value=user_prefs.get('max_chars_display') is None,
            help="Show all characters/words or limit to top 50"
        )
        
        if not show_all_results:
            max_chars_display = st.slider(
                "Maximum items to display",
                min_value=10,
                max_value=200,
                value=user_prefs.get('max_chars_display', 50),
                help="Limit the number of items shown in results"
            )
        else:
            max_chars_display = None
        
        show_chart_type = st.selectbox(
            "Chart type",
            ["Bar Chart", "Pie Chart", "Treemap"],
            index=["Bar Chart", "Pie Chart", "Treemap"].index(user_prefs.get('show_chart_type', 'Bar Chart').title()),
            help="Choose how to visualize the frequency data"
        )
        
        analysis_type = st.selectbox(
            "Analysis type",
            ["Characters", "Words", "Both"],
            index=["Characters", "Words", "Both"].index(user_prefs.get('preferred_analysis_type', 'Both').title()),
            help="Choose to analyze characters, words, or both"
        )
        
        # Save preferences when changed
        current_prefs = {
            'preferred_analysis_type': analysis_type.lower(),
            'min_frequency': min_frequency,
            'max_chars_display': max_chars_display,
            'show_chart_type': show_chart_type.lower()
        }
        
        if current_prefs != user_prefs:
            db.update_user_preferences(user_data['user_id'], current_prefs)
    
    # Main content area
    if uploaded_file is not None:
        # Check if this is a new file
        if st.session_state.uploaded_filename != uploaded_file.name:
            st.session_state.uploaded_filename = uploaded_file.name
            st.session_state.analysis_results = None
            st.session_state.word_analysis_results = None
            st.session_state.pronunciation_data = None
            
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
                        
                        # Analyze pronunciations
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
                        
                        # Save analysis results to user database
                        analysis_data = {
                            'filename': uploaded_file.name,
                            'file_size': uploaded_file.size,
                            'analysis_type': analysis_type.lower(),
                            'character_stats': analysis_results,
                            'word_stats': word_analysis_results,
                            'top_characters': dict(analysis_results['character_frequency'].most_common(10)),
                            'top_words': dict(word_analysis_results['han_words'].most_common(10)),
                            'settings_used': current_prefs
                        }
                        
                        db.save_analysis_result(user_data['user_id'], analysis_data)
                        
                        st.success(f"✅ Analysis complete! Results saved to your progress.")
                        
                    finally:
                        # Clean up temporary file
                        os.unlink(tmp_file_path)
                        
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
                    return
    
    # Display results if available
    if st.session_state.analysis_results and st.session_state.word_analysis_results and st.session_state.pronunciation_data:
        char_results = st.session_state.analysis_results
        word_results = st.session_state.word_analysis_results
        pronunciation_data = st.session_state.pronunciation_data
        
        # Display different analysis types based on selection
        if analysis_type == "Characters":
            display_character_analysis(char_results, pronunciation_data['characters'], min_frequency, max_chars_display, show_chart_type)
        elif analysis_type == "Words":
            display_word_analysis(word_results, pronunciation_data['words'], min_frequency, max_chars_display, show_chart_type)
        else:  # Both
            display_combined_analysis(char_results, word_results, pronunciation_data, min_frequency, max_chars_display, show_chart_type)
        
        
        # Download section
        display_download_section(char_results, word_results, pronunciation_data, analysis_type)
    
    else:
        # Welcome screen when no file is uploaded
        st.info("👆 Please upload a file using the sidebar to begin Han character and word frequency analysis with Jyutping pronunciations.")
        
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
            - **Characters**: Analyze individual Han character frequency with Jyutping pronunciations
            - **Words**: Analyze word frequency using Chinese word segmentation with Jyutping pronunciations
            - **Both**: View both character and word analysis in separate tabs
            
            **Perfect for:**
            - Analyzing Chinese text difficulty with pronunciation guides
            - Identifying common characters and words for study
            - Learning proper Cantonese pronunciations (Jyutping)
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
