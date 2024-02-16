from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QMessageBox
)
from PyQt6.QtGui import (
    QCloseEvent, QIcon
)
from PyQt6.QtCore import pyqtSignal
import pandas as pd

class BaseVentana(QMainWindow):
    # Clase utilizara CamelCase en funciones para mantener consistencia con Qt
    # Variables de clase, se comparten entre todas las instancias
    __icon = None
    __df = None
    def __init__(
            self, parent: QWidget | None = None,
            title: str = 'Ventana', safe_to_close: bool = True) -> None:
        super().__init__(parent)
        if BaseVentana.__icon != None:
            self.setWindowIcon(BaseVentana.__icon)
        self.setWindowTitle(title)
        self.confirmation_text = "¿Estás seguro de cerrar esta ventana? Puede que se cierre la aplicación."
        self.safe_to_close = safe_to_close
    
    @classmethod
    def setIcon(cls, icon: QIcon) -> None:
        cls.__icon = icon
    
    @classmethod
    def setDataFrame(cls, df: pd.DataFrame) -> None:
        cls.__df = df
        
    def setConfirmationText(self, text: str):
        self.confirmation_text = text
    
    def setSafeToClose(self, safe: bool):
        self.safe_to_close = safe
    
    def closeEvent(self, event: QCloseEvent | None) -> None:
        if not self.safe_to_close:
            confirmacion = QMessageBox.question(
                self, "Confirmar cierre", 
                self.confirmation_text,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirmacion == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            super().closeEvent(event)