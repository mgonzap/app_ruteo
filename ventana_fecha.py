from src.base_classes.base_ventana import BaseVentana
from PyQt6.QtWidgets import (
    QVBoxLayout, QCalendarWidget, QPushButton, QWidget, QLabel
)
from PyQt6.QtCore import pyqtSignal

class VentanaFecha(BaseVentana):
    fecha_seleccionada = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(
            parent= parent,
            title= "Selección de Fecha",
            safe_to_close= False
        )
        self.setGeometry(100, 100, 400, 300)
        self.setCentralWidget(QWidget())

        layout = QVBoxLayout()
        layout.addWidget(
            QLabel("Seleccione la fecha para la cual se buscarán entregas.")
        )

        self.calendar = QCalendarWidget()
        layout.addWidget(self.calendar)

        self.select_button = QPushButton("Buscar Entregas")
        self.select_button.clicked.connect(self.__onDatePicked)
        layout.addWidget(self.select_button)
        
        self.centralWidget().setLayout(layout)

    def __onDatePicked(self):
        selected_date = self.calendar.selectedDate()
        #print("Fecha elegida:", selected_date.toString('dd-MM-yyyy'))
        self.setSafeToClose(True)
        self.fecha_seleccionada.emit(selected_date.toString('dd-MM-yyyy'))
