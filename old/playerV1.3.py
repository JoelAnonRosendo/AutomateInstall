# --- START OF FILE player.py ---

import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil
import requests
import subprocess
import threading
import time

# Intenta importar pywinauto, necesario para Autologon GUI
try:
    from pywinauto.application import Application, ProcessNotFoundError
    from pywinauto.findwindows import ElementNotFoundError, WindowNotFoundError
    from pywinauto.timings import TimeoutError as PywinautoTimeoutError
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False
    print("ADVERTENCIA: pywinauto no está instalado. La configuración automática de Autologon no funcionará.")
    print("Instálalo con: pip install pywinauto")


# --- CONFIGURACIÓN DE APLICACIONES ---
APLICACIONES_CONFIG = {
    "Autologon": {
        "tipo": "configurar_autologon_gui",
        "exe_filename": "Autologon64.exe",
        "username": "player",
        "domain": "",
        "password": "player"
    },
    "Chrome": {
        "tipo": "instalar_local",
        "exe_filename": "Ninite Chrome Installer.exe",
        "args_instalacion": []
    },
    "Novalct": {
        "tipo": "instalar_manual_asistido", # Nuevo tipo
        "exe_filename": "NovaLCT V5.4.7.1.exe",
        "mensaje_usuario": "Se abrirá el instalador de NovaLCT.\n\nPor favor, completa la instalación manualmente siguiendo todos sus pasos (incluyendo los de drivers si los pide).\n\nUna vez que la instalación de NovaLCT haya FINALIZADO POR COMPLETO, cierra esta ventana para continuar con las demás aplicaciones."
    },
    "PlataformaUniversal": {
        "tipo": "instalar_local",
        "exe_filename": "LSPlayerVideo-0.11.3 Multicliente Standard Setup.exe",
        "args_instalacion": ["/VERYSILENT", "/SUPPRESSMSGBOXES"]
    },
    "TeamViewer": {
        "tipo": "instalar_local",
        "exe_filename": "TeamViewer_Host_Setup_x64.exe",
        "args_instalacion": ["/S"]
    },
    "VLC": {
        "tipo": "instalar_local",
        "exe_filename": "Ninite VLC Installer.exe",
        "args_instalacion": []
    }
}

# --- RUTAS IMPORTANTES ---
PROGRAMAS_DIR = "D:/Programas"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DESCARGAS_DIR = os.path.join(BASE_DIR, "archivos_descargados_temp")
DOCUMENTOS_DIR = os.path.join(os.path.expanduser("~"), "Documents")
os.makedirs(DESCARGAS_DIR, exist_ok=True)

# --- LÓGICA DE PROCESAMIENTO ---

