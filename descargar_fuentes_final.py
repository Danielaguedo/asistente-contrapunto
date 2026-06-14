import os
import urllib.request

# Crear carpeta data si no existe
data_dir = os.path.join(os.getcwd(), "data")
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Enlaces "RAW" oficiales (Directos al binario, sin HTML)
urls = {
    "Bravura.woff": "https://raw.githubusercontent.com/rism-digital/verovio/master/data/Bravura.woff",
    "Leipzig.woff": "https://raw.githubusercontent.com/rism-digital/verovio/master/data/Leipzig.woff"
}

print(f"⬇️ Iniciando descarga en: {data_dir}")

for nombre, url in urls.items():
    ruta_destino = os.path.join(data_dir, nombre)
    print(f"   Descargando {nombre}...")
    
    try:
        urllib.request.urlretrieve(url, ruta_destino)
        # Verificar tamaño (debe ser > 40KB)
        tamanio = os.path.getsize(ruta_destino)
        if tamanio > 40000:
            print(f"   ✅ ÉXITO: {nombre} descargado correctamente ({tamanio/1024:.1f} KB)")
        else:
            print(f"   ❌ ERROR: {nombre} es demasiado pequeño ({tamanio} bytes). Probablemente corrupto.")
    except Exception as e:
        print(f"   ❌ ERROR de conexión: {e}")

print("\nSi ambos archivos tienen check verde ✅, ya puedes ejecutar 'python cli_runner.py <archivo.musicxml>'")