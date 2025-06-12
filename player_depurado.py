# --- START OF FILE player.py ---

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont # Importar tkfont
import os
import shutil
import requests
import subprocess
import threading
import time

# Intenta importar pywinauto
try:
    from pywinauto.application import Application, ProcessNotFoundError
    from pywinauto.findwindows import ElementNotFoundError, WindowNotFoundError
    from pywinauto.timings import TimeoutError as PywinautoTimeoutError
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False
    print("ADVERTENCIA: pywinauto no está instalado.")

# --- CONFIGURACIÓN DE APLICACIONES ---
APLICACIONES_CONFIG = {
    "Autologon": {
        "tipo": "configurar_autologon_gui",
        "exe_filename": "Autologon64.exe",
        "username": "player",
        "domain": "",
        "password": "player",
        "icon": "👤" # Ejemplo de icono Unicode
    },
    "Chrome": {
        "tipo": "instalar_local",
        "exe_filename": "Ninite Chrome Installer.exe",
        "args_instalacion": [],
        "icon": "🌐"
    },
    "Novalct": {
        "tipo": "instalar_manual_asistido",
        "exe_filename": "NovaLCT V5.4.7.1.exe",
        "mensaje_usuario": "Se abrirá el instalador de NovaLCT.\n\nPor favor, completa la instalación manualmente.\n\nUna vez FINALIZADA, cierra esta ventana para continuar.",
        "icon": "💡"
    },
    "PlataformaUniversal": {
        "tipo": "instalar_local",
        "exe_filename": "LSPlayerVideo-0.11.3 Multicliente Standard Setup.exe",
        "args_instalacion": ["/VERYSILENT", "/SUPPRESSMSGBOXES"],
        "icon": "🎬"
    },
    "TeamViewer": {
        "tipo": "instalar_local",
        "exe_filename": "TeamViewer_Host_Setup_x64.exe",
        "args_instalacion": ["/S"],
        "icon": "💻"
    },
    "VLC": {
        "tipo": "instalar_local",
        "exe_filename": "Ninite VLC Installer.exe",
        "args_instalacion": [],
        "icon": "⏯️"
    }
}

# --- RUTAS IMPORTANTES ---
PROGRAMAS_DIR = "D:/Programas" # Asegúrate de que esta ruta existe y contiene las subcarpetas y EXEs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DESCARGAS_DIR = os.path.join(BASE_DIR, "archivos_descargados_temp")
DOCUMENTOS_DIR = os.path.join(os.path.expanduser("~"), "Documents")
os.makedirs(DESCARGAS_DIR, exist_ok=True)

# --- LÓGICA DE PROCESAMIENTO ---
progress_window = None
progress_bar = None
progress_label_status = None
progress_label_percentage = None

def actualizar_progreso_gui(valor_barra=None, texto_status=None, texto_porcentaje=None):
    if progress_window and progress_window.winfo_exists():
        if valor_barra is not None and progress_bar:
            progress_bar['value'] = valor_barra
        if texto_status and progress_label_status:
            progress_label_status.config(text=texto_status)
        if texto_porcentaje is not None and progress_label_percentage: # Allow empty string for percentage
            progress_label_percentage.config(text=texto_porcentaje)
        progress_window.update_idletasks()

