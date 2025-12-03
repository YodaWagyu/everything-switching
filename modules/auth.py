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
            /* Deep Blue Gradient Background (Matches Logout Button) */
            .stApp {
                background: linear-gradient(135deg, #2874a6 0%, #1b4f72 100%) !important;
            }
            
            /* Login Card - Glassmorphism with White Text */
            .login-container {
                max-width: 400px;
                margin: 100px auto;
                padding: 40px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 24px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                animation: fadeInUp 0.6s ease-out;
            }
            
            .login-title {
                font-size: 32px;
                font-weight: 700;
                color: #ffffff;
                margin-bottom: 10px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            .login-subtitle {
                color: rgba(255, 255, 255, 0.8);
                font-size: 16px;
                font-weight: 400;
            }
            
            /* Input Label Styling */
            .stTextInput label {
                color: white !important;
            }
            
            /* Button Styling - White variant for contrast */
            .stButton > button {
                background: white !important;
                color: #2874a6 !important;
                border: none;
                font-weight: 700 !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
            
            .stButton > button:hover {
                background: #f8f9fa !important;
                transform: translateY(-1px);
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
            }
            
            /* Input Field Styling */
            .stTextInput > div > div > input {
                background-color: rgba(255, 255, 255, 0.9);
                border: none;
                color: #1a1a1a;
            }
        </style>
    """, unsafe_allow_html=True)

    # Center the login card using columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div class="login-container">
                <div class="login-header">
                    <div class="login-title">Everything Switching</div>
                    <div class="login-subtitle">Premium Analytics Dashboard</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            password = st.text_input("Access Password", type="password", placeholder="Enter your secure password")
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Sign In", use_container_width=True)
            
            if submit:
                if password:
                    success, role = authenticate(password)
                    if success:
                        st.session_state["authenticated"] = True
                        st.session_state["role"] = role
                        st.success(f"Welcome back! Signing you in...")
                        st.rerun()
                    else:
                        st.error("Incorrect password. Please try again.")
                else:
                    st.warning("Please enter your password.")
