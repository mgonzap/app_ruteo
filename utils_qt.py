from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QMessageBox
)
import pandas as pd
from procesamiento_datos import obtener_dataframe_datos, obtener_dataframe_entregas_clientes

path_icono = "logo\\WSC-LOGO2.ico"

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
        df = obtener_dataframe_datos(self.fecha)
        self.finished.emit(df)
        
class EntregasClientesThread(QThread):
    finished = pyqtSignal(pd.DataFrame)
    def __init__(self, fecha, lista_clientes, df_original):
        super().__init__()
        self.fecha = fecha
        self.lista_clientes = lista_clientes
        self.df_original = df_original
        self.setTerminationEnabled(True)
    
    def run(self):
        df = obtener_dataframe_entregas_clientes(self.fecha, self.lista_clientes, self.df_original)
        self.finished.emit(df)
