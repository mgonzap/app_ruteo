from PyQt6.QtCore import (
    QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel,
    pyqtSignal
)
from pandas import DataFrame
from typing import Iterable

# Modelo para que Qt pueda mostrar un DataFrame de pandas en un QTableView
class ModeloDataframe(QAbstractTableModel):
    # Señal para advertir que se esta intentando remover todas las filas
    removing_all = pyqtSignal()
    def __init__(self, data: DataFrame, can_delete_all: bool = False):
        super(QAbstractTableModel, self).__init__()
        self._data: DataFrame = data
        self._row_remove_list = []
        self._can_delete_all = can_delete_all
        
    def rowCount(self, parent=None) -> int:
        return self._data.shape[0]

    def columnCount(self, parent=None) -> int:
        return self._data.shape[1]
    
    def removeRow(self, row, parent=QModelIndex()) -> bool:
        if 0 <= row < self.rowCount():
            self.beginRemoveRows(parent, row, row)
            self._data.drop(row, inplace=True)
            # Necesario, puesto que los indices del modelo
            # si se recalculan, causando desfase desde la primera eliminacion
            self._data.reset_index(drop=True, inplace=True)
            self.endRemoveRows()
            return True
        return False
    
    def addToRowRemoveList(self, row_id: int) -> None:
        if (self.rowCount() <= self.rowRemoveListCount() + 1):
            self.removing_all.emit()
            if not self._can_delete_all:
                return
        self._row_remove_list.append(row_id)
    
    def removeFromRowRemoveList(self, row_id: int) -> None:
        self._row_remove_list.remove(row_id)
        
    def isRowInRemoveList(self, row_id: int) -> bool:
        return row_id in self._row_remove_list
    
    def rowRemoveListCount(self) -> int:
        return len(self._row_remove_list)
        
    def processRowRemoveList(self) -> None:
        self.beginResetModel()
        self._data.drop(self._row_remove_list, inplace=True)
        self.endResetModel()
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        return super().flags(index)
    
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


# Modelo filtro que instancia inmediatamente a un ModeloDataframe como sourceModel
class ModeloDataframeFiltro(QSortFilterProxyModel):
    def __init__(self, allowed_column_names: Iterable[str] = []):
        super().__init__()
        self.allowed_column_names = allowed_column_names
    
    def flags(self, index: QModelIndex):
        return Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled
    
    def filterAcceptsColumn(self, source_column, source_parent):
        nombre_columna = self.sourceModel().headerData(source_column, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        return nombre_columna in self.allowed_column_names


# Modelo encargado de filtrar filas con coordenadas incorrectas
# TODO: elegir entre mostrar direccion o datos transporte externo
class ModeloDataframeCoordenadas(ModeloDataframeFiltro):
    def __init__(
        self, allowed_column_names: Iterable[str], 
        buscar_externo: bool = False):
        super().__init__(allowed_column_names)
        self.buscar_ext = buscar_externo
    
    def flags(self, index: QModelIndex):
        # las últimas 2 columnas son latitud, longitud y son las unicas editables
        if index.column() < (self.columnCount() - 2):
            return Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsEditable
    
    # se muestran solo filas que retornen True al aplicarse el filtro
    def filterAcceptsRow(self, source_row, source_parent):
        # indices fueron obtenidos con df.columns.get_loc("LATITUD"), longitud es el indice siguiente
        model = self.sourceModel()
        idx_lat = model.index(source_row, 29, source_parent)
        idx_long = model.index(source_row, 30, source_parent)
        # df.columns.get_loc("DATOS TRANSPORTE EXTERNO")
        idx_trans_ext = model.index(source_row, 22, source_parent)
        # .data() devuelve un str
        transporte_ext = (self.buscar_ext == (model.data(idx_trans_ext) != 'NO APLICA'))
        lat = float(model.data(idx_lat))
        long = float(model.data(idx_long))
        error_georef = (lat == 0.0 or long == 0.0)
        # coords_stgo -> lat: aprox entre -33.45 y -33.35
        #               long: aprox entre -70.65 y -70.55
        fuera_de_stgo = (int(lat) != -33) or (int(long) != -70)
        return (error_georef or fuera_de_stgo) and transporte_ext
    

class ModeloDataframeVerificacion(ModeloDataframeFiltro):
    def __init__(self):
        super().__init__(
            [
                "N° CARPETA", "SERVICIO", "CLIENTE", "DIRECCION", 
                "COMUNA", "TIPO DE ENTREGA", "EJECUTIVO"
            ]
        )
        
    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled
    
    # se muestran solo filas que retornen True al aplicarse el filtro
    def filterAcceptsRow(self, source_row, source_parent):
        # indices fueron obtenidos con self.df.columns.get_loc("LATITUD"), longitud es el indice siguiente
        idx_tipo_entrega = self.sourceModel().index(source_row, 6, source_parent)
        
        tipo_entrega = self.sourceModel().data(idx_tipo_entrega)
        return (tipo_entrega in ['REVISAR DESPACHO GRATUITO NO INCLUIDO', 'SIN ESPECIFICAR'])
    