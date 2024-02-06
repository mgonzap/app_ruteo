from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QDialog, QTableView, QMenu, QHeaderView
from PyQt6.QtCore import QAbstractTableModel, Qt, QSortFilterProxyModel, pyqtSignal, QSize, QAbstractItemModel
from PyQt6.QtGui import QAction, QGuiApplication
import pandas as pd
from urllib.parse import quote
from ventana_navegador import *
from procesamiento_datos import *

# Clase dedicada al procesamiento de datos (temporalmente, desde el excel)
# En caso de que los datos necesiten procesamiento extra (ej, georef no logra obtener coordenadas)
# se pide ayuda a usuario para corregir

class VentanaDatos(QMainWindow):
    edicion_terminada = pyqtSignal(pd.DataFrame)
    def __init__(self, icono):
        super(QMainWindow, self).__init__()
        self.icono = icono
        
        # TODO: ejecutar procesar_data de forma asincrona
        # pues el procesamiento de datos espera a que se cierre el dialogo para iniciar
        # self.generar_dialogo("Por favor espere, procesando los datos...")
        self.recibir_datos(procesar_dataframe(procesar_query())[0])
        
        self.setWindowIcon(self.icono)
        self.setWindowTitle("Procesamiento de Datos")

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

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
        
        # TODO: ventana queda corta horizontalmente
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
    
    def finalizar_edicion(self):
        copia_df = self.df.copy()
        self.edicion_terminada.emit(copia_df)
        # TODO: geo está escribiendo dos veces en el archivo, la primera al georreferenciar coordenadas
        # y ahora que recibe el df editado. Ver que se haga una sola vez.
        georef.actualizar_coordenadas(copia_df)
        self.close()
    
    def generar_dialogo(self, texto):
        dlg = QDialog()
        dlg.setWindowIcon(self.icono)
        dlg.setWindowTitle("Procesando Datos")
        
        layout = QVBoxLayout()
        mensaje = QLabel(texto)
        
        layout.addWidget(mensaje)
        
        dlg.setLayout(layout)
        dlg.exec()  
    
    def recibir_datos(self, df):
        self.df = df
        self.modelo_tabla = ModeloDataframe(self.df)
        
        # ProxyModel que filtre la tabla para mostrar solo filas que necesiten correccion
        self.modelo_proxy_tabla = ModeloProxyDataframe()
        self.modelo_proxy_tabla.setSourceModel(self.modelo_tabla)
    
    # reemplazamos la funcion show para que revise si hay datos que necesiten corrección
    # si no, simplemente se considera la edición finalizada.
    def show(self):
        if self.vista_tabla.model() is None or self.vista_tabla.model().rowCount() == 0:
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
        # Para direccion expandimos totalmente
        self.resizeColumnToContents(1)
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
        index_latitud = self.sourceModel().index(source_row, 27, source_parent)
        index_longitud = self.sourceModel().index(source_row, 28, source_parent)
        #print("resultado index_latitud", float(self.sourceModel().data(index_latitud)) == 0.0)
        #print("resultado index_longitud", float(self.sourceModel().data(index_longitud)) == 0.0)
        # TODO: condicion == no funciona, castear a float lo arregla, pero mejor indagar que tipo devuelve data
        return float(self.sourceModel().data(index_latitud)) == 0.0 or float(self.sourceModel().data(index_longitud)) == 0.0
    
    # se muestran solo las columnas las cuales retornen True al aplicar el filtro
    def filterAcceptsColumn(self, source_column, source_parent):
        # Obtenemos el nombre de la columna
        nombre_columna = self.sourceModel().headerData(source_column, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)

        # Solo se mostraran columnas que pertenezcan a la lista
        return nombre_columna in ["CLIENTE", "DIRECCION", "DATOS TRANSPORTE EXTERNO", "TELEF. CONTACTO", "N° CARPETA", "LATITUD", "LONGITUD"]


# Ejemplo de uso
if __name__ == "__main__":
    app = QApplication([])

    ventana_datos = VentanaDatos()
    ventana_datos.show()

    app.exec()