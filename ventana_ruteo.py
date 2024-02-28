from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDialog,
    QMessageBox,
    QApplication,
    QToolBar,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon, QAction
from app_ruteo import Entregas, Camion
from ventanas_base import VentanaDataframe
from ventana_camiones import VentanaCamion
from ventanas_despachos import VentanaDespachos
from copy import deepcopy
from functools import partial
from widgets_camion import CamionListWidget
import sys
import numpy as np


class VentanaRuteo(VentanaDataframe):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent=parent,
            title="Modelo de Optimización de rutas WScargo",
            safe_to_close=False,
        )
        self.setGeometry(100, 100, 550, 550)

        self.setCentralWidget(QWidget(self))
        self.centralWidget().setContentsMargins(10, 5, 10, 5)

        self.addToolBar(self.RuteoToolbar())

        self.main_layout = QHBoxLayout(self.centralWidget())

        self.left_layout = self.RuteoLeftLayout()
        self.right_layout = self.RuteoRightLayout()

        self.left_layout.lista_camiones.camion_enviado.connect(
            partial(self.right_layout.lista_camiones.addCamion, ruteo=True)
        )
        self.right_layout.lista_camiones.camion_enviado.connect(
            self.left_layout.lista_camiones.addCamion
        )
        self.main_layout.addLayout(self.left_layout, 40)
        self.main_layout.setSpacing(20)
        self.main_layout.addLayout(self.right_layout, 60)

    class RuteoToolbar(QToolBar):
        calendar_icon = QIcon("icons\\calendar-event.svg")
        box_icon = QIcon("icons\\box-seam.svg")

        toolbar_stylesheet = """
            QToolBar {
                background-color: rgb(220, 220, 220);
            }
            QToolBar::separator {
                background-color: rgb(120, 120, 120);
                width: 1px;
                margin-right: 5px;
                margin-left: 5px;
            }
        """

        def __init__(self):
            super().__init__("Barra de Herramientas")
            self.setMovable(False)
            self.toggleViewAction().setEnabled(False)
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            self.setStyleSheet(self.toolbar_stylesheet)

            self.logo_label = QLabel()
            self.logo_label.setContentsMargins(2, 2, 5, 2)
            self.logo_label.setPixmap(QPixmap("logo\\WSC-LOGO.png"))
            self.logo_label.setAlignment(
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
            )
            self.addWidget(self.logo_label)

            self.addSeparator()

            self.stretch = QLabel()
            self.stretch.setTextFormat(Qt.TextFormat.MarkdownText)
            self.stretch.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stretch.setSizePolicy(
                QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Ignored
            )
            self.actualizar_vol_total()
            self.addWidget(self.stretch)

            # VentanaDataframe.getFecha()
            self.fecha_action = QAction(
                self.calendar_icon, VentanaDataframe.getFecha(), self
            )
            self.fecha_action.setEnabled(False)
            self.despachos_action = QAction(self.box_icon, "Ver Despachos", self)
            self.despachos_action.triggered.connect(self.ver_ventana_despachos)

            self.addAction(self.despachos_action)
            self.addAction(self.fecha_action)

        def ver_ventana_despachos(self):
            self.ventana_despachos = VentanaDespachos()
            # self.ventana_despachos.finished.connect(self.actualizar_label_vol_total_despachos)
            self.ventana_despachos.show()
            
        def actualizar_vol_total(self):
            vol_total = np.float64(VentanaDataframe.getDataFrame()['VOLUMEN'].sum()).round(2)
            self.stretch.setText(
                f"*Volumen total de despachos: {vol_total}*"
            )

    class RuteoLeftLayout(QVBoxLayout):
        def __init__(self):
            super().__init__()
            self.crear_boton = QPushButton("Crear Camión")
            self.crear_boton.clicked.connect(self.abrir_ventana_creacion)
            self.addWidget(self.crear_boton)

            self.v_layout = QVBoxLayout()
            self.v_layout.setSpacing(10)

            self.label = QLabel("### Camiones disponibles")
            self.label.setTextFormat(Qt.TextFormat.MarkdownText)
            self.label.setAlignment(
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom
            )
            self.v_layout.addWidget(self.label)

            self.lista_camiones = CamionListWidget()
            self.v_layout.addWidget(self.lista_camiones)
            
            self.addLayout(self.v_layout)

        def abrir_ventana_creacion(self):
            self.ventana_creacion = VentanaCamion()
            self.ventana_creacion.resultado_camion.connect(self.crear_camion)
            self.ventana_creacion.show()

        def crear_camion(self, nombre, capacidad, vueltas, entregas):
            camion_creado = Camion(capacidad, 0, vueltas, entregas)
            self.lista_camiones.addCamion(nombre, camion_creado)
            self.ventana_creacion.close()
            

    class RuteoRightLayout(QVBoxLayout):
        def __init__(self):
            super().__init__()
            self.entregas = Entregas()

            self.v_layout = QVBoxLayout()
            self.v_layout.setSpacing(10)

            self.label = QLabel("### Camiones considerados para Ruteo")
            self.label.setTextFormat(Qt.TextFormat.MarkdownText)
            self.label.setAlignment(
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom
            )
            self.v_layout.addWidget(self.label)

            self.lista_camiones = CamionListWidget(ruteo=True)
            for nombre, camion in self.entregas.camiones.items():
                self.lista_camiones.addCamion(nombre, camion, ruteo=True)
                
            self.lista_camiones.camion_enviado.connect(self.actualizar_volumen_ruta)
            self.lista_camiones.cambio.connect(self.actualizar_volumen_ruta)
                
            self.volumen_ruta = QLabel()
            self.volumen_ruta.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.volumen_ruta.setTextFormat(Qt.TextFormat.MarkdownText)
            self.actualizar_volumen_ruta()
            self.v_layout.addWidget(self.volumen_ruta)

            self.v_layout.addWidget(self.lista_camiones)
            self.addLayout(self.v_layout)

            self.ruteo_boton = QPushButton("Calcular Vueltas y Servicios")
            self.ruteo_boton.clicked.connect(self.ejecutar_modelo)
            self.addWidget(self.ruteo_boton)

        def ejecutar_modelo(self):
            """
            if len(self.lista_camiones.widgets_camiones) == 0:
                self.generar_advertencia(
                    "Es necesario por lo menos un camión para calcular rutas."
                )
                return

            if self.worker_thread != None and self.worker_thread.isRunning():
                self.generar_advertencia(
                    "Ya se están calculando rutas. Se debe esperar a que termine el proceso."
                )
                return
            """
            camiones_ruteo = {}
            for nombre, camion in [
                x.getCamion() for x in self.lista_camiones.widgets_camiones
            ]:
                camiones_ruteo[nombre] = camion
            self.worker_thread = RoutesThread(
                VentanaDataframe.getDataFrame(), self.entregas, camiones_ruteo
            )
            self.worker_thread.setTerminationEnabled(True)
            self.worker_thread.finished.connect(self.__on_finished)
            self.worker_thread.start()
            self.calc_dlg = ConfirmDialog(self.lista_camiones)
            self.calc_dlg.salida_confirmada.connect(self.__on_model_cancel)
            self.calc_dlg.exec()

        def __on_model_cancel(self):
            self.worker_thread.terminate()
            self.calc_dlg.close_directly()

        def __on_finished(self):
            self.calc_dlg.close_directly()
            
        def actualizar_volumen_ruta(self, nombre="", truck=None):
            vol_total = 0
            dict_camiones = self.lista_camiones.toDict()
            for camion in dict_camiones:
                vol_total += dict_camiones[camion].capacidad * dict_camiones[camion].vueltas
            self.volumen_ruta.setText(
                f"*Volumen teórico de ruteo: {vol_total}*"
            )


