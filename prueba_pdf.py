# prueba_pdf.py
import exportar_pdf

svg_path = "partitura_debug.svg"  # Ajusta al nombre que uses en verovio_png
pdf_path = exportar_pdf.generar_pdf_partitura(svg_path, output_pdf="partitura_debug.pdf")

if pdf_path:
    print(f"PDF generado en: {pdf_path}")
else:
    print("Error al generar el PDF de la partitura.")
