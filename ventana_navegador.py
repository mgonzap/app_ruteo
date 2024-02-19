from ventanas_base import Ventana
from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QWidget, QLabel, QMessageBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from urllib.parse import quote
import re

class VentanaNavegador(Ventana):
    coordenadas_obtenidas = pyqtSignal(float, float)
    # TODO: arreglar warnings
    def __init__(self, parent: QWidget | None = None, direccion: str=''):
        super().__init__(
            parent,
            title= "Selección de Ubicación",
            safe_to_close= True
        )
        
        self.instruction_label = QLabel(
            "En caso de que aparezcan múltiples direcciones, elija la que considere correcta."
        )
        self.instruction_label2 = QLabel(
            "Luego cierre el panel lateral y coloque el marcador rojo en el medio de la pantalla, en lo posible, con el zoom máximo."
        )
        
        self.web_view = QWebEngineView()
        self.web_view.load(QUrl(f'https://www.google.com/maps/search/{quote(direccion)}'))

        self.ready_button = QPushButton("Obtener coordenadas")
        self.ready_button.clicked.connect(self.getCurrentUrl)

        layout = QVBoxLayout()
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.instruction_label2)
        layout.addWidget(self.web_view)
        layout.addWidget(self.ready_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        screen_size = QGuiApplication.primaryScreen().availableSize()
        
        self.move(
            int((screen_size.width() - self.size().width())/2),
            int((screen_size.height() - self.size().height())/2)
        )

    def getCurrentUrl(self):
        current_url = self.web_view.url().toString()
        #print("URL resultante:", current_url)
        patron_coordenadas = r'@(-?\d+\.\d+),(-?\d+\.\d+)'
        coincidencias = re.search(patron_coordenadas, current_url)
        if coincidencias:
            lat, long = coincidencias.groups()
            self.coordenadas_obtenidas.emit(float(lat), float(long))
            self.close()
        else:
            QMessageBox.warning(
                self, "Selección de Ubicación",
                "No se pudieron capturar las coordenadas, inténtelo de nuevo.\n" + \
                    "Si el error persiste, cierre el mapa y ábralo nuevamente. "
            )


