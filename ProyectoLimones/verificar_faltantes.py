import os
import csv

# --- CONFIGURACIÓN ---
# Pega aquí la ruta EXACTA de la carpeta "Desecho_95" (o la que quieras revisar)
CARPETA_A_REVISAR = r"C:\Users\PC\Desktop\dataser_sizer-20251110T003551Z-1-001\dataser_sizer"

# El nombre de tu archivo de resultados
ARCHIVO_CSV = "resultados_finales.csv"

def encontrar_faltantes():
    print(f"--- ANALIZANDO: {os.path.basename(CARPETA_A_REVISAR)} ---")
    
    # 1. Obtener lista de archivos REALES en la carpeta
    archivos_en_carpeta = set()
    total_archivos_sistema = 0
    
    if not os.path.exists(CARPETA_A_REVISAR):
        print("¡ERROR! La ruta de la carpeta no existe. Revísala.")
        return

    for filename in os.listdir(CARPETA_A_REVISAR):
        total_archivos_sistema += 1
        # Solo nos importan las imagenes
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            archivos_en_carpeta.add(filename)
    
    print(f"Total objetos en carpeta (Windows): {total_archivos_sistema}")
    print(f"Total imágenes válidas detectadas: {len(archivos_en_carpeta)}")

    # 2. Obtener lista de archivos PROCESADOS en el CSV
    archivos_en_csv = set()
    try:
        with open(ARCHIVO_CSV, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # Saltar cabecera
            for row in reader:
                if row and len(row) > 0:
                    # La columna 0 tiene el nombre del archivo
                    archivos_en_csv.add(row[0])
    except FileNotFoundError:
        print("¡ERROR! No encuentro el archivo .csv")
        return

    # 3. Comparar (Matemáticas de conjuntos)
    # Faltantes = Lo que hay en carpeta MENOS lo que hay en CSV
    # (Pero solo comparamos los nombres que coinciden con la carpeta actual)
    
    # Filtramos el CSV para ver solo los que deberían estar en esta carpeta
    # (Asumiendo que los nombres son únicos o buscando intersección)
    faltantes = archivos_en_carpeta - archivos_en_csv
    
    print(f"------------------------------------------------")
    print(f"Imágenes que NO aparecen en el Excel: {len(faltantes)}")
    print(f"------------------------------------------------")
    
    if len(faltantes) > 0:
        print("LISTA DE FALTANTES:")
        for falta in faltantes:
            print(f" - {falta}")
    else:
        diff = total_archivos_sistema - len(archivos_en_carpeta)
        print("¡TODO PERFECTO! Todas las imágenes válidas están en el Excel.")
        if diff > 0:
            print(f"(La diferencia de {diff} archivos son cosas de sistema como Thumbs.db o carpetas ocultas)")

if __name__ == "__main__":
    encontrar_faltantes()