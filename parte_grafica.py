# -*- coding: utf-8 -*-
"""
Created on Sun Oct 22 22:40:45 2023

@author: Ignacio Carvajal
"""
import tkinter as tk
from tkinter import filedialog
from tkinter import PhotoImage

from tkinter import ttk  # Importa ttk para widgets modernos

import shutil
import os

def seleccionar_archivo():
    archivo_ruta = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx")])
    if archivo_ruta:
        # Obtener la ruta de la carpeta de destino
        carpeta_destino = 'C://Users//Usuario//Desktop//sergio//pedidos'#filedialog.askdirectory()

        if carpeta_destino:
            # Generar la ruta completa de destino
            nombre_archivo = os.path.basename(archivo_ruta)
            ruta_destino = os.path.join(carpeta_destino, nombre_archivo)

            try:
                # Copiar el archivo Excel a la carpeta de destino
                shutil.copy(archivo_ruta, ruta_destino)
                mensaje.config(text=f"Archivo {nombre_archivo} guardado en {ruta_destino}")
            except Exception as e:
                mensaje.config(text=f"Error al guardar el archivo: {str(e)}")

def ejecutar_modelo():
    try:
        # Obtener el valor ingresado en el campo de entrada y convertirlo a un entero
        #num_rutas = int(entrada_num_rutas.get())
        mensaje.config(text=f"Modelo en ejecución con {num_rutas} rutas...")
        
        
        # Aquí puedes utilizar num_rutas según tus necesidades
    except ValueError:
        mensaje.config(text="Ingresa un número válido para las rutas.")

"""
# Configuración de la ventana tkinter principal
ventana = tk.Tk()
ventana.title("Cargador de Archivos Excel")
ventana.geometry("600x400")

# Botón para seleccionar un archivo Excel
btn_seleccionar = tk.Button(ventana, text="Seleccionar archivo Excel", command=seleccionar_archivo)
btn_seleccionar.pack(pady=20)

# Etiqueta para mostrar un mensaje
mensaje = tk.Label(ventana, text="")
mensaje.pack()

# Etiqueta para indicar al usuario que ingrese el número de rutas
#lbl_num_rutas = tk.Label(ventana, text="Ingrese el número de rutas:")
#lbl_num_rutas.pack()

# Campo de entrada para el número de rutas
#entrada_num_rutas = tk.Entry(ventana)
#entrada_num_rutas.pack()

# Botón para ejecutar el modelo
btn_ejecutar = tk.Button(ventana, text="Ejecutar Modelo", command=ejecutar_modelo)
btn_ejecutar.pack()

# Configuración de la segunda ventana (ventana del modelo)
ventana_modelo = tk.Toplevel(ventana)
ventana_modelo.title("Ventana del Modelo")
ventana_modelo.geometry("600x400")
ventana_modelo.withdraw()  # Ocultar la ventana del modelo al inicio

# Mostrar la ventana del modelo cuando se haga clic en el botón de ejecución
btn_ejecutar.config(command=lambda: ventana_modelo.deiconify())

ventana.mainloop()

"""

ventana = tk.Tk()
ventana.title("Cargador de Archivos Excel")
ventana.geometry("400x200")

# Establecer el fondo blanco
ventana.configure(bg="white")

# Cargar la imagen
imagen = PhotoImage(file="WSC-LOGO-FINAL.png")

# Mostrar la imagen en la parte superior derecha
imagen_label = tk.Label(ventana, image=imagen, bg="white")
imagen_label.place(relx=1.0, rely=0, anchor="ne")

# Crear un marco para los botones y el mensaje
boton_marco = tk.Frame(ventana, bg="white")
boton_marco.pack(expand=True)

# Utilizar ttk para botones modernos con esquinas redondeadas
style = ttk.Style()
style.configure("TButton", padding=6, relief="flat", background="lightblue", borderwidth=0)
style.map("TButton", background=[("active", "lightblue")])

btn_seleccionar = ttk.Button(boton_marco, text="Seleccionar archivo Excel", command=seleccionar_archivo)
btn_seleccionar.pack(side="top", pady=20)

mensaje = tk.Label(boton_marco, text="", bg="white")
mensaje.pack()

btn_ejecutar = ttk.Button(boton_marco, text="Ejecutar Modelo", command=ejecutar_modelo)
btn_ejecutar.pack(side="top")

ventana_modelo = tk.Toplevel(ventana)
ventana_modelo.title("Ventana del Modelo")
ventana_modelo.geometry("400x200")
ventana_modelo.withdraw()

btn_ejecutar.config(command=lambda: ventana_modelo.deiconify())

ventana.mainloop()