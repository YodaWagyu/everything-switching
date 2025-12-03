"""
Authentication Module
Handles user authentication and role-based access control
"""

import streamlit as st
from typing import Optional, Tuple


def authenticate(password: str) -> Tuple[bool, Optional[str]]:
    """
    Authenticate user based on password
    Returns: (success: bool, role: Optional[str])
    
    Role is determined by which user's password matches
    No username needed - password alone determines role
    """
    try:
        users = st.secrets.get("users", {})
        
        # Check each user's password
        for username, user_data in users.items():
            if user_data.get("password") == password:
                role = user_data.get("role", "user")
                return True, role
        
        # No matching password found
        return False, None
        
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False, None


def is_authenticated() -> bool:
    """Check if user is currently authenticated"""
    return st.session_state.get("authenticated", False)


def is_admin() -> bool:
    """Check if current user has admin role"""
    return st.session_state.get("role") == "admin"


def logout():
    """Clear authentication state"""
    for key in ["authenticated", "role"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def show_login_page():
    """Display login page with premium split-screen design"""
    # Custom CSS for Split-Screen Login
    st.markdown("""
        <style>
            /* Global Background */
            .stApp {
                background-color: #0e1117;
                background-image: radial-gradient(circle at 50% 50%, #1a202c 0%, #0e1117 100%);
            }
            
            /* Hide default elements */
            #MainMenu, footer, header {visibility: hidden;}
            
            /* Target the Main Container to center our card */
            .block-container {
                padding-top: 5rem;
                max-width: 1000px;
            }
            
            /* Card Container Styling (The Row) */
            [data-testid="stHorizontalBlock"] {
                background: #1e293b;
                border-radius: 24px;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                overflow: hidden;
                border: 1px solid rgba(255, 255, 255, 0.05);
                min-height: 500px;
            }
            
            /* Left Column (Visual) */
            [data-testid="stColumn"]:nth-of-type(1) {
                background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
                padding: 0 !important;
                display: flex;
                flex-direction: column;
                justify-content: center;
                position: relative;
            }
            
            /* Right Column (Form) */
            [data-testid="stColumn"]:nth-of-type(2) {
                background: #1e293b; /* Dark Slate */
                padding: 40px !important;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            
            /* Typography & Elements */
            .brand-container {
                padding: 60px;
                color: white;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }
            
            .brand-title {
                font-family: 'Inter', sans-serif;
                font-size: 42px;
                font-weight: 800;
                line-height: 1.1;
                margin-bottom: 20px;
                background: linear-gradient(to right, #fff, #cbd5e1);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .brand-subtitle {
                font-family: 'Inter', sans-serif;
                font-size: 16px;
                color: rgba(255, 255, 255, 0.7);
                line-height: 1.6;
            }
            
            .glass-badge {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 8px 16px;
                border-radius: 50px;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 1px;
                text-transform: uppercase;
                width: fit-content;
                margin-bottom: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            /* Form Elements */
            .form-header {
                margin-bottom: 30px;
            }
            
            .form-title {
                font-size: 28px;
                font-weight: 700;
                color: white;
                margin-bottom: 8px;
            }
            
            .form-subtitle {
                color: #94a3b8;
                font-size: 14px;
            }
            
            /* Input Styling */
            .stTextInput > div > div > input {
                background-color: #334155 !important;
                border: 1px solid #475569 !important;
                color: white !important;
                border-radius: 8px !important;
                padding: 12px 16px !important;
                height: 50px;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: #38bdf8 !important;
                box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
            }
            
            /* Button Styling */
            .stButton > button {
                background: linear-gradient(90deg, #38bdf8 0%, #0ea5e9 100%) !important;
                color: white !important;
                border: none;
                border-radius: 8px !important;
                height: 50px;
                font-weight: 600 !important;
                font-size: 16px !important;
                width: 100%;
                margin-top: 10px;
                transition: all 0.2s;
            }
            
            .stButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
            }
            
            /* Hide Label */
            .stTextInput label {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

    # Split Layout: Left (Visual) - Right (Form)
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.markdown("""
            <div class="brand-container">
                <div>
                    <div class="glass-badge">Analytics Platform</div>
                    <div class="brand-title">Everything<br>Switching</div>
                    <div class="brand-subtitle">
                        Deep dive into customer behavior, brand loyalty, and market movement with our premium analytics suite.
                    </div>
                </div>
                <div style="font-size: 12px; color: rgba(255,255,255,0.4);">
                    © 2024 Data Intelligence
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
            <div class="form-header">
                <div class="form-title">Welcome back</div>
                <div class="form-subtitle">Please enter your access key to continue</div>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            password = st.text_input("Password", type="password", placeholder="Access Key", label_visibility="collapsed")
            
            st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
            
            submit = st.form_submit_button("Sign In", use_container_width=True)
            
            if submit:
                if password:
                    success, role = authenticate(password)
                    if success:
                        st.session_state["authenticated"] = True
                        st.session_state["role"] = role
                        st.success("Access Granted")
                        st.rerun()
                    else:
                        st.error("Invalid Access Key")
                else:
                    st.warning("Please enter key")