def descargar_archivo(url, ruta_destino_descarga):
    # <<<< MODIFIED: Ensure GUI updates for download are through root_gui.after >>>>
    # (Though progress_window.after should be fine if progress_window is a Toplevel of root_gui)
    # Using root_gui.after consistently is safer if any doubt. For this function, progress_window.after is likely okay.
    actualizar_progreso_gui(valor_barra=0, texto_porcentaje="0%")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        descargado = 0
        with open(ruta_destino_descarga, 'wb') as f:
            for data in response.iter_content(block_size):
                descargado += len(data)
                f.write(data)
                if total_size > 0:
                    porcentaje = int((descargado / total_size) * 100)
                    # Use progress_window.after as it's managed by this thread context more directly for high-frequency updates
                    progress_window.after(0, lambda p=porcentaje: actualizar_progreso_gui(valor_barra=p, texto_porcentaje=f"{p}%"))
                else:
                    progress_window.after(0, lambda d=descargado: actualizar_progreso_gui(valor_barra=(d // 1024) % 100, texto_porcentaje=f"{d // 1024} KB"))
        progress_window.after(0, lambda: actualizar_progreso_gui(valor_barra=100, texto_porcentaje="100%"))
        return True
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error de Descarga", f"No se pudo descargar {os.path.basename(ruta_destino_descarga)}:\n{e}")
        progress_window.after(0, lambda: actualizar_progreso_gui(texto_status=f"Error descargando {os.path.basename(ruta_destino_descarga)}"))
        return False

def instalar_exe(ruta_exe_a_instalar, args=None, wait_for_completion=False, timeout=None):
    if not os.path.exists(ruta_exe_a_instalar):
        ruta_normalizada = os.path.normpath(ruta_exe_a_instalar)
        messagebox.showerror("Error de Instalación", f"Archivo instalador no encontrado:\n{ruta_normalizada}")
        print(f"DEBUG: Archivo no encontrado en instalar_exe: {ruta_normalizada}")
        return False
    try:
        comando = [ruta_exe_a_instalar]
        if args:
            comando.extend(args)
        print(f"DEBUG: Ejecutando instalador: {comando}")
        
        proc = subprocess.Popen(comando, cwd=os.path.dirname(ruta_exe_a_instalar) or '.')
        if wait_for_completion:
            try:
                proc.wait(timeout=timeout) 
                print(f"DEBUG: Proceso {os.path.basename(ruta_exe_a_instalar)} terminado con código de salida: {proc.returncode}")
                if proc.returncode != 0:
                    print(f"ADVERTENCIA: El instalador {os.path.basename(ruta_exe_a_instalar)} terminó con un código de error: {proc.returncode}")
                    # Consider returning False if returncode is not 0, depending on strictness needed
                    # return False # Or let it be True if launching was successful
            except subprocess.TimeoutExpired:
                print(f"ADVERTENCIA: Timeout esperando a {os.path.basename(ruta_exe_a_instalar)}. El proceso puede seguir en segundo plano.")
                return False # Explicitly False on timeout if waiting was critical
        return True
    except Exception as e:
        messagebox.showerror("Error de Instalación", f"No se pudo ejecutar {os.path.basename(ruta_exe_a_instalar)}:\n{e}")
        print(f"DEBUG: Error al ejecutar instalador {ruta_exe_a_instalar}: {e}")
        return False

def copiar_a_documentos(ruta_origen_del_exe, nombre_destino_del_exe):
    if not os.path.exists(ruta_origen_del_exe):
        ruta_normalizada = os.path.normpath(ruta_origen_del_exe)
        messagebox.showerror("Error al Copiar", f"Archivo de origen no encontrado:\n{ruta_normalizada}")
        return False
    ruta_destino_final = os.path.join(DOCUMENTOS_DIR, nombre_destino_del_exe)
    try:
        shutil.copy2(ruta_origen_del_exe, ruta_destino_final)
        return True
    except Exception as e:
        messagebox.showerror("Error al Copiar", f"No se pudo copiar {nombre_destino_del_exe} a Documentos:\n{e}")
        return False

def configurar_autologon_gui_con_pywinauto(ruta_autologon_exe, username, domain, password, root_gui_for_update):
    if not PYWINAUTO_AVAILABLE:
        error_msg = "pywinauto no disponible para Autologon."
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0, texto_porcentaje="Error X"))
        root_gui_for_update.after(0, lambda: messagebox.showerror("Dependencia", error_msg))
        return False
    if not os.path.exists(ruta_autologon_exe):
        error_msg = f"Autologon no encontrado: {ruta_autologon_exe}"
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0, texto_porcentaje="Error X"))
        root_gui_for_update.after(0, lambda: messagebox.showerror("No Encontrado", error_msg))
        return False
    
    app = None 
    try:
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Iniciando Autologon...", valor_barra=10))
        app = Application(backend="uia").start(ruta_autologon_exe)
        dlg = None
        # Increased timeout for finding Autologon window slightly
        for _ in range(15): # try for 7.5 seconds
            try:
                # More specific title match if possible, but regex "^Autologon.*" is usually fine.
                dlg = app.window(title_re="^Autologon.*") 
                if dlg.exists() and dlg.is_visible(): break
            except (WindowNotFoundError, ElementNotFoundError, ProcessNotFoundError): 
                time.sleep(0.5)
            dlg = None # Reset dlg if not found in this iteration

        if not dlg or not dlg.exists(): 
            raise WindowNotFoundError("Ventana Autologon no encontrada después de varios intentos.")
        
        dlg.wait('visible', timeout=15) # Wait for it to be fully interactable
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Autologon detectado.", valor_barra=30))
        
        # Robustly find edit controls (assuming standard Autologon from Sysinternals)
        # This relies on the order, which is typical for pywinauto scripts for simple dialogs
        edit_controls = dlg.children(control_type="Edit")
        if len(edit_controls) < 3: 
            raise Exception(f"Autologon: Se esperaban al menos 3 campos de edición, se encontraron {len(edit_controls)}.")
        
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Rellenando campos...", valor_barra=50))
        edit_controls[0].set_edit_text(username)
        time.sleep(0.1) # Small pause
        edit_controls[1].set_edit_text(domain)
        time.sleep(0.1) # Small pause
        edit_controls[2].set_edit_text(password)
        time.sleep(0.2) # Slightly longer pause after password, just in case

        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Habilitando Autologon...", valor_barra=70))
        enable_button = dlg.child_window(title="Enable", control_type="Button")
        if not (enable_button.exists() and enable_button.is_enabled()):
            raise ElementNotFoundError("Botón 'Enable' de Autologon no encontrado o no habilitado.")
        enable_button.click_input()
        
        # Check if the window closes. If a "successful" dialog appears first, handle it.
        # For Autologon, it typically just closes on success.
        try:
            # Check for a success message box if Autologon shows one (often it doesn't, just closes)
            # Example: success_msg_box = app.window(title_re=".*Success.*", timeout=2)
            # if success_msg_box.exists(): success_msg_box.Ok.click(); success_msg_box.wait_not('visible', timeout=3)

            dlg.wait_not('visible', timeout=10) # Increased timeout for window to close
            root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Autologon configurado.", valor_barra=100, texto_porcentaje="Hecho ✓"))
            return True
        except PywinautoTimeoutError: 
            # Window didn't close in time. Check if it's still there.
            if dlg.exists() and dlg.is_visible():
                 messagebox.showwarning("Autologon", "La ventana de Autologon no se cerró como se esperaba. Por favor, verifica la configuración manualmente.")
                 root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Autologon: verificar manualmente.", valor_barra=90, texto_porcentaje="Aviso !"))
                 return False # Indicate that it might not be fully successful
            else: 
                 # Window closed, but after the main wait_not timeout somehow.
                 root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Autologon configurado (con aviso de demora).", valor_barra=100, texto_porcentaje="Hecho ✓"))
                 return True
    except Exception as e:
        error_msg = f"Error durante la configuración de Autologon (pywinauto): {e}"
        print(f"DEBUG: {error_msg}")
        root_gui_for_update.after(0, lambda em=error_msg: actualizar_progreso_gui(texto_status=em, valor_barra=0, texto_porcentaje="Error X"))
        root_gui_for_update.after(0, lambda em=error_msg: messagebox.showerror("Error Autologon", em))
        return False
    finally:
        # Ensure the Autologon process is terminated if it's still running and we started it.
        # This is tricky because other instances of Autologon might exist.
        # A more robust way would be to get app.process before and kill that specific PID.
        if app and app.is_process_running():
            try:
                # Only kill if we definitively know we launched *this* instance
                # For safety, only attempt if dlg might still be open and problematic.
                if dlg and dlg.exists() and dlg.is_visible():
                     print("ADVERTENCIA: Autologon.exe podría seguir ejecutándose. No se cerrará automáticamente por seguridad.")
                # app.kill() # Use with caution
            except Exception as e_kill:
                print(f"DEBUG: Error intentando cerrar Autologon: {e_kill}")

