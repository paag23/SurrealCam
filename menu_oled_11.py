from PIL import Image
import numpy as np
from shutil import copyfile
from datetime import datetime
import gc  # 🔹 NUEVO: Garbage collector

# ---------------------------
# Generar nombre de archivo
# ---------------------------
def generate_filename(prefix, ext):
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    return f"{prefix}_{timestamp}.{ext}"

# ---------------------------
# Filtro: sin cambios (solo copia)
# ---------------------------
def filtro_normal(input_path, output_path):
    """Copia la imagen sin modificaciones."""
    copyfile(input_path, output_path)

# ---------------------------
# HELPER: Cargar y redimensionar imagen de forma segura
# ---------------------------
def load_and_resize(input_path, max_size=(800, 600)):
    """
    Carga la imagen y la redimensiona de forma eficiente en memoria.
    Retorna: imagen PIL en modo RGB
    """
    try:
        # 🔹 CRÍTICO: Abrir en modo lazy (no carga toda la imagen en RAM aún)
        with Image.open(input_path) as img:
            # Convertir a RGB si es necesario
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # 🔹 OPTIMIZADO: Copiar para liberar el file descriptor
            img_copy = img.copy()
        
        # Redimensionar con LANCZOS para mejor calidad
        img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img_copy
    
    except Exception as e:
        print(f"⚠️ Error cargando {input_path}: {e}")
        raise

# ---------------------------
# Filtro: grano analógico (optimizado)
# ---------------------------
def filtro_grano_analogico(input_path, output_path, intensidad=20, max_size=(800, 600)):
    """
    Aplica efecto de grano analógico (film grain).
    - intensidad: cantidad de ruido (10-30 recomendado)
    - max_size: resolución máxima de salida
    """
    try:
        image = load_and_resize(input_path, max_size)
        
        # 🔹 OPTIMIZADO: Usar dtype más eficiente
        image_array = np.array(image, dtype=np.int16)
        
        # Calcular luminancia (media de RGB)
        lum = np.mean(image_array, axis=2, dtype=np.float32) / 255.0
        
        # Generar ruido
        noise = np.random.randint(-intensidad, intensidad+1, lum.shape, dtype=np.int16)
        
        # Escalar ruido según luminancia (más visible en sombras)
        scale = 0.5 + 0.5 * lum
        noise_scaled = (noise * scale).astype(np.int16)
        
        # 🔹 OPTIMIZADO: Aplicar ruido en una sola operación
        noisy_image = np.clip(
            image_array + noise_scaled[:, :, np.newaxis], 
            0, 255
        ).astype(np.uint8)
        
        # Guardar con compresión óptima
        result = Image.fromarray(noisy_image)
        result.save(output_path, quality=85, optimize=True)
        
        # 🔹 CRÍTICO: Liberar memoria
        del image, image_array, lum, noise, noise_scaled, noisy_image, result
        gc.collect()
        
    except Exception as e:
        print(f"❌ Error en filtro_grano: {e}")
        # En caso de error, copiar original
        copyfile(input_path, output_path)

# ------------------------------------
# FILTRO GLITCH DIGITAL (optimizado)
# ------------------------------------
def filtro_glitch_digital(input_path, output_path, max_size=(800, 600), shift=15, glitch_lines=20):
    """
    Aplica efecto glitch digital con desplazamiento de canales.
    - shift: desplazamiento máximo de píxeles
    - glitch_lines: número de líneas glitcheadas
    """
    try:
        image = load_and_resize(input_path, max_size)
        img_array = np.array(image, dtype=np.uint8)
        
        h, w, _ = img_array.shape
        
        # 🔹 OPTIMIZADO: Trabajar con views en lugar de copias
        r = img_array[:, :, 0]
        g = img_array[:, :, 1]
        b = img_array[:, :, 2]
        
        # Desplazar canal rojo
        offset = np.random.randint(-shift, shift)
        r[:] = np.roll(r, offset, axis=1)
        
        # 🔹 OPTIMIZADO: Aplicar glitches en menos iteraciones
        for _ in range(min(glitch_lines, 15)):  # Limitar a 15 líneas máximo
            y = np.random.randint(0, max(1, h - 10))
            slice_height = np.random.randint(2, 8)
            x_offset = np.random.randint(-shift, shift)
            
            # 🔹 CRÍTICO: Verificar límites antes de aplicar
            y_end = min(y + slice_height, h)
            img_array[y:y_end] = np.roll(img_array[y:y_end], x_offset, axis=1)
        
        # Guardar resultado
        result = Image.fromarray(img_array)
        result.save(output_path, quality=85, optimize=True)
        
        # Liberar memoria
        del image, img_array, r, g, b, result
        gc.collect()
        
    except Exception as e:
        print(f"❌ Error en filtro_glitch: {e}")
        copyfile(input_path, output_path)

