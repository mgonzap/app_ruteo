from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QCalendarWidget, QPushButton, QWidget, QLabel
from PyQt6.QtCore import QDate, pyqtSignal

class VentanaFecha(QMainWindow):
    fecha_seleccionada = pyqtSignal(str)
    def __init__(self, icono):
        super().__init__()

        self.setWindowTitle("Selección de Fecha")
        self.setWindowIcon(icono)
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()
        
        self.label = QLabel("Por favor seleccione la fecha para buscar entregas.")
        layout.addWidget(self.label)

        self.calendar = QCalendarWidget()
        layout.addWidget(self.calendar)

        self.select_button = QPushButton("Buscar Entregas")
        self.select_button.clicked.connect(self.on_select_date)
        layout.addWidget(self.select_button)

        self.central_widget.setLayout(layout)

    def on_select_date(self):
        selected_date = self.calendar.selectedDate()
        #print("Fecha elegida:", selected_date.toString('dd-MM-yyyy'))
        self.fecha_seleccionada.emit(selected_date.toString('dd-MM-yyyy'))

def main():
    app = QApplication([])
    window = VentanaFecha()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()