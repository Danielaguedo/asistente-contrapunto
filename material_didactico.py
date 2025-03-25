import streamlit as st

def seccion_material_didactico():
    with st.expander("📚 Libros Recomendados", expanded=True):
        col1, col2 = st.columns(2)  # Creamos dos columnas

        with col1:
            st.image("gradus_ad_parnassum.png", width=200)
            st.markdown("**Gradus ad Parnassum** - J.J. Fux")

        with col2:
            st.image("counterpoint_in_composition.png", width=200)
            st.markdown("**Counterpoint in Composition** - Salzer & Schachter")