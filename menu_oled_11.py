import os
import pigpio
import time
import subprocess
from datetime import datetime
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import filtros

# ---------------------------
# Configuración OLED
# ---------------------------
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)
device.clear()

try:
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 9)
except:
    font = ImageFont.load_default()

# ---------------------------
# Botones GPIO con debounce
# ---------------------------
BTN_UP = 17
BTN_DOWN = 22
BTN_ENTER = 27
BTN_TAKE = 24

pi = pigpio.pi()
if not pi.connected:
    print("⚠️ No se pudo conectar a pigpio daemon")
    exit()

for pin in [BTN_UP, BTN_DOWN, BTN_ENTER, BTN_TAKE]:
    pi.set_mode(pin, pigpio.INPUT)
    pi.set_pull_up_down(pin, pigpio.PUD_UP)

# Variables de debounce
last_btn_time = {BTN_UP: 0, BTN_DOWN: 0, BTN_ENTER: 0, BTN_TAKE: 0}
DEBOUNCE_TIME = 0.25  # 250ms

def read_button(pin):
    """Lee botón con debounce."""
    global last_btn_time
    current_time = time.time()
    
    if pi.read(pin) == 0:  # Botón presionado
        if current_time - last_btn_time[pin] > DEBOUNCE_TIME:
            last_btn_time[pin] = current_time
            return True
    return False

# ---------------------------
# Carpeta de fotos
# ---------------------------
PHOTO_DIR = "/home/fotos"
os.makedirs(PHOTO_DIR, exist_ok=True)

# ---------------------------
# Configuración Bluetooth
# ---------------------------
MAC_ANDROID = "XXXXXXXXXXXXXXXXXX"
CANAL_OBEX = "12"

# ---------------------------
# Menús
# ---------------------------
menu_options = [
    "Foto B/N",
    "Foto Color",
    "Filtros",
    "Borrar Fotos",
    "Enviar a Android",
    "Bluetooth",
    "Apagar Raspberry",
]

submenu_filtros_options = [
    "Normal",
    "Grano Analogico",
    "Glitch Digital",
    "Rojo Contraste",
    "Sepia",
    "Azul Klein",
    "Verde"
]

# ---------------------------
# Variables de estado
# ---------------------------
current_index = 0
scroll_offset = 0
submenu_active = False
filtro_index = 0
filtro_scroll = 0
filtro_seleccionado = "Normal"
running = True
bluetooth_active = True

# ---------------------------
# Funciones de Display CORREGIDAS
# ---------------------------

def get_text_size(draw, text, font):
    """Obtiene el tamaño del texto de forma compatible con Pillow 10+."""
    try:
        # Para Pillow 10+
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except:
        # Fallback para versiones antiguas
        return draw.textsize(text, font=font)

def show_message(text, duration=2):
    """Muestra un mensaje centrado en la pantalla."""
    image = Image.new("1", (device.width, device.height), "black")
    draw = ImageDraw.Draw(image)
    
    # Dividir texto en múltiples líneas si es muy largo
    lines = []
    words = text.split()
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        w, h = get_text_size(draw, test_line, font)
        if w <= device.width - 4:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    # Centrar líneas verticalmente
    total_height = len(lines) * 12
    y = (device.height - total_height) // 2
    
    for line in lines:
        w, h = get_text_size(draw, line, font)
        x = (device.width - w) // 2
        draw.text((x, y), line, font=font, fill="white")
        y += 12
    
    device.display(image)
    time.sleep(duration)

def show_progress(main_text, sub_text=""):
    """Muestra mensaje de progreso sin borrar automáticamente."""
    image = Image.new("1", (device.width, device.height), "black")
    draw = ImageDraw.Draw(image)
    
    # Texto principal centrado
    w, h = get_text_size(draw, main_text, font)
    x = (device.width - w) // 2
    y = (device.height - h) // 2 - 6
    draw.text((x, y), main_text, font=font, fill="white")
    
    # Subtexto
    if sub_text:
        w2, h2 = get_text_size(draw, sub_text, font)
        x2 = (device.width - w2) // 2
        y2 = y + 14
        draw.text((x2, y2), sub_text, font=font, fill="white")
    
    device.display(image)

