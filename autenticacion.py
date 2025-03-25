import streamlit as st
from firebase_admin import auth, exceptions

def mostrar_login():
    with st.form("login_form"):
        st.subheader(" Iniciar Sesión")
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")

        if st.form_submit_button("Ingresar"):
            try:
                user = auth.get_user_by_email(email)
                st.session_state['autenticado'] = True
                st.session_state['email'] = email
                st.success("¡Bienvenido!")
            except (auth.UserNotFoundError, exceptions.FirebaseError):
                st.error("Usuario o contraseña incorrectos")
                
def mostrar_registro():
    with st.form("registro_form"):
        st.subheader(" Registro (Solo profesores)")
        codigo = st.text_input("Código de invitación (obtenlo del administrador)")
        email = st.text_input("Correo institucional")
        password = st.text_input("Contraseña", type="password")
        
        if st.form_submit_button("Crear cuenta"):
            if codigo == "CONTRAPUNTO2024":  # Código secreto para registros
                try:
                    user = auth.create_user(email=email, password=password)
                    st.success("¡Cuenta creada! Ahora puedes iniciar sesión.")
                except exceptions.FirebaseError as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Código de invitación inválido")