def instalar_manual_asistido_app(nombre_app, ruta_exe, mensaje_al_usuario, root_gui_for_update):
    root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=f"Preparando {nombre_app} (manual)...", valor_barra=10, texto_porcentaje=""))
    if not os.path.exists(ruta_exe):
        error_msg = f"Instalador {nombre_app} no encontrado: {os.path.normpath(ruta_exe)}"
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0, texto_porcentaje="Error X"))
        root_gui_for_update.after(0, lambda: messagebox.showerror("No Encontrado", error_msg))
        return False
    
    try:
        subprocess.Popen([ruta_exe], cwd=os.path.dirname(ruta_exe) or '.')
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=f"Instalador {nombre_app} lanzado. Esperando intervención del usuario...", valor_barra=50, texto_porcentaje="Manual"))
    except Exception as e:
        error_msg_launch = f"No se pudo lanzar {nombre_app}: {e}"
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg_launch, valor_barra=0, texto_porcentaje="Error X"))
        root_gui_for_update.after(0, lambda: messagebox.showerror("Error Lanzamiento", error_msg_launch))
        return False
    
    progress_was_grabbed = False
    if progress_window and progress_window.winfo_exists() and progress_window.grab_status():
        progress_window.grab_release()
        progress_was_grabbed = True

    # Ensure the messagebox appears above other windows
    # Creating a temporary invisible root for messagebox to be a child of can help focus
    temp_root = None
    try:
        temp_root = tk.Tk()
        temp_root.withdraw() # Hide the temp root window
        temp_root.attributes("-topmost", True)
        confirmed = messagebox.askokcancel(f"Instalación Manual: {nombre_app}", mensaje_al_usuario, parent=temp_root)
    finally:
        if temp_root:
            temp_root.destroy()

    if progress_was_grabbed and progress_window and progress_window.winfo_exists():
        progress_window.grab_set()

    if confirmed:
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=f"{nombre_app} confirmado por usuario.", valor_barra=100, texto_porcentaje="Hecho ✓"))
        return True
    else:
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=f"{nombre_app} cancelado por usuario.", valor_barra=0, texto_porcentaje="Cancelado X"))
        return False