def draw_menu(selected_index, offset, items, title="Menu"):
    """Dibuja el menú en la pantalla OLED."""
    image = Image.new("1", (device.width, device.height), "black")
    draw = ImageDraw.Draw(image)
    draw.text((2, 0), title, font=font, fill="white")

    # Icono de Bluetooth
    icon_color = "white" if bluetooth_active else "black"
    draw.rectangle((device.width-20, 0, device.width-15, 5), fill=icon_color)

    max_visible = 3
    start_idx = offset
    end_idx = min(offset + max_visible, len(items))
    y = 12
    
    for i in range(start_idx, end_idx):
        prefix = "->" if i == selected_index else "  "
        text = f"{prefix} {items[i]}"
        # Truncar si es muy largo
        if len(text) > 20:
            text = text[:17] + "..."
        draw.text((2, y), text, font=font, fill="white")
        y += 12

    # Indicadores de scroll
    if offset > 0:
        draw.text((device.width - 10, 2), "↑", font=font, fill="white")
    if end_idx < len(items):
        draw.text((device.width - 10, device.height - 10), "↓", font=font, fill="white")
    
    device.display(image)

def update_display():
    """Actualiza el display según el menú activo."""
    if submenu_active:
        draw_menu(filtro_index, filtro_scroll, submenu_filtros_options, title="Filtros")
    else:
        draw_menu(current_index, scroll_offset, menu_options, title="Menu")

# ---------------------------
# Navegación
# ---------------------------

def scroll_up():
    """Navega hacia arriba en el menú."""
    global current_index, scroll_offset, filtro_index, filtro_scroll
    max_visible = 3
    
    if submenu_active:
        filtro_index = (filtro_index - 1) % len(submenu_filtros_options)
        if filtro_index < filtro_scroll:
            filtro_scroll = filtro_index
    else:
        current_index = max(0, current_index - 1)
        if current_index < scroll_offset:
            scroll_offset = current_index
    update_display()

def scroll_down():
    """Navega hacia abajo en el menú."""
    global current_index, scroll_offset, filtro_index, filtro_scroll
    max_visible = 3
    
    if submenu_active:
        filtro_index = (filtro_index + 1) % len(submenu_filtros_options)
        if filtro_index >= filtro_scroll + max_visible:
            filtro_scroll = filtro_index - max_visible + 1
    else:
        current_index = min(len(menu_options) - 1, current_index + 1)
        if current_index >= scroll_offset + max_visible:
            scroll_offset = current_index - max_visible + 1
    update_display()

# ---------------------------
# Funciones del sistema
# ---------------------------

def toggle_bluetooth():
    """Activa/desactiva Bluetooth."""
    global bluetooth_active
    bluetooth_active = not bluetooth_active
    estado = "Activo" if bluetooth_active else "Inactivo"
    show_message(f"Bluetooth {estado}", duration=1.5)
    update_display()

def delete_photos():
    """Borra todas las fotos de la carpeta."""
    try:
        files = [f for f in os.listdir(PHOTO_DIR) if f.endswith(('.jpg', '.dng'))]
        count = len(files)
        
        if count == 0:
            show_message("No hay fotos", duration=2)
            update_display()
            return
        
        show_progress("Borrando...", f"{count} archivos")
        
        for file in files:
            os.remove(os.path.join(PHOTO_DIR, file))
        
        show_message(f"✅ {count} fotos borradas", duration=2)
        
    except Exception as e:
        show_message("❌ Error borrando", duration=2)
    
    update_display()

