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

## Para catualizar la version de los .exe

Aparte de cambiarlo en su carpeta respectiva se debe cambiar el el player.py

"exe_filename": "Nuevo.exe",