progress_window = None
progress_bar = None
progress_label_status = None
progress_label_percentage = None
# Variable global para manejar la espera de la ventana manual de NovaLCT
# Esto es útil si la ventana de aviso se crea desde el hilo principal de Tkinter
# pero la lógica de proceso está en otro hilo. En este caso, usamos un simple messagebox.askokcancel
# que es bloqueante en el hilo donde se llama.

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
        
        # Para NovaLCT (manual) y otras que puedan ser manuales
        if wait_for_completion:
            process = subprocess.Popen(comando, cwd=os.path.dirname(ruta_exe_a_instalar) or '.')
            try:
                process.wait(timeout=timeout) # Esperar a que el proceso termine
                print(f"DEBUG: Proceso {os.path.basename(ruta_exe_a_instalar)} terminado con código de salida: {process.returncode}")
                if process.returncode != 0:
                    print(f"ADVERTENCIA: El instalador {os.path.basename(ruta_exe_a_instalar)} terminó con un código de error: {process.returncode}")
                    # No necesariamente es un fallo catastrófico para el flujo principal si el usuario lo maneja
            except subprocess.TimeoutExpired:
                print(f"ADVERTENCIA: Timeout esperando a {os.path.basename(ruta_exe_a_instalar)}. El proceso puede seguir en segundo plano.")
                # Considerar si esto es un fallo o si se debe continuar
                return False # Para instalaciones manuales, esto podría ser un problema si se espera cierre.
        else:
            # Para instalaciones silenciosas que se ejecutan en segundo plano
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
    # (Este código permanece igual que en la versión anterior que incluía pywinauto)
    if not PYWINAUTO_AVAILABLE:
        error_msg = "pywinauto no está disponible. No se puede configurar Autologon automáticamente."
        print(f"DEBUG: {error_msg}")
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0))
        root_gui_for_update.after(0, lambda: messagebox.showerror("Error de Dependencia", error_msg + "\nPor favor, instálalo con 'pip install pywinauto'."))
        return False

    if not os.path.exists(ruta_autologon_exe):
        error_msg = f"Autologon no encontrado en: {ruta_autologon_exe}"
        print(f"DEBUG: {error_msg}")
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0))
        root_gui_for_update.after(0, lambda: messagebox.showerror("Archivo No Encontrado", error_msg))
        return False

    app = None 
    try:
        print(f"DEBUG: Iniciando Autologon desde: {ruta_autologon_exe}")
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Iniciando Autologon...", valor_barra=10))
        app = Application(backend="uia").start(ruta_autologon_exe)
        
        dlg = None
        for _ in range(10): 
            try:
                dlg = app.window(title_re="^Autologon.*") 
                if dlg.exists() and dlg.is_visible():
                    break
            except (WindowNotFoundError, ElementNotFoundError, ProcessNotFoundError):
                time.sleep(0.5)
        if not dlg or not dlg.exists():
            raise WindowNotFoundError("No se pudo encontrar la ventana de Autologon.")

        dlg.wait('visible', timeout=10) 
        print("DEBUG: Ventana de Autologon encontrada.")
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Ventana de Autologon detectada.", valor_barra=30))

        edit_controls = dlg.children(control_type="Edit")
        
        if len(edit_controls) < 3:
            raise Exception(f"Autologon no tiene los 3 campos de edición esperados. Encontrados: {len(edit_controls)}")

        print(f"DEBUG: Rellenando campos: Usuario='{username}', Dominio='{domain}', Contraseña='****'")
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Rellenando campos...", valor_barra=50))
        
        edit_controls[0].set_edit_text(username)
        edit_controls[1].set_edit_text(domain) 
        edit_controls[2].set_edit_text(password) 
        
        time.sleep(0.2)

        print("DEBUG: Buscando botón 'Enable'.")
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Habilitando Autologon...", valor_barra=70))
        enable_button = dlg.child_window(title="Enable", control_type="Button")
        enable_button.click_input()
        
        try:
            dlg.wait_not('visible', timeout=5) 
            print("DEBUG: Autologon configurado y ventana cerrada.")
            root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Autologon configurado.", valor_barra=100, texto_porcentaje="Hecho ✓"))
            return True
        except PywinautoTimeoutError: 
            print("DEBUG: La ventana de Autologon no se cerró como se esperaba (timeout).")
            if dlg.exists() and dlg.is_visible():
                 messagebox.showwarning("Autologon", "La ventana de Autologon no se cerró. Por favor, verifica manualmente.")
                 root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Autologon: verificar manualmente.", valor_barra=90))
                 return False
            else: 
                 print("DEBUG: Autologon (probablemente) configurado. Ventana cerrada, pero 'wait_not' falló el timeout.")
                 root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status="Autologon configurado (con aviso).", valor_barra=100, texto_porcentaje="Hecho ✓"))
                 return True

    except Exception as e:
        error_msg = f"Error configurando Autologon con pywinauto: {e}"
        print(f"DEBUG: {error_msg}")
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0))
        root_gui_for_update.after(0, lambda: messagebox.showerror("Error Autologon", error_msg))
        return False
    finally:
        pass


