import streamlit as st

def mostrar_seccion():
    st.header("🧑‍🎓 Gestión de Alumnos")
    st.subheader("Lista de Alumnos")

    # Simulación de datos de alumnos (reemplazar con tu lógica real)
    alumnos = [
        {"id": 1, "nombre": "Ana Pérez", "email": "ana.perez@email.com"},
        {"id": 2, "nombre": "Carlos López", "email": "carlos.lopez@email.com"},
        {"id": 3, "nombre": "Sofía Gómez", "email": "sofia.gomez@email.com"},
    ]

    if alumnos:
        st.table(alumnos)
    else:
        st.info("No hay alumnos registrados aún.")

    st.subheader("Añadir Nuevo Alumno")
    with st.form("nuevo_alumno"):
        nombre = st.text_input("Nombre del Alumno")
        email = st.text_input("Email del Alumno")
        submitted = st.form_submit_button("Añadir Alumno")

        if submitted:
            # Aquí iría la lógica para añadir el alumno a tu sistema
            st.success(f"Alumno '{nombre}' con email '{email}' añadido.")

    st.subheader("Otras Acciones")
    # Aquí puedes añadir más funcionalidades como editar o eliminar alumnos
    st.info("Próximamente: Editar y eliminar alumnos.")

if __name__ == "__main__":
    mostrar_seccion() # Para probar el módulo directamente