# ------------------------------------
# FILTRO ROJO/NEGRO (contraste luminoso)
# ------------------------------------
def filtro_rojo_contraste(input_path, output_path, max_size=(800, 600)):
    """
    Convierte la imagen a escala rojo/negro según luminosidad.
    """
    try:
        image = load_and_resize(input_path, max_size)
        
        # Convertir a escala de grises
        gray = image.convert("L")
        gray_array = np.array(gray, dtype=np.uint8)
        
        # 🔹 OPTIMIZADO: Crear array directamente con el tamaño correcto
        h, w = gray_array.shape
        red_array = np.zeros((h, w, 3), dtype=np.uint8)
        red_array[:, :, 0] = gray_array  # Canal rojo = brillo
        
        # Guardar resultado
        result = Image.fromarray(red_array)
        result.save(output_path, quality=85, optimize=True)
        
        # Liberar memoria
        del image, gray, gray_array, red_array, result
        gc.collect()
        
    except Exception as e:
        print(f"❌ Error en filtro_rojo: {e}")
        copyfile(input_path, output_path)

# ------------------------------------
# FILTRO SEPIA (contraste luminoso)
# ------------------------------------
def filtro_sepia_contraste(input_path, output_path, max_size=(800, 600)):
    """
    Convierte la imagen a tonos sepia según luminosidad.
    """
    try:
        image = load_and_resize(input_path, max_size)
        
        gray = image.convert("L")
        gray_array = np.array(gray, dtype=np.float32)  # 🔹 float32 para cálculos
        
        h, w = gray_array.shape
        sepia_array = np.zeros((h, w, 3), dtype=np.uint8)
        
        # 🔹 OPTIMIZADO: Calcular todos los canales en una sola pasada
        sepia_array[:, :, 0] = np.clip(gray_array * 1.0, 0, 255).astype(np.uint8)  # Rojo
        sepia_array[:, :, 1] = np.clip(gray_array * 0.8, 0, 255).astype(np.uint8)  # Verde
        sepia_array[:, :, 2] = np.clip(gray_array * 0.5, 0, 255).astype(np.uint8)  # Azul
        
        result = Image.fromarray(sepia_array)
        result.save(output_path, quality=85, optimize=True)
        
        # Liberar memoria
        del image, gray, gray_array, sepia_array, result
        gc.collect()
        
    except Exception as e:
        print(f"❌ Error en filtro_sepia: {e}")
        copyfile(input_path, output_path)

# ------------------------------------
# FILTRO AZUL (contraste luminoso)
# ------------------------------------
def filtro_azul_contraste(input_path, output_path, max_size=(800, 600)):
    """
    Convierte la imagen a escala azul/negro según luminosidad.
    """
    try:
        image = load_and_resize(input_path, max_size)
        
        gray = image.convert("L")
        gray_array = np.array(gray, dtype=np.uint8)
        
        h, w = gray_array.shape
        blue_array = np.zeros((h, w, 3), dtype=np.uint8)
        blue_array[:, :, 2] = gray_array  # Canal azul = brillo
        
        result = Image.fromarray(blue_array)
        result.save(output_path, quality=85, optimize=True)
        
        # Liberar memoria
        del image, gray, gray_array, blue_array, result
        gc.collect()
        
    except Exception as e:
        print(f"❌ Error en filtro_azul: {e}")
        copyfile(input_path, output_path)

# ------------------------------------
# 🔹 NUEVO: Función de limpieza de memoria
# ------------------------------------
def cleanup_memory():
    """Fuerza la liberación de memoria."""
    gc.collect()

# ------------------------------------
# 🔹 NUEVO: Verificar espacio en disco
# ------------------------------------
def check_disk_space(path="/home/fotos"):
    """
    Verifica si hay espacio suficiente en disco (mínimo 50MB).
    Retorna True si hay espacio, False si no.
    """
    try:
        import shutil
        stat = shutil.disk_usage(path)
        free_mb = stat.free / (1024 * 1024)
        return free_mb > 50
    except:
        return True  # Asumir que hay espacio si falla la verificación

