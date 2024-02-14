from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QListWidget, QListWidgetItem, QDialog,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from app_ruteo import Entregas
from crear_camion_ventana import VentanaCreacionCamion
from copy import deepcopy

class VentanaPrincipal(QMainWindow):

    def __init__(self, df_filtrado, fecha, icono):
        super().__init__()

        self.worker_thread = None
        self.entregas = Entregas()
        # cargamos el DataFrame
        self.entregas.df = df_filtrado
        
        self.setWindowIcon(icono)
        self.icono = icono

        self.camiones_seleccionados = list(self.entregas.camiones.keys())
        self.dict_camiones = deepcopy(self.entregas.camiones)

        self.setWindowTitle("Modelo de Optimización de rutas WScargo")
        self.setGeometry(100, 100, 700, 400)

        self.central_widget = QWidget(self)
        self.central_widget.setContentsMargins(10, 5, 10, 5)
        self.setCentralWidget(self.central_widget)

        # Layout Base
        self.layout = QHBoxLayout(self.central_widget)
        
        ## Layout para ComboBox y sus botones (izquierda de la pantalla)
        self.v_combo_layout = QVBoxLayout()
        self.v_combo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        ### Logo
        self.logo_label = QLabel()
        self.pixmap_test = QPixmap("logo\\WSC-LOGO.png")
        self.logo_label.setPixmap(self.pixmap_test)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_combo_layout.addWidget(self.logo_label)
        
        ### Spacing 
        self.v_combo_layout.addSpacing(30)
        
        ### Fecha
        # TODO: recibir fecha desde VentanaDatos o algun otra alternativa
        self.fecha_line_edit = QLabel(f"Se calcularán rutas para: {fecha}", self)
        self.fecha_line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_combo_layout.addWidget(self.fecha_line_edit)
        
        self.v_combo_layout.addSpacing(30)

        ### ComboBox reflejara los camiones que esten almacenados en el objeto Entregas
        self.combo_camiones = QComboBox()
        self.combo_camiones.addItems(self.entregas.camiones.keys())
        self.v_combo_layout.addWidget(self.combo_camiones)

        ### Boton Agregar Camion
        self.agregar_button = QPushButton("Agregar Camión a Lista", self)
        self.agregar_button.clicked.connect(self.agregar_camion)
        self.v_combo_layout.addWidget(self.agregar_button)
        
        ### Boton Quitar Camion
        self.quitar_button = QPushButton("Quitar Camión de Lista", self)
        self.quitar_button.setProperty('class', 'danger')
        self.quitar_button.clicked.connect(self.quitar_camion)
        self.v_combo_layout.addWidget(self.quitar_button)
        
        self.crear_boton = QPushButton("Crear Nuevo Camión", self)
        self.crear_boton.clicked.connect(self.abrir_ventana_creacion)
        self.v_combo_layout.addWidget(self.crear_boton)
        
        self.layout.addLayout(self.v_combo_layout, 35)
        
        # Spacer
        self.layout.addSpacing(20)
        
        # Layout para la lista de camiones y el calculo de resultados
        self.v_list_layout = QVBoxLayout()

        # Generamos el widget para la lista de camiones
        # La lista de camiones reflejara los camiones considerados para el cálculo
        self.lista_camiones = QListWidget(self)
        self.v_list_layout.addWidget(self.lista_camiones)
        # Populamos la lista
        for camion in self.camiones_seleccionados:
            nuevo_item = QListWidgetItem(camion)
            nuevo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lista_camiones.addItem(nuevo_item)

        self.worker_thread = None
        self.calcular_button = QPushButton("Calcular Vueltas y Servicios", self)
        self.calcular_button.clicked.connect(self.ejecutar_modelo)
        self.v_list_layout.addWidget(self.calcular_button)
        
        self.layout.addLayout(self.v_list_layout, 65)

    def ejecutar_modelo(self):
        if self.worker_thread != None and self.worker_thread.isRunning():
            self.generar_advertencia("Ya se están calculando rutas. Se debe esperar a que termine el proceso.")
            return
        
        self.worker_thread = RoutesThread(self.entregas, self.camiones_seleccionados)
        self.worker_thread.setTerminationEnabled(True)
        self.worker_thread.finished.connect(self.__on_finished)
        self.worker_thread.start()
        self.calc_dlg = ConfirmDialog(self)
        self.calc_dlg.salida_confirmada.connect(self.__on_model_cancel)
        self.calc_dlg.exec()
    
    def __on_model_cancel(self):
        self.worker_thread.terminate()
        self.calc_dlg.close_directly()

    def abrir_ventana_creacion(self):
        camion_ventana = VentanaCreacionCamion(self, self.agregar_camion, self.entregas)
        camion_ventana.mostrar()

    def agregar_camion(self):
        camion_seleccionado = self.combo_camiones.currentText()
        if camion_seleccionado not in self.camiones_seleccionados:
            self.camiones_seleccionados.append(camion_seleccionado)
            self.entregas.camiones[camion_seleccionado] = self.dict_camiones[camion_seleccionado]
            nuevo_item = QListWidgetItem(camion_seleccionado)
            nuevo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lista_camiones.addItem(nuevo_item)

        else:
            self.generar_advertencia("Camión seleccionado ya se encuentra en la lista.")

    def quitar_camion(self):
        camion_a_eliminar = self.lista_camiones.currentItem()
        # Llamar error si no hay camion seleccionado
        if camion_a_eliminar is None:
            self.generar_advertencia("Seleccione un camión para eliminar.")
            return
        camion_a_eliminar = camion_a_eliminar.text()
        if camion_a_eliminar in self.entregas.camiones:
            # Aquí se elimina el camión de la 'db', no es lo ideal
            del self.entregas.camiones[camion_a_eliminar]
            self.actualizar_combo_camiones()
            self.quitar_camion_lista()

    def actualizar_combo_camiones(self):
        camiones_disponibles = list(self.dict_camiones.keys())
        self.combo_camiones.clear()
        self.combo_camiones.addItems(camiones_disponibles)

    def quitar_camion_lista(self):
        camion_a_quitar = self.lista_camiones.currentItem().text()
        self.camiones_seleccionados.remove(camion_a_quitar)
        self.lista_camiones.takeItem(self.lista_camiones.currentRow())
    
    def generar_advertencia(self, texto):
        dlg = QDialog(self)
        dlg.setWindowTitle("Error")
        
        layout = QVBoxLayout()
        mensaje = QLabel(texto)
        
        layout.addWidget(mensaje)
        
        dlg.setLayout(layout)
        dlg.exec()
        
    def __on_finished(self):
        self.calc_dlg.close_directly()


