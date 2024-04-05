from ventanas_base import Ventana, VentanaDataframe
from ventana_ruteo import VentanaRuteo
from ventana_fecha import VentanaFecha
from ventanas_despachos import (
    VentanaDespachosVerificacion,
    VentanaDespachosCoordenadas,
    VentanaDespachosClientesVerificacion,
)
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from utils_qt import ConfirmDialog, DataThread, EntregasClientesThread
import sys
import pandas as pd
from procesamiento_datos import agrupar_entregas

# Aqui se crea la aplicacion principal
# Coordina la transmision de datos/signals entre distintas ventanas

class MainApp(QApplication):
    def __init__(self):
        super(QApplication, self).__init__(["AppRuteo"])
        Ventana.setIcon(QIcon("logo\\WSC-LOGO2.ico"))
        
        self.icono = QIcon("logo\\WSC-LOGO2.ico")
        self.ventana_fecha = VentanaFecha()
        self.ventana_fecha.fecha_seleccionada.connect(self.__on_fecha_elegida)
        self.ventana_fecha.show()
        
    def __on_fecha_elegida(self, fecha):
        VentanaDataframe.setFecha(fecha)
        # iniciamos worker thread encargado de obtener los datos
        self.worker_thread = DataThread(fecha)
        self.worker_thread.finished.connect(self.__on_datos_recibidos)
        self.worker_thread.start()
        
        self.confirmar_data = ConfirmDialog(
            titulo = "Procesando Datos",
            texto = "Por favor espere, obteniendo y procesando los datos necesarios...",
            texto_confirmar = "¿Estás seguro de que quieres cerrar la aplicación?"
        )
        self.confirmar_data.salida_confirmada.connect(sys.exit)
        
        self.ventana_fecha.close()
        self.confirmar_data.exec()
    
    def __on_datos_recibidos(self, df):
        VentanaDataframe.setDataFrame(df)
        if VentanaDataframe.getDataFrame().empty:
            msg = QMessageBox(
                QMessageBox.Icon.Critical,
                "Error", "No se han encontrado despachos para la fecha indicada. La aplicación se cerrará."
            )
            msg.setWindowIcon(Ventana.getIcon())
            msg.exec()
            sys.exit()
        self.confirmar_data.close_directly()
        
        self.worker_thread = EntregasClientesThread(
            VentanaDataframe.getFecha(), 
            VentanaDataframe.getDataFrame()['fk_cliente'].unique().tolist(),
            VentanaDataframe.getDataFrame()
        )
        self.worker_thread.finished.connect(self.__on_datos_cliente_recibidos)
        self.worker_thread.start()
        
        self.confirmar_data_clientes = ConfirmDialog(
            titulo = "Procesando Datos",
            texto = "Por favor espere, obteniendo y procesando los datos necesarios...",
            texto_confirmar = "¿Estás seguro de que quieres cerrar la aplicación?"
        )
        self.confirmar_data_clientes.salida_confirmada.connect(sys.exit)
        self.confirmar_data_clientes.exec()
        return

    def __on_datos_cliente_recibidos(self, df):
        VentanaDataframe.setClientesDataFrame(df)
        self.confirmar_data_clientes.close_directly()
        if VentanaDataframe.getClientesDataFrame().empty:
            self.__on_despachos_clientes_verificados()
            return
        self.ventana_entregas_clientes = VentanaDespachosClientesVerificacion()
        self.ventana_entregas_clientes.finished.connect(self.__on_despachos_clientes_verificados)
        self.ventana_entregas_clientes.show()
    
    def __on_despachos_clientes_verificados(self):
        # TODO: Combinar DF clientes con DF principal. Evitar duplicados.
        if not VentanaDataframe.getClientesDataFrame().empty:
            new_df = pd.concat([
                VentanaDataframe.getDataFrame(),
                VentanaDataframe.getClientesDataFrame()
            ])
            new_df = agrupar_entregas(new_df)
            VentanaDataframe.setDataFrame(new_df)
        self.ventana_tipo_despacho = VentanaDespachosVerificacion()
        self.ventana_tipo_despacho.finished.connect(self.__on_despachos_verificados)
        self.ventana_tipo_despacho.show()
    
    def __on_despachos_verificados(self):
        # TODO: generar aqui la ventana de despachos por cliente
        self.ventana_coordenadas = VentanaDespachosCoordenadas()
        self.ventana_coordenadas.finished.connect(self.__on_coordenadas_corregidas)
        self.ventana_coordenadas.show()
    
    def __on_coordenadas_corregidas(self):
        self.ventana_principal = VentanaRuteo()
        self.ventana_principal.show()

if __name__ == "__main__":
    print("Ejecutando aplicación de ruteo...")
    app = MainApp()
    sys.exit(app.exec())