from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, 
    QTableView, QMenu, QHeaderView, QMessageBox
)
from PyQt6.QtCore import (
    QAbstractTableModel, Qt, pyqtSignal, 
    QSize, QModelIndex
)
from PyQt6.QtGui import QAction, QGuiApplication
import pandas as pd

# Ventana para mostrar la lista completa de despachos al usuario.
# Usuario puede desde aquí eliminar despachos indeseados.

class VentanaDespachos(QMainWindow):
    edicion_terminada = pyqtSignal(pd.DataFrame)
    def __init__(self, df, icono):
        super(QMainWindow, self).__init__()
        self.df = df
        self.modelo_tabla = ModeloDataframe(self.df)
        
        self.setWindowIcon(icono)
        self.setWindowTitle("Despachos")

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)

        self.label_nombre = QLabel("Aquí se presentan todos los despachos. " + \
            "También es posible eliminar despachos indeseados con clic derecho.")
        self.layout.addWidget(self.label_nombre)
            
        self.vista_tabla = VistaTablaDespachos(self)
        self.vista_tabla.setModel(self.modelo_tabla)
        self.layout.addWidget(self.vista_tabla)
        
        screen = QGuiApplication.primaryScreen().availableSize()
        altura_calculada = int(
            self.vista_tabla.rowHeight(0) * self.modelo_tabla.rowCount() \
                + self.vista_tabla.horizontalHeader().height() \
                    + 2 * self.vista_tabla.frameWidth()
        )
        altura = max(
            350,
            min(screen.height(), altura_calculada)
        )
        self.resize(QSize(screen.width(), altura))
        self.vista_tabla.ajustar_columnas()
            
        self.finalizar_button = QPushButton("Finalizar")
        self.finalizar_button.clicked.connect(self.finalizar_edicion)
        self.layout.addWidget(self.finalizar_button)
        self.move(
            0, 
            int((screen.height() - altura)/2)
        )
    
    def finalizar_edicion(self):
        count = self.modelo_tabla.getRowRemoveListCount()
        if self.modelo_tabla.rowCount() <= count:
            aviso = QMessageBox.warning(
                self, "Despachos - Advertencia",
                "Debe quedar por lo menos un despacho.",
                QMessageBox.StandardButton.Ok
            )
            # TODO: si va a estar esto, dar posibilidad de
            # desmarcar filas
            return
        if 0 < count:
            confirmar = QMessageBox.question(
                self, "Confirmar", 
                f"¿Estás seguro de eliminar {count} fila{'s' if count > 2 else '' }?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirmar == QMessageBox.StandardButton.Yes:
                print("----------------ANTES DE BORRAR----------------")
                print(self.df)
                print("----------------DESPUES DE BORRAR----------------")
                self.modelo_tabla.processRowRemoveList()
                print(self.df)
                pass
            else:
                print("no confirmao")
                pass
        self.close()
    
    # reemplazamos la funcion show para que revise si hay datos que necesiten corrección
    # si no, simplemente se considera la edición finalizada.
    def show(self):
        if self.df.empty or self.vista_tabla.model() is None or self.vista_tabla.model().rowCount() == 0:
            self.finalizar_edicion()
        else:
            super().show()

class VistaTablaDespachos(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Conectar el evento customContextMenuRequested a la función que muestra el menú
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.verticalHeader().hide()
    
    def ajustar_columnas(self):
        return

    def mostrar_menu_contextual(self, pos):
        menu = QMenu(self)
        accion = QAction("Marcar para eliminación", self)
        accion.triggered.connect(self.marcar_despacho)
        menu.addAction(accion)

        # Mostrar el menú en la posición del clic derecho
        menu.exec(self.viewport().mapToGlobal(pos))
    
    def marcar_despacho(self):
        index = self.selectionModel().currentIndex()
        model: ModeloDataframe = self.model()
        model.addToRowRemoveList(index.row())

# Modelo de datos para que Qt pueda mostrar un DataFrame de pandas en un QTableWidget
class ModeloDataframe(QAbstractTableModel):
    def __init__(self, data):
        super(QAbstractTableModel, self).__init__()
        self._data: pd.DataFrame = data
        self._row_remove_list = []
        
    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]
    
    def removeRow(self, row, parent=QModelIndex()):
        if 0 <= row < self.rowCount():
            self.beginRemoveRows(parent, row, row)
            self._data.drop(row, inplace=True)
            # Necesario, puesto que los indices del modelo
            # si se recalculan, causando desfase desde la primera eliminacion
            self._data.reset_index(drop=True, inplace=True)
            self.endRemoveRows()
            return True
        return False
    
    def addToRowRemoveList(self, row_id):
        print("agregando a lista de eliminacion:", row_id)
        self._row_remove_list.append(row_id)
    
    def getRowRemoveListCount(self):
        return len(self._row_remove_list)
        
    def processRowRemoveList(self):
        self.beginResetModel()
        self._data.drop(self._row_remove_list, inplace=True)
        self.endResetModel()
    
    # Retornar False indica que no se actualizó la data, para que TableView no aplique el cambio
    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            try:
                value = float(value)
            except:
                return False
            self._data.iloc[index.row(),index.column()] = value
            return True

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._data.columns[col]
        return None