# ------------------------------------
# FILTRO MATRIX CÓDIGO TIPO TERMINAL (máxima delgadez)
# -----------------------------------
def filtro_matrix_verde(input_path, output_path, max_size=(800, 600)):
    """
    Efecto Matrix que simula un terminal con texto delgado y definido.
    """
    try:
        image = load_and_resize(input_path, max_size)
        gray = image.convert("L")
        gray_array = np.array(gray, dtype=np.uint8)
        
        h, w = gray_array.shape
        matrix_array = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Base verde más oscura para mejor contraste
        matrix_array[:, :, 1] = np.clip(gray_array * 0.8, 0, 255).astype(np.uint8)
        matrix_array[:, :, 0] = gray_array // 8
        matrix_array[:, :, 2] = gray_array // 16
        
        # 🔹 CÓDIGO TIPO TERMINAL - LÍNEAS MUY DELGADAS
        # Usar bloques muy pequeños para máxima definición
        cell_h, cell_w = 3, 2
        
        for y in range(0, h, cell_h):
            for x in range(0, w, cell_w):
                if y < h and x < w and np.random.random() < 0.15:
                    # Solo en áreas oscuras
                    y_end = min(y + cell_h, h)
                    x_end = min(x + cell_w, w)
                    
                    if np.mean(gray_array[y:y_end, x:x_end]) < 100:
                        
                        # 🔹 PATRONES MUY DELGADOS:
                        pattern_type = np.random.choice([1, 2, 3, 4])
                        
                        if pattern_type == 1:  # Punto individual
                            center_y = y + cell_h // 2
                            center_x = x + cell_w // 2
                            if center_y < h and center_x < w:
                                matrix_array[center_y, center_x, 1] = 255
                                
                        elif pattern_type == 2:  # Línea vertical de 1 píxel
                            center_x = x + cell_w // 2
                            if center_x < w:
                                matrix_array[y:y_end, center_x, 1] = 255
                                
                        elif pattern_type == 3:  # Línea horizontal de 1 píxel
                            center_y = y + cell_h // 2
                            if center_y < h:
                                matrix_array[center_y, x:x_end, 1] = 255
                                
                        else:  # Esquina de 1 píxel
                            if np.random.random() > 0.5:
                                # Esquina superior izquierda a inferior derecha
                                for i in range(min(cell_h, cell_w)):
                                    yy = y + i
                                    xx = x + i
                                    if yy < h and xx < w:
                                        matrix_array[yy, xx, 1] = 255
                            else:
                                # Esquina superior derecha a inferior izquierda
                                for i in range(min(cell_h, cell_w)):
                                    yy = y + i
                                    xx = x + (cell_w - 1 - i)
                                    if yy < h and xx >= 0:
                                        matrix_array[yy, xx, 1] = 255
        
        # 🔹 LLUVIA MUY DELGADA (1 píxel de ancho)
        for _ in range(h // 25):
            x = np.random.randint(0, w)
            length = np.random.randint(20, min(60, h // 1.5))
            start_y = np.random.randint(0, max(1, h - length))
            
            for i in range(length):
                y_pos = start_y + i
                if y_pos < h:
                    matrix_array[y_pos, x, 1] = 255  # Línea de 1 píxel
        
        result = Image.fromarray(matrix_array)
        result.save(output_path, quality=95, optimize=True)
        
        del image, gray, gray_array, matrix_array, result
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"❌ Error en filtro_matrix_terminal: {e}")
        copyfile(input_path, output_path)
        return False





# ------------------------------------
# FILTRO MATRIX VERDE SIMPLIFICADO (más rápido)
# ------------------------------------
def filtro_matrix_simple(input_path, output_path, max_size=(800, 600)):
    """
    Versión simplificada del efecto Matrix - más rápida y con menos memoria.
    """
    try:
        image = load_and_resize(input_path, max_size)
        
        # Convertir directamente a matriz numpy
        img_array = np.array(image, dtype=np.uint8)
        
        # 🔹 EFECTO PRINCIPAL: Enfatizar canal verde, reducir rojo y azul
        # Fórmula: Verde = (original), Rojo = verde/3, Azul = verde/6
        matrix_array = np.zeros_like(img_array)
        matrix_array[:, :, 1] = img_array[:, :, 1]  # Verde igual
        matrix_array[:, :, 0] = img_array[:, :, 1] // 3  # Rojo = verde/3  
        matrix_array[:, :, 2] = img_array[:, :, 1] // 6  # Azul = verde/6
        
        # 🔹 AGREGAR PUNTOS BRILLANTES VERDES (simulan código)
        h, w, _ = matrix_array.shape
        for _ in range(w * h // 100):  # ~1% de píxeles serán código
            x, y = np.random.randint(0, w), np.random.randint(0, h)
            if matrix_array[y, x, 1] < 200:  # Solo en áreas no muy brillantes
                matrix_array[y, x, 1] = 255  # Verde máximo
                matrix_array[y, x, 0] = 100  # Rojo medio
                matrix_array[y, x, 2] = 100  # Azul medio
        
        result = Image.fromarray(matrix_array)
        result.save(output_path, quality=90, optimize=True)
        
        # Liberar memoria
        del image, img_array, matrix_array, result
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"❌ Error en filtro_matrix_simple: {e}")
        copyfile(input_path, output_path)
        return False