def instalar_manual_asistido_app(nombre_app, ruta_exe, mensaje_al_usuario, root_gui_for_update):
    """
    Lanza un instalador y muestra un mensaje para que el usuario lo complete manualmente.
    Retorna True si el usuario confirma que ha completado, False si cancela o falla el lanzamiento.
    """
    root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=f"Preparando instalación manual de {nombre_app}...", valor_barra=10))
    
    if not os.path.exists(ruta_exe):
        error_msg = f"Instalador para {nombre_app} no encontrado en: {ruta_exe}"
        print(f"DEBUG: {error_msg}")
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0, texto_porcentaje="Error X"))
        root_gui_for_update.after(0, lambda: messagebox.showerror("Archivo No Encontrado", error_msg))
        return False

    print(f"DEBUG: Lanzando instalador manual para {nombre_app} desde {ruta_exe}")
    
    # No queremos que Popen bloquee aquí, solo lo lanzamos.
    # La espera del usuario la manejará el messagebox.
    try:
        subprocess.Popen([ruta_exe], cwd=os.path.dirname(ruta_exe) or '.')
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=f"Instalador de {nombre_app} lanzado. Esperando al usuario...", valor_barra=50))
    except Exception as e:
        error_msg_launch = f"No se pudo lanzar el instalador de {nombre_app}: {e}"
        print(f"DEBUG: {error_msg_launch}")
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg_launch, valor_barra=0, texto_porcentaje="Error X"))
        root_gui_for_update.after(0, lambda: messagebox.showerror("Error de Lanzamiento", error_msg_launch))
        return False

    # Mostrar el messagebox. Esto SÍ es bloqueante para el hilo actual (el de procesamiento).
    # Necesitamos ejecutarlo de una forma que la GUI principal siga activa.
    # Si messagebox.askokcancel se llama directamente desde el hilo de procesamiento,
    # y ese hilo fue iniciado por la GUI, debería funcionar bien, bloqueando
    # ese hilo secundario, pero no la GUI principal (gracias al threading).

    # Creamos una Event para sincronizar si fuera necesario (aquí messagebox es modal)
    # user_confirmation_event = threading.Event()
    # def ask_user():
    #     # Este messagebox es modal para la aplicación, detendrá el hilo actual hasta que se cierre.
    #     # No detendrá el event loop de Tkinter si este se ejecuta en el hilo principal.
    #     confirmed = messagebox.askokcancel(
    #         f"Instalación Manual: {nombre_app}",
    #         mensaje_al_usuario,
    #         parent=progress_window # Para que aparezca sobre la ventana de progreso si está visible
    #     )
    #     if confirmed:
    #         user_confirmation_event.set()
    # # root_gui_for_update.after(0, ask_user) # Esto lo pondría en la cola del hilo de la GUI, puede ser no ideal
    # # user_confirmation_event.wait() # Esperar a que el usuario responda

    # Más simple: messagebox directamente, es modal
    # Asegurarse que este mensaje sea visible para el usuario.
    # Ejecutar messagebox desde el hilo de trabajo (no el de la GUI principal directamente)
    # está bien siempre y cuando ese hilo no sea el principal de Tkinter y el mensaje sea modal.
    
    # Como `procesar_seleccion` se ejecuta en un hilo, podemos llamar a messagebox directamente
    # y bloqueará este hilo hasta que el usuario responda. La GUI principal
    # (creada en `crear_ventana_principal`) debería seguir responsiva.
    
    # Antes de mostrar el mensaje, hacemos la ventana de progreso no-modal temporalmente
    # para que el usuario pueda interactuar con el messagebox.
    progress_was_grabbed = False
    if progress_window and progress_window.winfo_exists() and progress_window.grab_status():
        progress_window.grab_release()
        progress_was_grabbed = True

    confirmed = messagebox.askokcancel( # `parent` no es necesario aquí, se centrará en pantalla.
        f"Instalación Manual Asistida: {nombre_app}",
        mensaje_al_usuario
    )

    if progress_was_grabbed and progress_window and progress_window.winfo_exists():
        progress_window.grab_set() # Restaurar modalidad si la tenía


    if confirmed:
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=f"Usuario confirmó finalización de {nombre_app}.", valor_barra=100, texto_porcentaje="Hecho ✓"))
        return True
    else:
        root_gui_for_update.after(0, lambda: actualizar_progreso_gui(texto_status=f"Usuario canceló continuación tras {nombre_app}.", valor_barra=0, texto_porcentaje="Cancelado X"))
        # Podríamos querer que el proceso entero se detenga si cancela. Por ahora solo esta app.
        return False


