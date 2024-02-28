from typing import Iterable, Tuple, Callable
from PyQt6.QtWidgets import (
    QStyleOptionViewItem, QTableView, QMenu, QHeaderView, QWidget,
    QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import (
    QAbstractItemModel, QModelIndex, Qt, QSortFilterProxyModel, QPoint, pyqtSignal
)
from PyQt6.QtGui import (
    QAction, QPainter, QColor
)
from modelos_dataframe import ModeloDataframe, ModeloDataframeCoordenadas
import pandas as pd
import os

class VistaDataframe(QTableView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.custom_context_menu = QMenu(self)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showCustomContextMenu)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.verticalHeader().hide()
        
    def getContentHeight(self):
        return int(
            self.rowHeight(0) * self.model().rowCount() \
                + self.horizontalHeader().height() \
                    + 2 * self.frameWidth())
        
    def showCustomContextMenu(self, pos: QPoint):
        idx = self.indexAt(pos)
        if idx.isValid():
            self.custom_context_menu.exec(self.viewport().mapToGlobal(pos))
    
    def addCustomContextMenuAction(self, action: QAction, callback: Callable) -> None:
        action.setParent(self)
        action.triggered.connect(callback)
        self.custom_context_menu.addAction(action)
    
    def addCustomContextMenuActions(self, action_callback_tuple: Iterable[Tuple[QAction, Callable]]) -> None:
        for action, callback in action_callback_tuple:
            self.addCustomContextMenuAction(action, callback)


class EliminacionDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.fillRect(option.rect, QColor(255, 50, 50))
        if (option.state & QStyle.StateFlag.State_Selected) == QStyle.StateFlag.State_Selected:
            if (option.state & QStyle.StateFlag.State_Active) != QStyle.StateFlag.State_Active:
                option.backgroundBrush = QColor(50, 150, 50)
                painter.fillRect(option.rect, option.backgroundBrush)
        super().paint(painter, option, index)

class VistaDataframeEliminacion(VistaDataframe):
    def __init__(
            self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.delegado_eliminacion = EliminacionDelegate()
        self.toggle_delete_action = QAction()
        self.addCustomContextMenuAction(
            self.toggle_delete_action,
            self.toggleRowDeletion
        )
        
    def getDataframeModel(self) -> ModeloDataframe:
        model = self.model()
        if isinstance(model, QSortFilterProxyModel):
            model = model.sourceModel()
        return model
        
    def showCustomContextMenu(self, pos: QPoint):
        model = self.getDataframeModel()
        action_text = "Desmarcar despacho" if model.isRowInRemoveList(self.rowAt(pos.y())) else "Marcar despacho para eliminación"
        self.toggle_delete_action.setText(action_text)
        self.custom_context_menu.exec(self.viewport().mapToGlobal(pos))
    
    def toggleRowDeletion(self):
        model = self.getDataframeModel()
        row = self.selectionModel().currentIndex().row()
        if not model.isRowInRemoveList(row):
            model.addToRowRemoveList(row)
            # Model can reject adding the row
            if model.isRowInRemoveList(row):
                self.setItemDelegateForRow(row, self.delegado_eliminacion)
        else:
            model.removeFromRowRemoveList(row)
            self.setItemDelegateForRow(row, self.itemDelegate())
        self.selectionModel().clearSelection()


class VistaDataframePagoDespacho(VistaDataframeEliminacion):
    def __init__(
            self, parent: QWidget | None = None) -> None:
        # TODO: can_remove_all puede causar problemas
        #       si es que todos los despachos disponibles tienen que revisarse
        #       puede que terminemos eliminando todos los despachos q hay 
        super().__init__(parent)
    
    def setModel(self, model: ModeloDataframeCoordenadas | None) -> None:
        super().setModel(model)
        # 4 = DIRECCION, 6 = CLIENTE
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setDefaultSectionSize(200)
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
            

class CoordenadasDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        # Set the background color for selected items
        option.backgroundBrush = QColor(50, 255, 50) 
        if (option.state & QStyle.StateFlag.State_Selected) == QStyle.StateFlag.State_Selected:
            if (option.state & QStyle.StateFlag.State_Active) != QStyle.StateFlag.State_Active:
                option.backgroundBrush = QColor(50, 150, 50)
                painter.fillRect(option.rect, option.backgroundBrush)
        painter.fillRect(option.rect, option.backgroundBrush)
        super().paint(painter, option, index)
        

class VistaDataframeCoordenadas(VistaDataframe):
    direccion = pyqtSignal(str)
    def __init__(
                self, parent: QWidget | None = None,
                buscar_externo: bool = False) -> None:
        super().__init__(parent)
        self.delegado_coordenadas = CoordenadasDelegate()
        self.buscar_externo = buscar_externo
        self.addCustomContextMenuAction(
            QAction("Buscar dirección en Google Maps"),
            self.enviar_direccion
        )
    
    def setModel(self, model: QAbstractItemModel | None) -> None:
        super().setModel(model)
        # TODO: CAMBIAR BIEN INDICE, NO TAN HARDCODEADO
        # 1 = DIRECCION, 3 = CLIENTE, 4 = DATOS TRANSPORTE EXTERNO
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.idx_col_dir = 1 if not self.buscar_externo else 3
        self.horizontalHeader().setSectionResizeMode(self.idx_col_dir, QHeaderView.ResizeMode.Stretch)
        #self.cargar_cache()
    
    def cargar_cache(self):
        if not os.path.exists('cache/coordenadas.xlsx'):
            return
        df_cache = pd.read_excel('cache/coordenadas.xlsx')
        # ir leyendo las filas del modelo
        print("cargando cache...")
        self.model().beginResetModel()
        for model_row in range(self.model().rowCount()):
            col_name, dir = self.getDireccion(model_row)
            row_cached = df_cache[df_cache[col_name] == dir]
            for idx, cache_row in row_cached.iterrows():
                lat = float(cache_row['LATITUD'])
                long = float(cache_row['LONGITUD'])
                self.actualizar_coordenadas(lat, long, model_row)
                self.setItemDelegateForRow(model_row, self.itemDelegate())
        self.model().endResetModel()
        
    def enviar_direccion(self):
        self.model_idx_dir = self.model().index(self.selectionModel().currentIndex().row(), self.idx_col_dir)
        # obtener texto de la celda seleccionada
        direccion: str = self.model().data(self.model_idx_dir)
        try:
            dir_split = direccion.split(' | ')[1].upper().replace('DESPACHO A ', '')
            direccion = dir_split
        except IndexError:
            pass
        self.direccion.emit(direccion)
    
    def actualizar_coordenadas(self, lat, long, row=-1):
        if row <= -1:
            row = self.model_idx_dir.row()
        # latitud y longitud son las ultimas 2 columnas
        column_count = self.model().columnCount()
        indice_latitud = self.model().index(row, column_count - 2)
        indice_longitud = self.model().index(row, column_count - 1)

        self.model().setData(indice_latitud, lat, Qt.ItemDataRole.EditRole)
        self.model().setData(indice_longitud, long, Qt.ItemDataRole.EditRole)
        self.setItemDelegateForRow(row, self.delegado_coordenadas)
        self.selectionModel().clearSelection()
    
    # TODO: funcion tiene mas sentido en el modelo mismo
    def getCoords(self, row) -> Tuple[float, float]:
        model = self.model()
        col_count = model.columnCount()
        lat = float(model.data(model.index(row, col_count - 2)))
        long = float(model.data(model.index(row, col_count - 1)))
        return lat, long
    
    def getDireccion(self, row) -> Tuple[str, str]:
        col_name = self.model().headerData(self.idx_col_dir, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        dir = self.model().data(self.model().index(row, self.idx_col_dir))
        return col_name, dir
        
    def coordenadas_invalidas(self) -> bool:
        for row in range(self.model().rowCount()):
            lat, long = self.getCoords(row)
            if (lat == 0.0) or (long == 0.0) or (int(lat) != -33) or (int(long) != -70):
                return True
        return False