class ConfirmDialog(QDialog):
    salida_confirmada = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        if parent != None:
            self.setWindowIcon(parent.icono)
        self.setWindowTitle("Calculando Rutas")
        texto = "Calculando rutas para las entregas..."
        layout = QVBoxLayout()
        mensaje = QLabel(texto)
        
        cancelar = QPushButton("Cancelar Ruteo")
        cancelar.clicked.connect(self.closeEvent)
        
        layout.addWidget(mensaje)
        layout.addWidget(cancelar)       
        self.setLayout(layout)
        
    def closeEvent(self, event):
        confirmacion = QMessageBox.question(self, "Confirmar", 
                                             "¿Estás seguro de que quieres cancelar el cálculo de rutas?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirmacion == QMessageBox.StandardButton.Yes:
            # al cancelar ruteo
            if event == False:
                self.salida_confirmada.emit()
                return
            event.accept()
            self.salida_confirmada.emit()
        else:
            event.ignore()
    
    def close_directly(self):
        self.closeEvent = lambda event: event.accept()
        self.close()

class RoutesThread(QThread):
    finished = pyqtSignal()
    
    def __init__(self, entregas, camiones):
        super().__init__()
        self.entregas: Entregas = entregas
        self.camiones = camiones

    def run(self):
        print("Camiones seleccionados para ejecucion:", self.camiones)
        self.entregas.ejecutar_modelo()
        self.finished.emit()