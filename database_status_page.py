"""
Database status and migration page for MongoDB integration.
"""

import streamlit as st
from mongodb_config import get_mongo_manager


def show_database_status():
    """Display database status and connection information."""
    st.header("🗄️ Database Status")
    
    mongo = get_mongo_manager()
    
    if mongo.is_connected():
        st.success("✅ MongoDB Connected")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Connection Details")
            st.write("**Status:** Connected")
            st.write(f"**Database:** {mongo.database.name}")
            
        with col2:
            st.subheader("Collections")
            try:
                collections = mongo.database.list_collection_names()
                if collections:
                    for collection in collections:
                        count = mongo.database[collection].count_documents({})
                        st.write(f"**{collection}:** {count:,} documents")
                else:
                    st.write("No collections found")
            except Exception as e:
                st.error(f"Error listing collections: {e}")
        
        # Performance test
        st.subheader("📊 Performance Test")
        if st.button("Test MongoDB Performance"):
            test_mongodb_performance(mongo)
    
    else:
        st.warning("⚠️ MongoDB Not Connected")
        st.info("Using JSON file fallback storage for development")
        
        # Show fallback data status
        st.subheader("Fallback Storage Status")
        
        import os
        data_files = ['data/users.json', 'data/files.json', 'data/learning_progress.json']
        
        for file_path in data_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                st.write(f"**{file_path}:** {size:,} bytes")
            else:
                st.write(f"**{file_path}:** Not found")


def test_mongodb_performance(mongo):
    """Test MongoDB performance with sample operations."""
    import time
    
    with st.spinner("Testing MongoDB performance..."):
        try:
            # Test write performance
            start_time = time.time()
            test_collection = mongo.get_collection('performance_test')
            
            # Insert test documents
            test_docs = [{'test_id': i, 'data': f'test_data_{i}'} for i in range(100)]
            test_collection.insert_many(test_docs)
            write_time = time.time() - start_time
            
            # Test read performance
            start_time = time.time()
            result = list(test_collection.find({'test_id': {'$lt': 50}}))
            read_time = time.time() - start_time
            
            # Cleanup
            test_collection.drop()
            
            # Display results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Write Speed", f"{write_time:.3f}s", "100 documents")
            with col2:
                st.metric("Read Speed", f"{read_time:.3f}s", f"{len(result)} documents")
            with col3:
                st.metric("Total Time", f"{write_time + read_time:.3f}s")
            
            st.success("✅ Performance test completed successfully!")
            
        except Exception as e:
            st.error(f"❌ Performance test failed: {e}")


def show_migration_tools():
    """Show tools for migrating between JSON and MongoDB."""
    st.header("🔄 Migration Tools")
    
    st.info("These tools help migrate data between JSON files and MongoDB.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("JSON → MongoDB")
        if st.button("Migrate JSON to MongoDB", type="primary"):
            migrate_json_to_mongodb()
    
    with col2:
        st.subheader("MongoDB → JSON")
        if st.button("Export MongoDB to JSON"):
            export_mongodb_to_json()


def migrate_json_to_mongodb():
    """Migrate data from JSON files to MongoDB."""
    mongo = get_mongo_manager()
    
    if not mongo.is_connected():
        st.error("MongoDB is not connected. Cannot perform migration.")
        return
    
    with st.spinner("Migrating data to MongoDB..."):
        try:
            import json
            import os
            
            migration_count = 0
            
            # Migrate users
            if os.path.exists('data/users.json'):
                with open('data/users.json', 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                
                users_collection = mongo.get_collection('users')
                for user_id, user_data in users_data.items():
                    users_collection.replace_one(
                        {'user_id': user_id},
                        user_data,
                        upsert=True
                    )
                    migration_count += 1
                st.write(f"✅ Migrated {len(users_data)} users")
            
            # Migrate files
            if os.path.exists('data/files.json'):
                with open('data/files.json', 'r', encoding='utf-8') as f:
                    files_data = json.load(f)
                
                files_collection = mongo.get_collection('files')
                for file_id, file_data in files_data.items():
                    files_collection.replace_one(
                        {'file_id': file_id},
                        file_data,
                        upsert=True
                    )
                    migration_count += 1
                st.write(f"✅ Migrated {len(files_data)} files")
            
            # Migrate learning progress
            if os.path.exists('data/learning_progress.json'):
                with open('data/learning_progress.json', 'r', encoding='utf-8') as f:
                    learning_data = json.load(f)
                
                learning_collection = mongo.get_collection('learning_progress')
                for user_id, progress_data in learning_data.items():
                    progress_data['user_id'] = user_id
                    learning_collection.replace_one(
                        {'user_id': user_id},
                        progress_data,
                        upsert=True
                    )
                    migration_count += 1
                st.write(f"✅ Migrated {len(learning_data)} learning records")
            
            st.success(f"🎉 Migration completed! Processed {migration_count} records.")
            
        except Exception as e:
            st.error(f"❌ Migration failed: {e}")


def export_mongodb_to_json():
    """Export data from MongoDB to JSON files."""
    mongo = get_mongo_manager()
    
    if not mongo.is_connected():
        st.error("MongoDB is not connected. Cannot perform export.")
        return
    
    with st.spinner("Exporting MongoDB data to JSON..."):
        try:
            import json
            import os
            
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            
            export_count = 0
            
            # Export users
            users_collection = mongo.get_collection('users')
            users_data = {}
            for user in users_collection.find():
                user.pop('_id', None)
                user_id = user['user_id']
                users_data[user_id] = user
            
            with open('data/users_export.json', 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=2, ensure_ascii=False)
            export_count += len(users_data)
            st.write(f"✅ Exported {len(users_data)} users to users_export.json")
            
            # Export files
            files_collection = mongo.get_collection('files')
            files_data = {}
            for file_doc in files_collection.find():
                file_doc.pop('_id', None)
                file_id = file_doc['file_id']
                files_data[file_id] = file_doc
            
            with open('data/files_export.json', 'w', encoding='utf-8') as f:
                json.dump(files_data, f, indent=2, ensure_ascii=False)
            export_count += len(files_data)
            st.write(f"✅ Exported {len(files_data)} files to files_export.json")
            
            # Export learning progress
            learning_collection = mongo.get_collection('learning_progress')
            learning_data = {}
            for progress in learning_collection.find():
                progress.pop('_id', None)
                user_id = progress.pop('user_id')
                learning_data[user_id] = progress
            
            with open('data/learning_progress_export.json', 'w', encoding='utf-8') as f:
                json.dump(learning_data, f, indent=2, ensure_ascii=False)
            export_count += len(learning_data)
            st.write(f"✅ Exported {len(learning_data)} learning records to learning_progress_export.json")
            
            st.success(f"🎉 Export completed! Processed {export_count} records.")
            
        except Exception as e:
            st.error(f"❌ Export failed: {e}")


def main_database_page():
    """Main database management page."""
    st.title("🗄️ Database Management")
    
    tab1, tab2 = st.tabs(["📊 Status", "🔄 Migration"])
    
    with tab1:
        show_database_status()
    
    with tab2:
        show_migration_tools()