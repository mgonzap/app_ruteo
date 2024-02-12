from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QDialog, QSpinBox
from PyQt6 import QtGui
from app_ruteo import Camion

# TODO: que herede de QMainWindow para aplicar show() sin necesitar la funcion mostrar()
class VentanaCreacionCamion:
    def __init__(self, parent, agregar_camion_callback, objeto):
        self.parent = parent
        
        self.ventana_creacion = QMainWindow(self.parent)
        
        self.ventana_creacion.setWindowIcon(QtGui.QIcon("logo\\WSC-LOGO2.ico"))
        self.ventana_creacion.setWindowTitle("Crear Camión")

        self.central_widget = QWidget(self.ventana_creacion)
        self.ventana_creacion.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        label_nombre = QLabel("Nombre:")
        self.layout.addWidget(label_nombre)
        self.entry_nombre = QLineEdit()
        self.layout.addWidget(self.entry_nombre)

        label_capacidad = QLabel("Capacidad:")
        self.layout.addWidget(label_capacidad)
        self.entry_capacidad = QSpinBox()
        self.layout.addWidget(self.entry_capacidad)

        #label_sub_capacidad = QLabel("Sub Capacidad:")
        #self.layout.addWidget(label_sub_capacidad)
        #self.entry_sub_capacidad = QSpinBox()
        #self.layout.addWidget(self.entry_sub_capacidad)
        
        #label_peso = QLabel("Peso Máximo (Kg):")
        #self.layout.addWidget(label_peso)
        #self.entry_peso = QSpinBox()
        #self.layout.addWidget(self.entry_peso)

        label_vueltas = QLabel("Vueltas:")
        self.layout.addWidget(label_vueltas)
        self.entry_vueltas = QSpinBox()
        self.layout.addWidget(self.entry_vueltas)

        label_max_entregas = QLabel("Máximo Entregas:")
        self.layout.addWidget(label_max_entregas)
        self.entry_max_entregas = QSpinBox()
        self.layout.addWidget(self.entry_max_entregas)

        # Función para agregar el camión con la información proporcionada
        def agregar_camion_nuevo():
            # TODO: agregar el peso al crear el camión
            # pero primero se debe ajustar el modelo para que lo reciba
            try:
                nombre = self.entry_nombre.text()
                capacidad = self.entry_capacidad.value()
                vueltas = self.entry_vueltas.value()
                max_entregas = self.entry_max_entregas.value()
            except:
                self.generar_advertencia("Recuerde rellenar todos los campos")
                return
            val = objeto.crear_camion(nombre, capacidad, 0, vueltas, max_entregas)
            if not val:
                self.generar_advertencia("Ocurrió un error al crear el camión. \nRevise que ya no exista un camión con ese nombre o que los valores sean válidos.")
                return
            self.parent.dict_camiones[nombre] = Camion(capacidad, 0, vueltas, max_entregas)
            self.ventana_creacion.close()
            self.parent.actualizar_combo_camiones()
            

        # Botón para confirmar la creación del camión
        boton_confirmar = QPushButton("Confirmar", self.ventana_creacion)
        boton_confirmar.clicked.connect(agregar_camion_nuevo)
        self.layout.addWidget(boton_confirmar)

    def mostrar(self):
        self.ventana_creacion.show()
        
    def generar_advertencia(self, texto):
        dlg = QDialog(self.ventana_creacion)
        dlg.setWindowTitle("Error")
        
        layout = QVBoxLayout()
        mensaje = QLabel(texto)
        
        layout.addWidget(mensaje)
        
        dlg.setLayout(layout)
        dlg.exec()   
        

def agregar_camion_callback(objeto, nombre, capacidad, sub_capacidad, vueltas, max_entregas):
    print(f"Camión agregado: {nombre}, {capacidad}, {sub_capacidad}, {vueltas}, {max_entregas}")
