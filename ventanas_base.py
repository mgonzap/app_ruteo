from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QPushButton
)
from PyQt6.QtGui import (
    QCloseEvent, QIcon, QGuiApplication
)
from PyQt6.QtCore import (
    pyqtSignal, QSize, QSortFilterProxyModel
)
from pandas import DataFrame
from modelos_dataframe import ModeloDataframe
from vistas_dataframe import VistaDataframe
from typing import Callable


class Ventana(QMainWindow):
    # Clase utilizara CamelCase en funciones para mantener consistencia con Qt
    # Variables de clase, se comparten entre todas las instancias
    __icon: QIcon | None = None
    def __init__(
            self, parent: QWidget | None = None,
            title: str = 'Ventana', safe_to_close: bool = True) -> None:
        super().__init__(parent)
        if Ventana.__icon != None:
            self.setWindowIcon(Ventana.__icon)
        self.setWindowTitle(title)
        self.confirmation_text = "¿Estás seguro de cerrar esta ventana? Se cerrará también la aplicación."
        self.safe_to_close = safe_to_close
    
    @classmethod
    def setIcon(cls, icon: QIcon) -> None:
        cls.__icon = icon
        
    @classmethod
    def getIcon(cls) -> QIcon:
        return cls.__icon
        
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
            if confirmacion == QMessageBox.StandardButton.No:
                event.ignore()
                return
        event.accept()
    
    def forceClose(self):
        self.closeEvent = lambda event: event.accept()
        self.close()
        
    def createQPushButton(self, text: str, clicked_callback: Callable) -> QPushButton:
        button = QPushButton(text, self)
        button.clicked.connect(clicked_callback)
        return button


# Clase retiene dataframe
class VentanaDataframe(Ventana):
    # Variables de clase, se comparten entre todas las instancias
    __df: DataFrame | None = None
    __clients_df: DataFrame | None = None
    __fecha: str = ''
    def __init__(
            self, parent: QWidget | None = None,
            title: str = 'Ventana Dataframe', safe_to_close: bool = True) -> None:
        super().__init__(parent, title, safe_to_close)
    
    @classmethod
    def setDataFrame(cls, df: DataFrame) -> None:
        cls.__df = df
        
    @classmethod
    def getDataFrame(cls) -> DataFrame | None:
        return cls.__df
    
    @classmethod
    def setClientesDataFrame(cls, df: DataFrame) -> None:
        cls.__clients_df = df
        
    @classmethod
    def getClientesDataFrame(cls) -> DataFrame | None:
        return cls.__clients_df
    
    @classmethod
    def setFecha(cls, fecha: str) -> None:
        cls.__fecha = fecha
        
    @classmethod
    def getFecha(cls) -> str:
        return cls.__fecha
            

class VentanaVistaDataframe(VentanaDataframe):
    finished = pyqtSignal()
    def __init__(
            self, parent: QWidget | None = None, 
            title: str = 'Ventana', safe_to_close: bool = True) -> None:
        super().__init__(parent, title, safe_to_close)
        self.model = ModeloDataframe(self.getDataFrame())
        self._proxy_model: QSortFilterProxyModel | None = None
        self._view: VistaDataframe | None = None
        
    @property
    def view(self):
        return self._view
    
    @view.setter
    def view(self, new_view: VistaDataframe | None):
        self._view = new_view
        if self._view is None:
            return
        if self._proxy_model == None:
            self._view.setModel(self.model)
        elif isinstance(self._proxy_model, QSortFilterProxyModel):
            self._view.setModel(self._proxy_model)
    
    @property
    def proxy_model(self):
        return self._proxy_model
    
    @proxy_model.setter
    def proxy_model(self, new_proxy_model: QSortFilterProxyModel | None):
        self._proxy_model = new_proxy_model
        if self._proxy_model is None:
            return
        else:
            self._proxy_model.setSourceModel(self.model)
    
    # might be slightly inacurrate, but should do the trick
    def resizeToContents(self, move_to_center: bool = False):
        if self.view is None:
            return
        screen_size = QGuiApplication.primaryScreen().availableSize()
        content_height = self._view.getContentHeight()
        height = max(
            350,
            min(screen_size.height() - 50, content_height)
        )
        self.resize(QSize(screen_size.width(), height))
        if move_to_center:
            self.move(
                0, 
                int((screen_size.height() - height)/2)
            )
    
    def show(self):
        if self.getDataFrame().empty or self.view.model() is None or self.view.model().rowCount() == 0:
            self.finished.emit()
        else:
            super().show()
            

class VentanaDataframeEliminacion(VentanaVistaDataframe):
    def __init__(
                self, parent: QWidget | None = None, 
                title: str = 'Ventana', safe_to_close: bool = True) -> None:
        super().__init__(
            parent, title, 
            safe_to_close
        )
        self.model.removing_all.connect(self.delete_warning)
    
    def delete_warning(self):
        QMessageBox.warning(
            self, "Advertencia",
            "Debe quedar por lo menos un despacho sin eliminar."
        )
    
    def process_deletion(self):
        count = self.model.rowRemoveListCount()
        if 0 < count:
            confirmar = QMessageBox.question(
                self, "Confirmar", 
                f"¿Estás seguro de eliminar {count} despacho{'s' if count > 2 else '' }?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirmar == QMessageBox.StandardButton.Yes:
                self.model.processRowRemoveList()
            else:
                return
        self.finished.emit()
        self.forceClose()
    
    # reemplazamos la funcion show para que revise si hay datos que necesiten corrección
    # si no, simplemente se considera la edición finalizada.
    def show(self):
        if self.getDataFrame().empty or self.view.model() is None or self.view.model().rowCount() == 0:
            self.process_deletion()
        else:
            super().show()

