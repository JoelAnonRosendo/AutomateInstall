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
PROGRAMAS_DIR = "D:/Programas"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DESCARGAS_DIR = os.path.join(BASE_DIR, "archivos_descargados_temp")
DOCUMENTOS_DIR = os.path.join(os.path.expanduser("~"), "Documents")
os.makedirs(DESCARGAS_DIR, exist_ok=True)

# --- LÓGICA DE PROCESAMIENTO (sin cambios visuales aquí) ---
progress_window = None
progress_bar = None
progress_label_status = None
progress_label_percentage = None

# ... (TODAS LAS FUNCIONES DE LÓGICA: actualizar_progreso_gui, descargar_archivo, etc.
#      PERMANECEN IGUALES QUE EN LA VERSIÓN ANTERIOR)
def actualizar_progreso_gui(valor_barra=None, texto_status=None, texto_porcentaje=None):
    if progress_window and progress_window.winfo_exists():
        if valor_barra is not None and progress_bar:
            progress_bar['value'] = valor_barra
        if texto_status and progress_label_status:
            progress_label_status.config(text=texto_status)
        if texto_porcentaje and progress_label_percentage:
            progress_label_percentage.config(text=texto_porcentaje)
        progress_window.update_idletasks()

def descargar_archivo(url, ruta_destino_descarga):
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
        
        if wait_for_completion:
            process = subprocess.Popen(comando, cwd=os.path.dirname(ruta_exe_a_instalar) or '.')
            try:
                process.wait(timeout=timeout) 
                print(f"DEBUG: Proceso {os.path.basename(ruta_exe_a_instalar)} terminado con código de salida: {process.returncode}")
                if process.returncode != 0:
                    print(f"ADVERTENCIA: El instalador {os.path.basename(ruta_exe_a_instalar)} terminó con un código de error: {process.returncode}")
            except subprocess.TimeoutExpired:
                print(f"ADVERTENCIA: Timeout esperando a {os.path.basename(ruta_exe_a_instalar)}. El proceso puede seguir en segundo plano.")
                return False 
        else:
            subprocess.Popen(comando, cwd=os.path.dirname(ruta_exe_a_instalar) or '.')
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
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0))
        root_gui_for_update.after(0, lambda: messagebox.showerror("Dependencia", error_msg))
        return False
    if not os.path.exists(ruta_autologon_exe):
        error_msg = f"Autologon no encontrado: {ruta_autologon_exe}"
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0))
        root_gui_for_update.after(0, lambda: messagebox.showerror("No Encontrado", error_msg))
        return False
    app = None 
    try:
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Iniciando Autologon...", valor_barra=10))
        app = Application(backend="uia").start(ruta_autologon_exe)
        dlg = None
        for _ in range(10): 
            try:
                dlg = app.window(title_re="^Autologon.*") 
                if dlg.exists() and dlg.is_visible(): break
            except (WindowNotFoundError, ElementNotFoundError, ProcessNotFoundError): time.sleep(0.5)
        if not dlg or not dlg.exists(): raise WindowNotFoundError("Ventana Autologon no encontrada.")
        dlg.wait('visible', timeout=10) 
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Autologon detectado.", valor_barra=30))
        edit_controls = dlg.children(control_type="Edit")
        if len(edit_controls) < 3: raise Exception(f"Autologon: campos de edición insuficientes ({len(edit_controls)}).")
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Rellenando campos...", valor_barra=50))
        edit_controls[0].set_edit_text(username); edit_controls[1].set_edit_text(domain); edit_controls[2].set_edit_text(password)
        time.sleep(0.2)
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Habilitando Autologon...", valor_barra=70))
        dlg.child_window(title="Enable", control_type="Button").click_input()
        try:
            dlg.wait_not('visible', timeout=5) 
            root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Autologon configurado.", valor_barra=100, texto_porcentaje="Hecho ✓"))
            return True
        except PywinautoTimeoutError: 
            if dlg.exists() and dlg.is_visible():
                 messagebox.showwarning("Autologon", "Ventana Autologon no se cerró. Verificar.")
                 root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Autologon: verificar.", valor_barra=90))
                 return False
            else: 
                 root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Autologon configurado (aviso).", valor_barra=100, texto_porcentaje="Hecho ✓"))
                 return True
    except Exception as e:
        error_msg = f"Error Autologon (pywinauto): {e}"
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0))
        root_gui_for_update.after(0, lambda: messagebox.showerror("Error Autologon", error_msg))
        return False

