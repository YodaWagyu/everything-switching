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
    """Display login page with split-screen design (White Form / Dark Teal Info)"""
    import random
    
    # Random Quotes for the Right Panel
    quotes = [
        {
            "text": "Understanding why customers leave is the first step to keeping them.",
            "author": "Customer Retention Strategy"
        },
        {
            "text": "In the world of data, every switch tells a story. Listen to it.",
            "author": "Data Intelligence"
        },
        {
            "text": "Brand loyalty is earned. Analytics helps you keep it.",
            "author": "Market Insights"
        },
        {
            "text": "Turn customer movement into your competitive advantage.",
            "author": "Competitive Analysis"
        }
    ]
    selected_quote = random.choice(quotes)

    # Custom CSS for Split-Screen
    st.markdown("""
        <style>
            /* Global Background - Full Height with Flexbox Centering */
            .stApp {
                background-color: #f8f9fa;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            /* Hide default elements */
            #MainMenu, footer, header {visibility: hidden;}
            
            /* Main Container - Centered with Flexbox */
            .block-container {
                padding: 2rem !important;
                max-width: min(1200px, 90vw);
                width: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: auto !important;
            }
            
            /* The Split Card Container - Responsive Sizing */
            [data-testid="stHorizontalBlock"] {
                background: white;
                border-radius: 24px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                min-height: min(600px, 80vh);
                max-height: 90vh;
                width: 100%;
            }
            
            /* Left Column (Form) - White */
            [data-testid="stColumn"]:nth-of-type(1) {
                background: white;
                padding: clamp(40px, 8vw, 80px) !important;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            
            /* Right Column (Info) - Dark Teal */
            [data-testid="stColumn"]:nth-of-type(2) {
                background: linear-gradient(135deg, #0f3d3e 0%, #1a5f60 100%);
                padding: clamp(40px, 8vw, 80px) !important;
                display: flex;
                flex-direction: column;
                justify-content: center;
                color: white;
                position: relative;
            }
            
            /* Typography - Left */
            .welcome-header {
                font-family: 'Inter', sans-serif;
                font-size: clamp(24px, 4vw, 32px);
                font-weight: 700;
                color: #1a1a1a;
                margin-bottom: 10px;
            }
            
            .welcome-sub {
                font-family: 'Inter', sans-serif;
                font-size: clamp(14px, 2vw, 16px);
                color: #666;
                margin-bottom: 40px;
                line-height: 1.5;
            }
            
            /* Typography - Right */
            .info-header {
                font-family: 'Inter', sans-serif;
                font-size: clamp(24px, 4vw, 36px);
                font-weight: 700;
                line-height: 1.3;
                margin-bottom: 30px;
            }
            
            .quote-box {
                margin-top: 40px;
                border-left: 4px solid rgba(255,255,255,0.3);
                padding-left: 20px;
            }
            
            .quote-text {
                font-size: clamp(14px, 2.5vw, 18px);
                line-height: 1.6;
                opacity: 0.9;
                font-style: italic;
            }
            
            .quote-author {
                margin-top: 15px;
                font-weight: 600;
                font-size: clamp(12px, 1.5vw, 14px);
                opacity: 0.7;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            /* Input Styling */
            .stTextInput > div > div > input {
                background-color: white !important;
                border: 1px solid #e0e0e0 !important;
                color: #333 !important;
                border-radius: 8px !important;
                padding: 12px 16px !important;
                height: 50px;
                font-size: 16px;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: #0f3d3e !important;
                box-shadow: 0 0 0 2px rgba(15, 61, 62, 0.1) !important;
            }
            
            /* Button Styling */
            .stButton > button {
                background: #0f3d3e !important; /* Dark Teal */
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
                background: #165253 !important;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(15, 61, 62, 0.2);
            }
            
            /* Hide Labels */
            .stTextInput label {
                color: #333 !important;
                font-weight: 500;
                margin-bottom: 8px;
                display: block !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Split Layout: Left (Form) - Right (Info)
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 40px;">
                <!-- Logo Mark -->
                <div style="
                    width: 40px; 
                    height: 40px; 
                    background: #0f3d3e; 
                    border-radius: 10px; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center;
                    color: white;
                    font-family: 'Inter', sans-serif;
                    font-weight: 800;
                    font-size: 16px;
                    letter-spacing: -1px;
                    box-shadow: 0 4px 10px rgba(15, 61, 62, 0.2);
                ">
                    ES
                </div>
                <!-- Brand Name -->
                <div style="
                    font-family: 'Inter', sans-serif; 
                    font-weight: 700; 
                    font-size: 20px; 
                    color: #0f3d3e; 
                    letter-spacing: -0.5px;
                ">
                    Everything Switching
                </div>
            </div>
            
            <div class="welcome-header">Welcome Back</div>
            <div class="welcome-sub">
                Please enter your password to access the dashboard.
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            password = st.text_input("Password", type="password", placeholder="Enter your access key")
            
            # Spacing
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

    with col2:
        st.markdown(f"""
            <div class="info-header">
                Unlock Market Insights<br>with Precision Data
            </div>
            <div class="quote-box">
                <div class="quote-text">"{selected_quote['text']}"</div>
                <div class="quote-author">{selected_quote['author']}</div>
            </div>
        """, unsafe_allow_html=True)
