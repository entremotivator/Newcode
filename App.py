import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Code Template Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 900;
        color: #1a1a1a;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    
    .editable-table {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'templates_data' not in st.session_state:
    st.session_state.templates_data = pd.DataFrame({
        "Number": [1, 2, 3],
        "Title": ["Landing Page", "Dashboard UI", "Contact Form"],
        "Category": ["HTML/CSS", "HTML/CSS", "HTML/CSS"],
        "Description": ["Modern landing page", "Analytics dashboard", "Contact form with validation"],
        "Code": ["<html>...</html>", "<html>...</html>", "<html>...</html>"]
    })

if 'selected_row' not in st.session_state:
    st.session_state.selected_row = None

if 'gcp_credentials' not in st.session_state:
    st.session_state.gcp_credentials = None

if 'sheet_connected' not in st.session_state:
    st.session_state.sheet_connected = False

# ============================================================================
# CONFIGURATION
# ============================================================================

GOOGLE_SHEETS_ID = "1eFZcnDoGT2NJHaEQSgxW5psN5kvlkYx1vtuXGRFTGTk"
GOOGLE_SHEETS_SHEET_NAME = "demo_examples"

# ============================================================================
# GOOGLE SHEETS FUNCTIONS
# ============================================================================

def fetch_google_sheets_data() -> Optional[pd.DataFrame]:
    """Fetch data from Google Sheets using credentials."""
    try:
        if st.session_state.gcp_credentials is None:
            st.warning("Please upload Google Cloud credentials first.")
            return None
        
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.session_state.gcp_credentials,
            scope
        )
        
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = sheet.worksheet(GOOGLE_SHEETS_SHEET_NAME)
        
        data = worksheet.get_all_records()
        
        if data:
            df = pd.DataFrame(data)
            st.session_state.sheet_connected = True
            return df
        else:
            return None
    
    except Exception as e:
        st.error(f"Error fetching Google Sheets data: {str(e)}")
        return None

