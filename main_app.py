from ventana_principal import *
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

        self.data_window = VentanaDatos(self.icono)
        self.data_window.edicion_terminada.connect(self.__on_edicion_terminada)
        self.data_window.show()
    
    def __on_edicion_terminada(self, df):
        print("señal recibida")
        df.to_excel('geo_test.xlsx', index=False)
        self.ventana_principal = VentanaPrincipal(df, self.icono)
        self.ventana_principal.show()
        #self.data_window.close()
        #print("ventana datos cerrada")
        #print("ventana principal abierta")

if __name__ == "__main__":
    print("Ejecutando main_app")
    ### corra el filtro de fecha, luego geo, luego crear entrega con geo.xlsx
    # abrir df de datos de xlsx, filtrar por fecha, pasar a geo
    # geo entrega df con coordenadas, hacer checkeo de las coords
    # si faltan coordenadas, abrir ventana para realizar input de coordenadas
    # checkear que sea coordenada valida (buscar)
    app = MainApp()
    # tomorrow_date = (date.today() + timedelta(days=1)).strftime('%d-%m-%Y')
    sys.exit(app.exec())