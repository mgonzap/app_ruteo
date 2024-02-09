import sys
from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from urllib.parse import quote
import re

class VentanaNavegador(QMainWindow):
    coordenadas_obtenidas = pyqtSignal(float, float)
    # TODO: arreglar warnings
    def __init__(self, url):
        super().__init__()

        self.setWindowTitle("Selección de Ubicación")
        self.setWindowIcon(QIcon("logo\\WSC-LOGO2.ico"))
        
        self.instructions_label = QLabel()
        self.instructions_label.setText("En caso de que aparezcan múltiples direcciones, elija la que considere correcta.")
        
        self.instructions_label2 = QLabel()
        self.instructions_label2.setText("Luego cierre el panel lateral y coloque el marcador rojo en el medio de la pantalla, en lo posible, con el zoom máximo.")
        
        self.web_view = QWebEngineView()
        self.web_view.load(QUrl(url))

        self.ready_button = QPushButton("Obtener coordenadas")
        self.ready_button.clicked.connect(self.get_current_url)

        layout = QVBoxLayout()
        layout.addWidget(self.instructions_label)
        layout.addWidget(self.instructions_label2)
        layout.addWidget(self.web_view)
        layout.addWidget(self.ready_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def get_current_url(self):
        current_url = self.web_view.url().toString()
        #print("URL resultante:", current_url)
        patron_coordenadas = r'@(-?\d+\.\d+),(-?\d+\.\d+)'
        coincidencias = re.search(patron_coordenadas, current_url)
        if coincidencias:
            lat, long = coincidencias.groups()
            #print("Coordenadas capturadas:", coincidencias.group())
            #print(lat, long)
            self.coordenadas_obtenidas.emit(float(lat), float(long))
            self.close()
        else:
            # TODO: llamar un dialogo para decirle al usuario
            print("No se encontraron coincidencias")

def main():
    app = QApplication(sys.argv)
    direccion = quote("Sendero del adobe, parcela 18e, peñalolen 18, PEÑALOLÉN, METROPOLITANA DE SANTIAGO")
    initial_url = f"https://www.google.com/maps/search/{direccion}"
    browser_window = VentanaNavegador(initial_url)
    browser_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    


