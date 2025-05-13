# primera_especie/analisis.py
import streamlit as st 
from primera_especie.reglas import analizar_reglas_contrapunto
import traceback 

class ResultadoAnalisis:
    def __init__(self, errores, evaluacion, observaciones=None): # Asegurar que 'observaciones' esté en __init__
        self.errores = errores
        self.evaluacion = evaluacion
        self.observaciones = observaciones if observaciones is not None else [] # Inicializar como lista vacía

def seccion_analizar_ejercicio(score_m21_completo, cf_part_identificada, cp_part_identificada):
    """
    Analiza la partitura.
    Retorna un objeto ResultadoAnalisis con 'errores', 'evaluacion', y 'observaciones'.
    """
    # Inicializar valores por defecto para el caso de error temprano
    errores_analisis = []
    observaciones_analisis = []
    evaluacion_predeterminada = "Error durante el análisis."

    try:
        if not cf_part_identificada or not cp_part_identificada:
            errores_analisis.append("Partes CF/CP no proporcionadas para el análisis de reglas.")
            observaciones_analisis.append("Error interno: Faltan partes para analizar.")
            return ResultadoAnalisis(errores_analisis, "Error en Configuración de Análisis", observaciones_analisis)

        # analizar_reglas_contrapunto ahora devuelve dos listas: errores y observaciones
        errores_reglas, observaciones_de_reglas = analizar_reglas_contrapunto(cf_part_identificada, cp_part_identificada)
        
        errores_analisis.extend(errores_reglas) # Acumular errores de reglas
        observaciones_analisis.extend(observaciones_de_reglas) # Acumular observaciones

        evaluacion_final = "Análisis de reglas completado."
        if errores_analisis: # Usar la lista acumulada de errores
            evaluacion_final = f"Se encontraron {len(errores_analisis)} errores en las reglas de contrapunto."
        else:
            evaluacion_final = "¡Ejercicio correcto según las reglas de contrapunto!"
        
        return ResultadoAnalisis(errores_analisis, evaluacion_final, observaciones_analisis)
            
    except Exception as e:
        print(f"ERROR en seccion_analizar_ejercicio (primera_especie/analisis.py): {e}")
        traceback.print_exc() 
        errores_analisis.append(f"Error técnico en análisis de reglas: {str(e)}")
        observaciones_analisis.append(f"Excepción durante el análisis: {str(e)}")
        return ResultadoAnalisis(errores_analisis, evaluacion_predeterminada, observaciones_analisis)
