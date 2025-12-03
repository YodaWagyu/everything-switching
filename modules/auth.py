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
    """Display login page"""
    st.title("🔐 Brand Switching Analysis")
    st.markdown("### Login")
    
    with st.form("login_form"):
        password = st.text_input("Password", type="password", help="Enter your access password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if password:
                success, role = authenticate(password)
                if success:
                    st.session_state["authenticated"] = True
                    st.session_state["role"] = role
                    st.success(f"✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid password. Please try again.")
            else:
                st.warning("⚠️ Please enter a password.")
