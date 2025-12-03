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
    """Display login page with premium centered card design"""
    # Custom CSS for Login Page
    st.markdown("""
        <style>
            /* Global Background - Dark Teal/Slate Radial */
            .stApp {
                background-color: #1e293b;
                background-image: radial-gradient(circle at 50% 50%, #243b55 0%, #141e30 100%);
            }
            
            /* Hide default elements */
            #MainMenu, footer, header {visibility: hidden;}
            
            /* Center the card container */
            [data-testid="stVerticalBlock"] {
                align-items: center;
            }
            
            /* The Login Card Container */
            [data-testid="stForm"] {
                background: rgba(30, 41, 59, 0.7);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                padding: 60px 50px;
                width: 100%;
                max-width: 500px;
                margin: 0 auto;
            }
            
            /* Input Styling - Light Gray/Silver as per image */
            .stTextInput > div > div > input {
                background-color: #cbd5e1 !important; /* Light gray */
                border: 1px solid #94a3b8 !important;
                color: #0f172a !important; /* Dark text */
                border-radius: 8px !important;
                padding: 14px 20px !important;
                font-size: 15px !important;
                height: 50px;
            }
            
            .stTextInput > div > div > input::placeholder {
                color: #64748b !important;
            }
            
            .stTextInput > div > div > input:focus {
                background-color: #e2e8f0 !important;
                border-color: #38bdf8 !important;
                box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2) !important;
            }
            
            /* Button Styling - White with Dark Text */
            .stButton > button {
                background: #ffffff !important;
                color: #0f172a !important;
                border: none;
                border-radius: 8px !important;
                height: 50px;
                font-weight: 700 !important;
                font-size: 14px !important;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                width: 100%;
                margin-top: 15px;
                transition: all 0.2s;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
            
            .stButton > button:hover {
                background: #f8fafc !important;
                transform: translateY(-1px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            }
            
            /* Hide Label */
            .stTextInput label {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

    # Centering Layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            # Header Content
            st.markdown("""
                <div style="text-align: center; margin-bottom: 40px;">
                    <!-- Icon Box -->
                    <div style="
                        width: 60px; 
                        height: 60px; 
                        background: linear-gradient(135deg, #0ea5e9, #0284c7); 
                        border-radius: 12px; 
                        margin: 0 auto 25px auto;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 32px;
                        box-shadow: 0 10px 25px -5px rgba(14, 165, 233, 0.5);
                        border: 2px solid rgba(255,255,255,0.1);
                    ">
                        🔄
                    </div>
                    
                    <!-- Title -->
                    <h1 style="
                        color: white; 
                        font-family: 'Inter', sans-serif; 
                        font-weight: 800; 
                        font-size: 32px; 
                        margin: 0 0 15px 0; 
                        letter-spacing: -0.5px;
                    ">Everything Switching</h1>
                    
                    <!-- Separator -->
                    <div style="
                        width: 30px; 
                        height: 4px; 
                        background: #0ea5e9; 
                        margin: 0 auto 15px auto; 
                        border-radius: 2px;
                    "></div>
                    
                    <!-- Subtitle -->
                    <p style="
                        color: #94a3b8; 
                        font-family: 'Inter', sans-serif; 
                        font-size: 12px; 
                        font-weight: 600; 
                        letter-spacing: 1.5px; 
                        text-transform: uppercase;
                        margin: 0;
                    ">Premium Analytics Dashboard</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Input
            password = st.text_input("Password", type="password", placeholder="Enter your secure access key", label_visibility="collapsed")
            
            # Button
            submit = st.form_submit_button("ENTER DASHBOARD", use_container_width=True)
            
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
