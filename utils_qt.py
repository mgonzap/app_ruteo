from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QMessageBox
)
import pandas as pd
from procesamiento_datos import obtener_dataframe

path_icono = "logo\\WSC-LOGO2.ico"

# TODO:
class IconHolder():
    pass

class ConfirmDialog(QDialog):
    salida_confirmada = pyqtSignal()
    
    def __init__(self, parent=None, titulo='', texto='', texto_confirmar=''):
        super().__init__(parent)
        self.setWindowIcon(QIcon(path_icono))
        self.setWindowTitle(titulo)
        layout = QVBoxLayout()
        mensaje = QLabel(texto)
        self.texto_confirmar = texto_confirmar
        
        layout.addWidget(mensaje)       
        self.setLayout(layout)
        
    def closeEvent(self, event):
        confirmacion = QMessageBox.question(self, "Confirmar cierre", 
                                             self.texto_confirmar,
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirmacion == QMessageBox.StandardButton.Yes:
            self.salida_confirmada.emit()
            event.accept()
        else:
            event.ignore()
    
    def close_directly(self):
        self.closeEvent = lambda event: event.accept()
        self.close()

# THREADS
class DataThread(QThread):
    finished = pyqtSignal(pd.DataFrame)
    def __init__(self, fecha):
        super().__init__()
        self.fecha = fecha
        self.setTerminationEnabled(True)
    
    def run(self):
        df = obtener_dataframe(self.fecha)
        self.finished.emit(df)
