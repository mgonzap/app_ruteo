from modelos_dataframe import *
from vistas_dataframe import *
from ventanas_base import *
from ventana_navegador import VentanaNavegador
from PyQt6.QtWidgets import (
    QVBoxLayout, QLabel
)
from functools import partial
import pandas as pd
import os

class VentanaDespachos(VentanaDataframeEliminacion):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent, "Despachos", 
            safe_to_close=True
        )

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)

        self.label_nombre = QLabel("Aquí se presentan todos los despachos. " + \
            "También es posible eliminar despachos indeseados con clic derecho.")
        self.layout.addWidget(self.label_nombre)
        
        self.view = VistaDataframeEliminacion(self)
        self.layout.addWidget(self.view)
        
        self.layout.addWidget(self.createQPushButton("Finalizar", self.process_deletion))
        
        self.resizeToContents(move_to_center=True)
    

class VentanaDespachosVerificacion(VentanaDataframeEliminacion):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent, "Verificar despachos no gratuitos", 
            safe_to_close=False
        )

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)

        self.label_nombre = QLabel("Aquí se presentan todos los despachos no gratuitos. " + \
            "También es posible eliminar despachos no pagados con clic derecho.")
        self.layout.addWidget(self.label_nombre)
        
        self.proxy_model = ModeloDataframeVerificacion()
        self.view = VistaDataframePagoDespacho(self)
        self.layout.addWidget(self.view)
            
        self.layout.addWidget(self.createQPushButton("Finalizar", self.process_deletion))
        
        self.resizeToContents(move_to_center=True)


class VentanaDespachosCoordenadas(VentanaDataframeEliminacion):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent, "Corregir coordenadas de despacho", 
            safe_to_close=False
        )

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)

        # DESPACHOS A CLIENTE (DIRECCION)
        self.label_nombre = QLabel("Es necesario corregir las siguientes coordenadas. " + \
            "Haga click derecho en la dirección o en los datos de transporte externo para buscar coordenadas:")
        self.layout.addWidget(self.label_nombre)
        
        self.proxy_model = ModeloDataframeCoordenadas(
            [
                "CLIENTE", "DIRECCION", "TELEF. CONTACTO", 
                "N° CARPETA", "LATITUD", "LONGITUD"
            ],
            buscar_externo= False
        )
        self.view: VistaDataframeCoordenadas = VistaDataframeCoordenadas(self, buscar_externo=False)
        self.view.direccion.connect(partial(self.abrir_ventana_navegador, view=self.view))
        self.layout.addWidget(self.view)
        
        self.label_nombre_ext = QLabel(
            "Haga click derecho en los datos de transporte externo para buscar coordenadas:"
        )
        self.layout.addWidget(self.label_nombre_ext)
        
        self.proxy_model_ext = ModeloDataframeCoordenadas(
            [
                "CLIENTE", "DATOS TRANSPORTE EXTERNO", 
                "TELEF. CONTACTO", "N° CARPETA", "LATITUD", "LONGITUD"
            ],
            buscar_externo= True
        )
        self.proxy_model_ext.setSourceModel(self.model)
        self.view_ext = VistaDataframeCoordenadas(self, buscar_externo=True)
        self.view_ext.direccion.connect(partial(self.abrir_ventana_navegador, view=self.view_ext))
        self.view_ext.setModel(self.proxy_model_ext)
        
        self.layout.addWidget(self.view_ext)
        self.layout.addWidget(self.createQPushButton("Finalizar", self.finalizar_edicion))
        
        self.resizeToContents(move_to_center=True)
    
    def abrir_ventana_navegador(self, direccion: str, view: VistaDataframeCoordenadas):
        self.ventana_navegador = VentanaNavegador(None, direccion)
        self.ventana_navegador.coordenadas_obtenidas.connect(view.actualizar_coordenadas)
        self.ventana_navegador.show()
    
    # override para que tome view_ext tambien    
    def resizeToContents(self, move_to_center: bool = False):
        if self.view == None:
            return
        content_height = self.view.getContentHeight()
        ext_height = 0
        if self.view_ext != None:
            ext_height = self.view_ext.getContentHeight()
        screen_size = QGuiApplication.primaryScreen().availableSize()
        content_height +=  ext_height
        height = max(
            350,
            min(screen_size.height(), content_height)
        )
        self.resize(QSize(screen_size.width(), height))
        if move_to_center:
            self.move(
                0, 
                int((screen_size.height() - height)/2)
            )
    
    def finalizar_edicion(self):
        if self.view.coordenadas_invalidas() or self.view_ext.coordenadas_invalidas():
            confirmar = QMessageBox.warning(
                self, "Aviso", 
                "Todavía quedan despachos con coordenadas incorrectas." + \
                    "\n¿Estás seguro de continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirmar == QMessageBox.StandardButton.No:
                return
        self.finished.emit()
        self.guardar_cache_coordenadas()
        self.forceClose()
    
    # TODO: esta es una implementacion rapida, logica pertenece mas al modelo
    def guardar_cache_coordenadas(self):
        if not os.path.exists('cache'):
            os.makedirs('cache')
        cache_list = []
        for row in range(self.view.model().rowCount()):
            lat, long = self.view.getCoords(row)
            # solo guardamos coordenadas validas
            if lat != 0.0 and long != 0.0:
                col_name, dir = self.view.getDireccion(row)
                cache_row = {
                    'DIRECCION': dir if col_name=='DIRECCION' else '',
                    'DATOS TRANSPORTE EXTERNO': dir if col_name=='DATOS TRANSPORTE EXTERNO' else '',
                    'LATITUD': lat,
                    'LONGITUD': long
                }
                cache_list.append(cache_row)
        for row in range(self.view_ext.model().rowCount()):
            lat, long = self.view_ext.getCoords(row)
            # solo guardamos coordenadas validas
            if lat != 0.0 and long != 0.0:
                col_name, dir = self.view_ext.getDireccion(row)
                cache_row = {
                    'DIRECCION': dir if col_name=='DIRECCION' else '',
                    'DATOS TRANSPORTE EXTERNO': dir if col_name=='DATOS TRANSPORTE EXTERNO' else '',
                    'LATITUD': lat,
                    'LONGITUD': long
                }
                cache_list.append(cache_row)
        if len(cache_list) <= 0:
            return
        df_cache = pd.DataFrame(cache_list)
        if os.path.exists('cache/coordenadas.xlsx'):
            df_cache_antiguo = pd.read_excel('cache/coordenadas.xlsx')
            df_cache = pd.concat([df_cache_antiguo, df_cache])
            df_cache = df_cache.drop_duplicates(
                ['DIRECCION', 'DATOS TRANSPORTE EXTERNO'], 
                keep='last', 
                ignore_index=True
            )
        df_cache.to_excel('cache/coordenadas.xlsx', index=False)
    
    # reemplazamos la funcion show para que revise si hay datos que necesiten corrección
    # si no, simplemente se considera la edición finalizada.
    def show(self):
        if self.getDataFrame().empty or (self.view.model() is None and self.view_ext.model() is None) \
                or (self.view.model().rowCount() == 0 and self.view_ext.model().rowCount() == 0):
            self.finalizar_edicion()
        else:
            super(Ventana, self).show()
            

