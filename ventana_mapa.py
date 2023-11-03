import tkinter as tk
import webbrowser

# Función para abrir el navegador web con la página HTML
def abrir_pagina_html():
    webbrowser.open("mapa_clusters.html")

# Crear una ventana de tkinter
ventana = tk.Tk()
ventana.title("Página web en una ventana")

# Botón para abrir la página HTML
abrir_pagina_button = tk.Button(ventana, text="Abrir Página HTML", command=abrir_pagina_html)
abrir_pagina_button.pack()

# Iniciar la aplicación
ventana.mainloop()
