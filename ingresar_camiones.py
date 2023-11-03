# -*- coding: utf-8 -*-
"""
Created on Wed Nov 1 16:58:40 2023

@author: Ignacio Carvajal
"""

import tkinter as tk
import webbrowser

# Función para correr el modelo
def correr_modelo():
    # Abre el archivo HTML en el navegador web predeterminado
    webbrowser.open("mapa_clusters.html")

# Función para agregar un registro
def agregar_registro():
    nombre = nombre_entry.get()
    capacidad = capacidad_entry.get()
    min_volumen = min_volumen_entry.get()
    max_vueltas = max_vueltas_entry.get()
    max_servicios = max_servicios_entry.get()
    registros_listbox.insert(tk.END, f"Nombre: {nombre}, Capacidad: {capacidad}, Mínimo de Volumen: {min_volumen}, Máximo de Vueltas: {max_vueltas}, Máximo de Servicios: {max_servicios}")
    nombre_entry.delete(0, tk.END)
    capacidad_entry.delete(0, tk.END)
    min_volumen_entry.delete(0, tk.END)
    max_vueltas_entry.delete(0, tk.END)
    max_servicios_entry.delete(0, tk.END)

# Crear la ventana principal
ventana = tk.Tk()
ventana.title("Aplicación de Registro")

# Etiquetas y campos de entrada a la izquierda
nombre_label = tk.Label(ventana, text="Nombre:")
nombre_label.pack()
nombre_entry = tk.Entry(ventana)
nombre_entry.pack()

capacidad_label = tk.Label(ventana, text="Capacidad:")
capacidad_label.pack()
capacidad_entry = tk.Entry(ventana)
capacidad_entry.pack()

min_volumen_label = tk.Label(ventana, text="Mínimo de Volumen:")
min_volumen_label.pack()
min_volumen_entry = tk.Entry(ventana)
min_volumen_entry.pack()

max_vueltas_label = tk.Label(ventana, text="Máximo de Vueltas:")
max_vueltas_label.pack()
max_vueltas_entry = tk.Entry(ventana)
max_vueltas_entry.pack()

# Nueva etiqueta y campo de entrada para el número máximo de servicios
max_servicios_label = tk.Label(ventana, text="Máximo de Servicios:")
max_servicios_label.pack()
max_servicios_entry = tk.Entry(ventana)
max_servicios_entry.pack()

# Botones
agregar_button = tk.Button(ventana, text="Agregar Registro", command=agregar_registro)
agregar_button.pack()

# Lista de registros a la izquierda
registros_listbox = tk.Listbox(ventana, width=120, height=20)
registros_listbox.pack()

# Botón para correr el modelo y abrir el archivo HTML
correr_modelo_button = tk.Button(ventana, text="Correr Modelo", command=correr_modelo)
correr_modelo_button.pack()

# Iniciar la aplicación
ventana.mainloop()
