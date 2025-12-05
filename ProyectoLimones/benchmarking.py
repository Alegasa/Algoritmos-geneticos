import os
import csv
import socket
from flask import Flask, request, Response
from PIL import Image

# --- CONFIGURACIÓN ---
# Asegúrate de que esta ruta sea correcta
ROOT_FOLDER = r"C:\Users\PC\Desktop\dataser_sizer-20251110T003551Z-1-001\dataser_sizer" 
 
# Configuración del servidor
PORT = 5000
HOST_IP = "0.0.0.0" 

# Tamaño del modelo (Edge Impulse)
WIDTH = 96
HEIGHT = 96

app = Flask(__name__)
image_queue = []
current_index = 0
results_file = "resultados_finales.csv"

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def load_images():
    global image_queue
    print("--- ESCANEANDO CARPETAS ---")
    for root, dirs, files in os.walk(ROOT_FOLDER):
        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(root, filename)
                real_label = os.path.basename(root)
                image_queue.append({'path': full_path, 'name': filename, 'label': real_label})
    
    print(f"Total de imágenes encontradas: {len(image_queue)}")
    
    # Preparamos el archivo CSV
    with open(results_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Archivo", "Etiqueta_REAL", "Prediccion_ESP32", "Detalle_Completo"])

@app.route('/get-next-image', methods=['GET'])
def get_next_image():
    global current_index
    
    if current_index >= len(image_queue):
        return "DONE", 204 

    img_info = image_queue[current_index]
    print(f"[{current_index+1}/{len(image_queue)}] Procesando: {img_info['name']}...")
    
    try:
        # 1. Abrir imagen original
        img = Image.open(img_info['path'])
        
        # --- NUEVA ESTRATEGIA: RECORTE CENTRAL (CROP) ---
        # En lugar de rotar o aplastar, cortamos un cuadrado del centro.
        # Esto mantiene la forma REAL del limón (sin hacerlo gordo ni flaco).
        
        w, h = img.size
        min_dim = min(w, h) # Tomamos el lado más corto
        
        # Calculamos las coordenadas para cortar justo el centro
        left = (w - min_dim) / 2
        top = (h - min_dim) / 2
        right = (w + min_dim) / 2
        bottom = (h + min_dim) / 2
        
        # Cortamos
        img = img.crop((left, top, right, bottom))
        
        # 2. CONVERTIR A RGBA (Obligatorio para ESP32)
        img = img.convert('RGBA')
        
        # 3. REDIMENSIONAR A 96x96
        # Ahora que la imagen ya es cuadrada por el corte, 
        # al reducirla NO se deforma.
        img = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        
        # --- DEBUG VISUAL ---
        if current_index == 0: 
            img.save("test_debug_lo_que_ve_la_esp32.png")
            print(">> REVISA 'test_debug_lo_que_ve_la_esp32.png'.")
            print(">> El limón debe verse con su FORMA NATURAL (no aplastado).")

        raw_data = img.tobytes()
        return Response(raw_data, mimetype='application/octet-stream')
        
    except Exception as e:
        print(f"Error procesando imagen: {e}")
        current_index += 1
        return "ERROR", 500
    
@app.route('/report-result', methods=['POST'])
def report_result():
    global current_index
    
    prediction_text = request.data.decode('utf-8')
    
    if current_index < len(image_queue):
        img_info = image_queue[current_index]
        
        clean_pred = prediction_text.replace("\n", " | ")
        print(f" -> Resultado: {clean_pred[:50]}...")
        
        with open(results_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([img_info['name'], img_info['label'], clean_pred, prediction_text])
            
        current_index += 1
        return "OK", 200
    return "DONE", 200

if __name__ == '__main__':
    load_images()
    mi_ip = get_local_ip()
    print(f"\n=============================================")
    print(f" COPIA ESTA IP EN TU CÓDIGO ARDUINO: {mi_ip}")
    print(f"=============================================\n")
    app.run(host=HOST_IP, port=PORT)