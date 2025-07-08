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
from analysis_page import main_analysis_page

# Configure page
st.set_page_config(
    page_title="Cantonese Learning - Han Character Frequency Analysis",
    page_icon="🈯",
    layout="wide",
    initial_sidebar_state="expanded"
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
    
    # Show progress dashboard if requested
    if st.session_state.show_progress:
        user_data = st.session_state.current_user
        db = UserDatabase()
        show_user_progress(user_data, db)
        if st.button("← Back to Analysis"):
            st.session_state.show_progress = False
            st.rerun()
        return
    
    # Use refactored analysis page
    main_analysis_page()

if __name__ == "__main__":
    main()