print("--- Iniciando prueba de importación de music21 ---")
try:
    from music21.voiceLeading import MotionType
    print("ÉXITO: Se importó MotionType desde music21.voiceLeading")
    print(f"MotionType object: {MotionType}")
except ImportError as e:
    print(f"FALLO al importar MotionType desde music21.voiceLeading: {e}")
    print("Intentando importar music21.voiceLeading como módulo...")
    try:
        from music21 import voiceLeading as voiceLeading_module
        print("ÉXITO al importar music21.voiceLeading como módulo.")
        # Descomenta la siguiente línea si quieres ver todos los atributos, puede ser largo
        # print(f"Atributos de voiceLeading_module: {dir(voiceLeading_module)}")
        if hasattr(voiceLeading_module, 'MotionType'):
            print("MotionType ENCONTRADO como atributo de voiceLeading_module.")
            print(f"voiceLeading_module.MotionType object: {voiceLeading_module.MotionType}")
        else:
            print("MotionType NO ENCONTRADO como atributo de voiceLeading_module.")
        
        if hasattr(voiceLeading_module, '__file__'):
            print(f"Ruta del módulo voiceLeading: {voiceLeading_module.__file__}")
        else:
            print("El módulo voiceLeading no tiene el atributo __file__.")

    except ImportError as e2:
        print(f"FALLO al importar el módulo music21.voiceLeading: {e2}")
    except Exception as e_gen_vl:
        print(f"Otra excepción al inspeccionar voiceLeading: {e_gen_vl}")
finally:
    print("\nIntentando importar información general de music21...")
    try:
        import music21
        print(f"Versión de music21 instalada: {music21.__version__}")
        if hasattr(music21, '__file__'):
            print(f"Ruta de la biblioteca music21: {music21.__file__}")
    except ImportError as e3:
        print(f"FALLO CRÍTICO: No se pudo importar la biblioteca music21: {e3}")
    except Exception as e_gen_m21:
        print(f"Otra excepción al importar music21: {e_gen_m21}")
print("--- Fin de la prueba ---")