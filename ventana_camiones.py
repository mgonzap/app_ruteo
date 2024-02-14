from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QDialog, QSpinBox
)
from PyQt6.QtCore import pyqtSignal
from PyQt6 import QtGui
from app_ruteo import Camion

class VentanaCamion(QMainWindow):
    resultado_camion = pyqtSignal(str, int, int, int)
    def __init__(self, parent, camion_a_editar: tuple[str, Camion] | None = None):
        super().__init__(parent)
        
        self.setWindowIcon(QtGui.QIcon("logo\\WSC-LOGO2.ico"))

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        label_nombre = QLabel("Nombre:")
        layout.addWidget(label_nombre)
        self.entry_nombre = QLineEdit()
        layout.addWidget(self.entry_nombre)

        label_capacidad = QLabel("Capacidad:")
        layout.addWidget(label_capacidad)
        self.entry_capacidad = QSpinBox()
        layout.addWidget(self.entry_capacidad)

        label_vueltas = QLabel("Vueltas:")
        layout.addWidget(label_vueltas)
        self.entry_vueltas = QSpinBox()
        layout.addWidget(self.entry_vueltas)

        label_max_entregas = QLabel("Máximo Entregas:")
        layout.addWidget(label_max_entregas)
        self.entry_max_entregas = QSpinBox()
        layout.addWidget(self.entry_max_entregas)
        
        if camion_a_editar == None:
            self.setWindowTitle("Crear Camión")
        else:
            self.setWindowTitle("Editar Camión")
            # TODO: setear valores
            self.entry_nombre.setText(camion_a_editar[0])
            self.entry_nombre.setDisabled(True)
            self.entry_capacidad.setValue(camion_a_editar[1].capacidad)
            self.entry_vueltas.setValue(camion_a_editar[1].vueltas)
            self.entry_max_entregas.setValue(camion_a_editar[1].maximo_entregas)

        # Función para emitir señal con datos de camion
        def enviar_camion():
            try:
                nombre = self.entry_nombre.text()
                if nombre == '':
                    raise ValueError('Nombre no puede estar vacío.')
                capacidad = self.entry_capacidad.value()
                vueltas = self.entry_vueltas.value()
                max_entregas = self.entry_max_entregas.value()
                if capacidad <= 0 or vueltas <= 0 or max_entregas <= 0:
                    raise ValueError('No pueden haber valores menor o iguales a 0.')
            except ValueError as e:
                self.generar_advertencia(str(e))
                return
            except Exception as e:
                print(repr(e))
                self.generar_advertencia("Recuerde rellenar todos los campos y utilizar valores válidos.")
                return
            
            self.resultado_camion.emit(nombre, capacidad, vueltas, max_entregas)

        # Botón para confirmar la creación del camión
        boton_confirmar = QPushButton("Confirmar", self)
        boton_confirmar.clicked.connect(enviar_camion)
        layout.addWidget(boton_confirmar)
        
    def generar_advertencia(self, texto):
        dlg = QDialog(self)
        dlg.setWindowTitle("Error")
        
        layout = QVBoxLayout()
        mensaje = QLabel(texto)
        
        layout.addWidget(mensaje)
        
        dlg.setLayout(layout)
        dlg.exec()   