def save_to_google_sheets(df: pd.DataFrame) -> bool:
    """Save DataFrame to Google Sheets."""
    try:
        if st.session_state.gcp_credentials is None:
            st.warning("Please upload Google Cloud credentials first.")
            return False
        
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.session_state.gcp_credentials,
            scope
        )
        
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = sheet.worksheet(GOOGLE_SHEETS_SHEET_NAME)
        
        worksheet.clear()
        
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        
        return True
    
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {str(e)}")
        return False

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### 📊 Template Dashboard")
    st.markdown("---")
    
    st.markdown("### 🔑 Google Cloud Credentials")
    
    uploaded_file = st.file_uploader(
        "Upload Service Account JSON",
        type=['json'],
        help="Upload your Google Cloud service account credentials"
    )
    
    if uploaded_file is not None:
        try:
            credentials = json.load(uploaded_file)
            st.session_state.gcp_credentials = credentials
            st.success("Credentials loaded!")
            st.caption(f"Service Account: {credentials.get('client_email', 'N/A')}")
        except Exception as e:
            st.error(f"Invalid JSON file: {str(e)}")
    
    st.markdown("---")
    
    if st.session_state.gcp_credentials:
        if st.button("🔄 Sync with Google Sheets", use_container_width=True):
            with st.spinner("Fetching from Google Sheets..."):
                fetched_data = fetch_google_sheets_data()
                if fetched_data is not None:
                    st.session_state.templates_data = fetched_data
                    st.success(f"Loaded {len(fetched_data)} rows!")
                    st.rerun()
        
        if st.button("💾 Save to Google Sheets", use_container_width=True):
            with st.spinner("Saving to Google Sheets..."):
                if save_to_google_sheets(st.session_state.templates_data):
                    st.success("Saved successfully!")
                    time.sleep(1)
                    st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 📂 Actions")
    
    if st.button("➕ Add New Template", use_container_width=True):
        new_row = pd.DataFrame({
            "Number": [len(st.session_state.templates_data) + 1],
            "Title": ["New Template"],
            "Category": ["HTML/CSS"],
            "Description": ["Description here"],
            "Code": ["<html></html>"]
        })
        st.session_state.templates_data = pd.concat([st.session_state.templates_data, new_row], ignore_index=True)
        st.rerun()
    
    if st.button("🗑️ Clear All Data", use_container_width=True):
        st.session_state.templates_data = pd.DataFrame(columns=["Number", "Title", "Category", "Description", "Code"])
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 📥 Import/Export")
    
    uploaded_json = st.file_uploader("Import JSON", type=['json'], key="json_import")
    
    if uploaded_json is not None:
        try:
            data = json.load(uploaded_json)
            st.session_state.templates_data = pd.DataFrame(data)
            st.success("JSON imported!")
            st.rerun()
        except Exception as e:
            st.error(f"Invalid JSON: {str(e)}")
    
    if len(st.session_state.templates_data) > 0:
        json_export = st.session_state.templates_data.to_json(orient='records', indent=2)
        st.download_button(
            label="📥 Export JSON",
            data=json_export,
            file_name=f"templates_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.markdown('<div class="main-header">📊 Code Template Dashboard</div>', unsafe_allow_html=True)

if st.session_state.sheet_connected:
    st.success(f"✅ Connected to Google Sheets")
else:
    st.info("ℹ️ Upload credentials to connect to Google Sheets")

# Tabs
tab1, tab2, tab3 = st.tabs(["📋 Sheet View", "✏️ Editor", "📊 Analytics"])

# ============================================================================
# TAB 1: SHEET VIEW
# ============================================================================

with tab1:
    st.markdown("### 📋 Template Library")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search templates...", placeholder="Search by title, category, or description")
    
    with col2:
        categories = ["All"] + st.session_state.templates_data["Category"].unique().tolist()
        selected_category = st.selectbox("📂 Filter by Category", categories)
    
    filtered_df = st.session_state.templates_data.copy()
    
    if search_query:
        mask = (
            filtered_df["Title"].str.contains(search_query, case=False, na=False) |
            filtered_df["Category"].str.contains(search_query, case=False, na=False) |
            filtered_df["Description"].str.contains(search_query, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["Category"] == selected_category]
    
    st.markdown(f"**Showing {len(filtered_df)} of {len(st.session_state.templates_data)} templates**")
    
    st.markdown("---")
    
    if len(filtered_df) > 0:
        display_df = filtered_df[["Number", "Title", "Category", "Description"]].copy()
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        st.markdown("---")
        
        st.markdown("### 🎯 View Template Details")
        
        selected_number = st.selectbox(
            "Select template number to view:",
            filtered_df["Number"].tolist(),
            format_func=lambda x: f"#{x} - {filtered_df[filtered_df['Number'] == x]['Title'].iloc[0]}"
        )
        
        if selected_number:
            selected_template = filtered_df[filtered_df["Number"] == selected_number].iloc[0]
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown(f"**Title:** {selected_template['Title']}")
                st.markdown(f"**Category:** {selected_template['Category']}")
                st.markdown(f"**Description:** {selected_template['Description']}")
            
            with col2:
                code_length = len(selected_template['Code'])
                st.metric("Code Length", f"{code_length} chars")
                
                if st.button("✏️ Edit This Template", use_container_width=True):
                    st.session_state.selected_row = selected_number
                    st.rerun()
            
            st.markdown("### 💻 Code Preview")
            st.code(selected_template['Code'], language="html", line_numbers=True)
            
            st.download_button(
                label="📥 Download Code",
                data=selected_template['Code'],
                file_name=f"{selected_template['Title'].replace(' ', '_')}.html",
                mime="text/html",
                use_container_width=True
            )
    else:
        st.info("No templates found matching your search criteria.")

# ============================================================================
# TAB 2: EDITOR
# ============================================================================

with tab2:
    st.markdown("### ✏️ Template Editor")
    
    if st.session_state.selected_row is not None:
        row_index = st.session_state.templates_data[st.session_state.templates_data["Number"] == st.session_state.selected_row].index[0]
        current_data = st.session_state.templates_data.iloc[row_index]
        
        st.markdown(f"**Editing Template #{st.session_state.selected_row}**")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            title = st.text_input("Title", value=current_data["Title"])
        
        with col2:
            category = st.selectbox(
                "Category",
                ["HTML/CSS", "JavaScript", "Python", "React", "Other"],
                index=["HTML/CSS", "JavaScript", "Python", "React", "Other"].index(current_data["Category"]) if current_data["Category"] in ["HTML/CSS", "JavaScript", "Python", "React", "Other"] else 0
            )
        
        description = st.text_area("Description", value=current_data["Description"], height=100)
        
        st.markdown("### 💻 Code Editor")
        code = st.text_area("Code", value=current_data["Code"], height=400)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save Changes", use_container_width=True, type="primary"):
                st.session_state.templates_data.at[row_index, "Title"] = title
                st.session_state.templates_data.at[row_index, "Category"] = category
                st.session_state.templates_data.at[row_index, "Description"] = description
                st.session_state.templates_data.at[row_index, "Code"] = code
                st.success("Changes saved!")
                time.sleep(1)
                st.rerun()
        
        with col2:
            if st.button("🗑️ Delete Template", use_container_width=True):
                st.session_state.templates_data = st.session_state.templates_data[st.session_state.templates_data["Number"] != st.session_state.selected_row].reset_index(drop=True)
                st.session_state.selected_row = None
                st.rerun()
        
        with col3:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.selected_row = None
                st.rerun()
        
        st.markdown("---")
        
        st.markdown("### 👁️ Live Preview")
        
        if category in ["HTML/CSS", "JavaScript", "React"]:
            with st.expander("View HTML Preview", expanded=False):
                st.components.v1.html(code, height=400, scrolling=True)
        else:
            st.code(code, language="python" if category == "Python" else "html")
    
    else:
        st.info("Select a template from the Sheet View to edit, or create a new one from the sidebar.")
        
        if st.button("➕ Create New Template", use_container_width=True, type="primary"):
            new_number = len(st.session_state.templates_data) + 1
            new_row = pd.DataFrame({
                "Number": [new_number],
                "Title": ["New Template"],
                "Category": ["HTML/CSS"],
                "Description": ["Description here"],
                "Code": ["<html>\n  <head>\n    <title>New Template</title>\n  </head>\n  <body>\n    <h1>Hello World</h1>\n  </body>\n</html>"]
            })
            st.session_state.templates_data = pd.concat([st.session_state.templates_data, new_row], ignore_index=True)
            st.session_state.selected_row = new_number
            st.rerun()

# ============================================================================
# TAB 3: ANALYTICS
# ============================================================================

with tab3:
    st.markdown("### 📊 Template Analytics")
    
    if len(st.session_state.templates_data) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="metric-card"><div style="font-size: 0.9rem;">Total Templates</div><div style="font-size: 2rem; font-weight: 900;">{len(st.session_state.templates_data)}</div></div>', unsafe_allow_html=True)
        
        with col2:
            categories_count = st.session_state.templates_data["Category"].nunique()
            st.markdown(f'<div class="metric-card"><div style="font-size: 0.9rem;">Categories</div><div style="font-size: 2rem; font-weight: 900;">{categories_count}</div></div>', unsafe_allow_html=True)
        
        with col3:
            avg_code_length = st.session_state.templates_data["Code"].str.len().mean()
            st.markdown(f'<div class="metric-card"><div style="font-size: 0.9rem;">Avg Code Length</div><div style="font-size: 2rem; font-weight: 900;">{int(avg_code_length)}</div></div>', unsafe_allow_html=True)
        
        with col4:
            total_code_length = st.session_state.templates_data["Code"].str.len().sum()
            st.markdown(f'<div class="metric-card"><div style="font-size: 0.9rem;">Total Code</div><div style="font-size: 2rem; font-weight: 900;">{total_code_length}</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📂 Templates by Category")
            
            category_counts = st.session_state.templates_data["Category"].value_counts()
            
            fig_category = go.Figure(data=[
                go.Pie(
                    labels=category_counts.index,
                    values=category_counts.values,
                    hole=0.3
                )
            ])
            
            fig_category.update_layout(height=350)
            st.plotly_chart(fig_category, use_container_width=True)
        
        with col2:
            st.markdown("#### 📏 Code Length Distribution")
            
            code_lengths = st.session_state.templates_data.copy()
            code_lengths["Code Length"] = code_lengths["Code"].str.len()
            
            fig_length = go.Figure(data=[
                go.Bar(
                    x=code_lengths["Title"],
                    y=code_lengths["Code Length"],
                    marker=dict(color=code_lengths["Code Length"], colorscale="Viridis")
                )
            ])
            
            fig_length.update_layout(
                xaxis_title="Template",
                yaxis_title="Code Length (chars)",
                height=350
            )
            st.plotly_chart(fig_length, use_container_width=True)
        
        st.markdown("---")
        
        st.markdown("#### 📋 Full Data Table")
        
        analytics_df = st.session_state.templates_data.copy()
        analytics_df["Code Length"] = analytics_df["Code"].str.len()
        
        st.dataframe(
            analytics_df[["Number", "Title", "Category", "Code Length"]],
            use_container_width=True,
            hide_index=True
        )
    
    else:
        st.info("No data available for analytics. Add some templates to see statistics!")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; padding: 20px;">
    <p>📊 Code Template Dashboard | Built with Streamlit</p>
    <p>Connected to Google Sheets for live sync</p>
</div>
""", unsafe_allow_html=True)
