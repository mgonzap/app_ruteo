# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 17:01:53 2023

@author: Ignacio Carvajal
"""

# georreferenciacion
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
import os

# Recibe un dataframe filtrado por fecha, a partir del cual genera latitud y longitud para las direcciones
# Guardando los resultados del nuevo Dataframe dentro de un excel y tambien retorna el df con las coordenadas agregadas
def pasar_a_coordenadas(df_filtrado):
    """Genera latitud y longitud para direcciones obtenidas desde un DataFrame
    
    Guardando los resultados del nuevo Dataframe dentro de un excel y tambien retorna el df con las coordenadas agregadas

    Argumentos:
        df_filtrado (pandas.DataFrame): DataFrame con columna "DIRECCION"
        test_prints (bool, optional): Si se printean las latitudes y longitudes que se van generando, False por defecto.

    Retorna:
        pandas.Dataframe: retorna el DataFrame recibido con columnas agregadas de "LATITUD" y "LONGITUD"
    """    """"""
    
    # agregamos las columnas de coordenadas con valor 0.0 por defecto
    df_filtrado['LATITUD'] = 0.0
    df_filtrado['LONGITUD'] = 0.0
    
    cache_path = 'cache/coordenadas.xlsx'
    df_filtrado = cargar_cache(df_filtrado, cache_path)
    
    bodega = "Camino a noviciado 1945, Bodega 19, Pudahuel, Región Metropolitana"
    # Crea una instancia de Nominatim
    geolocator = Nominatim(user_agent="myGeoco", timeout=50)
    # Define la función de limitación de velocidad
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=3)
    
    # Realiza la geocodificación
    #location = geocode(f"{calle}, {ciudad}")
    latitudes = []
    longitudes = []
    
    # Si comuna está en Santiago, usar 'DIRECCION' para coordenadas.
    # En caso contrario, usar 'DATOS TRANSPORTE EXTERNO', pero se debe formatear el string
    # estos strings vienen la mayoría en formato 'NOMBRE_EXTERNO | DIRECCION', sin embargo
    # existe una excepción que es TVP.
    df_geo = df_filtrado[(df_filtrado['LATITUD'] == 0.0) | (df_filtrado['LONGITUD'] == 0.0)]
    print("rows a georef:", df_geo.shape[0])
    
    dict_dir = None
    new_cache_rows = []
    cache_cols = ['DIRECCION', 'DATOS TRANSPORTE EXTERNO', 'LATITUD', 'LONGITUD']
    for direccion, datos_externo in zip(df_geo["DIRECCION"], df_geo["DATOS TRANSPORTE EXTERNO"]):
        dir_string = direccion
        ext_string = datos_externo
        
        if datos_externo != "NO APLICA":
            dir_string = ''
            datos_externo = datos_externo.split('|')

            try:
                datos_externo = datos_externo[1]
                dict_dir = direccion_a_dict(datos_externo)
            except IndexError:
                datos_externo = datos_externo[0]
                dict_dir = datos_externo
        else:
            ext_string = ''
            dict_dir = direccion_a_dict(direccion)

        location = geocode(dict_dir, country_codes="CL")
        
        if location is not None:
            latitud = location.latitude
            longitud = location.longitude
            latitudes.append(latitud)
            longitudes.append(longitud)
            
            dir_row = [dir_string, ext_string, latitud, longitud]
            new_cache_rows.append(dir_row)
            
        else:
            # Idea sería cambiar por S/I pero da error con app_ruteo.ejecutar_modelo(), pues necesita floats
            latitud = 0.00
            longitud = 0.00
            
            latitudes.append(latitud)
            longitudes.append(longitud)
    
    df_geo.loc[:, "LATITUD"] = latitudes
    df_geo.loc[:, "LONGITUD"] = longitudes
    
    # cargamos al df original coordenadas obtenidas en georef
    for idx_geo in df_geo.index:
        df_filtrado.loc[idx_geo, ["LATITUD", "LONGITUD"]] = df_geo.loc[idx_geo, ["LATITUD", "LONGITUD"]]
    
    # Guardamos el cache como un archivo excel
    df_cache = pd.DataFrame(data=new_cache_rows, columns=cache_cols)
    if os.path.exists(cache_path):
        df_cache_antiguo = pd.read_excel(cache_path)
        if df_cache.empty:
            df_cache = df_cache_antiguo
        else:
            df_cache = pd.concat([df_cache_antiguo, df_cache])
            df_cache = df_cache.drop_duplicates(
                ['DIRECCION', 'DATOS TRANSPORTE EXTERNO'], 
                keep='last', 
                ignore_index=True
            )
    df_cache.to_excel(cache_path, index=False)
    
    return df_filtrado

# Nominatim tiene 2 formas de hacer query, normal sin estructura, y una estructurada
# La estructurada corresponde a recibir un diccionario con parametros, los que nos interesan son:
#     street:  housenumber and streetname
#       city:  city
#      state:  state
#    country:  country
# las direcciones, ya sean de empresa ext o no, vienen en el siguiente formato:
# dir.direccion,' ',dir.numero,', ',comunas.nombre,', ',region.nombre
# tdr.calle_empresa_ext,' ',tdr.numeracion_empresa_ext,', ',comunas2.nombre,', ',region2.nombre
def direccion_a_dict(dir: str) -> dict:
    data = dir.split(", ")
    dict_dir = {
        'street': ", ".join(data[:-2]).strip(),
        'city': data[-2].strip(),
        'state': data[-1].strip(),
        'country': 'Chile'
    }
    return dict_dir

def cargar_cache(df: pd.DataFrame, cache_path: str) -> pd.DataFrame:
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
        return df
    
    print("df rows:", df.shape[0])
    df_cached = pd.read_excel(cache_path)
    # TODO: iterrows es lento, cuando despachos escalen se debe cambiar a algo mas eficiente
    # quizas itertuples
    cache_hits = 0
    for idx, fila in df_cached.iterrows():
        df_temp = df[
            (df['DIRECCION'] == fila['DIRECCION']) | 
            (df['DATOS TRANSPORTE EXTERNO'] == fila['DATOS TRANSPORTE EXTERNO'])
        ]
        # TODO: for dentro de un for, esencial cambiar a metodo mas eficiente
        for idx_temp in df_temp.index:
            df.loc[idx_temp, ['LATITUD', 'LONGITUD']] = df_cached.loc[idx, ['LATITUD', 'LONGITUD']]
            cache_hits += 1
    print("cache hits:", cache_hits)
    return df