def procesar_seleccion(apps_seleccionadas_nombres, root_gui):
    global progress_window, progress_bar, progress_label_status, progress_label_percentage
    
    # This function runs in a thread. GUI updates MUST use root_gui.after(...)
    def crear_ventana_progreso_threadsafe():
        nonlocal root_gui # Make sure root_gui from outer scope is used
        global progress_window, progress_bar, progress_label_status, progress_label_percentage
        
        progress_window = tk.Toplevel(root_gui)
        progress_window.title("Procesando Tareas...")
        s = ttk.Style(progress_window)
        try: s.theme_use(root_gui.tk.call("ttk::style", "theme", "use"))
        except tk.TclError: s.theme_use('clam')
        
        progress_window.geometry("500x200") 
        progress_window.resizable(False, False)
        progress_window.transient(root_gui) 
        progress_window.grab_set()          

        try:
            root_x, root_y = root_gui.winfo_x(), root_gui.winfo_y()
            root_width, root_height = root_gui.winfo_width(), root_gui.winfo_height()
            prog_width, prog_height = 500, 200
            center_x = root_x + (root_width // 2) - (prog_width // 2)
            center_y = root_y + (root_height // 2) - (prog_height // 2)
            progress_window.geometry(f"{prog_width}x{prog_height}+{center_x}+{center_y}")
        except tk.TclError: pass # In case root_gui is already destroyed

        main_frame = ttk.Frame(progress_window, padding="15 15 15 15")
        main_frame.pack(expand=True, fill=tk.BOTH)

        status_font = tkfont.Font(family="Segoe UI", size=10)
        percentage_font = tkfont.Font(family="Segoe UI", size=9, weight="bold")

        progress_label_status = ttk.Label(main_frame, text="Iniciando...", font=status_font, wraplength=450, anchor="w")
        progress_label_status.pack(pady=(0,10), padx=5, fill="x")
        
        progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=400, mode="determinate")
        progress_bar.pack(pady=10, padx=5, fill="x")
        
        progress_label_percentage = ttk.Label(main_frame, text="", font=percentage_font, anchor="e")
        progress_label_percentage.pack(pady=5, padx=5, fill="x")

    # Create progress window from main thread context, wait for it to exist
    root_gui.after(0, crear_ventana_progreso_threadsafe)
    while not (progress_window and progress_window.winfo_exists()): time.sleep(0.1)

    ordered_apps_seleccionadas = []
    novalct_key = None
    # Prioritize Novalct if it's selected (manual installation first)
    for key in apps_seleccionadas_nombres:
        if APLICACIONES_CONFIG[key]["tipo"] == "instalar_manual_asistido" and key == "Novalct":
            novalct_key = key
        else: ordered_apps_seleccionadas.append(key)
    if novalct_key: ordered_apps_seleccionadas.insert(0, novalct_key)

    total_apps = len(ordered_apps_seleccionadas)
    all_tasks_successful = True # Track overall success

    for i, app_nombre_key in enumerate(ordered_apps_seleccionadas):
        if not (progress_window and progress_window.winfo_exists()): # Check if progress window was closed early
            print("WARN: Progress window closed, aborting further tasks.")
            messagebox.showwarning("Cancelado", "Ventana de progreso cerrada. Tareas restantes no se ejecutarán.")
            all_tasks_successful = False
            break

        app_config_detalle = APLICACIONES_CONFIG[app_nombre_key]
        tipo_accion = app_config_detalle["tipo"]
        status_actual = f"Procesando: {app_nombre_key} ({i+1}/{total_apps})"
        # <<<< MODIFIED: Ensure all GUI updates use root_gui.after >>>>
        root_gui.after(0, lambda s=status_actual: actualizar_progreso_gui(texto_status=s, valor_barra=0, texto_porcentaje=""))
        
        success_flag = False # Success for the current app
        
        if tipo_accion == "instalar_manual_asistido":
            ruta_exe_origen = os.path.join(PROGRAMAS_DIR, app_nombre_key, app_config_detalle["exe_filename"])
            mensaje_usuario = app_config_detalle["mensaje_usuario"]
            if instalar_manual_asistido_app(app_nombre_key, ruta_exe_origen, mensaje_usuario, root_gui):
                success_flag = True
            else: # User cancelled or an error occurred in instalar_manual_asistido_app
                all_tasks_successful = False
                # Message already shown by instalar_manual_asistido_app or here
                # If cancelled, let's stop further processing.
                if progress_label_percentage and progress_label_percentage.cget("text") == "Cancelado X": # Check state set by function
                    root_gui.after(0, lambda: messagebox.showwarning("Proceso Detenido", f"Instalación de {app_nombre_key} cancelada por el usuario. Tareas restantes no se ejecutarán."))
                else: # Some other error within instalar_manual_asistido_app
                     root_gui.after(0, lambda: messagebox.showerror("Error", f"Falló la instalación manual de {app_nombre_key}. Tareas restantes no se ejecutarán."))
                # Cleanly close progress window and return
                root_gui.after(500, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)
                return 

        elif tipo_accion == "descargar_e_instalar":
            url = app_config_detalle["url_descarga"]
            nombre_archivo_guardado = app_config_detalle["nombre_archivo_descargado"]
            ruta_descarga_completa = os.path.join(DESCARGAS_DIR, nombre_archivo_guardado)
            args_inst = app_config_detalle.get("args_instalacion")
            wait_flag = app_config_detalle.get("wait_for_completion", False) # Check if we need to wait
            
            root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Descargando {an}..."))
            if descargar_archivo(url, ruta_descarga_completa): # descargar_archivo handles its own progress bar %
                root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Instalando {an}...", valor_barra=0, texto_porcentaje="0%"))
                if instalar_exe(ruta_descarga_completa, args_inst, wait_for_completion=wait_flag):
                    success_flag = True
                    final_text = "Instalado ✓" if wait_flag else "Lanzado"
                    root_gui.after(0, lambda ft=final_text: actualizar_progreso_gui(valor_barra=100, texto_porcentaje=ft))
                # else: Error message set by instalar_exe or actualizar_progreso_gui will set failure text
            if not success_flag: # Combined failure from download or install
                 all_tasks_successful = False
                 # Error text for progress already set by descargar_archivo or instalar_exe's chain
                 root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Fallo en {an}", texto_porcentaje="Error X"))


        elif tipo_accion == "instalar_local":
            nombre_exe_en_subcarpeta = app_config_detalle["exe_filename"]
            ruta_exe_origen = os.path.join(PROGRAMAS_DIR, app_nombre_key, nombre_exe_en_subcarpeta)
            args_inst = app_config_detalle.get("args_instalacion")
            wait_flag = app_config_detalle.get("wait_for_completion", False)
            timeout_install = app_config_detalle.get("timeout", None)


            root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Instalando {an}...", valor_barra=0, texto_porcentaje="..."))
            if os.path.exists(ruta_exe_origen):
                if instalar_exe(ruta_exe_origen, args_inst, wait_for_completion=wait_flag, timeout=timeout_install):
                    success_flag = True
                    final_text = "Instalado ✓" if wait_flag and (not timeout_install or timeout_install) else "Lanzado" # Adjust based on wait
                    root_gui.after(0, lambda ft=final_text: actualizar_progreso_gui(valor_barra=100, texto_porcentaje=ft))
                else: # instalar_exe returned false (e.g. launch error, or timeout if wait_flag was true)
                    all_tasks_successful = False
                    # Assuming instalar_exe or a subsequent message from it handles the error messagebox.
                    # We just update our progress status text.
                    root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Fallo instalando {an}", valor_barra=0, texto_porcentaje="Error X"))
            else:
                all_tasks_successful = False
                error_msg_detalle = f"Instalador no encontrado: {os.path.normpath(ruta_exe_origen)}"
                root_gui.after(0, lambda emd=error_msg_detalle: actualizar_progreso_gui(texto_status=emd, valor_barra=0, texto_porcentaje="Error X"))
                root_gui.after(0, lambda emd=error_msg_detalle: messagebox.showerror("No Encontrado", emd))
        
        elif tipo_accion == "copiar_exe":
            nombre_exe_en_subcarpeta = app_config_detalle["exe_filename"]
            ruta_exe_origen = os.path.join(PROGRAMAS_DIR, app_nombre_key, nombre_exe_en_subcarpeta)
            root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Copiando {an}...", valor_barra=0, texto_porcentaje=""))
            if os.path.exists(ruta_exe_origen):
                if copiar_a_documentos(ruta_exe_origen, nombre_exe_en_subcarpeta):
                    success_flag = True
                    root_gui.after(0, lambda: actualizar_progreso_gui(valor_barra=100, texto_porcentaje="Copiado ✓"))
                else: # copiar_a_documentos shows its own error messagebox
                    all_tasks_successful = False
                    root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Fallo copia {an}", valor_barra=0, texto_porcentaje="Error X"))
            else:
                all_tasks_successful = False
                error_msg_detalle = f"Archivo a copiar no encontrado: {os.path.normpath(ruta_exe_origen)}"
                root_gui.after(0, lambda emd=error_msg_detalle: actualizar_progreso_gui(texto_status=emd, valor_barra=0, texto_porcentaje="Error X"))
                root_gui.after(0, lambda emd=error_msg_detalle: messagebox.showerror("No Encontrado", emd))
        
        elif tipo_accion == "configurar_autologon_gui":
            nombre_exe_en_subcarpeta = app_config_detalle["exe_filename"]
            ruta_exe_origen = os.path.join(PROGRAMAS_DIR, app_nombre_key, nombre_exe_en_subcarpeta)
            username, domain, password = app_config_detalle["username"], app_config_detalle["domain"], app_config_detalle["password"]
            
            root_gui.after(0, lambda: actualizar_progreso_gui(texto_status=f"Configurando Autologon...", valor_barra=0, texto_porcentaje=""))
            if PYWINAUTO_AVAILABLE:
                if configurar_autologon_gui_con_pywinauto(ruta_exe_origen, username, domain, password, root_gui):
                    success_flag = True # Function sets "Hecho ✓" or similar on success
                else:
                    # configurar_autologon_gui_con_pywinauto returned False.
                    # It should have already updated the GUI with a specific error/warning message.
                    # And success_flag remains False.
                    all_tasks_successful = False
                    # <<<< REMOVED: Cross-thread cget and redundant GUI update >>>>
                    # if progress_label_percentage.cget("text") not in ["Hecho ✓", "Hecho ✔"]: # This check is unsafe
                    #    root_gui.after(0, lambda: actualizar_progreso_gui(texto_status="Fallo Autologon.", valor_barra=0, texto_porcentaje="Error X"))
            else: # PYWINAUTO_AVAILABLE is False
                all_tasks_successful = False
                error_msg = "Autologon: pywinauto no disponible."
                root_gui.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0, texto_porcentaje="Error X"))
                root_gui.after(0, lambda: messagebox.showerror("Dependencia", "pywinauto no instalado. No se puede configurar Autologon."))
        
        # --- End of per-app processing ---
        # <<<< MODIFIED: Simplified sleep logic based only on success_flag >>>>
        if success_flag:
            time.sleep(0.5) # Brief pause to see the success status for the app
        else:
            # If not successful, an error message should already be visible or was shown.
            # A short pause or specific handling for critical failures might be desired here.
            # For now, we continue to the next app unless 'all_tasks_successful' is used to break.
            time.sleep(0.2)
            # Example: if not all_tasks_successful and some_app_is_critical: break

    # --- After loop ---
    final_status_message = "Proceso finalizado."
    final_percentage_text = "Completado ✓"
    if not all_tasks_successful:
        final_status_message = "Proceso finalizado con uno o más errores/avisos."
        final_percentage_text = "Completado con avisos X"

    root_gui.after(0, lambda: actualizar_progreso_gui(texto_status=final_status_message, valor_barra=100, texto_porcentaje=final_percentage_text))
    root_gui.after(2500, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)
    
    # Use root_gui.after for the final messagebox as well
    def show_final_message():
        if all_tasks_successful:
            messagebox.showinfo("Finalizado", "Tareas solicitadas han sido procesadas o iniciadas.")
        else:
            messagebox.showwarning("Finalizado con Errores", "Algunas tareas no se completaron correctamente. Revisa los mensajes.")
    root_gui.after(100, show_final_message)


