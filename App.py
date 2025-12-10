import streamlit as st
import pandas as pd
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, List, Any
import io
import base64
from collections import Counter

# Page configuration
st.set_page_config(
    page_title="Code Template Manager",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .category-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    .code-preview {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        overflow-x: auto;
        max-height: 400px;
        overflow-y: auto;
    }
    .stats-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .info-box {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .data-table {
        font-size: 0.9rem;
    }
    .edit-button {
        background: #667eea;
        color: white;
        border: none;
        padding: 0.4rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
    }
    .delete-button {
        background: #dc3545;
        color: white;
        border: none;
        padding: 0.4rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
    }
    .search-box {
        padding: 0.8rem;
        border: 2px solid #667eea;
        border-radius: 8px;
        font-size: 1rem;
        width: 100%;
    }
    .filter-chip {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: #e9ecef;
        border-radius: 20px;
        margin: 0.3rem;
        cursor: pointer;
        transition: all 0.3s;
    }
    .filter-chip:hover {
        background: #667eea;
        color: white;
    }
    .filter-chip.active {
        background: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets configuration
GOOGLE_SHEETS_ID = "1eFZcnDoGT2NJHaEQSgxW5psN5kvlkYx1vtuXGRFTGTk"
GOOGLE_SHEETS_SHEET_NAME = "demo_examples"

# Session state initialization
def initialize_session_state():
    if 'gsheet_credentials' not in st.session_state:
        st.session_state.gsheet_credentials = None
    if 'templates_data' not in st.session_state:
        st.session_state.templates_data = None
    if 'last_sync' not in st.session_state:
        st.session_state.last_sync = None
    if 'selected_template' not in st.session_state:
        st.session_state.selected_template = None
    if 'filter_category' not in st.session_state:
        st.session_state.filter_category = "All"
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'show_preview' not in st.session_state:
        st.session_state.show_preview = False

initialize_session_state()

# Utility Functions
def fetch_google_sheets_data() -> Optional[pd.DataFrame]:
    """Fetch data from Google Sheets using credentials."""
    if not st.session_state.gsheet_credentials:
        st.warning("Please upload Google Cloud service account credentials first.")
        return None
    
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.session_state.gsheet_credentials,
            scope
        )
        
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = sheet.worksheet(GOOGLE_SHEETS_SHEET_NAME)
        
        data = worksheet.get_all_records()
        
        if data:
            df = pd.DataFrame(data)
            st.session_state.last_sync = datetime.now()
            return df
        else:
            return None
    
    except Exception as e:
        st.error(f"Error fetching Google Sheets data: {str(e)}")
        return None

def push_to_google_sheets(df: pd.DataFrame) -> bool:
    """Push updated data back to Google Sheets."""
    if not st.session_state.gsheet_credentials:
        st.error("No credentials found")
        return False
    
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.session_state.gsheet_credentials,
            scope
        )
        
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = sheet.worksheet(GOOGLE_SHEETS_SHEET_NAME)
        
        # Clear existing data
        worksheet.clear()
        
        # Update with new data
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        
        st.session_state.last_sync = datetime.now()
        return True
    
    except Exception as e:
        st.error(f"Error pushing to Google Sheets: {str(e)}")
        return False

def get_category_colors() -> Dict[str, str]:
    """Get color mapping for categories."""
    return {
        "HTML/CSS": "#e74c3c",
        "JavaScript": "#f39c12",
        "Python": "#3498db",
        "React": "#61dafb",
        "Vue": "#42b883",
        "API": "#9b59b6",
        "Database": "#2ecc71",
        "Other": "#95a5a6"
    }

def format_code_for_display(code: str, max_lines: int = 20) -> str:
    """Format code for preview display."""
    lines = code.split('\n')
    if len(lines) > max_lines:
        return '\n'.join(lines[:max_lines]) + f"\n\n... ({len(lines) - max_lines} more lines)"
    return code

def export_to_json(df: pd.DataFrame) -> str:
    """Export DataFrame to JSON string."""
    return df.to_json(orient='records', indent=2)

def import_from_json(json_str: str) -> Optional[pd.DataFrame]:
    """Import DataFrame from JSON string."""
    try:
        data = json.loads(json_str)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error parsing JSON: {str(e)}")
        return None

def get_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate statistics from template data."""
    if df is None or len(df) == 0:
        return {
            'total_templates': 0,
            'categories': {},
            'avg_code_length': 0,
            'total_code_length': 0,
            'most_common_category': None
        }
    
    categories = Counter(df['Category'].tolist()) if 'Category' in df.columns else {}
    code_lengths = df['Code'].apply(len).tolist() if 'Code' in df.columns else [0]
    
    return {
        'total_templates': len(df),
        'categories': dict(categories),
        'avg_code_length': sum(code_lengths) / len(code_lengths) if code_lengths else 0,
        'total_code_length': sum(code_lengths),
        'most_common_category': categories.most_common(1)[0][0] if categories else None
    }

def create_sample_data() -> pd.DataFrame:
    """Create sample template data for demonstration."""
    sample_data = {
        'Number': [1, 2, 3, 4, 5],
        'Title': [
            'Login Form',
            'Dashboard Layout',
            'API Endpoint',
            'Data Visualization',
            'Contact Form'
        ],
        'Category': ['HTML/CSS', 'React', 'Python', 'JavaScript', 'HTML/CSS'],
        'Description': [
            'Modern login form with validation',
            'Responsive dashboard with sidebar',
            'RESTful API endpoint with authentication',
            'Interactive chart using D3.js',
            'Contact form with email integration'
        ],
        'Code': [
            '<form class="login-form">\n  <input type="email" placeholder="Email">\n  <input type="password" placeholder="Password">\n  <button type="submit">Login</button>\n</form>',
            'import React from "react";\n\nconst Dashboard = () => {\n  return <div className="dashboard">...</div>;\n};',
            'from flask import Flask, jsonify\n\napp = Flask(__name__)\n\n@app.route("/api/data")\ndef get_data():\n    return jsonify({"status": "success"})',
            'const data = [10, 20, 30, 40, 50];\nd3.select("svg")\n  .selectAll("rect")\n  .data(data)\n  .enter()\n  .append("rect");',
            '<form class="contact-form">\n  <input type="text" placeholder="Name">\n  <input type="email" placeholder="Email">\n  <textarea placeholder="Message"></textarea>\n  <button type="submit">Send</button>\n</form>'
        ]
    }
    return pd.DataFrame(sample_data)

# Sidebar
with st.sidebar:
    st.markdown("### 📝 Code Template Manager")
    st.markdown("---")
    
    # Google Sheets Credentials Upload
    st.markdown("#### 🔐 Google Sheets Connection")
    
    uploaded_file = st.file_uploader(
        "Upload Service Account JSON",
        type=['json'],
        help="Upload your Google Cloud service account credentials"
    )
    
    if uploaded_file is not None:
        try:
            credentials = json.load(uploaded_file)
            st.session_state.gsheet_credentials = credentials
            st.success(f"✅ Connected as: {credentials.get('client_email', 'Unknown')[:30]}...")
        except Exception as e:
            st.error(f"❌ Invalid JSON file: {str(e)}")
    
    if st.session_state.gsheet_credentials:
        st.info(f"📧 Service Account: {st.session_state.gsheet_credentials.get('client_email', 'Unknown')[:30]}...")
    
    st.markdown("---")
    
    # Data Management
    st.markdown("#### 📊 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Sync from Sheets", use_container_width=True):
            with st.spinner("Fetching data..."):
                df = fetch_google_sheets_data()
                if df is not None:
                    st.session_state.templates_data = df
                    st.success("✅ Synced!")
                    st.rerun()
    
    with col2:
        if st.button("📤 Push to Sheets", use_container_width=True):
            if st.session_state.templates_data is not None:
                with st.spinner("Pushing data..."):
                    if push_to_google_sheets(st.session_state.templates_data):
                        st.success("✅ Pushed!")
                    else:
                        st.error("❌ Push failed")
            else:
                st.warning("No data to push")
    
    if st.button("📋 Load Sample Data", use_container_width=True):
        st.session_state.templates_data = create_sample_data()
        st.success("✅ Sample data loaded!")
        st.rerun()
    
    if st.session_state.last_sync:
        st.caption(f"Last sync: {st.session_state.last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
    
    st.markdown("---")
    
    # Export/Import
    st.markdown("#### 💾 Import/Export")
    
    if st.session_state.templates_data is not None:
        json_data = export_to_json(st.session_state.templates_data)
        st.download_button(
            label="📥 Export JSON",
            data=json_data,
            file_name=f"templates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
        
        csv_data = st.session_state.templates_data.to_csv(index=False)
        st.download_button(
            label="📊 Export CSV",
            data=csv_data,
            file_name=f"templates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    json_upload = st.file_uploader("Import JSON", type=['json'])
    if json_upload:
        imported_df = import_from_json(json_upload.read().decode())
        if imported_df is not None:
            st.session_state.templates_data = imported_df
            st.success("✅ Imported successfully!")
            st.rerun()
    
    st.markdown("---")
    
    # Statistics
    if st.session_state.templates_data is not None:
        stats = get_statistics(st.session_state.templates_data)
        
        st.markdown("#### 📈 Quick Stats")
        st.metric("Total Templates", stats['total_templates'])
        st.metric("Categories", len(stats['categories']))
        if stats['most_common_category']:
            st.metric("Most Used", stats['most_common_category'])

# Main Content
st.markdown('<div class="main-header">📝 Code Template Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Manage, edit, and view your code templates with live Google Sheets sync</div>', unsafe_allow_html=True)

# Check if data is loaded
if st.session_state.templates_data is None:
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    ### 👋 Welcome to Code Template Manager!
    
    **To get started:**
    1. Upload your Google Cloud service account JSON in the sidebar
    2. Click "Sync from Sheets" to load your templates
    3. Or click "Load Sample Data" to see how it works
    
    **Features:**
    - 📊 Spreadsheet-style view and editing
    - 🔍 Advanced search and filtering
    - 👁️ Live code preview
    - 📤 Sync with Google Sheets
    - 💾 Import/Export JSON and CSV
    - 📈 Analytics and visualizations
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

df = st.session_state.templates_data

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Sheet View",
    "✏️ Editor",
    "👁️ Preview",
    "📈 Analytics",
    "⚙️ Bulk Operations"
])

# Tab 1: Sheet View
with tab1:
    st.markdown("### 📊 Template Sheet View")
    
    # Search and Filter
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search templates",
            value=st.session_state.search_query,
            placeholder="Search by title, description, or code...",
            key="search_input"
        )
        st.session_state.search_query = search_query
    
    with col2:
        if 'Category' in df.columns:
            categories = ["All"] + sorted(df['Category'].unique().tolist())
            filter_category = st.selectbox(
                "Category Filter",
                categories,
                index=categories.index(st.session_state.filter_category) if st.session_state.filter_category in categories else 0
            )
            st.session_state.filter_category = filter_category
        else:
            filter_category = "All"
    
    with col3:
        sort_by = st.selectbox(
            "Sort By",
            ["Number", "Title", "Category"] if 'Category' in df.columns else ["Number", "Title"]
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    if search_query:
        mask = filtered_df.apply(
            lambda row: search_query.lower() in str(row).lower(),
            axis=1
        )
        filtered_df = filtered_df[mask]
    
    if filter_category != "All" and 'Category' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Category'] == filter_category]
    
    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(sort_by)
    
    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} templates**")
    
    # Display data in editable format
    if len(filtered_df) > 0:
        # Category color coding
        if 'Category' in filtered_df.columns:
            category_colors = get_category_colors()
            
            st.markdown("**Categories:**")
            for cat in sorted(filtered_df['Category'].unique()):
                color = category_colors.get(cat, "#95a5a6")
                st.markdown(
                    f'<span class="category-badge" style="background-color: {color}; color: white;">{cat}</span>',
                    unsafe_allow_html=True
                )
        
        st.markdown("---")
        
        # Display each template as a card
        for idx, row in filtered_df.iterrows():
            with st.expander(f"**{row.get('Number', idx)}. {row.get('Title', 'Untitled')}**"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Category:** {row.get('Category', 'N/A')}")
                    st.markdown(f"**Description:** {row.get('Description', 'No description')}")
                    
                    if 'Code' in row:
                        st.markdown("**Code Preview:**")
                        code_preview = format_code_for_display(str(row['Code']), max_lines=10)
                        st.code(code_preview, language='python')
                        
                        st.text(f"Total lines: {len(str(row['Code']).split(chr(10)))}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{idx}", use_container_width=True):
                        st.session_state.selected_template = idx
                        st.session_state.edit_mode = True
                        st.rerun()
                    
                    if st.button("👁️ Preview", key=f"preview_{idx}", use_container_width=True):
                        st.session_state.selected_template = idx
                        st.session_state.show_preview = True
                        st.rerun()
                    
                    if st.button("🗑️ Delete", key=f"delete_{idx}", use_container_width=True):
                        st.session_state.templates_data = st.session_state.templates_data.drop(idx).reset_index(drop=True)
                        st.success("Template deleted!")
                        st.rerun()
                    
                    if 'Code' in row:
                        st.download_button(
                            label="💾 Download",
                            data=str(row['Code']),
                            file_name=f"{row.get('Title', 'template').replace(' ', '_')}.txt",
                            mime="text/plain",
                            key=f"download_{idx}",
                            use_container_width=True
                        )
    else:
        st.info("No templates found matching your criteria.")

# Tab 2: Editor
with tab2:
    st.markdown("### ✏️ Template Editor")
    
    if st.session_state.selected_template is not None and st.session_state.edit_mode:
        idx = st.session_state.selected_template
        
        if idx in df.index:
            template = df.loc[idx]
            
            st.markdown(f"**Editing Template #{template.get('Number', idx)}**")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                new_title = st.text_input("Title", value=str(template.get('Title', '')))
                new_description = st.text_area("Description", value=str(template.get('Description', '')), height=100)
                new_code = st.text_area("Code", value=str(template.get('Code', '')), height=400)
            
            with col2:
                if 'Category' in df.columns:
                    categories = sorted(df['Category'].unique().tolist())
                    current_category = str(template.get('Category', ''))
                    category_index = categories.index(current_category) if current_category in categories else 0
                    new_category = st.selectbox("Category", categories, index=category_index)
                else:
                    new_category = st.text_input("Category", value=str(template.get('Category', '')))
                
                st.markdown("---")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if st.button("💾 Save", use_container_width=True):
                        st.session_state.templates_data.at[idx, 'Title'] = new_title
                        st.session_state.templates_data.at[idx, 'Description'] = new_description
                        st.session_state.templates_data.at[idx, 'Code'] = new_code
                        if 'Category' in st.session_state.templates_data.columns:
                            st.session_state.templates_data.at[idx, 'Category'] = new_category
                        
                        st.success("✅ Template saved!")
                        st.session_state.edit_mode = False
                        st.rerun()
                
                with col_b:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.session_state.edit_mode = False
                        st.rerun()
                
                st.markdown("---")
                
                st.markdown("**Quick Actions:**")
                
                if st.button("📋 Copy Code", use_container_width=True):
                    st.code(new_code, language='python')
                    st.info("Code displayed above - use browser copy function")
                
                line_count = len(new_code.split('\n'))
                char_count = len(new_code)
                st.metric("Lines", line_count)
                st.metric("Characters", char_count)
        else:
            st.warning("Template not found. It may have been deleted.")
            st.session_state.edit_mode = False
    else:
        st.info("Select a template from the Sheet View to edit it.")
        
        # Add new template section
        st.markdown("---")
        st.markdown("### ➕ Add New Template")
        
        with st.form("new_template_form"):
            new_title = st.text_input("Title")
            
            if 'Category' in df.columns:
                categories = [""] + sorted(df['Category'].unique().tolist())
                new_category = st.selectbox("Category", categories)
            else:
                new_category = st.text_input("Category")
            
            new_description = st.text_area("Description", height=100)
            new_code = st.text_area("Code", height=300)
            
            submitted = st.form_submit_button("➕ Add Template")
            
            if submitted:
                if new_title and new_code:
                    new_number = df['Number'].max() + 1 if 'Number' in df.columns else len(df) + 1
                    
                    new_row = {
                        'Number': new_number,
                        'Title': new_title,
                        'Category': new_category,
                        'Description': new_description,
                        'Code': new_code
                    }
                    
                    st.session_state.templates_data = pd.concat([
                        st.session_state.templates_data,
                        pd.DataFrame([new_row])
                    ], ignore_index=True)
                    
                    st.success("✅ Template added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in at least Title and Code fields")

# Tab 3: Preview
with tab3:
    st.markdown("### 👁️ Code Preview")
    
    if st.session_state.selected_template is not None and st.session_state.show_preview:
        idx = st.session_state.selected_template
        
        if idx in df.index:
            template = df.loc[idx]
            
            st.markdown(f"## {template.get('Title', 'Untitled')}")
            st.markdown(f"**Category:** {template.get('Category', 'N/A')}")
            st.markdown(f"**Description:** {template.get('Description', 'No description')}")
            
            st.markdown("---")
            
            tab_a, tab_b, tab_c = st.tabs(["📝 Code", "🌐 Rendered (HTML)", "📊 Statistics"])
            
            with tab_a:
                code = str(template.get('Code', ''))
                
                # Detect language
                language = 'python'
                if template.get('Category') == 'HTML/CSS':
                    language = 'html'
                elif template.get('Category') == 'JavaScript':
                    language = 'javascript'
                elif template.get('Category') == 'React':
                    language = 'jsx'
                
                st.code(code, language=language)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Lines", len(code.split('\n')))
                with col2:
                    st.metric("Characters", len(code))
                with col3:
                    st.metric("Words", len(code.split()))
            
            with tab_b:
                if template.get('Category') in ['HTML/CSS', 'JavaScript', 'React']:
                    st.markdown("**Rendered Output:**")
                    st.components.v1.html(str(template.get('Code', '')), height=600, scrolling=True)
                else:
                    st.info("HTML rendering is only available for HTML/CSS, JavaScript, and React templates.")
            
            with tab_c:
                code = str(template.get('Code', ''))
                
                # Code statistics
                lines = code.split('\n')
                non_empty_lines = [l for l in lines if l.strip()]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Lines", len(lines))
                    st.metric("Non-Empty Lines", len(non_empty_lines))
                    st.metric("Empty Lines", len(lines) - len(non_empty_lines))
                
                with col2:
                    st.metric("Characters", len(code))
                    st.metric("Characters (no spaces)", len(code.replace(' ', '')))
                    st.metric("Words", len(code.split()))
                
                # Line length distribution
                line_lengths = [len(line) for line in lines]
                fig = px.histogram(
                    x=line_lengths,
                    nbins=30,
                    title="Line Length Distribution",
                    labels={'x': 'Line Length', 'y': 'Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            if st.button("❌ Close Preview"):
                st.session_state.show_preview = False
                st.rerun()
        else:
            st.warning("Template not found.")
            st.session_state.show_preview = False
    else:
        st.info("Select a template from the Sheet View to preview it.")
        
        # Show all templates in a gallery view
        st.markdown("---")
        st.markdown("### 🖼️ Template Gallery")
        
        cols_per_row = 3
        for i in range(0, len(df), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(df):
                    idx = df.index[i + j]
                    row = df.loc[idx]
                    
                    with col:
                        st.markdown(f"**{row.get('Title', 'Untitled')}**")
                        st.caption(row.get('Category', 'N/A'))
                        
                        code_preview = format_code_for_display(str(row.get('Code', '')), max_lines=5)
                        st.code(code_preview, language='python')
                        
                        if st.button("👁️ View", key=f"gallery_view_{idx}", use_container_width=True):
                            st.session_state.selected_template = idx
                            st.session_state.show_preview = True
                            st.rerun()

# Tab 4: Analytics
with tab4:
    st.markdown("### 📈 Template Analytics")
    
    stats = get_statistics(df)
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{stats["total_templates"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Total Templates</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{len(stats["categories"])}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Categories</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{int(stats["avg_code_length"]):,}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Avg Code Length</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{int(stats["total_code_length"]):,}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Total Characters</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if stats['categories']:
            # Category distribution pie chart
            fig = px.pie(
                values=list(stats['categories'].values()),
                names=list(stats['categories'].keys()),
                title='Templates by Category',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'Code' in df.columns:
            # Code length by template bar chart
            code_lengths = df['Code'].apply(len).tolist()
            titles = df['Title'].tolist() if 'Title' in df.columns else [f"Template {i+1}" for i in range(len(df))]
            
            fig = px.bar(
                x=titles,
                y=code_lengths,
                title='Code Length by Template',
                labels={'x': 'Template', 'y': 'Characters'},
                color=code_lengths,
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Timeline or trends (if we had timestamp data)
    if 'Code' in df.columns and 'Category' in df.columns:
        st.markdown("---")
        st.markdown("### 📊 Category Statistics")
        
        category_stats = df.groupby('Category').agg({
            'Code': ['count', lambda x: x.apply(len).mean(), lambda x: x.apply(len).sum()]
        }).round(0)
        
        category_stats.columns = ['Count', 'Avg Length', 'Total Length']
        category_stats = category_stats.reset_index()
        
        st.dataframe(category_stats, use_container_width=True)

# Tab 5: Bulk Operations
with tab5:
    st.markdown("### ⚙️ Bulk Operations")
    
    st.markdown("**Perform operations on multiple templates at once**")
    
    # Select templates for bulk operations
    st.markdown("#### 1️⃣ Select Templates")
    
    if 'Title' in df.columns:
        selected_indices = st.multiselect(
            "Choose templates",
            options=df.index.tolist(),
            format_func=lambda x: f"{df.loc[x, 'Number']}. {df.loc[x, 'Title']}" if 'Number' in df.columns else f"{df.loc[x, 'Title']}"
        )
    else:
        selected_indices = st.multiselect(
            "Choose templates",
            options=df.index.tolist(),
            format_func=lambda x: f"Template {x}"
        )
    
    if selected_indices:
        st.success(f"✅ {len(selected_indices)} templates selected")
        
        st.markdown("---")
        st.markdown("#### 2️⃣ Choose Operation")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🏷️ Change Category**")
            if 'Category' in df.columns:
                categories = sorted(df['Category'].unique().tolist())
                new_category = st.selectbox("New category", categories, key="bulk_category")
                
                if st.button("Apply Category Change", use_container_width=True):
                    for idx in selected_indices:
                        st.session_state.templates_data.at[idx, 'Category'] = new_category
                    st.success(f"✅ Updated {len(selected_indices)} templates!")
                    st.rerun()
        
        with col2:
            st.markdown("**💾 Export Selected**")
            
            selected_df = df.loc[selected_indices]
            
            json_export = export_to_json(selected_df)
            st.download_button(
                label="📥 Download JSON",
                data=json_export,
                file_name=f"selected_templates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
            
            csv_export = selected_df.to_csv(index=False)
            st.download_button(
                label="📊 Download CSV",
                data=csv_export,
                file_name=f"selected_templates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col3:
            st.markdown("**🗑️ Delete Selected**")
            st.warning(f"This will delete {len(selected_indices)} templates")
            
            if st.button("🗑️ Confirm Delete", use_container_width=True):
                st.session_state.templates_data = st.session_state.templates_data.drop(selected_indices).reset_index(drop=True)
                st.success(f"✅ Deleted {len(selected_indices)} templates!")
                st.rerun()
        
        st.markdown("---")
        
        # Preview selected templates
        st.markdown("#### 📋 Selected Templates Preview")
        
        for idx in selected_indices:
            row = df.loc[idx]
            with st.expander(f"{row.get('Number', idx)}. {row.get('Title', 'Untitled')}"):
                st.markdown(f"**Category:** {row.get('Category', 'N/A')}")
                st.markdown(f"**Description:** {row.get('Description', 'No description')}")
                if 'Code' in row:
                    st.code(format_code_for_display(str(row['Code']), max_lines=5), language='python')
    else:
        st.info("Select one or more templates above to perform bulk operations.")
    
    st.markdown("---")
    
    # Other bulk operations
    st.markdown("#### 🔧 Other Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔄 Re-number Templates**")
        st.info("This will reset all template numbers to sequential order (1, 2, 3...)")
        
        if st.button("Re-number All Templates"):
            if 'Number' in st.session_state.templates_data.columns:
                st.session_state.templates_data['Number'] = range(1, len(st.session_state.templates_data) + 1)
                st.success("✅ Templates re-numbered!")
                st.rerun()
    
    with col2:
        st.markdown("**🧹 Clean Data**")
        st.info("Remove empty rows and reset index")
        
        if st.button("Clean Data"):
            # Remove rows where all values are empty
            st.session_state.templates_data = st.session_state.templates_data.dropna(how='all').reset_index(drop=True)
            st.success("✅ Data cleaned!")
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p>📝 Code Template Dashboard | Built with Streamlit | 
    <a href='https://github.com' target='_blank'>View on GitHub</a></p>
</div>
""", unsafe_allow_html=True)
