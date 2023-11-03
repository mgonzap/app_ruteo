# -*- coding: utf-8 -*-
"""
Created on Tue Oct 31 17:33:07 2023

@author: Ignacio Carvajal
"""

import tkinter as tk
from tkinter import ttk

def calcular_vueltas():
    camion = combo_camiones.get()
    capacidad = int(entry_capacidad.get())
    sub_capacidad = int(entry_sub_capacidad.get())
    max_vueltas = int(entry_max_vueltas.get())
    max_servicios = int(entry_max_servicios.get())
    
    vueltas = min(max_vueltas, (capacidad - sub_capacidad) // camiones[camion]["capacidad"])
    servicios_por_vuelta = min(max_servicios, max_vueltas * camiones[camion]["vueltas"])
    
    resultado.set(f"Vueltas para {camion}: {vueltas}, Servicios por vuelta: {servicios_por_vuelta}")

def agregar_camion():
    camion_seleccionado = combo_camiones.get()
    if camion_seleccionado not in camiones_seleccionados:
        camiones_seleccionados.append(camion_seleccionado)
        lista_camiones.insert("end", camion_seleccionado)

def quitar_camion():
    seleccion = lista_camiones.curselection()
    if seleccion:
        camion_a_quitar = lista_camiones.get(seleccion[0])
        camiones_seleccionados.remove(camion_a_quitar)
        lista_camiones.delete(seleccion[0])

camiones = {
    "sinotrack": {"capacidad": 16, "sub_capacidad": 6, "vueltas": 3},
    "jak": {"capacidad": 26, "sub_capacidad": 16, "vueltas": 3},
    "hyundai": {"capacidad": 6, "sub_capacidad": 0, "vueltas": 1},
    "externo_1": {"capacidad": 22, "sub_capacidad": 16, "vueltas": 2}
}

camiones_seleccionados = []

ventana = tk.Tk()
ventana.title("Cálculo de Vueltas y Servicios")

frame = ttk.Frame(ventana)
frame.grid(row=0, column=0, padx=20, pady=20)

combo_camiones = ttk.Combobox(frame, values=list(camiones.keys()))
combo_camiones.set(list(camiones.keys())[0])
combo_camiones.grid(row=0, column=0, padx=10, pady=5)

entry_capacidad = ttk.Entry(frame)
entry_sub_capacidad = ttk.Entry(frame)
entry_capacidad.grid(row=1, column=0, padx=10, pady=5)
entry_sub_capacidad.grid(row=2, column=0, padx=10, pady=5)

label_max_vueltas = ttk.Label(frame, text="Máximo de Vueltas:")
label_max_servicios = ttk.Label(frame, text="Máximo de Servicios por Vuelta:")
entry_max_vueltas = ttk.Entry(frame)
entry_max_servicios = ttk.Entry(frame)

label_max_vueltas.grid(row=3, column=0, padx=10, pady=5)
entry_max_vueltas.grid(row=4, column=0, padx=10, pady=5)
label_max_servicios.grid(row=5, column=0, padx=10, pady=5)
entry_max_servicios.grid(row=6, column=0, padx=10, pady=5)

calcular_button = ttk.Button(frame, text="Calcular Vueltas y Servicios", command=calcular_vueltas)
calcular_button.grid(row=7, column=0, padx=10, pady=10)

agregar_button = ttk.Button(frame, text="Agregar Camión", command=agregar_camion)
agregar_button.grid(row=8, column=0, padx=10, pady=10)

quitar_button = ttk.Button(frame, text="Quitar Camión", command=quitar_camion)
quitar_button.grid(row=9, column=0, padx=10, pady=10)

lista_camiones = tk.Listbox(frame)
lista_camiones.grid(row=0, column=1, rowspan=10, padx=10, pady=10)

resultado = tk.StringVar()
resultado_label = tk.Label(frame, textvariable=resultado)
resultado_label.grid(row=10, column=0, columnspan=2, padx=10, pady=10)

ventana.mainloop()
