# AutomateInstall: Asistente de Configuración Automatizada

Este proyecto (`player.py`) proporciona una interfaz gráfica para automatizar la instalación y configuración de aplicaciones en sistemas Windows. Permite seleccionar programas y realizar acciones como instalaciones silenciosas, asistidas o configuraciones específicas.

---
## ⚠️ ADVERTENCIAS IMPORTANTES ⚠️

*   **REEMPLAZAR ARCHIVOS `.EXE` DE EJEMPLO:** La carpeta `Programas/` distribuida con este script podría contener archivos de texto (`.txt`) renombrados como `.exe` (o simplemente ser marcadores de posición vacíos). **DEBES REEMPLAZARLOS por los archivos instaladores `.exe` REALES y correspondientes a cada aplicación antes de usar el script o compilarlo.** El script no funcionará correctamente sin los instaladores válidos.
*   **PYTHON Y DEPENDENCIAS (SOLO PARA MODIFICAR Y RECOMPILAR):** Si solo vas a ejecutar el archivo `.exe` proporcionado, **no necesitas instalar Python ni ninguna de sus dependencias**. Sin embargo, si planeas modificar el código fuente (`player.py`) y necesitas generar un nuevo archivo `.exe`, entonces sí necesitarás tener Python instalado en tu sistema junto con las dependencias listadas más abajo.
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
```
```bash
python -m pip install pywinauto
```
```bash
python -m pip install pyinstaller
```
---
## ⚙️ Generar el Archivo Ejecutable (`.exe`)

Una vez que tengas Python, las dependencias (incluyendo `pyinstaller`) instaladas, y hayas modificado el script `player.py` a tu gusto (especialmente la variable `PROGRAMAS_DIR` si es necesario y te has asegurado de tener los instaladores reales), puedes generar un archivo `.exe` independiente.

Abre una terminal (CMD o PowerShell) en el directorio donde se encuentra tu archivo `player.py` y ejecuta el siguiente comando:

```bash
pyinstaller --onefile --windowed --hidden-import=requests player.py
```
Explicación del comando:
*   `pyinstaller`: Es la herramienta que empaqueta tu script.
*   `--onefile`: Crea un único archivo ejecutable `.exe` en lugar de una carpeta con múltiples archivos.
*   `--windowed`: Indica que es una aplicación con interfaz gráfica (GUI) y no debe abrirse una ventana de consola al ejecutar el `.exe`.
*   `--hidden-import=requests`: Asegura que la biblioteca `requests` (y cualquier otra que `PyInstaller` pueda no detectar automáticamente) se incluya correctamente en el ejecutable. Si usas otras bibliotecas que `PyInstaller` podría omitir, puedes añadirlas aquí de forma similar (ej. `--hidden-import=otralib`).
*   `player.py`: Es el nombre de tu script principal.
Después de que el comando se complete, encontrarás el archivo `player.exe` (o el nombre que `PyInstaller` le asigne por defecto si no lo especificas con `--name`) dentro de una subcarpeta llamada `dist` en el mismo directorio. Este archivo `.exe` ya no requiere Python ni las dependencias para ejecutarse en otras máquinas Windows.

---
## 🐍 Cómo instalar Tkinter

Tkinter es parte de la biblioteca estándar de Python y, por lo general, **ya viene incluido** con las instalaciones de Python en Windows. No suele requerir una instalación separada.

Para verificar si `tkinter` está disponible, puedes abrir una terminal de Python (escribe `python` y presiona Enter) e intentar importar el módulo:
```python
import tkinter
```
Si no recibes ningún error, `tkinter` está instalado y listo para usarse.

En el caso improbable de que `tkinter` no esté presente (lo que podría ocurrir con instalaciones de Python muy personalizadas o mínimas), la forma más sencilla de obtenerlo es reinstalar Python desde [python.org](https://www.python.org/downloads/windows/), asegurándote de que la opción "tcl/tk and IDLE" (o similar, referente a Tk) esté seleccionada durante el proceso de instalación.

En sistemas basados en Debian/Ubuntu (Linux), si Python fue instalado sin Tk, se instalaría con:
```bash
sudo apt-get install python3-tk
```
---
## 📜 Licencia

Este proyecto es de código abierto. Siéntete libre de usarlo y modificarlo.

---
## 👤 Autor

Desarrollado por Joel Añón Rosendo.
