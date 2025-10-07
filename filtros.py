from PIL import Image
import numpy as np
from shutil import copyfile
from datetime import datetime
import gc

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
        with Image.open(input_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img_copy = img.copy()
        
        img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img_copy
    
    except Exception as e:
        print(f"Error cargando {input_path}: {e}")
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
        image_array = np.array(image, dtype=np.int16)
        
        lum = np.mean(image_array, axis=2, dtype=np.float32) / 255.0
        noise = np.random.randint(-intensidad, intensidad+1, lum.shape, dtype=np.int16)
        scale = 0.5 + 0.5 * lum
        noise_scaled = (noise * scale).astype(np.int16)
        
        noisy_image = np.clip(
            image_array + noise_scaled[:, :, np.newaxis], 
            0, 255
        ).astype(np.uint8)
        
        result = Image.fromarray(noisy_image)
        result.save(output_path, quality=85, optimize=True)
        
        del image, image_array, lum, noise, noise_scaled, noisy_image, result
        gc.collect()
        
    except Exception as e:
        print(f"Error en filtro_grano: {e}")
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
        
        r = img_array[:, :, 0]
        g = img_array[:, :, 1]
        b = img_array[:, :, 2]
        
        offset = np.random.randint(-shift, shift)
        r[:] = np.roll(r, offset, axis=1)
        
        for _ in range(min(glitch_lines, 15)):
            y = np.random.randint(0, max(1, h - 10))
            slice_height = np.random.randint(2, 8)
            x_offset = np.random.randint(-shift, shift)
            
            y_end = min(y + slice_height, h)
            img_array[y:y_end] = np.roll(img_array[y:y_end], x_offset, axis=1)
        
        result = Image.fromarray(img_array)
        result.save(output_path, quality=85, optimize=True)
        
        del image, img_array, r, g, b, result
        gc.collect()
        
    except Exception as e:
        print(f"Error en filtro_glitch: {e}")
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
        
        gray = image.convert("L")
        gray_array = np.array(gray, dtype=np.uint8)
        
        h, w = gray_array.shape
        red_array = np.zeros((h, w, 3), dtype=np.uint8)
        red_array[:, :, 0] = gray_array
        
        result = Image.fromarray(red_array)
        result.save(output_path, quality=85, optimize=True)
        
        del image, gray, gray_array, red_array, result
        gc.collect()
        
    except Exception as e:
        print(f"Error en filtro_rojo: {e}")
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
        gray_array = np.array(gray, dtype=np.float32)
        
        h, w = gray_array.shape
        sepia_array = np.zeros((h, w, 3), dtype=np.uint8)
        
        sepia_array[:, :, 0] = np.clip(gray_array * 1.0, 0, 255).astype(np.uint8)
        sepia_array[:, :, 1] = np.clip(gray_array * 0.8, 0, 255).astype(np.uint8)
        sepia_array[:, :, 2] = np.clip(gray_array * 0.5, 0, 255).astype(np.uint8)
        
        result = Image.fromarray(sepia_array)
        result.save(output_path, quality=85, optimize=True)
        
        del image, gray, gray_array, sepia_array, result
        gc.collect()
        
    except Exception as e:
        print(f"Error en filtro_sepia: {e}")
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
        blue_array[:, :, 2] = gray_array
        
        result = Image.fromarray(blue_array)
        result.save(output_path, quality=85, optimize=True)
        
        del image, gray, gray_array, blue_array, result
        gc.collect()
        
    except Exception as e:
        print(f"Error en filtro_azul: {e}")
        copyfile(input_path, output_path)

# ------------------------------------
# FILTRO DISTORSIÓN ESPIRAL
# ------------------------------------
def filtro_espiral(input_path, output_path, max_size=(800, 600), intensidad=5.0):
    """
    Distorsiona la imagen en forma de espiral desde el centro.
    - intensidad: fuerza de la rotación espiral (1.0-5.0)
                  Valores más altos = espiral más pronunciada
    # Espiral suave (recomendado para Pi Zero 2W)
        filtros.filtro_espiral(base_file, final_file, intensidad=2.0)

    # Espiral moderada
        filtros.filtro_espiral(base_file, final_file, intensidad=3.0)

    # Espiral extrema
        filtros.filtro_espiral(base_file, final_file, intensidad=5.0)
    """
    try:
        image = load_and_resize(input_path, max_size)
        img_array = np.array(image, dtype=np.uint8)
        
        h, w, c = img_array.shape
        center_y, center_x = h // 2, w // 2
        
        output_array = np.zeros_like(img_array)
        
        max_radius = np.sqrt(center_x**2 + center_y**2)
        
        for y in range(h):
            for x in range(w):
                dx = x - center_x
                dy = y - center_y
                distance = np.sqrt(dx**2 + dy**2)
                
                if distance == 0:
                    output_array[y, x] = img_array[y, x]
                    continue
                
                angle = np.arctan2(dy, dx)
                
                rotation = (distance / max_radius) * intensidad
                new_angle = angle + rotation
                
                source_x = int(center_x + distance * np.cos(new_angle))
                source_y = int(center_y + distance * np.sin(new_angle))
                
                if 0 <= source_x < w and 0 <= source_y < h:
                    output_array[y, x] = img_array[source_y, source_x]
                else:
                    output_array[y, x] = 0
        
        result = Image.fromarray(output_array)
        result.save(output_path, quality=85, optimize=True)
        
        del image, img_array, output_array, result
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"Error en filtro_espiral: {e}")
        copyfile(input_path, output_path)
        return False