# ---------------------------
# Enviar foto individual por BT (menú) - VERSIÓN QUE FUNCIONA
# ---------------------------
def send_single_photo_menu():
    fotos = [f for f in os.listdir(PHOTO_DIR) if f.lower().endswith(('.jpg', '.dng'))]
    if not fotos:
        show_message("No hay fotos", duration=2)
        return

    index = 0
    # Esperar a soltar ENTER
    while pi.read(BTN_ENTER) == 0:
        time.sleep(0.05)

    while True:
        nombre = fotos[index]
        linea1 = nombre[:14]
        linea2 = nombre[14:28] if len(nombre) > 14 else ""

        image = Image.new("1", (device.width, device.height), "black")
        draw = ImageDraw.Draw(image)
        draw.text((2, 0), "Enviar Foto", font=font, fill="white")
        draw.text((2, 15), f"-> {linea1}", font=font, fill="white")
        if linea2:
            draw.text((5, 27), f"{linea2}", font=font, fill="white")
        draw.text((2, 42), "ENTER: Enviar", font=font, fill="white")
        draw.text((2, 54), "TAKE: Cancelar", font=font, fill="white")
        device.display(image)

        if pi.read(BTN_UP) == 0:
            index = (index - 1) % len(fotos)
            time.sleep(0.15)
        elif pi.read(BTN_DOWN) == 0:
            index = (index + 1) % len(fotos)
            time.sleep(0.15)
        elif pi.read(BTN_ENTER) == 0:
            ruta_completa = os.path.join(PHOTO_DIR, fotos[index])
            show_message("📤 Enviando...", 0.8)
            try:
                comando = [
                    "obexftp", "--nopath", "--noconn", "--uuid", "none",
                    "-b", MAC_ANDROID, "-B", CANAL_OBEX, "-p", ruta_completa
                ]
                # Si es una imagen sin filtro (posible gran tamaño), damos más tiempo
                timeout = 240  if not any(t in nombre.upper() for t in ["GLITCH", "GRAIN", "ROJO", "SEP", "AZUL"]) else 90
                proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                salida, error = proceso.communicate(timeout=timeout)
                if proceso.returncode == 0:
                    show_message(f"✅ {fotos[index][:10]}...", 2)
                else:
                    print("obex error:", error.decode(errors="ignore"))
                    show_message("❌ Error envío", 2)
            except subprocess.TimeoutExpired:
                proceso.kill()
                show_message("⌛ Timeout", 2)
            break
        elif pi.read(BTN_TAKE) == 0:
            show_message("Cancelado", 0.8)
            break

# ---------------------------
# Captura de fotos con feedback visual CORREGIDA
# ---------------------------

def check_disk_space_safe():
    """Verifica espacio en disco de forma segura."""
    try:
        # Intentar llamar a la función en filtros.py sin parámetros
        return filtros.check_disk_space()
    except TypeError:
        # Si falla, usar implementación simple
        try:
            stat = os.statvfs(PHOTO_DIR)
            free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            return free_mb > 100  # 100MB mínimo
        except:
            return True  # Si no podemos verificar, asumir que hay espacio

