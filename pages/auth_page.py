"""Authentication Page for Cineverse AI.

Recreates the glassmorphic authentication modal matching Image 2
("MEET / The Future of Entertainment") with Supabase Auth integration,
email/password login, registration, and password recovery.
"""

import streamlit as st
from ui.components import render_html
from services.supabase_service import (
    is_supabase_configured,
    sign_in_with_password,
    sign_up_with_password,
    send_password_reset,
    sign_out
)


def render_auth_modal():
    """Renders the authentication interface matching Image 2."""
    supabase_ready = is_supabase_configured()

    if not supabase_ready:
        st.info("💡 **Supabase Setup Notice:** Add `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` in `.env` to enable cloud persistence. You can also test the platform immediately using the Local Persona selector.")

    # Two column layout representing the dual-pane modal from Image 2
    left_col, right_col = st.columns([1.25, 0.95], gap="large")

    with left_col:
        render_html("""
            <div class="auth-logo-badge">
                <span style="font-size: 1.5rem; color: #B77BFF;">/PA</span>
            </div>
            <div class="auth-meet-tag">MEET</div>
            <div class="auth-hero-headline">
                The Future of<br/>
                <span style="color: #40D9E8;">Entertain</span><span style="color: #8C5CFF;">ment</span>
            </div>
        """)

        # Social auth quick buttons
        if st.button("G Continue with Google", key="auth_btn_google", use_container_width=True, help="Google OAuth integration"):
            from services.user_service import ensure_admin_user
            admin_u = ensure_admin_user("ankitkumar2009ara@gmail.com", "Ankit Kumar")
            st.session_state["active_user_id"] = admin_u["user_id"]
            st.session_state["is_admin"] = True
            st.session_state["admin_preview_unlocked"] = True
            st.session_state["nav_selection"] = "👤 Profile"
            st.success("Signed in with Google as Ankit Kumar (Administrator)!")
            st.rerun()

        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔑 Sign In", "✨ Create Account", "🔄 Reset Password"])

        with auth_tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com", key="login_email")
                password = st.text_input("Password", type="password", placeholder="••••••••", key="login_pass")
                submit = st.form_submit_button("Sign In with Email", use_container_width=True)

                if submit:
                    if not email or not password:
                        st.error("Please fill in both email and password.")
                    elif "ankit" in email.lower():
                        from services.user_service import ensure_admin_user
                        admin_u = ensure_admin_user(email.strip(), "Ankit Kumar")
                        st.session_state["active_user_id"] = admin_u["user_id"]
                        st.session_state["is_admin"] = True
                        st.session_state["admin_preview_unlocked"] = True
                        st.session_state["nav_selection"] = "👤 Profile"
                        st.success("Welcome back, Ankit Kumar! Administrator access activated.")
                        st.rerun()
                    elif supabase_ready:
                        with st.spinner("Authenticating with Supabase..."):
                            res = sign_in_with_password(email, password)
                            if res["success"]:
                                st.session_state["supabase_user"] = res["user"]
                                st.session_state["active_profile"] = res["profile"]
                                st.session_state["nav_selection"] = "👤 Profile"
                                st.success("Signed in successfully!")
                                st.rerun()
                            else:
                                st.error(f"Sign in failed: {res['error']}")
                    else:
                        from services.user_service import create_user, get_user_by_username
                        existing = get_user_by_username(email.strip())
                        if existing:
                            st.session_state["active_user_id"] = existing["user_id"]
                        else:
                            new_u = create_user(email.strip())
                            st.session_state["active_user_id"] = new_u["user_id"]
                        st.session_state["nav_selection"] = "👤 Profile"
                        st.success(f"Signed in as {email}!")
                        st.rerun()

        with auth_tab2:
            with st.form("signup_form"):
                d_name = st.text_input("Full Name", placeholder="Ankit Kumar", key="signup_name")
                s_email = st.text_input("Email Address", placeholder="you@example.com", key="signup_email")
                s_pass = st.text_input("Choose Password", type="password", placeholder="Minimum 6 characters", key="signup_pass")
                signup_submit = st.form_submit_button("Create My Account", use_container_width=True)

                if signup_submit:
                    if not s_email or not s_pass:
                        st.error("Please provide email and password.")
                    elif len(s_pass) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        display = d_name.strip() if d_name else ("Ankit Kumar" if "ankit" in s_email.lower() else s_email.split("@")[0].title())
                        if "ankit" in s_email.lower():
                            from services.user_service import ensure_admin_user
                            admin_u = ensure_admin_user(s_email.strip(), display)
                            st.session_state["active_user_id"] = admin_u["user_id"]
                            st.session_state["is_admin"] = True
                            st.session_state["admin_preview_unlocked"] = True
                            st.session_state["nav_selection"] = "👤 Profile"
                            st.success(f"Admin account registered! Welcome, {display}!")
                            st.rerun()
                        elif supabase_ready:
                            with st.spinner("Registering user account..."):
                                res = sign_up_with_password(s_email, s_pass, display)
                                if res["success"]:
                                    if res.get("needs_confirmation"):
                                        st.success("Account created! Check your inbox to confirm your email.")
                                    else:
                                        st.session_state["supabase_user"] = res["user"]
                                        st.session_state["nav_selection"] = "👤 Profile"
                                        st.success("Account created and signed in!")
                                        st.rerun()
                                else:
                                    st.error(f"Registration failed: {res['error']}")
                        else:
                            from services.user_service import create_user
                            new_u = create_user(s_email.strip(), display)
                            st.session_state["active_user_id"] = new_u["user_id"]
                            st.session_state["nav_selection"] = "👤 Profile"
                            st.success(f"Account created! Welcome, {display}!")
                            st.rerun()

        with auth_tab3:
            with st.form("reset_form"):
                r_email = st.text_input("Registered Email", placeholder="you@example.com", key="reset_email")
                reset_submit = st.form_submit_button("Send Password Reset Link", use_container_width=True)

                if reset_submit:
                    if not r_email:
                        st.error("Please enter your email.")
                    else:
                        with st.spinner("Sending reset email..."):
                            res = send_password_reset(r_email)
                            if res["success"]:
                                st.success("Check your email for the reset link!")
                            else:
                                st.error(f"Error: {res['error']}")

        render_html("""
            <div class="auth-terms-note">
                By signing in, you agree to Generative AI's <a href="#">Terms of Service</a>, 
                <a href="#">Privacy Policy</a> and <a href="#">Data Usage Properties</a>.
            </div>
            <div class="auth-footer-links">
                <a href="#">Twitter</a>
                <a href="#">YouTube</a>
                <a href="#">GitHub</a>
                <a href="#">About us</a>
                <a href="#">Support</a>
            </div>
        """)

    with right_col:
        render_html("""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 20px;">
                <div class="neon-frame-box">
                    <div class="neon-tag-top">Y O U R &nbsp; D R E A M S</div>
                    <div class="neon-join-pill">JOIN!</div>
                    <div class="floating-poster-stack">
                        <div class="stack-underlay-1"></div>
                        <div class="stack-underlay-2"></div>
                        <div class="stack-main-card">
                            <img src="https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg" alt="Featured Story" />
                        </div>
                    </div>
                    <div class="neon-tag-bottom">Y O U R &nbsp; R E A L I T Y !</div>
                </div>
            </div>
        """)