# ------------------------------------
# FILTRO WES ANDERSON (Paleta Pastel Rosada)
# ------------------------------------
def filtro_wes_anderson(input_path, output_path, max_size=(800, 600)):
    """
    Aplica una paleta de colores pastel inspirada en películas de Wes Anderson.
    Tonos: rosa pastel, durazno, crema, azul suave, amarillo cálido.
    """
    try:
        image = load_and_resize(input_path, max_size)
        img_array = np.array(image, dtype=np.float32)
        
        h, w, _ = img_array.shape
        
        # Paleta de colores Wes Anderson (RGB normalizado 0-1)
        palette_colors = np.array([
            [247, 220, 220],  # Rosa pastel muy suave
            [255, 200, 180],  # Durazno
            [250, 235, 215],  # Crema/Beige
            [230, 190, 200],  # Rosa malva
            [180, 200, 220],  # Azul pastel
            [255, 240, 200],  # Amarillo crema
            [220, 180, 200],  # Lila rosado
            [240, 210, 190],  # Arena cálida
        ], dtype=np.float32)
        
        # Convertir imagen a float para procesamiento
        img_float = img_array / 255.0
        
        # PASO 1: Aumentar ligeramente la saturación pastel
        # Convertir RGB a HSV para manipular saturación
        img_pil = Image.fromarray(img_array.astype(np.uint8))
        
        # Ajustar brillo y contraste para look pastel
        # Reducir contraste (más suave)
        contrast_factor = 0.85
        img_contrast = img_float * contrast_factor + (1 - contrast_factor) * 0.5
        
        # Aumentar brillo general (más luminoso)
        brightness_factor = 1.15
        img_bright = np.clip(img_contrast * brightness_factor, 0, 1)
        
        # PASO 2: Aplicar tinte rosado cálido general
        # Aumentar canal rojo y verde, reducir azul ligeramente
        warm_tint = img_bright.copy()
        warm_tint[:, :, 0] = np.clip(warm_tint[:, :, 0] * 1.08, 0, 1)  # Rojo +8%
        warm_tint[:, :, 1] = np.clip(warm_tint[:, :, 1] * 1.05, 0, 1)  # Verde +5%
        warm_tint[:, :, 2] = np.clip(warm_tint[:, :, 2] * 0.95, 0, 1)  # Azul -5%
        
        # PASO 3: Añadir overlay rosado pastel suave
        pink_overlay = np.array([1.0, 0.92, 0.92], dtype=np.float32)  # Rosa muy suave
        pink_strength = 0.25  # 15% de mezcla
        
        result_float = warm_tint * (1 - pink_strength) + pink_overlay * pink_strength
        
        # PASO 4: Suavizar (reducir ruido digital)
        # Convertir de vuelta a uint8 para filtro bilateral
        result_uint8 = np.clip(result_float * 255, 0, 255).astype(np.uint8)
        result_image = Image.fromarray(result_uint8)
        
        # Aplicar suavizado muy ligero (opcional, puede comentarse si es muy lento)
        # from PIL import ImageFilter
        # result_image = result_image.filter(ImageFilter.SMOOTH)
        
        # PASO 5: Ajuste final de saturación (más pastel)
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Color(result_image)
        result_image = enhancer.enhance(0.9)  # Reducir saturación 10%
        
        # Guardar resultado
        result_image.save(output_path, quality=90, optimize=True)
        
        # Liberar memoria
        del image, img_array, img_float, img_contrast, img_bright, warm_tint
        del result_float, result_uint8, result_image
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"Error en filtro_wes_anderson: {e}")
        copyfile(input_path, output_path)
        return False