def procesar_seleccion(apps_seleccionadas_nombres, root_gui):
    global progress_window, progress_bar, progress_label_status, progress_label_percentage

    def crear_ventana_progreso_threadsafe():
        # (Igual que antes)
        global progress_window, progress_bar, progress_label_status, progress_label_percentage
        progress_window = tk.Toplevel(root_gui)
        progress_window.title("Procesando...")
        progress_window.geometry("450x170") 
        progress_window.resizable(False, False)
        progress_window.transient(root_gui) 
        progress_window.grab_set()          

        try:
            root_x = root_gui.winfo_x(); root_y = root_gui.winfo_y()
            root_width = root_gui.winfo_width(); root_height = root_gui.winfo_height()
            prog_width = 450; prog_height = 170
            center_x = root_x + (root_width // 2) - (prog_width // 2)
            center_y = root_y + (root_height // 2) - (prog_height // 2)
            progress_window.geometry(f"{prog_width}x{prog_height}+{center_x}+{center_y}")
        except tk.TclError: pass

        progress_label_status = ttk.Label(progress_window, text="Iniciando...", font=("Arial", 10), wraplength=380)
        progress_label_status.pack(pady=(15,5), padx=10, fill="x")
        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=380, mode="determinate")
        progress_bar.pack(pady=10, padx=10)
        progress_label_percentage = ttk.Label(progress_window, text="", font=("Arial", 10))
        progress_label_percentage.pack(pady=5)

    root_gui.after(0, crear_ventana_progreso_threadsafe)
    while not (progress_window and progress_window.winfo_exists()):
        time.sleep(0.1)

    # Determinar si NovaLCT está en la selección y ponerla primero
    ordered_apps_seleccionadas = []
    novalct_key = None
    for key in apps_seleccionadas_nombres:
        if APLICACIONES_CONFIG[key]["tipo"] == "instalar_manual_asistido" and key == "Novalct": # Ser específico
            novalct_key = key
        else:
            ordered_apps_seleccionadas.append(key)
    
    if novalct_key:
        ordered_apps_seleccionadas.insert(0, novalct_key) # Poner NovaLCT primero

    total_apps = len(ordered_apps_seleccionadas)
    for i, app_nombre_key in enumerate(ordered_apps_seleccionadas):
        app_config_detalle = APLICACIONES_CONFIG[app_nombre_key]
        tipo_accion = app_config_detalle["tipo"]
        status_actual = f"Procesando: {app_nombre_key} ({i+1}/{total_apps})"
        root_gui.after(0, lambda s=status_actual: actualizar_progreso_gui(texto_status=s, valor_barra=0, texto_porcentaje=""))
        
        success_flag = False

        if tipo_accion == "instalar_manual_asistido":
            nombre_exe_en_subcarpeta = app_config_detalle["exe_filename"]
            ruta_exe_origen = os.path.join(PROGRAMAS_DIR, app_nombre_key, nombre_exe_en_subcarpeta)
            mensaje_usuario = app_config_detalle["mensaje_usuario"]
            
            # La función `instalar_manual_asistido_app` es bloqueante hasta que el usuario responda al messagebox
            if instalar_manual_asistido_app(app_nombre_key, ruta_exe_origen, mensaje_usuario, root_gui):
                success_flag = True
            else:
                # Si el usuario cancela aquí, podríamos querer detener todo el proceso.
                root_gui.after(0, lambda: actualizar_progreso_gui(texto_status="Proceso cancelado por el usuario.", valor_barra=0))
                root_gui.after(1000, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)
                messagebox.showwarning("Cancelado", f"Instalación de {app_nombre_key} cancelada. Las tareas restantes no se ejecutarán.")
                return # Termina todo el hilo de procesamiento


        elif tipo_accion == "descargar_e_instalar":
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
                # (Manejo de error si no existe)
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
                else:
                    root_gui.after(0, lambda an=app_nombre_key: actualizar_progreso_gui(texto_status=f"Fallo copia {an}", valor_barra=0, texto_porcentaje="Error X"))
            else:
                # (Manejo de error si no existe)
                error_msg_detalle = f"Archivo a copiar no encontrado: {os.path.normpath(ruta_exe_origen)}"
                root_gui.after(0, lambda emd=error_msg_detalle: actualizar_progreso_gui(texto_status=emd, valor_barra=0, texto_porcentaje="Error X"))
                root_gui.after(0, lambda emd=error_msg_detalle: messagebox.showerror("No Encontrado", emd))

        elif tipo_accion == "configurar_autologon_gui":
            # (Igual que antes)
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
                # (Manejo de error si pywinauto no está)
                error_msg = "Autologon: pywinauto no disponible."
                root_gui.after(0, lambda: actualizar_progreso_gui(texto_status=error_msg, valor_barra=0, texto_porcentaje="Error X"))
                root_gui.after(0, lambda: messagebox.showerror("Dependencia", "pywinauto no instalado para Autologon."))
        
        if success_flag and progress_label_percentage.cget("text") in ["Hecho ✓", "Copiado ✓", "Lanzado"]:
            time.sleep(0.5) 
        else:
            time.sleep(0.2)
            
    root_gui.after(0, lambda: actualizar_progreso_gui(texto_status="Proceso finalizado.", valor_barra=100, texto_porcentaje="Completado"))
    root_gui.after(3000, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)
    root_gui.after(100, lambda: messagebox.showinfo("Finalizado", "Tareas solicitadas han sido procesadas o iniciadas."))


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
            exe_f_display = config.get("exe_filename", config.get("nombre_archivo_descargado", "archivo_desconocido.exe"))

            if config["tipo"] == "instalar_manual_asistido":
                resumen_acciones_str += f"- {nombre_app_key}: Iniciar instalación manual de '{exe_f_display}'.\n   (Se te pedirá confirmación para continuar después de esta).\n"
                if nombre_app_key == "Novalct":
                    novalct_seleccionado = True
            elif config["tipo"] == "configurar_autologon_gui":
                 resumen_acciones_str += f"- {nombre_app_key}: Configurar Autologon para '{config['username']}'.\n"
                 requiere_pywinauto_seleccionado = True
            elif config["tipo"] == "descargar_e_instalar":
                resumen_acciones_str += f"- {nombre_app_key}: Descargar e instalar '{exe_f_display}'.\n"
            elif config["tipo"] == "instalar_local":
                resumen_acciones_str += f"- {nombre_app_key}: Instalar '{exe_f_display}' desde local.\n"
            elif config["tipo"] == "copiar_exe":
                resumen_acciones_str += f"- {nombre_app_key}: Copiar '{exe_f_display}' a Documentos.\n"


    if not hay_seleccion:
        messagebox.showwarning("Sin Selección", "No has seleccionado ninguna aplicación.")
        return

    if requiere_pywinauto_seleccionado and not PYWINAUTO_AVAILABLE:
        messagebox.showerror("Dependencia Faltante",
                             "Ha seleccionado Autologon que requiere 'pywinauto', pero no está instalado.\n"
                             "Instálalo con 'pip install pywinauto' o deselecciona Autologon.")
        return

    if novalct_seleccionado and len(seleccionadas_keys) > 1:
        resumen_acciones_str += "\nATENCIÓN: NovaLCT se procesará primero. Deberás completar su instalación y luego confirmar para que el resto de las tareas continúen.\n"
    
    resumen_acciones_str += "\n¿Deseas continuar?"
    if messagebox.askyesno("Confirmar Acciones", resumen_acciones_str):
        thread = threading.Thread(target=procesar_seleccion, args=(seleccionadas_keys, root_gui), daemon=True)
        thread.start()

# --- INTERFAZ GRÁFICA PRINCIPAL ---
def crear_ventana_principal():
    root = tk.Tk()
    root.title("Instalador Personalizado (v1.3 - NovaLCT Manual)") 
    root.geometry("520x550") 
    root.minsize(480, 450)   

    try: # Centrar ventana
        window_width = 520; window_height = 550
        screen_width = root.winfo_screenwidth(); screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        if center_x < 0: center_x = 0 
        if center_y < 0: center_y = 0
        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    except tk.TclError: pass

    if not os.path.isdir(PROGRAMAS_DIR): # Comprobar ruta programas
         messagebox.showerror("Error Crítico", f"Carpeta de programas NO encontrada en:\n'{PROGRAMAS_DIR}'\nEl programa se cerrará.")
         root.destroy()
         return

    frame_apps = ttk.LabelFrame(root, text="Selecciona programas", padding=(15, 10))
    frame_apps.pack(padx=15, pady=15, fill="x", expand=False)

    app_vars = {} 
    s_chk = ttk.Style()
    s_chk.configure('TCheckbutton', font=('Arial', 10), padding=3)

    for nombre_app_en_config, config_detalle in APLICACIONES_CONFIG.items():
        var = tk.BooleanVar()
        chk_text = nombre_app_en_config
        chk_state = tk.NORMAL
        
        tipo_actual = config_detalle["tipo"]
        if tipo_actual == "configurar_autologon_gui" and not PYWINAUTO_AVAILABLE:
            chk_text += " (pywinauto no disp.)"
            chk_state = tk.DISABLED
            var.set(False)
        # NovaLCT manual no depende de pywinauto
        
        chk = ttk.Checkbutton(frame_apps, text=chk_text, variable=var, style='TCheckbutton', state=chk_state)
        chk.pack(anchor="w", padx=5, pady=(3, 4))
        app_vars[nombre_app_en_config] = var

    frame_inferior = ttk.Frame(root)
    frame_inferior.pack(side=tk.BOTTOM, fill="x", padx=15, pady=(0, 15))
    next_button = ttk.Button(frame_inferior, text="Siguiente", command=lambda: on_siguiente_click(app_vars, root), width=15)
    next_button.pack(side=tk.RIGHT, pady=(10,0))

    info_text_parts = [
        f"Programas en: '{PROGRAMAS_DIR}'",
        f"Copia a: '{DOCUMENTOS_DIR}'"
    ]
    if not PYWINAUTO_AVAILABLE:
        info_text_parts.append("Autologon (GUI) requiere 'pywinauto'.")
    
    info_label = ttk.Label(frame_inferior, text="\n".join(info_text_parts), justify=tk.LEFT, font=("Arial", 8), padding=(0,5))
    info_label.pack(side=tk.LEFT, pady=(10,0), fill="x", expand=True)

    if not PYWINAUTO_AVAILABLE:
        root.after(100, lambda: messagebox.showwarning("Advertencia", 
                               "Librería 'pywinauto' no instalada.\n"
                               "Configuración de Autologon (GUI) no funcionará.\n"
                               "Instala con 'pip install pywinauto'."))
    root.mainloop()

if __name__ == "__main__":
    crear_ventana_principal()