def on_siguiente_click(app_vars_dict, root_gui):
    seleccionadas_keys = []
    resumen_acciones_str = "Se realizarán las siguientes acciones:\n\n"
    hay_seleccion = False
    requiere_pywinauto_seleccionado = False
    novalct_seleccionado = False

    for nombre_app_key, var_tk_bool in app_vars_dict.items():
        if var_tk_bool.get():
            hay_seleccion = True
            seleccionadas_keys.append(nombre_app_key)
            config = APLICACIONES_CONFIG[nombre_app_key]
            icon = config.get("icon", "") + " " if config.get("icon") else "" 
            exe_f_display = config.get("exe_filename", config.get("nombre_archivo_descargado", "archivo_desconocido.exe"))

            if config["tipo"] == "instalar_manual_asistido":
                resumen_acciones_str += f"- {icon}{nombre_app_key}: Iniciar instalación manual.\n"
                if nombre_app_key == "Novalct": novalct_seleccionado = True
            elif config["tipo"] == "configurar_autologon_gui":
                 resumen_acciones_str += f"- {icon}{nombre_app_key}: Configurar Autologon para '{config['username']}'.\n"
                 requiere_pywinauto_seleccionado = True
            elif config["tipo"] == "descargar_e_instalar":
                resumen_acciones_str += f"- {icon}{nombre_app_key}: Descargar e instalar '{exe_f_display}'.\n"
            elif config["tipo"] == "instalar_local":
                resumen_acciones_str += f"- {icon}{nombre_app_key}: Instalar '{exe_f_display}' desde local.\n"
            elif config["tipo"] == "copiar_exe":
                resumen_acciones_str += f"- {icon}{nombre_app_key}: Copiar '{exe_f_display}' a Documentos.\n"

    if not hay_seleccion:
        messagebox.showwarning("Sin Selección", "No has seleccionado ninguna aplicación.")
        return

    if requiere_pywinauto_seleccionado and not PYWINAUTO_AVAILABLE:
        messagebox.showerror("Dependencia Faltante", "La tarea 'Autologon' requiere la librería 'pywinauto', que no está instalada.\nPor favor, deselecciona Autologon o instala pywinauto ('pip install pywinauto').")
        return

    if novalct_seleccionado and len(seleccionadas_keys) > 1:
        resumen_acciones_str += "\nATENCIÓN: NovaLCT (instalación manual) se procesará primero si está seleccionada.\n"
    
    resumen_acciones_str += "\n¿Deseas continuar?"
    if messagebox.askyesno("Confirmar Acciones", resumen_acciones_str, icon='question'):
        # Pass root_gui to the thread target so it can schedule GUI updates
        thread = threading.Thread(target=procesar_seleccion, args=(seleccionadas_keys, root_gui), daemon=True)
        thread.start()