def take_photo(mode):
    """
    Captura foto y aplica filtro seleccionado.
    Mantiene la imagen original Y la filtrada.
    """
    # Verificar espacio en disco (forma segura)
    if not check_disk_space_safe():
        show_message("⚠️ Poco espacio", duration=2)
        return None
    
    # Matar procesos previos
    subprocess.run(["pkill", "-f", "rpicam-still"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    try:
        # Generar nombre de archivo base
        timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
        base_file = os.path.join(PHOTO_DIR, f"foto_{timestamp}.jpg")

        # PASO 1: Preparar captura
        show_progress("📷 Preparando...")
        time.sleep(0.3)  # Dar tiempo para que el usuario vea el mensaje
        
        # PASO 2: Capturar imagen
        show_progress("📷 Capturando...")
        
        if mode == "Foto B/N":
            cmd = ["rpicam-still", "-o", base_file, "--nopreview", "--saturation", "-100", "--timeout", "5000"]
        elif mode == "Foto Color":
            cmd = ["rpicam-still", "-o", base_file, "--nopreview", "--autofocus-on-capture", "--timeout", "5000"]
        else:
            return None

        result = subprocess.run(cmd, timeout=15, capture_output=True, text=True)
        
        if result.returncode != 0:
            show_message("❌ Error camara", duration=2)
            # Limpiar archivo si falló
            if os.path.exists(base_file):
                os.remove(base_file)
            return None

        # PASO 3: Foto capturada exitosamente
        show_progress("✅ Foto capturada!", "Procesando...")
        time.sleep(0.5)

        # PASO 4: Aplicar filtro si es necesario
        final_file = base_file
        
        if filtro_seleccionado != "Normal":
            # Aplicar filtro manteniendo el original
            show_progress("⚙️ Aplicando filtro...", filtro_seleccionado[:15])
            
            if filtro_seleccionado == "Grano Analogico":
                final_file = base_file.replace(".jpg", "_grano.jpg")
                try:
                    filtros.filtro_grano_analogico(base_file, final_file, intensidad=20)
                except:
                    final_file = base_file  # Fallback al original
                
            elif filtro_seleccionado == "Glitch Digital":
                final_file = base_file.replace(".jpg", "_glitch.jpg")
                try:
                    filtros.filtro_glitch_digital(base_file, final_file)
                except:
                    final_file = base_file
                
            elif filtro_seleccionado == "Rojo Contraste":
                final_file = base_file.replace(".jpg", "_rojo.jpg")
                try:
                    filtros.filtro_rojo_contraste(base_file, final_file)
                except:
                    final_file = base_file
                
            elif filtro_seleccionado == "Sepia":
                final_file = base_file.replace(".jpg", "_sepia.jpg")
                try:
                    filtros.filtro_sepia_contraste(base_file, final_file)
                except:
                    final_file = base_file
                
            elif filtro_seleccionado == "Azul Klein":
                final_file = base_file.replace(".jpg", "_azul.jpg")
                try:
                    filtros.filtro_azul_contraste(base_file, final_file)
                except:
                    final_file = base_file
            
            elif filtro_seleccionado == "Verde":
                final_file = base_file.replace(".jpg", "_verde.jpg")
                try:
                    filtros.filtro_matrix_simple(base_file, final_file)
                except:
                    final_file = base_file

            elif filtro_seleccionado == "Matrix Verde":
                final_file = base_file.replace(".jpg", "_matrix.jpg")
                try:
                    filtros.filtro_matrix_verde(base_file, final_file)
                except:
                    final_file = base_file

        
        # PASO 5: Limpiar memoria
        try:
            filtros.cleanup_memory()
        except:
            pass
        
        # PASO 6: Mensaje final
        show_message("✅ Listo!", duration=1.5)
        return os.path.basename(final_file)

    except subprocess.TimeoutExpired:
        show_message("⌛ Timeout camara", duration=2)
        # Limpiar archivo si falló
        if os.path.exists(base_file):
            os.remove(base_file)
        return None
    except Exception as e:
        show_message(f"❌ Error", duration=2)
        # Limpiar archivo si falló
        if os.path.exists(base_file):
            os.remove(base_file)
        return None

# ---------------------------
# Acciones del menú
# ---------------------------

def confirm_selection():
    """Confirma la selección del menú actual."""
    global submenu_active, filtro_seleccionado, running
    
    if submenu_active:
        # Estamos en submenú de filtros
        filtro_seleccionado = submenu_filtros_options[filtro_index]
        show_message(f"Filtro: {filtro_seleccionado}", 1.5)
        submenu_active = False
        
    else:
        # Estamos en menú principal
        option = menu_options[current_index]
        
        if option == "Filtros":
            submenu_active = True
            
        elif option == "Apagar Raspberry":
            show_message("🔴 Apagando...", 2)
            subprocess.run(["sudo", "poweroff"])
            running = False
            
        elif option == "Borrar Fotos":
            delete_photos()
            
        elif option == "Enviar a Android":
            if bluetooth_active:
                send_single_photo_menu()
            else:
                show_message("⚠️ Bluetooth OFF", duration=2)
                update_display()
                
        elif option == "Bluetooth":
            toggle_bluetooth()
            
        elif option in ["Foto B/N", "Foto Color"]:
            # Solo mostrar confirmación, no tomar foto
            show_message(f"Listo: {option}", 1)
    
    update_display()

def take_current_photo():
    """Toma foto según la opción seleccionada del menú."""
    option = menu_options[current_index]
    
    if option in ["Foto B/N", "Foto Color"]:
        taken = take_photo(option)
        # El mensaje ya se muestra en take_photo()
    
    update_display()

# ---------------------------
# Loop principal
# ---------------------------

update_display()

while running:
    try:
        if read_button(BTN_UP):
            scroll_up()
            
        elif read_button(BTN_DOWN):
            scroll_down()
            
        elif read_button(BTN_ENTER):
            confirm_selection()
            
        elif read_button(BTN_TAKE):
            take_current_photo()
        
        time.sleep(0.05)  # Pequeña pausa para no saturar CPU
        
    except Exception as e:
        print(f"Error en loop principal: {e}")
        time.sleep(0.1)

# Limpieza al salir
device.clear()
pi.stop()
