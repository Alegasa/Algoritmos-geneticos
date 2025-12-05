import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
import re

# --- CONFIGURACIÓN ---
NOMBRE_ARCHIVO_CSV = 'ProyectoLimones/resultados_finales.csv' 
# ---------------------

def parse_prediction(pred_str):
    """
    Analiza la cadena de texto de la ESP32 y extrae la etiqueta ganadora.
    Ejemplo entrada: "Limon: 0.10 | Botella: 0.90"
    Salida: "Botella"
    """
    if not isinstance(pred_str, str):
        return "Error"
    
    # Separar por el caracter pipe '|'
    parts = pred_str.split('|')
    
    max_score = -1.0
    best_label = "Desconocido"
    
    for part in parts:
        if ':' in part:
            try:
                # Separar "Etiqueta" de "Valor"
                label, score_str = part.split(':')
                score = float(score_str.strip())
                label = label.strip()
                
                # Buscamos quién tiene el score más alto
                if score > max_score:
                    max_score = score
                    best_label = label
            except:
                continue
                
    return best_label

def main():
    print("Cargando datos...")
    try:
        df = pd.read_csv(NOMBRE_ARCHIVO_CSV)
    except FileNotFoundError:
        print(f"ERROR: No encuentro el archivo {NOMBRE_ARCHIVO_CSV}")
        return

    # 1. Limpiar datos y extraer la predicción ganadora
    print("Analizando predicciones...")
    df['Prediccion_Final'] = df['Prediccion_ESP32'].apply(parse_prediction)
    
    # Filtrar errores (si hubo filas vacías)
    df = df[df['Prediccion_Final'] != "Error"]

    # 2. Obtener etiquetas únicas (ordenadas alfabéticamente para que la matriz se vea ordenada)
    labels = sorted(list(set(df['Etiqueta_REAL'].unique()) | set(df['Prediccion_Final'].unique())))

    # 3. Calcular la Matriz de Confusión
    cm = confusion_matrix(df['Etiqueta_REAL'], df['Prediccion_Final'], labels=labels)
    
    # 4. Calcular Precisión Global (Accuracy)
    accuracy = accuracy_score(df['Etiqueta_REAL'], df['Prediccion_Final'])
    print(f"\n============================================")
    print(f" PRECISIÓN GLOBAL (ACCURACY): {accuracy * 100:.2f}%")
    print(f"============================================")
    print("Este es el número que debes comparar con Edge Impulse.\n")

    # 5. Generar Reporte Detallado por clase
    print("--- REPORTE DETALLADO ---")
    print(classification_report(df['Etiqueta_REAL'], df['Prediccion_Final'], target_names=labels))

    # 6. GRAFICAR LA MATRIZ
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.xlabel('Predicción de la ESP32')
    plt.ylabel('Etiqueta Real (Carpeta)')
    plt.title(f'Matriz de Confusión (Accuracy: {accuracy*100:.2f}%)')
    
    print("Generando gráfico...")
    plt.show()

if __name__ == "__main__":
    main()