def instalar_manual_asistido_app(nombre_app, ruta_exe, mensaje_al_usuario, root_gui_for_update):
    root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=f"Preparando {nombre_app} (manual)...", valor_barra=10))
    if not os.path.exists(ruta_exe):
        error_msg = f"Instalador {nombre_app} no encontrado: {ruta_exe}"
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0, texto_porcentaje="Error X"))
        root_gui_for_update.after(0, lambda: messagebox.showerror("No Encontrado", error_msg))
        return False
    try:
        subprocess.Popen([ruta_exe], cwd=os.path.dirname(ruta_exe) or '.')
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=f"Instalador {nombre_app} lanzado. Esperando...", valor_barra=50))
    except Exception as e:
        error_msg_launch = f"No se pudo lanzar {nombre_app}: {e}"
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg_launch, valor_barra=0, texto_porcentaje="Error X"))
        root_gui_for_update.after(0, lambda: messagebox.showerror("Error Lanzamiento", error_msg_launch))
        return False
    
    progress_was_grabbed = False
    if progress_window and progress_window.winfo_exists() and progress_window.grab_status():
        progress_window.grab_release()
        progress_was_grabbed = True

    confirmed = messagebox.askokcancel(f"Instalación Manual: {nombre_app}", mensaje_al_usuario)

    if progress_was_grabbed and progress_window and progress_window.winfo_exists():
        progress_window.grab_set()

    if confirmed:
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=f"{nombre_app} confirmado por usuario.", valor_barra=100, texto_porcentaje="Hecho ✓"))
        return True
    else:
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=f"{nombre_app} cancelado.", valor_barra=0, texto_porcentaje="Cancelado X"))
        return False