class ConfirmDialog(QDialog):
    salida_confirmada = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(VentanaDataframe.getIcon())
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
        confirmacion = QMessageBox.question(
            self,
            "Confirmar",
            "¿Estás seguro de que quieres cancelar el cálculo de rutas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if event == False:
            # al cancelar ruteo
            self.salida_confirmada.emit()
            return
        if confirmacion == QMessageBox.StandardButton.Yes:
            event.accept()
            self.salida_confirmada.emit()
        else:
            event.ignore()

    def close_directly(self):
        self.closeEvent = lambda event: event.accept()
        self.close()


class RoutesThread(QThread):
    finished = pyqtSignal()

    def __init__(self, df, entregas, camiones):
        super().__init__()
        self.entregas: Entregas = entregas
        self.entregas.df_original = df
        self.entregas.camiones = deepcopy(camiones)

    def run(self):
        self.entregas.ejecutar_modelo()
        self.finished.emit()


if __name__ == "__main__":
    app = QApplication(["TEST"])

    window = VentanaRuteo()

    camiones = {
        "Sinotruk": Camion(26, 0, 2, 3),
        "JAC": Camion(16, 0, 3, 6),
        "Hyundai": Camion(6, 0, 3, 6),
        "Externo_1": Camion(17, 0, 1, 7),
    }

    window.show()
    sys.exit(app.exec())
