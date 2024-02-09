from ventana_principal import *
from ventana_fecha import *
from PyQt6.QtGui import QIcon
from qt_material import apply_stylesheet
import sys

# Aqui se crea la aplicacion principal
# Coordina la transmision de datos/signals entre distintas ventanas

class MainApp(QApplication):
    def __init__(self):
        super(QApplication, self).__init__(["AppRuteo"])
        # aplicar tema de libreria qt_material
        #apply_stylesheet(self, theme='dark_blue.xml', css_file='custom.css')
        self.icono = QIcon("logo\\WSC-LOGO2.ico")
        
        self.ventana_fecha = VentanaFecha(self.icono)
        self.ventana_fecha.fecha_seleccionada.connect(self.__on_fecha_elegida)
        self.ventana_fecha.show()
        
    def __on_fecha_elegida(self, fecha):
        self.data_window = VentanaDatos(fecha, self.icono)
        self.data_window.edicion_terminada.connect(self.__on_edicion_terminada)
        self.ventana_fecha.hide()
    
    def __on_edicion_terminada(self, df, df_separados):
        if df.empty and df_separados.empty:
            # TODO: popup/ventana que explique que no hay datos 
            sys.exit()
        try:
            df.to_excel('test/geo_test.xlsx', index=False)
        except PermissionError:
            print("No se pudo escribir 'test/geo_test.xlsx', permiso denegado.")
        self.ventana_principal = VentanaPrincipal(df, df_separados, self.icono)
        self.ventana_principal.show()
        self.ventana_fecha.close()
        #self.data_window.close()
        #print("ventana datos cerrada")
        #print("ventana principal abierta")

if __name__ == "__main__":
    print("Ejecutando main_app")
    app = MainApp()
    sys.exit(app.exec())