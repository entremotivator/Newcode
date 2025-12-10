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
    page_title="AI Code Generator Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING & THEME
# ============================================================================

st.markdown("""
<style>
    /* Main color scheme */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --accent-color: #f093fb;
        --success-color: #00d4ff;
        --error-color: #ff6b6b;
        --warning-color: #ffd93d;
    }
    
    /* Main header styling */
    .main-header {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1.5rem;
        text-align: center;
        letter-spacing: -1px;
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Agent badge styling */
    .agent-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
        margin: 5px 5px 5px 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .category-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 15px;
        font-size: 0.85rem;
        display: inline-block;
        margin: 5px 5px 5px 0;
    }
    
    /* Code preview styling */
    .code-preview {
        background: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        margin-top: 10px;
        border-left: 4px solid #667eea;
        font-family: 'Courier New', monospace;
        overflow-x: auto;
    }
    
    /* Message styling */
    .success-message {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #28a745;
        color: #155724;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        font-weight: 500;
    }
    
    .error-message {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 2px solid #dc3545;
        color: #721c24;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        font-weight: 500;
    }
    
    .info-message {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 2px solid #0c5460;
        color: #0c5460;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        font-weight: 500;
    }
    
    /* Metric card styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 900;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 10px 10px 0 0;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border-radius: 10px;
    }
    
    /* Sidebar styling */
    .sidebar-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        border-left: 4px solid #667eea;
    }
    
    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 10px;
    }
    
    /* Data table styling */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        color: #999;
        padding: 20px;
        margin-top: 40px;
        border-top: 1px solid #e0e0e0;
        font-size: 0.9rem;
    }
    
    /* Loading animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

N8N_WEBHOOK_URL = "https://agentonline-u29564.vm.elestio.app/webhook-test/Streamlitagentform1"
GOOGLE_SHEETS_ID = "1eFZcnDoGT2NJHaEQSgxW5psN5kvlkYx1vtuXGRFTGTk"
GOOGLE_SHEETS_SHEET_NAME = "demo_examples"

# Agent categories with descriptions
AGENT_CATEGORIES = {
    "HTML/CSS Generators": [
        ("🌐 Landing Page Generator", "Landing Page HTML/CSS Generator"),
        ("📊 Dashboard Generator", "Dashboard HTML/CSS Generator"),
        ("📝 Form Generator", "Form HTML/CSS Generator"),
        ("💼 Portfolio Generator", "Portfolio HTML/CSS Generator"),
        ("🔗 API Integration Generator", "API Integration HTML Generator"),
        ("🛒 E-commerce Page Generator", "E-commerce Page HTML Generator")
    ],
    "Python/Streamlit Generators": [
        ("📈 Data App Generator", "Streamlit Data App Generator"),
        ("🤖 ML App Generator", "Streamlit ML App Generator"),
        ("📊 Dashboard App Generator", "Streamlit Dashboard Generator"),
        ("📋 Form App Generator", "Streamlit Form App Generator")
    ]
}

EXAMPLE_PROMPTS = [
    "Create a modern landing page for a SaaS product with pricing table",
    "Build a dashboard to visualize sales data with real-time updates",
    "Generate a contact form with email validation and file upload",
    "Make a Streamlit app for data analysis with CSV upload",
    "Create an ML app for image classification predictions",
    "Build an e-commerce product page with shopping cart",
    "Generate a portfolio website showcasing projects",
    "Create a Streamlit dashboard for financial analytics"
]

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'generated_codes' not in st.session_state:
        st.session_state.generated_codes = []
    if 'current_code' not in st.session_state:
        st.session_state.current_code = None
    if 'current_agent' not in st.session_state:
        st.session_state.current_agent = None
    if 'current_category' not in st.session_state:
        st.session_state.current_category = None
    if 'gsheet_data' not in st.session_state:
        st.session_state.gsheet_data = None
    if 'last_gsheet_update' not in st.session_state:
        st.session_state.last_gsheet_update = None
    if 'api_response_time' not in st.session_state:
        st.session_state.api_response_time = 0

initialize_session_state()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def fetch_google_sheets_data() -> Optional[pd.DataFrame]:
    """
    Fetch all data from Google Sheets using gspread.
    
    Returns:
        DataFrame with all generated codes and metadata, or None if fetch fails.
    """
    try:
        # Define the scope for Google Sheets and Google Drive
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Check if secrets are configured
        if "gcp_service_account" not in st.secrets:
            st.error("""
### Google Sheets Configuration Required

To connect to Google Sheets, you need to:

1. Create a Google Cloud Project
2. Enable Google Sheets API and Google Drive API
3. Create a Service Account and download the JSON credentials
4. Share your Google Sheet with the service account email
5. Add the credentials to `.streamlit/secrets.toml`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```            """)
            return None
        
        # Create credentials from secrets
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"],
            scope
        )
        
        # Authorize and create client
        client = gspread.authorize(creds)
        
        # Open the Google Sheet
        try:
            sheet = client.open_by_key(GOOGLE_SHEETS_ID)
        except gspread.exceptions.SpreadsheetNotFound:
            st.error(f"Sheet with ID '{GOOGLE_SHEETS_ID}' not found. Make sure the sheet is shared with the service account email.")
            return None
        
        # Get the specific worksheet
        try:
            worksheet = sheet.worksheet(GOOGLE_SHEETS_SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"Worksheet '{GOOGLE_SHEETS_SHEET_NAME}' not found in the sheet.")
            return None
        
        # Get all values from the worksheet
        data = worksheet.get_all_records()
        
        # Convert to DataFrame
        if data:
            df = pd.DataFrame(data)
            st.session_state.last_gsheet_update = datetime.now()
            return df
        else:
            st.info("The Google Sheet is empty or has no data rows.")
            return None
    
    except Exception as e:
        st.error(f"Error fetching Google Sheets data: {str(e)}")
        return None

def send_to_n8n(user_input: str) -> Dict[str, Any]:
    """
    Send user request to n8n webhook and get response.
    
    Args:
        user_input: The user's code generation request
        
    Returns:
        Dictionary with response data or error information
    """
    try:
        start_time = time.time()
        
        response = requests.post(
            N8N_WEBHOOK_URL,
            json={"chatInput": user_input},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        st.session_state.api_response_time = time.time() - start_time
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "message": f"N8N returned status code {response.status_code}"
            }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Timeout",
            "message": "Request timed out. Code generation took too long. Please try again."
        }
    
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Connection Error",
            "message": "Could not connect to N8N. Please check the webhook URL and try again."
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": "Unknown Error",
            "message": f"An error occurred: {str(e)}"
        }

def test_n8n_connection() -> bool:
    """Test connection to N8N webhook."""
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json={"chatInput": "test connection"},
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

def format_code_preview(code: str, language: str = "html", max_lines: int = 30) -> str:
    """
    Format code for preview display.
    
    Args:
        code: The code to format
        language: Programming language (html, python, javascript)
        max_lines: Maximum number of lines to show
        
    Returns:
        Formatted code string
    """
    lines = code.split('\n')
    if len(lines) > max_lines:
        return '\n'.join(lines[:max_lines]) + f"\n\n... ({len(lines) - max_lines} more lines)"
    return code

def get_code_statistics() -> Dict[str, Any]:
    """Calculate statistics from generated codes."""
    if not st.session_state.generated_codes:
        return {
            "total": 0,
            "html": 0,
            "python": 0,
            "avg_length": 0,
            "total_length": 0
        }
    
    codes = st.session_state.generated_codes
    html_count = sum(1 for c in codes if c['code_type'] == 'HTML/CSS/JS')
    python_count = sum(1 for c in codes if c['code_type'] == 'Python/Streamlit')
    total_length = sum(len(c['code']) for c in codes)
    
    return {
        "total": len(codes),
        "html": html_count,
        "python": python_count,
        "avg_length": total_length // len(codes) if codes else 0,
        "total_length": total_length
    }

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("---")
    st.markdown('<div class="sidebar-section"><div class="sidebar-title">🤖 AI Code Generator Hub</div></div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Agent categories section
    st.markdown('<div class="sidebar-title">📚 Available Agents</div>', unsafe_allow_html=True)
    
    for category, agents in AGENT_CATEGORIES.items():
        with st.expander(f"**{category}**", expanded=True):
            for emoji_name, full_name in agents:
                st.markdown(f"- {emoji_name}")
    
    st.markdown("---")
    
    # Example prompts section
    st.markdown('<div class="sidebar-title">💡 Quick Start Examples</div>', unsafe_allow_html=True)
    
    for i, prompt in enumerate(EXAMPLE_PROMPTS):
        if st.button(prompt, key=f"example_{i}", use_container_width=True):
            st.session_state.example_prompt = prompt
            st.rerun()
    
    st.markdown("---")
    
    # Settings section
    st.markdown('<div class="sidebar-title">⚙️ Settings</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        show_raw_response = st.checkbox("Raw Response", value=False, key="show_raw")
    with col2:
        auto_download = st.checkbox("Auto Download", value=False, key="auto_dl")
    
    st.markdown("---")
    
    # Code history section
    st.markdown('<div class="sidebar-title">📊 Statistics</div>', unsafe_allow_html=True)
    
    stats = get_code_statistics()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", stats['total'])
    with col2:
        st.metric("HTML/CSS", stats['html'])
    with col3:
        st.metric("Python", stats['python'])
    
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.generated_codes = []
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    # N8N Connection section
    st.markdown('<div class="sidebar-title">🔗 N8N Connection</div>', unsafe_allow_html=True)
    
    if st.button("🔌 Test Connection", use_container_width=True):
        with st.spinner("Testing connection..."):
            if test_n8n_connection():
                st.success("✅ Connected to N8N!")
            else:
                st.error("❌ Connection failed. Check webhook URL.")
    
    st.markdown(f"**Webhook:** `{N8N_WEBHOOK_URL[:50]}...`")
    
    st.markdown("---")
    
    # Data refresh section
    st.markdown('<div class="sidebar-title">📥 Google Sheets</div>', unsafe_allow_html=True)
    
    if st.button("🔄 Refresh Sheet Data", use_container_width=True):
        with st.spinner("Fetching data..."):
            st.session_state.gsheet_data = fetch_google_sheets_data()
            if st.session_state.gsheet_data is not None:
                st.success("Data refreshed!")
    
    if st.session_state.last_gsheet_update:
        st.caption(f"Last updated: {st.session_state.last_gsheet_update.strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Header
st.markdown('<div class="main-header">🚀 AI Code Generator Hub</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Generate production-ready code with AI-powered agents</div>', unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📋 Code Library", "📊 Analytics", "📥 Google Sheets"])

# ============================================================================
# TAB 1: CHAT INTERFACE
# ============================================================================

with tab1:
    st.markdown("### 💬 Code Generation Chat")
    st.markdown("Describe the code you want to generate and our AI agents will create it for you.")
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                if "code" in message and message["code"]:
                    with st.expander("📝 View Generated Code"):
                        code_lang = "python" if "Streamlit" in message.get("agent", "") else "html"
                        preview = format_code_preview(message["code"], code_lang)
                        st.code(preview, language=code_lang)
    
    # Chat input
    st.markdown("---")
    
    user_input = st.chat_input("Describe the code you want to generate...", key="chat_input")
    
    # Check for example prompt
    if st.session_state.get('example_prompt'):
        user_input = st.session_state.example_prompt
        del st.session_state.example_prompt
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤖 AI Agent is generating your code..."):
                result = send_to_n8n(user_input)
                
                if result.get("success", False):
                    agent_name = result.get('agent', 'Unknown Agent')
                    category = result.get('category', 'Unknown Category')
                    generated_code = result.get('code', 'No code generated')
                    
                    # Store current code
                    st.session_state.current_code = generated_code
                    st.session_state.current_agent = agent_name
                    st.session_state.current_category = category
                    
                    # Create response message
                    response_msg = f"""
### ✨ Code Generated Successfully!

**Agent Used:** `{agent_name}`  
**Category:** `{category}`  
**Response Time:** `{st.session_state.api_response_time:.2f}s`  
**Generated at:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

Your code has been generated and will be logged to Google Sheets.
"""
                    
                    st.markdown(response_msg)
                    
                    # Show code preview
                    with st.expander("📝 Code Preview", expanded=True):
                        code_lang = "python" if "Streamlit" in agent_name else "html"
                        preview = format_code_preview(generated_code, code_lang, max_lines=40)
                        st.code(preview, language=code_lang)
                    
                    # Download button
                    file_extension = ".py" if "Streamlit" in agent_name else ".html"
                    filename = f"generated_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
                    
                    st.download_button(
                        label=f"⬇️ Download {file_extension.upper()} File",
                        data=generated_code,
                        file_name=filename,
                        mime="text/plain",
                        use_container_width=True
                    )
                    
                    # Store in session state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_msg,
                        "code": generated_code,
                        "agent": agent_name,
                        "category": category
                    })
                    
                    st.session_state.generated_codes.append({
                        "timestamp": datetime.now(),
                        "prompt": user_input,
                        "agent": agent_name,
                        "category": category,
                        "code": generated_code,
                        "code_type": "Python/Streamlit" if "Streamlit" in agent_name else "HTML/CSS/JS"
                    })
                    
                    # Show raw response if enabled
                    if show_raw_response:
                        with st.expander("🔍 Raw API Response"):
                            st.json(result)
                    
                    st.success("✨ Code generation completed!")
                    st.rerun()
                
                else:
                    error_msg = result.get("message", "Unknown error occurred")
                    st.markdown(f'<div class="error-message">❌ {error_msg}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {error_msg}"})

# ============================================================================
# TAB 2: CODE LIBRARY
# ============================================================================

with tab2:
    st.markdown("### 📋 Generated Code Library")
    
    if st.session_state.current_code:
        st.markdown("#### 🎯 Latest Generated Code")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**Agent:** {st.session_state.current_agent}")
            st.markdown(f"**Category:** {st.session_state.current_category}")
        
        with col2:
            code_lang = "python" if "Streamlit" in st.session_state.current_agent else "html"
            file_ext = ".py" if code_lang == "python" else ".html"
        
        with col3:
            st.download_button(
                label="⬇️ Download",
                data=st.session_state.current_code,
                file_name=f"code_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}",
                mime="text/plain",
                use_container_width=True
            )
        
        st.code(st.session_state.current_code, language=code_lang)
        st.markdown("---")
    
    if st.session_state.generated_codes:
        st.markdown("#### 📚 All Generated Codes")
        
        # Search and filter
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("🔍 Search codes...", key="search_codes")
        with col2:
            filter_type = st.selectbox(
                "Filter by type:",
                ["All", "HTML/CSS/JS", "Python/Streamlit"],
                key="filter_type"
            )
        
        # Filter codes
        filtered_codes = st.session_state.generated_codes
        
        if search_term:
            filtered_codes = [
                c for c in filtered_codes
                if search_term.lower() in c['prompt'].lower() or
                   search_term.lower() in c['agent'].lower()
            ]
        
        if filter_type != "All":
            filtered_codes = [c for c in filtered_codes if c['code_type'] == filter_type]
        
        # Display filtered codes
        for idx, code_entry in enumerate(reversed(filtered_codes)):
            with st.expander(f"🔹 {code_entry['category']} - {code_entry['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                st.markdown(f"**Prompt:** {code_entry['prompt']}")
                st.markdown(f"**Agent:** {code_entry['agent']}")
                st.markdown(f"**Type:** {code_entry['code_type']}")
                st.markdown(f"**Code Length:** {len(code_entry['code'])} characters")
                
                code_lang = "python" if code_entry['code_type'] == "Python/Streamlit" else "html"
                preview = format_code_preview(code_entry['code'], code_lang, max_lines=50)
                st.code(preview, language=code_lang)
                
                file_ext = ".py" if code_lang == "python" else ".html"
                st.download_button(
                    label="⬇️ Download This Code",
                    data=code_entry['code'],
                    file_name=f"code_{idx}_{code_entry['timestamp'].strftime('%Y%m%d_%H%M%S')}{file_ext}",
                    mime="text/plain",
                    key=f"download_{idx}",
                    use_container_width=True
                )
    else:
        st.info("📭 No code has been generated yet. Start chatting to generate code!")

# ============================================================================
# TAB 3: ANALYTICS DASHBOARD
# ============================================================================

with tab3:
    st.markdown("### 📊 Generation Analytics Dashboard")
    
    if st.session_state.generated_codes:
        # Create DataFrame
        df = pd.DataFrame([{
            'Timestamp': entry['timestamp'],
            'Agent': entry['agent'],
            'Category': entry['category'],
            'Code Type': entry['code_type'],
            'Code Length': len(entry['code']),
            'Prompt Length': len(entry['prompt'])
        } for entry in st.session_state.generated_codes])
        
        # KPI Metrics
        st.markdown("#### 📈 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Total Generations</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
        
        with col2:
            html_count = len(df[df['Code Type'] == 'HTML/CSS/JS'])
            st.markdown(f'<div class="metric-card"><div class="metric-label">HTML/CSS</div><div class="metric-value">{html_count}</div></div>', unsafe_allow_html=True)
        
        with col3:
            python_count = len(df[df['Code Type'] == 'Python/Streamlit'])
            st.markdown(f'<div class="metric-card"><div class="metric-label">Python</div><div class="metric-value">{python_count}</div></div>', unsafe_allow_html=True)
        
        with col4:
            avg_length = df['Code Length'].mean()
            st.markdown(f'<div class="metric-card"><div class="metric-label">Avg Code Length</div><div class="metric-value">{int(avg_length)}</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Agent usage distribution
        st.markdown("#### 🤖 Agent Usage Distribution")
        
        agent_counts = df['Agent'].value_counts()
        
        fig_agent = go.Figure(data=[
            go.Bar(
                x=agent_counts.index,
                y=agent_counts.values,
                marker=dict(
                    color=agent_counts.values,
                    colorscale='Viridis',
                    showscale=True
                ),
                text=agent_counts.values,
                textposition='auto'
            )
        ])
        
        fig_agent.update_layout(
            title="Code Generations by Agent",
            xaxis_title="Agent Name",
            yaxis_title="Count",
            height=400,
            showlegend=False,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_agent, use_container_width=True)
        
        st.markdown("---")
        
        # Category breakdown
        st.markdown("#### 📂 Category Breakdown")
        
        category_counts = df['Category'].value_counts()
        
        fig_category = go.Figure(data=[
            go.Pie(
                labels=category_counts.index,
                values=category_counts.values,
                hole=0.3,
                marker=dict(colors=px.colors.qualitative.Set3)
            )
        ])
        
        fig_category.update_layout(
            title="Code Generations by Category",
            height=400
        )
        
        st.plotly_chart(fig_category, use_container_width=True)
        
        st.markdown("---")
        
        # Code type distribution
        st.markdown("#### 💻 Code Type Distribution")
        
        code_type_counts = df['Code Type'].value_counts()
        
        fig_type = go.Figure(data=[
            go.Bar(
                x=code_type_counts.index,
                y=code_type_counts.values,
                marker=dict(
                    color=['#667eea', '#764ba2']
                ),
                text=code_type_counts.values,
                textposition='auto'
            )
        ])
        
        fig_type.update_layout(
            title="Code Type Distribution",
            xaxis_title="Code Type",
            yaxis_title="Count",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_type, use_container_width=True)
        
        st.markdown("---")
        
        # Timeline
        st.markdown("#### 📅 Generation Timeline")
        
        df_sorted = df.sort_values('Timestamp')
        df_sorted['Date'] = df_sorted['Timestamp'].dt.date
        timeline_counts = df_sorted.groupby('Date').size()
        
        fig_timeline = go.Figure(data=[
            go.Scatter(
                x=timeline_counts.index,
                y=timeline_counts.values,
                mode='lines+markers',
                fill='tozeroy',
                marker=dict(size=8, color='#667eea'),
                line=dict(color='#667eea', width=3)
            )
        ])
        
        fig_timeline.update_layout(
            title="Generation Timeline",
            xaxis_title="Date",
            yaxis_title="Count",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        st.markdown("---")
        
        # Detailed history table
        st.markdown("#### 📋 Detailed History")
        
        display_df = df[['Timestamp', 'Agent', 'Category', 'Code Type', 'Code Length']].copy()
        display_df['Timestamp'] = display_df['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        
        # Export analytics
        st.markdown("#### 📥 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Analytics CSV",
                data=csv,
                file_name=f"code_generation_analytics_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            json_data = df.to_json(orient='records', date_format='iso')
            st.download_button(
                label="📥 Download Analytics JSON",
                data=json_data,
                file_name=f"code_generation_analytics_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    else:
        st.info("📭 No analytics data available yet. Generate some code to see statistics!")

# ============================================================================
# TAB 4: GOOGLE SHEETS DATA
# ============================================================================

with tab4:
    st.markdown("### 📥 Google Sheets Integration")
    
    st.markdown(f"**Sheet ID:** `{GOOGLE_SHEETS_ID}`")
    st.markdown(f"**Sheet Name:** `{GOOGLE_SHEETS_SHEET_NAME}`")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Fetch Latest Data", use_container_width=True):
            with st.spinner("Fetching data from Google Sheets..."):
                st.session_state.gsheet_data = fetch_google_sheets_data()
                if st.session_state.gsheet_data is not None:
                    st.success(f"✅ Loaded {len(st.session_state.gsheet_data)} rows from Google Sheets!")
                else:
                    st.info("ℹ️ No data available in Google Sheets yet.")
    
    with col2:
        if st.button("📋 View Sheet Structure", use_container_width=True):
            st.info("""
**Google Sheets Columns:**
- Number: Sequential ID
- Title: User request summary
- Category: AI-classified category
- Description: Detailed description
- Code: Full generated code
- PDF_Enabled: PDF export flag
- Timestamp: ISO 8601 timestamp
- Agent_Name: Generator agent name
            """)
    
    st.markdown("---")
    
    if st.session_state.gsheet_data is not None and len(st.session_state.gsheet_data) > 0:
        st.markdown("#### 📊 Google Sheets Data")
        
        st.dataframe(
            st.session_state.gsheet_data,
            use_container_width=True,
            height=400
        )
        
        st.markdown("---")
        
        # Export options
        st.markdown("#### 📥 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = st.session_state.gsheet_data.to_csv(index=False)
            st.download_button(
                label="📥 CSV",
                data=csv,
                file_name=f"gsheet_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            json_data = st.session_state.gsheet_data.to_json(orient='records')
            st.download_button(
                label="📥 JSON",
                data=json_data,
                file_name=f"gsheet_export_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col3:
            # Excel export
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                st.session_state.gsheet_data.to_excel(writer, index=False)
            buffer.seek(0)
            
            st.download_button(
                label="📥 Excel",
                data=buffer.getvalue(),
                file_name=f"gsheet_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    else:
        st.info("📭 No data in Google Sheets yet. Generate some code to populate the sheet!")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div class="footer">
    <p>🤖 Powered by N8N AI Agents | Built with Streamlit | Connected to Google Sheets</p>
    <p>Version 2.0 | Enhanced Code Generator Hub</p>
    <p>Generated codes are automatically logged to Google Sheets for persistence and analytics</p>
</div>
""", unsafe_allow_html=True)
