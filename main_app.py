from ventana_principal import VentanaPrincipal
from ventana_tablas import VentanaTablas
from ventana_fecha import VentanaFecha
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from utils_qt import ConfirmDialog, DataThread
import sys

# Aqui se crea la aplicacion principal
# Coordina la transmision de datos/signals entre distintas ventanas

class MainApp(QApplication):
    def __init__(self):
        super(QApplication, self).__init__(["AppRuteo"])
        self.icono = QIcon("logo\\WSC-LOGO2.ico")
        
        self.ventana_fecha = VentanaFecha(self.icono)
        self.ventana_fecha.fecha_seleccionada.connect(self.__on_fecha_elegida)
        self.ventana_fecha.show()
        
    def __on_fecha_elegida(self, fecha):
        self.fecha = fecha
        # iniciamos worker thread encargado de obtener los datos
        self.worker_thread = DataThread(fecha)
        self.worker_thread.setTerminationEnabled(True)
        self.worker_thread.finished.connect(self.__on_datos_recibidos)
        self.worker_thread.start()
        
        self.confirmar = ConfirmDialog(
            titulo = "Procesando Datos",
            texto = "Por favor espere, obteniendo y procesando los datos necesarios...",
            texto_confirmar = "¿Estás seguro de que quieres cerrar la aplicación?"
        )
        self.confirmar.salida_confirmada.connect(sys.exit)
        
        self.ventana_fecha.close()
        self.confirmar.exec()
    
    def __on_datos_recibidos(self, df):
        print("datos recibidos")
        print(df)
        if df.empty:
            # TODO: popup/ventana que explique que no hay datos
            print('exiting program')
            sys.exit()
        self.df = df
        self.ventana_tablas = VentanaTablas(self.df, self.icono)
        self.ventana_tablas.edicion_terminada.connect(self.__on_edicion_terminada)
        self.confirmar.close_directly()
        self.ventana_tablas.show()
    
    def __on_edicion_terminada(self, df):
        print('abriendo ventana principal')
        self.ventana_principal = VentanaPrincipal(df, self.fecha, self.icono)
        self.ventana_principal.show()

if __name__ == "__main__":
    print("Ejecutando aplicación de ruteo...")
    app = MainApp()
    sys.exit(app.exec())