import streamlit_cookies as cookies

def inicializar_cookies():
    cookie_manager = cookies.manager()
    return cookie_manager

def obtener_cookie(cookie_manager, nombre_cookie):
    return cookie_manager.get(nombre_cookie)

def establecer_cookie(cookie_manager, nombre_cookie, valor_cookie):
    cookie_manager.set(nombre_cookie, valor_cookie)

def eliminar_cookie(cookie_manager, nombre_cookie):
    cookie_manager.delete(nombre_cookie)