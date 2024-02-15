from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, 
    QTableView, QMenu, QHeaderView
)
from PyQt6.QtCore import (
    QAbstractTableModel, Qt, QSortFilterProxyModel, pyqtSignal, 
    QSize, QModelIndex, QTimer
)
from PyQt6.QtGui import QAction, QGuiApplication
import pandas as pd
import georef
from urllib.parse import quote
from ventana_navegador import VentanaNavegador

# Clase dedicada al procesamiento de datos (temporalmente, desde el excel)
# En caso de que los datos necesiten procesamiento extra (ej, georef no logra obtener coordenadas)
# se pide ayuda a usuario para corregir

class VentanaTablas(QMainWindow):
    edicion_terminada = pyqtSignal(pd.DataFrame)
    def __init__(self, df, icono):
        super(QMainWindow, self).__init__()
        print("init ventana tablas")
        self.df = df
        self.modelo_tabla = ModeloDataframe(self.df)
        # ProxyModel que filtre la tabla para mostrar solo filas que necesiten correccion
    
        self.setWindowIcon(icono)
        self.setWindowTitle("Procesamiento de Datos")

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        if not df.empty:
            text = "A continuación se presentan los despachos no gratuitos. " + \
                "Haga click derecho en la fila correspondiente para remover despachos con pago no confirmado:"
                
            self.init_vista_tabla(
                text, 
                VistaTablaTipoRetiro, 
                ModeloFiltroTipoRetiro,
                "Incluir Servicios",
                self.finalizar_verificacion
            )
    
    def clear_layout(self):
        # Remove all widgets from the layout
        while self.layout.count():
            widget = self.layout.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()
        
    def init_vista_tabla(self, label_text, vista_tabla, modelo_proxy, button_text, signal_func):
        self.clear_layout()
        self.modelo_proxy_tabla = modelo_proxy()
        self.modelo_proxy_tabla.setSourceModel(self.modelo_tabla)

        self.label_nombre = QLabel(label_text)
        self.layout.addWidget(self.label_nombre)
            
        self.vista_tabla = vista_tabla(self)
        self.vista_tabla.setModel(self.modelo_proxy_tabla)
        self.layout.addWidget(self.vista_tabla)
        
        screen = QGuiApplication.primaryScreen().availableSize()
        altura_calculada = int(
            self.vista_tabla.rowHeight(0) * self.modelo_proxy_tabla.rowCount() \
                + self.vista_tabla.horizontalHeader().height() \
                    + 2 * self.vista_tabla.frameWidth()
        )
        altura = max(
            350,
            min(screen.height(), altura_calculada)
        )
        self.resize(QSize(screen.width(), altura))
        self.vista_tabla.ajustar_columnas()
            
        self.finalizar_button = QPushButton(button_text)
        self.finalizar_button.clicked.connect(signal_func)
        self.layout.addWidget(self.finalizar_button)
        self.move(
            0, 
            int((screen.height() - altura)/2)
        )
    
    def finalizar_edicion(self):
        print("edicion coordenadas finalizada")
        print(self.df)
        copia_df = self.df.copy()
        self.edicion_terminada.emit(copia_df)
        # TODO: geo está escribiendo dos veces en el archivo, la primera al georreferenciar coordenadas
        # y ahora que recibe el df editado. Ver que se haga una sola vez.
        georef.actualizar_coordenadas(copia_df)
        self.close()
    
    # Como se comparte la ventana, no es necesario emitir señal, solo cambiamos el layout y la vista
    def finalizar_verificacion(self):
        print("verificacion pago despacho finalizada")
        self.hide()
        text = "Es necesario corregir las siguientes coordenadas. " + \
            "Haga click derecho en la dirección o en los datos de transporte externo para buscar coordenadas:"
        self.init_vista_tabla(
            text,
            VistaTablaCoordenadas,
            ModeloFiltroCoordenadas,
            "Finalizar edición",
            self.finalizar_edicion
        )
        self.show()
    
    # reemplazamos la funcion show para que revise si hay datos que necesiten corrección
    # si no, simplemente se considera la edición finalizada.
    def show(self):
        print("show ventana tabla")
        if self.df.empty or self.vista_tabla.model() is None or self.vista_tabla.model().rowCount() == 0:
            if isinstance(self.vista_tabla, VistaTablaTipoRetiro):
                self.finalizar_verificacion()
            else:
                self.finalizar_edicion()
        else:
            super().show()


