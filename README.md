# AutomateInstall
Automatización de instalación


## WARNING --> Remplazar los .exe de la carpeta Programas por los verdaderos exe debido a que los que hay son txt

# Editar player.py

### ¡Es necesario tener instalado Python y estas dependencias de acontinuacion!
#### python -m pip install requests
#### python -m pip install pyinstaller


Si se quiere cambiar nombres o agregar servicios al .py.

Una vez editado el documento .py realizaremos estas acciones

1._ Iniciar PowerShell en modo administrador.

2._ Ir a la raiz donde esta el .py es decir D:\

3._ Ejecutar este comando para limpiar todo lo que tenga que ver con el ejecutable
    Remove-Item -Recurse -Force build, dist
    
4._ Ahora bolberemos a crear el exe y para eso escribimos el siguiente comando.
    pyinstaller --onefile --windowed --hidden-import=requests player.py
    
5._ Y por ultimo el exe se generara en la carpeta dist que esta en D:\dist, copias el exe y lo pones en D:\.
    ¡La carpeta dist esta oculta!
    
6._ Ya se puede ejecutar el exe.

## Para atualizar la version de los .exe

Aparte de cambiarlo en su carpeta respectiva se debe cambiar el el player.py

"exe_filename": "Nuevo.exe",












# Asistente de Configuración de PC (Player Setup)

Este script de Python (`player.py`) proporciona una interfaz gráfica de usuario (GUI) para automatizar la instalación y configuración de una serie de aplicaciones predefinidas en un sistema Windows.

## Características

*   Interfaz gráfica sencilla para seleccionar aplicaciones.
*   Instalación de aplicaciones desde archivos locales (`.exe`).
*   Configuración automática de "Autologon" (requiere `pywinauto`).
*   Instalación manual asistida para aplicaciones que lo requieran (ej. NovaLCT).
*   Copia de archivos a la carpeta "Documentos".
*   Barra de progreso y mensajes de estado durante las operaciones.

## Prerrequisitos

1.  **Sistema Operativo:** Windows.
2.  **Python:** Python 3.x (se recomienda 3.7 o superior). Asegúrate de que Python esté añadido al PATH del sistema durante la instalación.
3.  **PIP:** El gestor de paquetes de Python (normalmente se instala con Python).
4.  **Archivos de Programa/Instaladores:** Este es el requisito más importante. El script espera que los archivos ejecutables (.exe) de los programas a instalar estén ubicados en una estructura de carpetas específica dentro de `D:/Programas`. Debes crear esta estructura y colocar los archivos correspondientes:

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

    *   **Nota:** Si tu unidad principal no es `D:` o deseas usar una ruta diferente para los programas, deberás modificar la variable `PROGRAMAS_DIR` al principio del archivo `player.py`.

## Instalación de Dependencias de Python

Antes de ejecutar el script, necesitas instalar las bibliotecas de Python requeridas. Abre una terminal o Símbolo del sistema (CMD) y ejecuta:

```bash
pip install requests pywinauto
