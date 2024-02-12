from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, 
    QDialog, QTableView, QMenu, QMessageBox
)
from PyQt6.QtCore import (
    QAbstractTableModel, Qt, QSortFilterProxyModel, pyqtSignal, 
    QSize, QThread, QTimer
)
from PyQt6.QtGui import QAction, QCloseEvent, QGuiApplication
import pandas as pd
import georef
import sys
from urllib.parse import quote
from ventana_navegador import VentanaNavegador
from procesamiento_datos import procesar_dataframe, procesar_query

# Clase dedicada al procesamiento de datos (temporalmente, desde el excel)
# En caso de que los datos necesiten procesamiento extra (ej, georef no logra obtener coordenadas)
# se pide ayuda a usuario para corregir

class VentanaDatos(QMainWindow):
    edicion_terminada = pyqtSignal(pd.DataFrame)
    def __init__(self, fecha, icono):
        super(QMainWindow, self).__init__()
        self.icono = icono
        self.fecha = fecha
        #print("fecha recibida en ventana datos:", fecha)
        self.worker_thread = DataThread(fecha)
        self.worker_thread.setTerminationEnabled(True)
        self.worker_thread.finished.connect(self.__on_datos_received__)
        self.worker_thread.start()
        
        self.init_timer = QTimer()
        self.init_timer.setSingleShot(True)
        self.init_timer.timeout.connect(self.generar_dialogo)
        self.init_timer.start(100)
        
    def __on_datos_received__(self, df):
        self.recibir_datos(df)
        self.setWindowIcon(self.icono)
        self.setWindowTitle("Procesamiento de Datos")

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        if not df.empty:
            self.layout = QVBoxLayout(self.central_widget)

            self.label_nombre = QLabel(
                "Es necesario corregir las siguientes coordenadas. " +
                "Haga click derecho en la dirección o en los datos de transporte externo para buscar coordenadas:"
                )
            self.layout.addWidget(self.label_nombre)
            
            self.vista_tabla = CustomTableView()
            self.vista_tabla.setModel(self.modelo_proxy_tabla)
            # Esconder columna de IDs
            self.vista_tabla.verticalHeader().hide()
            self.layout.addWidget(self.vista_tabla)
            
            geometria_tabla = self.vista_tabla.frameGeometry()
            # Estilo modo oscuro de MainApp hace que resize quede pequeño horizontalmente
            # por eso obtenemos el tamaño horizontal de la pantalla y lo aplicamos
            screen = QGuiApplication.primaryScreen().availableSize()
            self.resize(QSize(screen.width(), geometria_tabla.height()))
            self.vista_tabla.ajustar_columnas()
            
            # Finalizar la edicion y pasar los datos al df 'de verdad'
            self.finalizar_button = QPushButton("Finalizar edición")
            self.finalizar_button.clicked.connect(self.finalizar_edicion)
            self.layout.addWidget(self.finalizar_button)
        self.move(0, self.y())
        self.show()
        self.dlg.close_directly()
    
    def generar_dialogo(self):
        self.dlg = ConfirmDialog(self)
        self.dlg.salida_confirmada.connect(sys.exit)
        self.dlg.exec()
    
    def finalizar_edicion(self):
        copia_df = self.df.copy()
        self.edicion_terminada.emit(copia_df)
        # TODO: geo está escribiendo dos veces en el archivo, la primera al georreferenciar coordenadas
        # y ahora que recibe el df editado. Ver que se haga una sola vez.
        georef.actualizar_coordenadas(copia_df)
        self.close()
    
    def recibir_datos(self, df):
        self.df = df
        self.modelo_tabla = ModeloDataframe(self.df)
        
        # ProxyModel que filtre la tabla para mostrar solo filas que necesiten correccion
        self.modelo_proxy_tabla = ModeloProxyDataframe()
        self.modelo_proxy_tabla.setSourceModel(self.modelo_tabla)
    
    # reemplazamos la funcion show para que revise si hay datos que necesiten corrección
    # si no, simplemente se considera la edición finalizada.
    def show(self):
        if self.df.empty or self.vista_tabla.model() is None or self.vista_tabla.model().rowCount() == 0:
            self.finalizar_edicion()
        else:
            super().show()


class CustomTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Conectar el evento customContextMenuRequested a la función que muestra el menú
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.mostrar_menu_contextual)
    
    def ajustar_columnas(self):
        # Para direccion
        self.horizontalHeader().resizeSection(1, int(self.viewport().size().width() * 1.0))
        # Para datos transporte externo no del todo
        self.horizontalHeader().resizeSection(4, int(self.viewport().size().width() * 0.35))

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
            print("Actualización de latitud exitosa")
        else:
            print("Error al actualizar latitud")
        
        if self.model().setData(indice_longitud, long, Qt.ItemDataRole.EditRole):
            print("Actualización de longitud exitosa")
        else:
            print("Error al actualizar longitud")


# Modelo de datos para que Qt pueda mostrar un DataFrame de pandas en un QTableWidget
class ModeloDataframe(QAbstractTableModel):
    def __init__(self, data):
        super(QAbstractTableModel, self).__init__()
        self._data = data
        
    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]
    
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


# Creamos nuestro propio ProxyModel para aplicar filtros a partir de un ModeloDataframe
class ModeloProxyDataframe(QSortFilterProxyModel):
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
        idx_latitud = self.sourceModel().index(source_row, 28, source_parent)
        idx_longitud = self.sourceModel().index(source_row, 29, source_parent)
        
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
        # Obtenemos el nombre de la columna
        nombre_columna = self.sourceModel().headerData(source_column, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)

        # Solo se mostraran columnas que pertenezcan a la lista
        return nombre_columna in ["CLIENTE", "DIRECCION", "DATOS TRANSPORTE EXTERNO", "TELEF. CONTACTO", "N° CARPETA", "LATITUD", "LONGITUD"]


class DataThread(QThread):
    finished = pyqtSignal(pd.DataFrame)
    def __init__(self, fecha):
        super().__init__()
        self.fecha = fecha
    
    def run(self):
        df = procesar_dataframe(procesar_query(self.fecha), self.fecha)
        self.finished.emit(df)


class ConfirmDialog(QDialog):
    salida_confirmada = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        if parent != None:
            self.setWindowIcon(parent.icono)
        self.setWindowTitle("Procesando Datos")
        texto = "Por favor espere, obteniendo y procesando los datos..."
        layout = QVBoxLayout()
        mensaje = QLabel(texto)
        
        layout.addWidget(mensaje)       
        self.setLayout(layout)
        
    def closeEvent(self, event):
        confirmacion = QMessageBox.question(self, "Confirmar cierre", 
                                             "¿Estás seguro de que quieres cerrar la aplicación?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirmacion == QMessageBox.StandardButton.Yes:
            self.salida_confirmada.emit()
            event.accept()
        else:
            event.ignore()
    
    def close_directly(self):
        self.closeEvent = lambda event: event.accept()
        self.close()