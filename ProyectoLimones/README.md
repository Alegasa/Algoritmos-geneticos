# Clasificación Automatizada de Calidad de Limones con TinyML (ESP32 + Edge Impulse)

![Status](https://img.shields.io/badge/Status-Completed-success)
![Platform](https://img.shields.io/badge/Platform-ESP32-blue)
![Framework](https://img.shields.io/badge/AI-Edge%20Impulse-green)
![Language](https://img.shields.io/badge/Language-Python%20%7C%20C%2B%2B-orange)

## Descripción del Proyecto

Este proyecto implementa un sistema de visión artificial embebido (**TinyML**) capaz de clasificar limones persas en 6 categorías de calidad/calibre utilizando un microcontrolador **ESP32-CAM** (u otro módulo ESP32 compatible).

El objetivo principal fue validar si un modelo de **Clasificación de Imágenes (MobileNetV2)** optimizado para hardware de bajos recursos podría distinguir sutiles diferencias de tamaño entre clases de limones vecinos con una precisión aceptable para la industria.

Para lograr una validación rigurosa sin depender de una cámara física en tiempo real durante el desarrollo, se diseñó una herramienta de **Benchmarking Automatizado en Python** que inyecta imágenes de prueba al ESP32 vía WiFi, simulando una banda transportadora de alta velocidad.

## Clases del Dataset

El modelo fue entrenado para identificar las siguientes categorías (basadas en estándares de "Desecho" o calibre):

| Etiqueta | Descripción | Desafío |
| :--- | :--- | :--- |
| `Desecho_75` | Calibre muy pequeño | Fácil de distinguir |
| `Desecho_95` | Pequeño | Distintivo por área |
| `Desecho_115` | Mediano | **Confusión alta con 140** |
| `Desecho_140` | Mediano-Grande | **Confusión alta con 115** |
| `Desecho_165` | Grande | Fácil de distinguir |
| `Desecho_200` | Muy Grande | Fácil de distinguir |

## Arquitectura de Validación (Hardware-in-the-Loop)

En lugar de validar el modelo solo en la nube (Web Testing), se creó un entorno de pruebas real:

1.  **Servidor de Imágenes (Python):**
    * Escanea un dataset local de validación.
    * Aplica pre-procesamiento geométrico (ver sección *Retos Técnicos*).
    * Convierte imágenes a **RGBA** (4 canales) para compatibilidad con el buffer del ESP32.
    * Expone un endpoint HTTP (`GET /get-next-image`).
2.  **Cliente TinyML (ESP32):**
    * Descarga la imagen cruda byte a byte.
    * Ejecuta la inferencia usando la librería C++ de Edge Impulse.
    * Retorna la predicción y el tiempo de cómputo al servidor (`POST /report-result`).
3.  **Análisis de Datos:**
    * Python genera una matriz de confusión en tiempo real y calcula el *Accuracy* real del hardware.

## Retos Técnicos y Soluciones (Diferencias Clave)

Durante el desarrollo, descubrimos discrepancias críticas entre la teoría (simulación web) y la práctica (ESP32).

### 1. El Problema de la "Deformación Geométrica" (Squash vs. Crop)
**El Problema:** Inicialmente, el modelo confundía drásticamente las clases `115` y `140`.
**La Causa:** El método de redimensión estándar ("Squash") aplastaba las imágenes rectangulares para forzarlas en el cuadro de 96x96 píxeles.
* Si el limón entraba vertical, se aplastaba y parecía más ancho ("gordo"), pareciéndose a un calibre mayor.
* Si se rotaba, se deformaba a la inversa.

**La Solución:** Implementamos un algoritmo de **"Center Crop" (Recorte Central)** y **"Fit Shortest Axis"**.
* En lugar de deformar la imagen, recortamos un cuadrado perfecto del centro del limón.
* Esto preservó la **geometría natural** (redondez) del fruto, permitiendo al modelo distinguir el volumen real sin distorsiones artificiales.

### 2. Formato de Color (RGB vs. RGBA)
La librería de inferencia en el ESP32 calcula los offsets de memoria en bloques de 4 bytes (`offset * 4`). Las imágenes enviadas originalmente en RGB (3 bytes) causaban desbordamientos de memoria y corrupción visual. Se corrigió el script de Python para enviar `RGBA`, sincronizando la comunicación.

## 📊 Resultados y Validación

Logramos demostrar que la implementación en hardware real superó las expectativas teóricas de la plataforma de entrenamiento.

### Comparativa de Precisión (Accuracy)

| Entorno de Prueba | Método de Imagen | Precisión Obtenida | Notas |
| :--- | :--- | :--- | :--- |
| **Edge Impulse (Web)** | Squash / Resize | **81.33%** | Estimación conservadora con datos de prueba. |
| **ESP32 Real (Python)** | **Center Crop (Optimizado)** | **88.14%** | Validación con miles de imágenes reales. |

> **Conclusión:** La optimización geométrica ("Center Crop") implementada en el código final mejoró la capacidad del modelo en un **~7%** respecto a la simulación inicial, demostrando la importancia del pre-procesamiento correcto en TinyML.

### Matriz de Confusión Final (Hardware)
*(Ver imagen adjunta en repositorio `img/matriz_final.png`)*

Se observa una precisión casi perfecta en los extremos (Clases 75, 95, 165, 200). La mayor parte del error residual (12%) se concentra lógicamente entre las clases vecinas 115 y 140, que poseen características visuales extremadamente similares.

## 💻 Instrucciones de Uso

### Requisitos
* Python 3.x (`pip install flask pillow`)
* Arduino IDE (con soporte ESP32 instalado)
* Librería de Edge Impulse exportada como Arduino Library.

### Pasos para Ejecutar
1.  **Configurar Arduino:**
    * Abrir `ESP32_Inference.ino`.
    * Modificar `ssid` y `password` con tus credenciales WiFi.
    * Cargar el código al ESP32.
2.  **Iniciar Servidor Python:**
    * Modificar la ruta `ROOT_FOLDER` en `server.py` apuntando a tu dataset de prueba.
    * Ejecutar: `python server.py`
    * Copiar la IP que se imprime en la consola.
3.  **Sincronizar:**
    * Pegar la IP del servidor en la variable `server_ip` del código Arduino y volver a subir si es necesario.
    * Abrir el Monitor Serie para ver el progreso.

## 🤝 Créditos

* **Plataforma de Entrenamiento:** [Edge Impulse](https://www.edgeimpulse.com/)
* **Hardware:** Espressif Systems (ESP32)
* **Autor:** Ing. Alexis Gabriel Saldaña Carvajal e Ing. Victoria Elizabeth Juárez Morales

---