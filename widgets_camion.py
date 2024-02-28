from PyQt6.QtWidgets import (
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
    QFrame,
    QSizePolicy,
    QScrollArea
)
from PyQt6.QtGui import QIcon
from app_ruteo import Camion
from PyQt6.QtCore import pyqtSignal, Qt
from typing import Callable
from ventana_camiones import VentanaCamion


class CamionWidget(QFrame):
    camion_enviado = pyqtSignal(str, Camion)

    edit_icon = QIcon("icons\\pencil-square.svg")
    add_icon = QIcon("icons\\box-arrow-in-right.svg")
    remove_icon = QIcon("icons\\box-arrow-left.svg")
    
    button_stylesheet = """
        QPushButton {
            border-radius: 10px;
        }
        QPushButton:hover {
            background-color: rgb(247, 199, 42);
        }
        QPushButton:pressed {
            background-color: rgb(230, 182, 25);
        }
    """
    bg_stylesheet = """
        QFrame {
            background-color: rgb(245, 245, 245);
        }
        QFrame:focus {
            background-color: rgb(230, 230, 230)
        }
    """

    def __init__(
        self, nombre: str, camion: Camion, added: bool = False, parent = None
    ) -> None:
        super().__init__(parent)
        self.ventana_edicion = None

        self.layout_h = QHBoxLayout()
        self.layout_h.setContentsMargins(10, 0, 0, 0)
        self.layout_v = QVBoxLayout()
        self.layout_v.setSpacing(0)

        self.nombre = nombre
        self.camion = camion

        self.camion_nombre_widget = self.CamionNombreWidget(nombre)
        self.layout_v.addLayout(self.camion_nombre_widget.layout())

        self.div = QWidget()
        self.div.setFixedHeight(2)
        self.div.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.div.setStyleSheet("background-color: rgb(80, 80, 80)")
        self.layout_v.addWidget(self.div)

        self.camion_parametros_layout = QVBoxLayout()
        self.camion_parametros_layout.setSpacing(0)

        self.camion_capacidad = self.CamionParametroWidget(
            "Capacidad", self.camion.capacidad
        )
        self.camion_parametros_layout.addLayout(self.camion_capacidad.layout())

        self.camion_vueltas = self.CamionParametroWidget("Vueltas", self.camion.vueltas)
        self.camion_parametros_layout.addLayout(self.camion_vueltas.layout())

        self.camion_entregas = self.CamionParametroWidget(
            "Entregas", self.camion.maximo_entregas
        )

        self.camion_parametros_layout.addLayout(self.camion_entregas.layout())
        self.camion_parametros_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.layout_v.addLayout(self.camion_parametros_layout)

        self.layout_v_buttons = QVBoxLayout()
        self.layout_v_buttons.setSpacing(2)

        self.edit_button = self.pushButton(
            self.edit_icon, "Editar Camión", self.__on_editar_camion__
        )
        self.layout_v_buttons.addWidget(self.edit_button)

        self.send_button = self.pushButton(
            self.add_icon, "Agregar camión a ruteo", self.__on_enviar_camion__
        )
        if added:
            self.send_button.setIcon(self.remove_icon)
            self.send_button.setToolTip("Retirar camión de ruteo")
        self.layout_v_buttons.addWidget(self.send_button)

        self.layout_h.addLayout(self.layout_v, 60)
        self.layout_h.addSpacing(10)
        self.layout_h.addLayout(self.layout_v_buttons, 40)

        self.setLayout(self.layout_h)
        self.initFrameAndColor()

    def initFrameAndColor(self):
        self.setFrameShape(self.Shape.Box)
        self.setAutoFillBackground(True)
        self.setStyleSheet(self.bg_stylesheet)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def pushButton(self, icon: QIcon, tooltip: str, callback: Callable):
        button = QPushButton()
        button.setIcon(icon)
        button.setToolTip(tooltip)
        button.setMinimumSize(36, 36)
        button.setStyleSheet(self.button_stylesheet)
        button.clicked.connect(callback)
        return button

    def __on_enviar_camion__(self):
        print(f"enviar {self.nombre}: {self.camion}")
        self.camion_enviado.emit(self.nombre, self.camion)

    def __on_editar_camion__(self):
        if self.ventana_edicion != None and self.ventana_edicion.isVisible():
            return
        self.ventana_edicion = VentanaCamion(self, (self.nombre, self.camion))
        self.ventana_edicion.resultado_camion.connect(self.updateCamionWidget)
        self.ventana_edicion.show()

    def updateCamionWidget(
        self, nombre: str, capacidad: int, vueltas: int, entregas: int
    ):
        self.nombre = nombre
        self.camion_nombre_widget.setNombre(nombre)

        self.camion.capacidad = capacidad
        self.camion_capacidad.setCantidad(capacidad)

        self.camion.vueltas = vueltas
        self.camion_vueltas.setCantidad(vueltas)

        self.camion.maximo_entregas = entregas
        self.camion_entregas.setCantidad(entregas)

        self.ventana_edicion.close()

    def getCamion(self):
        return (self.nombre, self.camion)

    class CamionParametroWidget:
        stylesheet_parametro = """
        QLabel {
            color: rgb(80, 80, 80);
            font-size: 8pt;
        }
        """

        def __init__(self, nombre_parametro: str, cantidad: int | float = 0):
            self.param_layout = QHBoxLayout()
            self.nombre = QLabel()

            self.nombre.setTextFormat(Qt.TextFormat.MarkdownText)
            self.nombre.setText(f"*{nombre_parametro}:*")
            self.nombre.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.nombre.setStyleSheet(self.stylesheet_parametro)
            self.nombre.setMinimumWidth(80)

            self.cantidad = QLabel()
            self.cantidad.setText(f"{cantidad}")
            self.cantidad.setMinimumWidth(20)
            self.cantidad.setStyleSheet(self.stylesheet_parametro)
            self.cantidad.setAlignment(Qt.AlignmentFlag.AlignRight)

            self.param_layout.addWidget(self.nombre, 70)
            self.param_layout.addWidget(self.cantidad, 30)

        def setNombre(self, nombre: str):
            self.nombre.setText(f"*{nombre}*:")

        def setCantidad(self, cantidad: int | float):
            self.cantidad.setText(f"{cantidad}")

        def layout(self):
            return self.param_layout

    class CamionNombreWidget:
        icono_nombre = QIcon("icons\\truck.svg")

        nombre_stylesheet = """
            QLabel {
                color: rgb(15, 15, 15);
            }
        """

        def __init__(self, nombre: str):
            self.nombre_layout = QHBoxLayout()

            self.icono_label = QLabel()
            self.icono_label.setPixmap(self.icono_nombre.pixmap(20))
            self.icono_label.setMinimumHeight(20)

            self.nombre_label = QLabel()
            self.nombre_label.setTextFormat(Qt.TextFormat.MarkdownText)
            self.nombre_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self.nombre_label.setMinimumHeight(20)
            self.nombre_label.setText(f"### {nombre}")
            self.nombre_label.setStyleSheet(self.nombre_stylesheet)

            self.nombre_layout.setSpacing(5)
            self.nombre_layout.addWidget(self.icono_label)
            self.nombre_layout.addWidget(self.nombre_label, 70)

        def layout(self):
            return self.nombre_layout

        def setNombre(self, nombre: str):
            self.nombre_label.setText(f"### {nombre}")