# --- INTERFAZ GRÁFICA PRINCIPAL ---
def crear_ventana_principal():
    root = tk.Tk()
    root.title("Asistente de Configuración de PC")
    
    style = ttk.Style(root)
    try:
        available_themes = style.theme_names()
        # print(f"Temas ttk disponibles: {available_themes}")
        if 'vista' in available_themes: style.theme_use('vista')
        elif 'clam' in available_themes: style.theme_use('clam')
        elif 'xpnative' in available_themes: style.theme_use('xpnative') # Another option for Windows
        # else use default
    except tk.TclError:
        print("No se pudo cambiar el tema ttk. Usando el predeterminado.")

    default_font_family = "Segoe UI"
    try:
        # Check if Segoe UI is available, otherwise fall back
        tkfont.Font(family="Segoe UI", size=10).actual()
    except tk.TclError:
        default_font_family = "Arial" # Or "Calibri", "Helvetica" etc.


    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family=default_font_family, size=10)
    header_font = tkfont.Font(family=default_font_family, size=16, weight="bold") # Use weight for bold
    label_font = tkfont.Font(family=default_font_family, size=11)
    small_font = tkfont.Font(family=default_font_family, size=8)


    window_width = 550
    window_height = 620 # Adjusted height slightly
    root.minsize(500, 500)

    try: 
        screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    except tk.TclError: pass # Fails if run without display, e.g. in some CI

    if not os.path.isdir(PROGRAMAS_DIR):
         messagebox.showerror("Error Crítico", f"La carpeta de programas NO fue encontrada:\n'{os.path.normpath(PROGRAMAS_DIR)}'\n\nEl programa se cerrará.")
         root.destroy()
         return

    main_frame = ttk.Frame(root, padding="20 20 20 20")
    main_frame.pack(expand=True, fill=tk.BOTH)

    header_label = ttk.Label(main_frame, text="Instalador de Aplicaciones", font=header_font, anchor="center")
    header_label.pack(pady=(0, 25), fill="x") # Increased padding

    apps_frame_container = ttk.LabelFrame(main_frame, text=" Selecciona las aplicaciones a instalar o configurar ", padding=(15,10,15,15))
    apps_frame_container.pack(fill="both", expand=True, pady=(0,20)) # Allow expansion if many apps
    
    style.configure('App.TCheckbutton', font=label_font, padding=(5,5)) 

    app_vars = {} 
    for nombre_app_key, config_detalle in APLICACIONES_CONFIG.items():
        var = tk.BooleanVar()
        icon = config_detalle.get("icon", "") 
        
        chk_text = f" {icon}  {nombre_app_key}" if icon else nombre_app_key
        
        chk_state = tk.NORMAL
        extra_info = "" # For things like "pywinauto no disponible"
        
        tipo_actual = config_detalle["tipo"]
        if tipo_actual == "configurar_autologon_gui" and not PYWINAUTO_AVAILABLE:
            extra_info = " (⚠ pywinauto no disponible)"
            chk_state = tk.DISABLED
            var.set(False)
        
        # Frame per checkbox for alignment and potential extra labels
        chk_frame = ttk.Frame(apps_frame_container) 
        chk_frame.pack(anchor="w", fill="x", pady=3) # fill x

        chk = ttk.Checkbutton(chk_frame, text=chk_text, variable=var, style='App.TCheckbutton', state=chk_state)
        chk.pack(side=tk.LEFT, padx=(5,0))

        if extra_info:
            info_label_chk = ttk.Label(chk_frame, text=extra_info, font=(default_font_family, 9, "italic"), foreground="gray")
            info_label_chk.pack(side=tk.LEFT, padx=(5,0))

        app_vars[nombre_app_key] = var

    bottom_frame = ttk.Frame(main_frame)
    bottom_frame.pack(side=tk.BOTTOM, fill="x", pady=(10, 0),  expand=False)

    style.configure('Accent.TButton', font=(label_font.cget("family"), label_font.cget("size"), "bold"))
    
    next_button = ttk.Button(bottom_frame, text="Continuar ➔",
                             style='Accent.TButton',
                             command=lambda: on_siguiente_click(app_vars, root),
                             width=15) # Fixed width for the button
    next_button.pack(side=tk.RIGHT, pady=(10,0), ipady=5) 

    info_text_parts = [
        f"Origen de programas: '{os.path.normpath(PROGRAMAS_DIR)}'",
        f"Archivos copiados a: '{os.path.normpath(DOCUMENTOS_DIR)}'"
    ]
    if not PYWINAUTO_AVAILABLE:
        info_text_parts.append("Aviso: Autologon (GUI) requiere 'pywinauto' (no instalado).")
    
    info_label_text = "\n".join(info_text_parts)
    info_label = ttk.Label(bottom_frame, text=info_label_text,
                           justify=tk.LEFT, font=small_font, foreground="#444444", wraplength=window_width - next_button.winfo_reqwidth() - 50) # Dynamic wraplength
    info_label.pack(side=tk.LEFT, pady=(10,0), fill="x", expand=True, anchor='sw')


    if not PYWINAUTO_AVAILABLE:
        root.after(200, lambda: messagebox.showwarning("Advertencia de Dependencia", 
                               "La librería 'pywinauto' no está instalada.\n"
                               "La funcionalidad para configurar 'Autologon' mediante GUI no estará disponible.\n\n"
                               "Si necesitas esta función, instala 'pywinauto' (ej: 'pip install pywinauto') y reinicia la aplicación."))
    root.mainloop()

if __name__ == "__main__":
    # Check for PROGRAMAS_DIR existence before even creating the window for a slightly better UX if it's critical
    # Though the GUI itself handles it nicely too.
    # if not os.path.isdir(PROGRAMAS_DIR):
    #     root_temp = tk.Tk()
    #     root_temp.withdraw() # Hide it
    #     messagebox.showerror("Error Crítico Inicial", f"La carpeta de programas NO fue encontrada:\n'{os.path.normpath(PROGRAMAS_DIR)}'\n\nEl programa no puede continuar.")
    #     root_temp.destroy()
    # else:
    crear_ventana_principal()