class VistaTablaCoordenadas(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Conectar el evento customContextMenuRequested a la función que muestra el menú
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        self.verticalHeader().hide()
    
    def ajustar_columnas(self):
        # 1 = DIRECCION, 3 = CLIENTE, 4 = DATOS TRANSPORTE EXTERNO
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().resizeSection(3, 200)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().resizeSection(4, 300)

    def mostrar_menu_contextual(self, pos):
        # Obtener la columna en la que se hizo clic derecho
        column_index = self.columnAt(pos.x())

        # Verificar si el clic derecho fue en la columna que deseamos
        # Index 1 debería corresponder a la columna de las direcciones
        if column_index in (1, 4):
            # Agregar menú y acciones
            menu = QMenu(self)
            buscar = QAction("Buscar dirección en Google Maps", self)
            buscar.triggered.connect(self.buscar_direccion)
            menu.addAction(buscar)

            # Mostrar el menú en la posición del clic derecho
            menu.exec(self.viewport().mapToGlobal(pos))
        
    def buscar_direccion(self):
        # obtenemos posición de la celda y la guardamos
        # es posible que el usuario cambie la seleccion mientras esta abierto el navegador
        self.indice_direccion = self.selectionModel().currentIndex()

        # Obtener el texto de la celda seleccionada
        # quote transforma el texto a un formato aceptado por URL
        direccion = self.model().data(self.indice_direccion)
        try:
            dir_split = direccion.split(' | ')[1].upper().replace('DESPACHO A ', '')
            direccion = dir_split
        except IndexError:
            pass
        self.ventana_navegador = VentanaNavegador(f'https://www.google.com/maps/search/{quote(direccion)}')
        self.ventana_navegador.coordenadas_obtenidas.connect(self.actualizar_coordenadas)
        self.ventana_navegador.show()
    
    def actualizar_coordenadas(self, lat, long):
        # latitud y longitud son las ultimas 2 columnas
        column_count = self.model().columnCount()
        indice_latitud = self.model().index(self.indice_direccion.row(), column_count - 2)
        indice_longitud = self.model().index(self.indice_direccion.row(), column_count - 1)

        if self.model().setData(indice_latitud, lat, Qt.ItemDataRole.EditRole):
            #print("Actualización de latitud exitosa")
            pass
        else:
            #print("Error al actualizar latitud")
            pass
        
        if self.model().setData(indice_longitud, long, Qt.ItemDataRole.EditRole):
            #print("Actualización de longitud exitosa")
            pass
        else:
            #print("Error al actualizar longitud")
            pass


# Creamos nuestro propio ProxyModel para aplicar filtros a partir de un ModeloDataframe
class ModeloFiltroCoordenadas(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(QSortFilterProxyModel, self).__init__(parent)
        
    def flags(self, index):
        # las últimas 2 columnas son latitud, longitud y son las unicas editables
        if index.column() < (self.columnCount() - 2):
            return Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsEditable
    
    # se muestran solo filas que retornen True al aplicarse el filtro
    def filterAcceptsRow(self, source_row, source_parent):
        # indices fueron obtenidos con self.df.columns.get_loc("LATITUD"), longitud es el indice siguiente
        idx_latitud = self.sourceModel().index(source_row, 29, source_parent)
        idx_longitud = self.sourceModel().index(source_row, 30, source_parent)
        
        # .data() devuelve un str
        lat = float(self.sourceModel().data(idx_latitud))
        long = float(self.sourceModel().data(idx_longitud))
        error_georef = (lat == 0.0 or long == 0.0)
        # coords_stgo -> lat: aprox entre -33.45 y -33.35
        #               long: aprox entre -70.65 y -70.55
        fuera_de_stgo = (int(lat) != -33) or (int(long) != -70)
        return error_georef or fuera_de_stgo
    
    # se muestran solo las columnas las cuales retornen True al aplicar el filtro
    def filterAcceptsColumn(self, source_column, source_parent):
        nombre_columna = self.sourceModel().headerData(source_column, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        return nombre_columna in ["CLIENTE", "DIRECCION", "DATOS TRANSPORTE EXTERNO", "TELEF. CONTACTO", "N° CARPETA", "LATITUD", "LONGITUD"]


class VistaTablaTipoRetiro(QTableView):
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
        # 4 = DIRECCION, 6 = CLIENTE
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setDefaultSectionSize(200)
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)

    def mostrar_menu_contextual(self, pos):
        # Verificar si el clic derecho fue en la columna que deseamos
        # Index 1 debería corresponder a la columna de las direcciones
        #       4 debería corresponder a despacho externo
        menu = QMenu(self)
        accion = QAction("Remover Despacho", self)
        accion.triggered.connect(self.remover_despacho)
        menu.addAction(accion)

        # Mostrar el menú en la posición del clic derecho
        menu.exec(self.viewport().mapToGlobal(pos))
    
    def remover_despacho(self):
        index = self.selectionModel().currentIndex()
        model = self.model()
        if isinstance(model, QSortFilterProxyModel):
            real_idx = model.mapToSource(index)
            print("row:", index.row(), "col:", index.column())
            print("row:", real_idx.row(), "col:", real_idx.column())
            real_model = model.sourceModel()
            real_model.removeRow(real_idx.row())

# Creamos nuestro propio ProxyModel para aplicar filtros a partir de un ModeloDataframe
class ModeloFiltroTipoRetiro(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(QSortFilterProxyModel, self).__init__(parent)
        
    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled
    
    # se muestran solo filas que retornen True al aplicarse el filtro
    def filterAcceptsRow(self, source_row, source_parent):
        # indices fueron obtenidos con self.df.columns.get_loc("LATITUD"), longitud es el indice siguiente
        idx_tipo_entrega = self.sourceModel().index(source_row, 6, source_parent)
        
        tipo_entrega = self.sourceModel().data(idx_tipo_entrega)
        return (tipo_entrega == 'REVISAR DESPACHO GRATUITO NO INCLUIDO')
    
    # se muestran solo las columnas las cuales retornen True al aplicar el filtro
    def filterAcceptsColumn(self, source_column, source_parent):
        # Obtenemos el nombre de la columna
        nombre_columna = self.sourceModel().headerData(source_column, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)

        # Solo se mostraran columnas que pertenezcan a la lista
        return nombre_columna in ["N° CARPETA", "SERVICIO", "CLIENTE", "DIRECCION", "COMUNA", "TIPO DE ENTREGA", "EJECUTIVO"]


# Modelo de datos para que Qt pueda mostrar un DataFrame de pandas en un QTableWidget
class ModeloDataframe(QAbstractTableModel):
    def __init__(self, data):
        super(QAbstractTableModel, self).__init__()
        self._data = data
        
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
