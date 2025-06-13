# AutomateInstall: Asistente de Configuración Automatizada

Este proyecto (`player.py`) proporciona una interfaz gráfica para automatizar la instalación y configuración de aplicaciones en sistemas Windows. Permite seleccionar programas y realizar acciones como instalaciones silenciosas, asistidas o configuraciones específicas.

---
## ⚠️ ADVERTENCIAS IMPORTANTES ⚠️

*   **REEMPLAZAR ARCHIVOS `.EXE` DE EJEMPLO:** La carpeta `Programas/` distribuida con este script podría contener archivos de texto (`.txt`) renombrados como `.exe` (o simplemente ser marcadores de posición vacíos). **DEBES REEMPLAZARLOS por los archivos instaladores `.exe` REALES y correspondientes a cada aplicación antes de usar el script o compilarlo.** El script no funcionará correctamente sin los instaladores válidos.
*   **PYTHON ES NECESARIO (PARA DESARROLLO/MODIFICACIÓN):** Para ejecutar el script directamente (`python player.py`) o para modificarlo, necesitas tener Python instalado en tu sistema y las dependencias necesarias.
*   **CONFIGURACIÓN DE RUTAS:** El script está configurado por defecto para buscar programas en `D:/Programas`. Si tus instaladores están en otra ubicación, deberás editar la variable `PROGRAMAS_DIR` dentro del archivo `player.py`.

---
## 🛠️ Prerrequisitos

1.  **Sistema Operativo:** Windows.
2.  **Python:** Python 3.x (se recomienda 3.7 o superior). Asegúrate de que Python esté añadido al PATH del sistema.
    *   La biblioteca **`tkinter`** (para la GUI) debe estar disponible. Usualmente viene con Python en Windows.
3.  **PIP:** El gestor de paquetes de Python (normalmente se instala con Python).
4.  **Archivos de Programa/Instaladores (¡REALES!):**
    Coloca los instaladores `.exe` reales en la siguiente estructura dentro de `D:/Programas` (o la ruta que configures en `PROGRAMAS_DIR` en el script):

    ```
    D:
    └── Programas
        ├── Autologon
        │   └── Autologon64.exe
        ├── Chrome
        │   └── Ninite Chrome Installer.exe
        ├── Novalct
        │   └── NovaLCT V5.4.7.1.exe
        ├── PlataformaUniversal
        │   └── LSPlayerVideo-0.11.3 Multicliente Standard Setup.exe
        ├── TeamViewer
        │   └── TeamViewer_Host_Setup_x64.exe
        └── VLC
            └── Ninite VLC Installer.exe
    ```

---
## 📦 Instalación de Dependencias de Python

Para que el script `player.py` funcione (ya sea ejecutándolo directamente o antes de compilarlo a un `.exe`), necesitas instalar las siguientes dependencias. Abre una terminal (CMD o PowerShell) y ejecuta estos comandos uno por uno:

```bash
python -m pip install requests
python -m pip install pywinauto
python -m pip install pyinstaller