def procesar_seleccion(apps_seleccionadas_nombres, root_gui):
    global progress_window, progress_bar, progress_label_status, progress_label_percentage
    def crear_ventana_progreso_threadsafe():
        global progress_window, progress_bar, progress_label_status, progress_label_percentage
        progress_window = tk.Toplevel(root_gui)
        progress_window.title("Procesando Tareas...")
        # Usar colores del tema para la ventana de progreso también
        s = ttk.Style(progress_window)
        try:
            s.theme_use(root_gui.tk.call("ttk::style", "theme", "use")) # Usa el mismo tema que root
        except tk.TclError:
            s.theme_use('clam') # Fallback
        
        # Hacerla un poco más grande y con más padding
        progress_window.geometry("500x200") 
        progress_window.resizable(False, False)
        progress_window.transient(root_gui) 
        progress_window.grab_set()          

        try:
            root_x = root_gui.winfo_x(); root_y = root_gui.winfo_y()
            root_width = root_gui.winfo_width(); root_height = root_gui.winfo_height()
            prog_width = 500; prog_height = 200
            center_x = root_x + (root_width // 2) - (prog_width // 2)
            center_y = root_y + (root_height // 2) - (prog_height // 2)
            progress_window.geometry(f"{prog_width}x{prog_height}+{center_x}+{center_y}")
        except tk.TclError: pass

        # Usar ttk.Frame para mejor control de padding
        main_frame = ttk.Frame(progress_window, padding="15 15 15 15")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Estilo de fuente mejorado
        status_font = tkfont.Font(family="Segoe UI", size=10) # O Arial, etc.
        percentage_font = tkfont.Font(family="Segoe UI", size=9, weight="bold")

        progress_label_status = ttk.Label(main_frame, text="Iniciando...", font=status_font, wraplength=450, anchor="w")
        progress_label_status.pack(pady=(0,10), padx=5, fill="x")
        
        progress_bar_style = ttk.Style(progress_window)
        # Podrías definir un estilo custom para la barra aquí si quieres (ej. colores)
        # progress_bar_style.configure("custom.Horizontal.TProgressbar", troughcolor ='gray', background='green')
        # progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=400, mode="determinate", style="custom.Horizontal.TProgressbar")
        progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=400, mode="determinate")
        progress_bar.pack(pady=10, padx=5, fill="x")
        
        progress_label_percentage = ttk.Label(main_frame, text="", font=percentage_font, anchor="e")
        progress_label_percentage.pack(pady=5, padx=5, fill="x")
        
        # Botón de cancelar (opcional, puede ser complejo de implementar bien)
        # cancel_button = ttk.Button(main_frame, text="Cancelar Proceso", command=lambda: print("Cancelar solicitado"))
        # cancel_button.pack(pady=(10,0))


    root_gui.after(0, crear_ventana_progreso_threadsafe)
    while not (progress_window and progress_window.winfo_exists()): time.sleep(0.1)

    ordered_apps_seleccionadas = []
    novalct_key = None
    for key in apps_seleccionadas_nombres:
        if APLICACIONES_CONFIG[key]["tipo"] == "instalar_manual_asistido" and key == "Novalct":
            novalct_key = key
        else: ordered_apps_seleccionadas.append(key)
    if novalct_key: ordered_apps_seleccionadas.insert(0, novalct_key)

    total_apps = len(ordered_apps_seleccionadas)
    for i, app_nombre_key in enumerate(ordered_apps_seleccionadas):
        app_config_detalle = APLICACIONES_CONFIG[app_nombre_key]
        tipo_accion = app_config_detalle["tipo"]
        status_actual = f"Procesando: {app_nombre_key} ({i+1}/{total_apps})"
        root_gui.after(0, lambda s=status_actual: actualizar_progreso_gui(texto_status=s, valor_barra=0, texto_porcentaje=""))
        
        success_flag = False
        # ... (Lógica de cada tipo_accion igual que antes) ...
        if tipo_accion == "instalar_manual_asistido":
            ruta_exe_origen = os.path.join(PROGRAMAS_DIR, app_nombre_key, app_config_detalle["exe_filename"])
            mensaje_usuario = app_config_detalle["mensaje_usuario"]
            if instalar_manual_asistido_app(app_nombre_key, ruta_exe_origen, mensaje_usuario, root_gui):
                success_flag = True
            else:
                root_gui.after(0, lambda: actualizar_progreso_gui(texto_status="Proceso cancelado por usuario.", valor_barra=0))
                root_gui.after(1000, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)
                messagebox.showwarning("Cancelado", f"Instalación de {app_nombre_key} cancelada. Tareas restantes no se ejecutarán.")
                return
        elif tipo_accion == "descargar_e_instalar":
            # ...
            url = app_config_detalle["url_descarga"]
            nombre_archivo_guardado = app_config_detalle["nombre_archivo_descargado"]
            ruta_descarga_completa = os.path.join(DESCARGAS_DIR, nombre_archivo_guardado)
            args_inst = app_config_detalle.get("args_instalacion")
            root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Descargando {an}..."))
            if descargar_archivo(url, ruta_descarga_completa):
                root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Instalando {an}..."))
                if instalar_exe(ruta_descarga_completa, args_inst):
                    success_flag = True
                    root_gui.after(0, lambda: actualizar_progreso_gui(valor_barra=100, texto_porcentaje="Lanzado"))
            if not success_flag:
                 root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Fallo {an}", valor_barra=0, texto_porcentaje="Error X"))

        elif tipo_accion == "instalar_local":
            # ...
            nombre_exe_en_subcarpeta = app_config_detalle["exe_filename"]
            ruta_exe_origen = os.path.join(PROGRAMAS_DIR, app_nombre_key, nombre_exe_en_subcarpeta)
            args_inst = app_config_detalle.get("args_instalacion")
            root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Instalando {an}...", valor_barra=0, texto_porcentaje=""))
            if os.path.exists(ruta_exe_origen):
                if instalar_exe(ruta_exe_origen, args_inst):
                    success_flag = True
                    root_gui.after(0, lambda: actualizar_progreso_gui(valor_barra=100, texto_porcentaje="Lanzado"))
                else:
                    root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Fallo {an}", valor_barra=0, texto_porcentaje="Error X"))
            else:
                error_msg_detalle = f"Instalador no encontrado: {os.path.normpath(ruta_exe_origen)}"
                root_gui.after(0, lambda emd=error_msg_detalle: actualizar_progreso_gui(texto_status=emd, valor_barra=0, texto_porcentaje="Error X"))
                root_gui.after(0, lambda emd=error_msg_detalle: messagebox.showerror("No Encontrado", emd))
        elif tipo_accion == "copiar_exe":
            # ...
            nombre_exe_en_subcarpeta = app_config_detalle["exe_filename"]
            ruta_exe_origen = os.path.join(PROGRAMAS_DIR, app_nombre_key, nombre_exe_en_subcarpeta)
            root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Copiando {an}...", valor_barra=0, texto_porcentaje=""))
            if os.path.exists(ruta_exe_origen):
                if copiar_a_documentos(ruta_exe_origen, nombre_exe_en_subcarpeta):
                    success_flag = True
                    root_gui.after(0, lambda: actualizar_progreso_gui(valor_barra=100, texto_porcentaje="Copiado ✓"))
                else:
                    root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Fallo copia {an}", valor_barra=0, texto_porcentaje="Error X"))
            else:
                error_msg_detalle = f"Archivo a copiar no encontrado: {os.path.normpath(ruta_exe_origen)}"
                root_gui.after(0, lambda emd=error_msg_detalle: actualizar_progreso_gui(texto_status=emd, valor_barra=0, texto_porcentaje="Error X"))
                root_gui.after(0, lambda emd=error_msg_detalle: messagebox.showerror("No Encontrado", emd))
        elif tipo_accion == "configurar_autologon_gui":
            # ...
            nombre_exe_en_subcarpeta = app_config_detalle["exe_filename"]
            ruta_exe_origen = os.path.join(PROGRAMAS_DIR, app_nombre_key, nombre_exe_en_subcarpeta)
            username = app_config_detalle["username"]; domain = app_config_detalle["domain"]; password = app_config_detalle["password"]
            root_gui.after(0, lambda: actualizar_progreso_gui(texto_status=f"Configurando Autologon...", valor_barra=0))
            if PYWINAUTO_AVAILABLE:
                if configurar_autologon_gui_con_pywinauto(ruta_exe_origen, username, domain, password, root_gui):
                    success_flag = True
                else:
                     if progress_label_percentage.cget("text") not in ["Hecho ✓", "Hecho ✔"]:
                         root_gui.after(0, lambda: actualizar_progreso_gui(texto_status="Fallo Autologon.", valor_barra=0, texto_porcentaje="Error X"))
            else:
                error_msg = "Autologon: pywinauto no disponible."
                root_gui.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0, texto_porcentaje="Error X"))
                root_gui.after(0, lambda: messagebox.showerror("Dependencia", "pywinauto no instalado para Autologon."))
        # ---
        if success_flag and progress_label_percentage.cget("text") in ["Hecho ✓", "Copiado ✓", "Lanzado"]:
            time.sleep(0.5) 
        else:
            time.sleep(0.2)
            
    root_gui.after(0, lambda: actualizar_progreso_gui(texto_status="Proceso finalizado.", valor_barra=100, texto_porcentaje="Completado"))
    root_gui.after(2500, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None) # Un poco menos de espera final
    root_gui.after(100, lambda: messagebox.showinfo("Finalizado", "Tareas solicitadas han sido procesadas o iniciadas."))

