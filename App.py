import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import time

# Page configuration
st.set_page_config(
    page_title="AI Code Generator Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .stChatMessage {
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .agent-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 10px;
    }
    .code-preview {
        background: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        margin-top: 10px;
    }
    .success-message {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .error-message {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# N8N Webhook URL
N8N_WEBHOOK_URL = "https://agentonline-u29564.vm.elestio.app/webhook-test/Streamlitagentform1"

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'generated_codes' not in st.session_state:
    st.session_state.generated_codes = []
if 'current_code' not in st.session_state:
    st.session_state.current_code = None
if 'current_agent' not in st.session_state:
    st.session_state.current_agent = None

# Sidebar
with st.sidebar:
    st.markdown("### 🤖 AI Code Generator Hub")
    st.markdown("---")
    
    st.markdown("#### 📊 Available Agents")
    agents = {
        "HTML/CSS Generators": [
            "🌐 Landing Page Generator",
            "📊 Dashboard Generator", 
            "📝 Form Generator",
            "💼 Portfolio Generator",
            "🔗 API Integration Generator",
            "🛒 E-commerce Page Generator"
        ],
        "Python/Streamlit Generators": [
            "📈 Data App Generator",
            "🤖 ML App Generator",
            "📊 Dashboard App Generator",
            "📋 Form App Generator"
        ]
    }
    
    for category, agent_list in agents.items():
        st.markdown(f"**{category}**")
        for agent in agent_list:
            st.markdown(f"- {agent}")
        st.markdown("")
    
    st.markdown("---")
    st.markdown("#### 💡 Example Prompts")
    example_prompts = [
        "Create a modern landing page for a SaaS product",
        "Build a dashboard to visualize sales data",
        "Generate a contact form with validation",
        "Make a Streamlit app for data analysis",
        "Create an ML app for prediction",
        "Build an e-commerce product page"
    ]
    
    for prompt in example_prompts:
        if st.button(prompt, key=f"example_{prompt[:20]}", use_container_width=True):
            st.session_state.example_prompt = prompt
    
    st.markdown("---")
    st.markdown("#### ⚙️ Settings")
    show_raw_response = st.checkbox("Show raw API response", value=False)
    auto_download = st.checkbox("Auto-download generated code", value=False)
    
    st.markdown("---")
    st.markdown("#### 📚 Code History")
    if st.session_state.generated_codes:
        st.write(f"Total generated: {len(st.session_state.generated_codes)}")
        if st.button("Clear History", use_container_width=True):
            st.session_state.generated_codes = []
            st.session_state.messages = []
            st.rerun()
    else:
        st.write("No codes generated yet")
    
    st.markdown("---")
    st.markdown("#### 🔗 N8N Integration")
    st.markdown(f"**Webhook URL:**")
    st.code(N8N_WEBHOOK_URL, language="text")
    
    # Connection test
    if st.button("Test Connection", use_container_width=True):
        try:
            response = requests.post(
                N8N_WEBHOOK_URL,
                json={"chatInput": "test connection"},
                timeout=5
            )
            if response.status_code == 200:
                st.success("✅ Connected!")
            else:
                st.error(f"❌ Error: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)}")

# Main content
st.markdown('<div class="main-header">🚀 AI Code Generator Hub</div>', unsafe_allow_html=True)
st.markdown("Generate production-ready HTML/CSS and Python/Streamlit code with AI-powered agents")

# Create tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat Interface", "📋 Generated Code", "📊 Analytics"])

with tab1:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "code" in message and message["code"]:
                with st.expander("View Generated Code"):
                    st.code(message["code"][:1000] + "..." if len(message["code"]) > 1000 else message["code"])
    
    # Chat input
    if prompt := st.chat_input("Describe the code you want to generate...") or st.session_state.get('example_prompt'):
        if st.session_state.get('example_prompt'):
            prompt = st.session_state.example_prompt
            del st.session_state.example_prompt
        
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Show assistant thinking
        with st.chat_message("assistant"):
            with st.spinner("🤖 AI Agent is generating your code..."):
                try:
                    # Send request to N8N webhook
                    response = requests.post(
                        N8N_WEBHOOK_URL,
                        json={"chatInput": prompt},
                        headers={"Content-Type": "application/json"},
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Extract information
                        agent_name = result.get('agent', 'Unknown Agent')
                        category = result.get('category', 'Unknown Category')
                        generated_code = result.get('code', 'No code generated')
                        
                        # Store current code
                        st.session_state.current_code = generated_code
                        st.session_state.current_agent = agent_name
                        
                        # Create response message
                        response_message = f"""
### ✨ Code Generated Successfully!

**Agent Used:** `{agent_name}`  
**Category:** `{category}`  
**Generated at:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

Your code has been generated and logged to Google Sheets. You can view it in the "Generated Code" tab.
"""
                        
                        st.markdown(response_message)
                        
                        # Show code preview
                        with st.expander("📝 Code Preview", expanded=True):
                            # Determine language for syntax highlighting
                            code_lang = "python" if "Streamlit" in agent_name else "html"
                            st.code(generated_code[:2000] + "..." if len(generated_code) > 2000 else generated_code, language=code_lang)
                        
                        # Add download button
                        file_extension = ".py" if "Streamlit" in agent_name else ".html"
                        filename = f"generated_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
                        
                        st.download_button(
                            label=f"⬇️ Download {file_extension.upper()} File",
                            data=generated_code,
                            file_name=filename,
                            mime="text/plain"
                        )
                        
                        # Store in session state
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_message,
                            "code": generated_code,
                            "agent": agent_name,
                            "category": category
                        })
                        
                        st.session_state.generated_codes.append({
                            "timestamp": datetime.now(),
                            "prompt": prompt,
                            "agent": agent_name,
                            "category": category,
                            "code": generated_code,
                            "code_type": "Python/Streamlit" if "Streamlit" in agent_name else "HTML/CSS/JS"
                        })
                        
                        # Auto-download if enabled
                        if auto_download:
                            st.success("✅ Code auto-downloaded!")
                        
                        # Show raw response if enabled
                        if show_raw_response:
                            with st.expander("🔍 Raw API Response"):
                                st.json(result)
                        
                        st.success("✨ Code generation completed!")
                        
                    else:
                        error_msg = f"❌ Error: Received status code {response.status_code}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
                except requests.exceptions.Timeout:
                    error_msg = "⏱️ Request timed out. The code generation is taking longer than expected. Please try again."
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
                except requests.exceptions.ConnectionError:
                    error_msg = "🔌 Connection error. Please check if the N8N webhook is accessible."
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
                except Exception as e:
                    error_msg = f"❌ An error occurred: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

with tab2:
    st.markdown("### 📋 Generated Code Library")
    
    if st.session_state.current_code:
        st.markdown("#### 🎯 Latest Generated Code")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**Agent:** {st.session_state.current_agent}")
        with col2:
            code_lang = "python" if "Streamlit" in st.session_state.current_agent else "html"
            file_ext = ".py" if code_lang == "python" else ".html"
            
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
        
        for idx, code_entry in enumerate(reversed(st.session_state.generated_codes)):
            with st.expander(f"🔹 {code_entry['category']} - {code_entry['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                st.markdown(f"**Prompt:** {code_entry['prompt']}")
                st.markdown(f"**Agent:** {code_entry['agent']}")
                st.markdown(f"**Type:** {code_entry['code_type']}")
                
                code_lang = "python" if code_entry['code_type'] == "Python/Streamlit" else "html"
                st.code(code_entry['code'], language=code_lang)
                
                file_ext = ".py" if code_lang == "python" else ".html"
                st.download_button(
                    label="⬇️ Download This Code",
                    data=code_entry['code'],
                    file_name=f"code_{idx}_{code_entry['timestamp'].strftime('%Y%m%d_%H%M%S')}{file_ext}",
                    mime="text/plain",
                    key=f"download_{idx}"
                )
    else:
        st.info("No code has been generated yet. Start chatting to generate code!")

with tab3:
    st.markdown("### 📊 Generation Analytics")
    
    if st.session_state.generated_codes:
        # Create DataFrame
        df = pd.DataFrame([{
            'Timestamp': entry['timestamp'],
            'Agent': entry['agent'],
            'Category': entry['category'],
            'Code Type': entry['code_type'],
            'Code Length': len(entry['code'])
        } for entry in st.session_state.generated_codes])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Generations", len(df))
        with col2:
            st.metric("HTML Generations", len(df[df['Code Type'] == 'HTML/CSS/JS']))
        with col3:
            st.metric("Python Generations", len(df[df['Code Type'] == 'Python/Streamlit']))
        
        st.markdown("---")
        
        # Agent usage chart
        st.markdown("#### 🤖 Agent Usage Distribution")
        agent_counts = df['Agent'].value_counts()
        st.bar_chart(agent_counts)
        
        st.markdown("---")
        
        # Category breakdown
        st.markdown("#### 📂 Category Breakdown")
        category_counts = df['Category'].value_counts()
        st.bar_chart(category_counts)
        
        st.markdown("---")
        
        # Full data table
        st.markdown("#### 📋 Detailed History")
        st.dataframe(
            df[['Timestamp', 'Agent', 'Category', 'Code Type', 'Code Length']],
            use_container_width=True,
            hide_index=True
        )
        
        # Export analytics
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Analytics CSV",
            data=csv,
            file_name=f"code_generation_analytics_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No analytics data available yet. Generate some code to see statistics!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🤖 Powered by N8N AI Agents | Built with Streamlit</p>
    <p>Connected to: <code>https://agentonline-u29564.vm.elestio.app</code></p>
</div>
""", unsafe_allow_html=True)
