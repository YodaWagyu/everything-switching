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
    """Display login page with premium design"""
    # Custom CSS for Login Page ONLY
    st.markdown("""
        <style>
            /* Premium Dark Gradient Background */
            .stApp {
                background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%) !important;
            }
            
            /* Hide the separate card HTML if it exists (cleanup) */
            .login-card { display: none; }
            
            /* The Form IS the Card */
            [data-testid="stForm"] {
                background: rgba(255, 255, 255, 0.03);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
                padding: 50px 40px;
            }
            
            /* Input Styling - Sleek & Minimal */
            .stTextInput > div > div > input {
                background-color: rgba(0, 0, 0, 0.2) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                color: white !important;
                border-radius: 12px !important;
                padding: 16px 20px !important;
                font-size: 16px !important;
                transition: all 0.3s ease;
            }
            
            .stTextInput > div > div > input:focus {
                background-color: rgba(0, 0, 0, 0.4) !important;
                border-color: #4facfe !important;
                box-shadow: 0 0 0 2px rgba(79, 172, 254, 0.3) !important;
            }
            
            /* Hide Input Label */
            .stTextInput label {
                display: none;
            }
            
            /* Button Styling - Gradient Pill */
            .stButton > button {
                background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important;
                color: #000000 !important;
                border: none;
                border-radius: 50px !important; /* Pill shape */
                padding: 16px !important;
                font-weight: 800 !important;
                letter-spacing: 1px;
                text-transform: uppercase;
                font-size: 14px !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 10px 30px rgba(0, 242, 254, 0.3);
                width: 100%;
                margin-top: 10px;
            }
            
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 15px 40px rgba(0, 242, 254, 0.5);
                filter: brightness(1.1);
            }
            
            /* Hide Streamlit elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

    # Use columns to center the card
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            # Header Content INSIDE the form for perfect unification
            st.markdown("""
                <div style="text-align: center; margin-bottom: 40px;">
                    <div style="font-size: 64px; margin-bottom: 20px; filter: drop-shadow(0 0 20px rgba(79, 172, 254, 0.4));">🔄</div>
                    <h1 style="color: white; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 32px; margin: 0; letter-spacing: -1px; text-shadow: 0 2px 10px rgba(0,0,0,0.5);">Everything Switching</h1>
                    <div style="height: 4px; width: 40px; background: linear-gradient(90deg, #4facfe, #00f2fe); margin: 15px auto; border-radius: 2px;"></div>
                    <p style="color: rgba(255,255,255,0.6); font-family: 'Inter', sans-serif; font-size: 14px; margin-top: 10px; font-weight: 400; letter-spacing: 1px; text-transform: uppercase;">Premium Analytics Dashboard</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Input with placeholder acting as label
            password = st.text_input("Password", type="password", placeholder="Enter your secure access key", label_visibility="collapsed")
            
            st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
            
            submit = st.form_submit_button("ENTER DASHBOARD", use_container_width=True)
            
            if submit:
                if password:
                    success, role = authenticate(password)
                    if success:
                        st.session_state["authenticated"] = True
                        st.session_state["role"] = role
                        st.success(f"Access Granted")
                        st.rerun()
                    else:
                        st.error("Access Denied: Invalid Key")
                else:
                    st.warning("Please enter access key")