def on_siguiente_click(app_vars_dict, root_gui):
    # ... (Lógica igual que antes) ...
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
            icon = config.get("icon", "") + " " if config.get("icon") else "" # Añadir icono al resumen
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
        messagebox.showerror("Dependencia Faltante", "Autologon requiere 'pywinauto' (no instalado).")
        return

    if novalct_seleccionado and len(seleccionadas_keys) > 1:
        resumen_acciones_str += "\nATENCIÓN: NovaLCT (manual) se procesará primero.\n"
    
    resumen_acciones_str += "\n¿Deseas continuar?"
    if messagebox.askyesno("Confirmar Acciones", resumen_acciones_str, icon='question'): # Añadir icono al messagebox
        thread = threading.Thread(target=procesar_seleccion, args=(seleccionadas_keys, root_gui), daemon=True)
        thread.start()
# --- INTERFAZ GRÁFICA PRINCIPAL ---
def crear_ventana_principal():
    root = tk.Tk()
    root.title("Asistente de Configuración de PC")
    
    # --- ESTILOS Y TEMA ---
    style = ttk.Style(root)
    try:
        # Temas disponibles: 'winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative'
        # 'clam' o 'vista' suelen ser buenas opciones para un look más moderno.
        # Elige uno que te guste y esté disponible en tu sistema.
        available_themes = style.theme_names()
        print(f"Temas ttk disponibles: {available_themes}")
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'vista' in available_themes: # Bueno para Windows
             style.theme_use('vista')
        # Puedes probar otros si los anteriores no te gustan o no están
    except tk.TclError:
        print("No se pudo cambiar el tema ttk. Usando el predeterminado.")

    # Definir fuentes
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family="Segoe UI", size=10) # O "Arial", "Calibri", etc.
    header_font = tkfont.Font(family="Segoe UI Semibold", size=16) # Para el título
    label_font = tkfont.Font(family="Segoe UI", size=11)
    small_font = tkfont.Font(family="Segoe UI", size=8)

    # Colores (opcional, puedes ajustarlos o quitarlos para depender del tema)
    # BG_COLOR = "#F0F0F0"  # Un gris claro
    # FG_COLOR = "#333333"  # Gris oscuro para texto
    # ACCENT_COLOR = "#0078D7" # Azul como acento
    # root.configure(bg=BG_COLOR)

    # --- LAYOUT ---
    window_width = 550
    window_height = 600 # Un poco más alta para acomodar el encabezado y mejor espaciado
    root.minsize(500, 500)

    try: # Centrar ventana
        screen_width = root.winfo_screenwidth(); screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    except tk.TclError: pass

    if not os.path.isdir(PROGRAMAS_DIR):
         messagebox.showerror("Error Crítico", f"Carpeta de programas NO encontrada:\n'{PROGRAMAS_DIR}'")
         root.destroy()
         return

    # Frame principal con padding
    main_frame = ttk.Frame(root, padding="20 20 20 20")
    main_frame.pack(expand=True, fill=tk.BOTH)

    # Encabezado
    header_label = ttk.Label(main_frame, text="Instalador de Aplicaciones", font=header_font, anchor="center")
    # header_label.configure(foreground=ACCENT_COLOR) # Si usas colores custom
    header_label.pack(pady=(0, 20), fill="x")

    # Frame para la lista de aplicaciones
    apps_frame_container = ttk.LabelFrame(main_frame, text=" Selecciona las aplicaciones a instalar o configurar ", padding=(15,10))
    apps_frame_container.pack(fill="x", expand=False, pady=(0,20))
    
    # Estilo para Checkbuttons dentro del LabelFrame
    style.configure('App.TCheckbutton', font=label_font, padding=(5,3)) # Padding (horizontal, vertical)

    app_vars = {} 
    for nombre_app_key, config_detalle in APLICACIONES_CONFIG.items():
        var = tk.BooleanVar()
        icon = config_detalle.get("icon", "") # Obtener el icono si existe
        
        # Construir el texto del checkbox
        chk_text = f" {icon}  {nombre_app_key}" if icon else nombre_app_key
        
        chk_state = tk.NORMAL
        
        tipo_actual = config_detalle["tipo"]
        if tipo_actual == "configurar_autologon_gui" and not PYWINAUTO_AVAILABLE:
            chk_text += " (⚠ pywinauto no disponible)" # Usar un icono de advertencia
            chk_state = tk.DISABLED
            var.set(False)
        
        # Crear un frame para cada checkbox para mejor alineación si se añaden más cosas
        chk_frame = ttk.Frame(apps_frame_container)
        chk_frame.pack(anchor="w", fill="x", pady=2)

        chk = ttk.Checkbutton(chk_frame, text=chk_text, variable=var, style='App.TCheckbutton', state=chk_state)
        chk.pack(side=tk.LEFT, padx=(5,0))
        # Aquí podrías añadir una pequeña descripción al lado si quisieras, por ejemplo:
        # desc_text = config_detalle.get("descripcion_corta", "")
        # if desc_text:
        #     desc_label = ttk.Label(chk_frame, text=desc_text, font=("Segoe UI", 8), foreground="#666666")
        #     desc_label.pack(side=tk.LEFT, padx=10)

        app_vars[nombre_app_key] = var

    # Frame para el botón y la info
    bottom_frame = ttk.Frame(main_frame) # No necesita ser LabelFrame
    bottom_frame.pack(side=tk.BOTTOM, fill="x", pady=(10, 0))

    # Botón "Siguiente" con mejor estilo
    style.configure('Accent.TButton', font=(label_font.cget("family"), label_font.cget("size"), "bold"))
    # Si el tema lo permite, puedes intentar cambiar el color de fondo del botón.
    # style.map('Accent.TButton', background=[('active', ACCENT_COLOR), ('!disabled', OTHER_ACCENT_COLOR)])
    
    next_button = ttk.Button(bottom_frame, text="Continuar ➔",
                             style='Accent.TButton',
                             command=lambda: on_siguiente_click(app_vars, root),
                             width=15)
    next_button.pack(side=tk.RIGHT, pady=(10,0), ipady=5) # ipady para hacerlo un poco más alto

    # Información en la parte inferior
    info_text_parts = [
        f"Origen de programas: '{PROGRAMAS_DIR}'",
        f"Archivos copiados a: '{DOCUMENTOS_DIR}'"
    ]
    if not PYWINAUTO_AVAILABLE:
        info_text_parts.append("Autologon (GUI) requiere 'pywinauto'.")
    
    info_label = ttk.Label(bottom_frame, text="\n".join(info_text_parts),
                           justify=tk.LEFT, font=small_font, foreground="#555555")
    info_label.pack(side=tk.LEFT, pady=(10,0), fill="x", expand=True, anchor='sw')

    # Mensaje inicial si falta pywinauto
    if not PYWINAUTO_AVAILABLE:
        root.after(150, lambda: messagebox.showwarning("Advertencia de Dependencia", 
                               "La librería 'pywinauto' no está instalada.\n"
                               "La funcionalidad de Autologon (GUI) no estará disponible.\n\n"
                               "Instala 'pywinauto' con 'pip install pywinauto' y reinicia."))
    root.mainloop()

if __name__ == "__main__":
    crear_ventana_principal()