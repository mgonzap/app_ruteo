from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt
from app_ruteo import *
from ventana_datos import *
from datetime import date, timedelta
from crear_camion_ventana import *
import webbrowser

class VentanaPrincipal(QMainWindow):

    def __init__(self, df_filtrado, icono):
        super().__init__()

        self.entregas = Entregas()
        # TODO: recibir fecha
        self.entregas.cargar_datos(df_filtrado)    
        
        self.setWindowIcon(icono)

        self.camiones_seleccionados = list(self.entregas.camiones.keys())

        self.setWindowTitle("Modelo de Optimización de rutas WScargo")
        self.setGeometry(100, 100, 700, 600)

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
        self.pixmap_test = QtGui.QPixmap("logo\\WSC-LOGO.png")
        self.logo_label.setPixmap(self.pixmap_test)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_combo_layout.addWidget(self.logo_label)
        
        ### Spacing 
        self.v_combo_layout.addSpacing(30)
        
        ### Fecha
        # TODO: recibir fecha desde VentanaDatos o algun otra alternativa
        self.fecha_line_edit = QLabel("Se calcularán rutas para mañana: " + (date.today() + timedelta(days=1)).strftime('%d-%m-%Y'), self)
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
        
        self.h_resultado_layout = QHBoxLayout()
        
        # TODO: Crear un widget que muestre el HTML de ruteo que se genera.
        self.resultado_label = QLabel(self)
        self.resultado_label.setText("RESULTADOS")
        self.resultado_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.h_resultado_layout.addWidget(self.resultado_label)
        
        self.v_list_layout.addLayout(self.h_resultado_layout)

        self.calcular_button = QPushButton("Calcular Vueltas y Servicios", self)
        self.calcular_button.clicked.connect(self.ejecutar_modelo)
        self.v_list_layout.addWidget(self.calcular_button)
        
        self.layout.addLayout(self.v_list_layout, 65)


    def abrir_ventana_creacion(self):
        camion_ventana = VentanaCreacionCamion(self, self.agregar_camion, self.entregas)
        camion_ventana.mostrar()

    def agregar_camion(self):
        camion_seleccionado = self.combo_camiones.currentText()
        if camion_seleccionado not in self.camiones_seleccionados:
            self.camiones_seleccionados.append(camion_seleccionado)
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
            # del self.entregas.camiones[camion_a_eliminar]
            self.actualizar_combo_camiones()
            self.quitar_camion_lista()

    def actualizar_combo_camiones(self):
        camiones_disponibles = list(self.entregas.camiones.keys())
        self.combo_camiones.clear()
        self.combo_camiones.addItems(camiones_disponibles)

    def quitar_camion_lista(self):
        camion_a_quitar = self.lista_camiones.currentItem().text()
        self.camiones_seleccionados.remove(camion_a_quitar)
        self.lista_camiones.takeItem(self.lista_camiones.currentRow())

    def ejecutar_modelo(self):
        # TODO: despues de ejecutar modelo llamar a widget para mostrar HTML de rutas
        self.resultado_label.setText(f"{self.camiones_seleccionados}")
        print("Camiones seleccionados para ejecucion:", self.camiones_seleccionados)
        # TODO: pasar a modelo lista de camiones a usar?
        self.entregas.ejecutar_modelo()
        file_path = ['mapas\mapa_3_Rutas.html', 'mapas\mapa_4_Rutas.html']
        for fpath in file_path:
            webbrowser.open('file://' + os.path.abspath(fpath))
    
    def generar_advertencia(self, texto):
        dlg = QDialog(self)
        dlg.setWindowTitle("Error")
        
        layout = QVBoxLayout()
        mensaje = QLabel(texto)
        
        layout.addWidget(mensaje)
        
        dlg.setLayout(layout)
        dlg.exec()