class CamionListWidget(QScrollArea):
    camion_enviado = pyqtSignal(str, Camion)
    
    def __init__(self, ruteo: bool = False) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.widgets_camiones: list[CamionWidget] = []
        self.ruteo = ruteo
    
        self.list_widget = QWidget()
        
        self.vbox_layout = QVBoxLayout(self.list_widget)
        self.vbox_layout.setContentsMargins(2, 2, 2, 2)
        self.vbox_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.vbox_layout.setSpacing(2)
        self.list_widget.setLayout(self.vbox_layout)
        self.setWidget(self.list_widget)

    def addCamion(self, nombre: str, camion: Camion, ruteo: bool = False):
        if nombre not in [x.getCamion()[0] for x in self.widgets_camiones]:
            camion_widget = CamionWidget(nombre, camion, ruteo)
            camion_widget.camion_enviado.connect(self.sendCamion)
            self.widgets_camiones.append(camion_widget)
            self.vbox_layout.addWidget(camion_widget)
    
    def sendCamion(self, nombre, camion):
        if self.ruteo:
            # Si es el ultimo camion, qmessagebox con warning y no emitir
            pass
        
        self.camion_enviado.emit(nombre, camion)
        for widget in self.widgets_camiones:
            if (widget.nombre == nombre):
                self.vbox_layout.removeWidget(widget)
                self.widgets_camiones.remove(widget)
        pass
    
    def toDict(self):
        dict_camiones = {}
        for nombre, camion in [x.getCamion() for x in self.widgets_camiones]:
            dict_camiones[nombre] = camion
        return dict_camiones