# ------------------------------------
# FILTRO MATRIX VERDE SIMPLIFICADO
# ------------------------------------
def filtro_matrix_simple(input_path, output_path, max_size=(800, 600)):
    """
    Versión simplificada del efecto Matrix - más rápida.
    """
    try:
        image = load_and_resize(input_path, max_size)
        
        img_array = np.array(image, dtype=np.uint8)
        
        matrix_array = np.zeros_like(img_array)
        matrix_array[:, :, 1] = img_array[:, :, 1]
        matrix_array[:, :, 0] = img_array[:, :, 1] // 3
        matrix_array[:, :, 2] = img_array[:, :, 1] // 6
        
        h, w, _ = matrix_array.shape
        for _ in range(w * h // 100):
            x, y = np.random.randint(0, w), np.random.randint(0, h)
            if matrix_array[y, x, 1] < 200:
                matrix_array[y, x, 1] = 255
                matrix_array[y, x, 0] = 100
                matrix_array[y, x, 2] = 100
        
        result = Image.fromarray(matrix_array)
        result.save(output_path, quality=90, optimize=True)
        
        del image, img_array, matrix_array, result
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"Error en filtro_matrix_simple: {e}")
        copyfile(input_path, output_path)
        return False

# ------------------------------------
# FILTRO MATRIX CÓDIGO TERMINAL
# ------------------------------------
def filtro_matrix_verde(input_path, output_path, max_size=(800, 600)):
    """
    Efecto Matrix que simula un terminal con texto definido.
    """
    try:
        image = load_and_resize(input_path, max_size)
        gray = image.convert("L")
        gray_array = np.array(gray, dtype=np.uint8)
        
        h, w = gray_array.shape
        matrix_array = np.zeros((h, w, 3), dtype=np.uint8)
        
        matrix_array[:, :, 1] = np.clip(gray_array * 0.8, 0, 255).astype(np.uint8)
        matrix_array[:, :, 0] = gray_array // 8
        matrix_array[:, :, 2] = gray_array // 16
        
        cell_h, cell_w = 3, 2
        
        for y in range(0, h, cell_h):
            for x in range(0, w, cell_w):
                if y < h and x < w and np.random.random() < 0.15:
                    y_end = min(y + cell_h, h)
                    x_end = min(x + cell_w, w)
                    
                    if np.mean(gray_array[y:y_end, x:x_end]) < 100:
                        pattern_type = np.random.choice([1, 2, 3, 4])
                        
                        if pattern_type == 1:
                            center_y = y + cell_h // 2
                            center_x = x + cell_w // 2
                            if center_y < h and center_x < w:
                                matrix_array[center_y, center_x, 1] = 255
                                
                        elif pattern_type == 2:
                            center_x = x + cell_w // 2
                            if center_x < w:
                                matrix_array[y:y_end, center_x, 1] = 255
                                
                        elif pattern_type == 3:
                            center_y = y + cell_h // 2
                            if center_y < h:
                                matrix_array[center_y, x:x_end, 1] = 255
                                
                        else:
                            if np.random.random() > 0.5:
                                for i in range(min(cell_h, cell_w)):
                                    yy = y + i
                                    xx = x + i
                                    if yy < h and xx < w:
                                        matrix_array[yy, xx, 1] = 255
                            else:
                                for i in range(min(cell_h, cell_w)):
                                    yy = y + i
                                    xx = x + (cell_w - 1 - i)
                                    if yy < h and xx >= 0:
                                        matrix_array[yy, xx, 1] = 255
        
        for _ in range(h // 25):
            x = np.random.randint(0, w)
            length = np.random.randint(20, min(60, h // 1.5))
            start_y = np.random.randint(0, max(1, h - length))
            
            for i in range(length):
                y_pos = start_y + i
                if y_pos < h:
                    matrix_array[y_pos, x, 1] = 255
        
        result = Image.fromarray(matrix_array)
        result.save(output_path, quality=95, optimize=True)
        
        del image, gray, gray_array, matrix_array, result
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"Error en filtro_matrix_terminal: {e}")
        copyfile(input_path, output_path)
        return False

# ------------------------------------
# FILTRO NEGATIVO (Inversión de colores)
# -----------------------------------
def filtro_negativo(input_path, output_path, max_size=(800, 600)):
    """
    Invierte todos los colores de la imagen (efecto negativo fotográfico).
    Blanco → Negro, Negro → Blanco, Rojo → Cian, etc.
    """
    try:
        image = load_and_resize(input_path, max_size)
        img_array = np.array(image, dtype=np.uint8)
        
        # Invertir todos los valores: nuevo_valor = 255 - valor_original
        negative_array = 255 - img_array
        
        result = Image.fromarray(negative_array)
        result.save(output_path, quality=85, optimize=True)
        
        # Liberar memoria
        del image, img_array, negative_array, result
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"Error en filtro_negativo: {e}")
        copyfile(input_path, output_path)
        return False






# ------------------------------------
# Función de limpieza de memoria
# ------------------------------------
def cleanup_memory():
    """Fuerza la liberación de memoria."""
    gc.collect()

# ------------------------------------
# Verificar espacio en disco
# ------------------------------------
def check_disk_space(path="/home/fotos"):
    """
    Verifica si hay espacio suficiente en disco (mínimo 50MB).
    """
    try:
        import shutil
        stat = shutil.disk_usage(path)
        free_mb = stat.free / (1024 * 1024)
        return free_mb > 50
    except:
        return True
