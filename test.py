from music21 import converter

# Reemplaza 'tu_archivo.xml' por la ruta a tu archivo MusicXML
print ("Número de partes:",)
archivo = 'c:/Users/Mirko/Documents/Proyectos de Dorico/Flows desde Ejercicio de prueba de primera especie en contrapunto 01\Ejercicio de prueba de primera especie en contrapunto 01 - Partitura completa - 01 Flow 1.musicxml'
score = converter.parse(archivo)

print("Número de partes:", len(score.parts))
if len(score.parts) >= 2:
    print("Notas en Soprano:", len(score.parts[0].flat.notes))
    print("Notas en Barítono:", len(score.parts[1].flat.notes))
else:
    print("No se encontraron dos partes separadas en el score.")
    
    