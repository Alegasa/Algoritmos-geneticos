/*
 * ESP32 Client - Benchmarking Automatizado
 * Solicita imágenes al PC, clasifica y devuelve el resultado.
 */

#include <WiFi.h>
#include <HTTPClient.h>

// --- INCLUDES DE EDGE IMPULSE (Ajusta el nombre si es necesario) ---
#include <Dataset_Limones_inferencing.h> 
#include "edge-impulse-sdk/dsp/image/image.hpp"

// --- DATOS WIFI ---
const char* ssid = "IZZI-CCBB";
const char* password = "50955128CCBB";

// --- DATOS DEL SERVIDOR (TU PC) ---
const char* server_ip = "192.168.0.14"; // <--- CAMBIA ESTO POR LA IP QUE TE DE PYTHON
const int server_port = 5000;

// --- CONFIGURACIÓN MODELO ---
#define EI_MODEL_INPUT_WIDTH     96
#define EI_MODEL_INPUT_HEIGHT    96
#define EI_MODEL_INPUT_BUFFER_SIZE  (EI_MODEL_INPUT_WIDTH * EI_MODEL_INPUT_HEIGHT * 4)

// Variables Globales
uint8_t *ei_pixel_buffer = NULL; 
bool is_finished = false;

// Helper: Convierte RGBA (que envía Python) a RGB (para Edge Impulse)
static int ei_camera_get_data(size_t offset, size_t length, float *out_ptr) {
    size_t pixel_ix = offset * 4; 
    size_t pixels_left = length;
    size_t out_ptr_ix = 0;

    while (pixels_left != 0) {
        // Extraer RGB e ignorar Alpha
        out_ptr[out_ptr_ix] = (ei_pixel_buffer[pixel_ix + 0] << 16) + 
                              (ei_pixel_buffer[pixel_ix + 1] << 8)  + 
                               ei_pixel_buffer[pixel_ix + 2];         
        out_ptr_ix++;
        pixel_ix += 4; 
        pixels_left--;
    }
    return 0;
}

void setup() {
  Serial.begin(115200);
  
  // Reservar memoria para recibir la imagen
  ei_pixel_buffer = (uint8_t *)malloc(EI_MODEL_INPUT_BUFFER_SIZE);
  if (!ei_pixel_buffer) {
    Serial.println("Error CRITICO: No hay RAM suficiente para el buffer.");
    return;
  }

  // Conectar WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Conectado.");
  Serial.print("IP ESP32: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (is_finished) return; // Si terminamos, no hacemos nada más.

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    // 1. PEDIR IMAGEN AL PC
    String url_get = String("http://") + server_ip + ":" + server_port + "/get-next-image";
    Serial.println(">> Pidiendo imagen...");
    
    http.begin(url_get);
    int httpCode = http.GET();

    if (httpCode == 200) {
      // Recibir los bytes
      int len = http.getSize();
      WiFiClient *stream = http.getStreamPtr();
      
      if (len == EI_MODEL_INPUT_BUFFER_SIZE) {
        int pos = 0;
        // Leer el stream en el buffer
        while (http.connected() && (len > 0 || len == -1)) {
          size_t size = stream->available();
          if (size) {
            int c = stream->readBytes(ei_pixel_buffer + pos, size);
            pos += c;
            if (len > 0) len -= c;
          }
          if (len == 0) break;
        }
        
        Serial.println("Imagen recibida. Clasificando...");
        
        // 2. CLASIFICAR CON EDGE IMPULSE
        ei::signal_t signal;
        signal.total_length = EI_MODEL_INPUT_WIDTH * EI_MODEL_INPUT_HEIGHT;
        signal.get_data = &ei_camera_get_data;

        ei_impulse_result_t result = { 0 };
        EI_IMPULSE_ERROR err = run_classifier(&signal, &result, false);

        String reporte = "";
        if (err != EI_IMPULSE_OK) {
            reporte = "Error de inferencia";
            Serial.printf("Error EI: %d\n", err);
        } else {
            // Crear string con resultados
            for (uint16_t i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
                reporte += String(ei_classifier_inferencing_categories[i]) + ": " + String(result.classification[i].value, 4) + "\n";
            }
        }
        
        http.end(); // Cerrar conexión GET

        // 3. ENVIAR RESULTADO AL PC
        String url_post = String("http://") + server_ip + ":" + server_port + "/report-result";
        http.begin(url_post);
        http.addHeader("Content-Type", "text/plain");
        int postCode = http.POST(reporte);
        
        if (postCode == 200) {
            Serial.println("Reporte enviado OK.");
        } else {
            Serial.println("Fallo enviando reporte.");
        }
        http.end(); // Cerrar conexión POST

      } else {
        Serial.println("Error: Tamaño de imagen incorrecto.");
        http.end();
      }
      
    } else if (httpCode == 204) {
      // Código 204 significa "No Content" -> Python dice que ya acabó
      Serial.println("\n-----------------------------");
      Serial.println("¡TODAS LAS IMÁGENES PROCESADAS!");
      Serial.println("-----------------------------");
      is_finished = true;
      http.end();
    } else {
      Serial.printf("Error conectando al servidor: %d\n", httpCode);
      http.end();
      delay(2000); // Reintentar si falló la conexión
    }
  }
  
  delay(100); // Pequeña pausa
}