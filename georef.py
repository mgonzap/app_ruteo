# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 17:01:53 2023

@author: Ignacio Carvajal
"""

# georreferenciacion
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Recibe un dataframe filtrado por fecha, a partir del cual genera latitud y longitud para las direcciones
# Guardando los resultados del nuevo Dataframe dentro de un excel y tambien retorna el df con las coordenadas agregadas
def pasar_a_coordenadas(df_filtrado, test_prints=False):
    """Genera latitud y longitud para direcciones obtenidas desde un DataFrame
    
    Guardando los resultados del nuevo Dataframe dentro de un excel y tambien retorna el df con las coordenadas agregadas

    Argumentos:
        df_filtrado (pandas.DataFrame): DataFrame con columna "DIRECCION"
        test_prints (bool, optional): Si se printean las latitudes y longitudes que se van generando, False por defecto.

    Retorna:
        pandas.Dataframe: retorna el DataFrame recibido con columnas agregadas de "LATITUD" y "LONGITUD"
    """    """"""
    
    if test_prints:
        print("Este es el inicio del programa georef.")
        #print(df_filtrado["DIRECCION"])
    
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
    
    dict_dir = None
    for direccion, datos_externo in zip(df_filtrado["DIRECCION"], df_filtrado["DATOS TRANSPORTE EXTERNO"]):
        #print(datos_externo)
        if datos_externo != "NO APLICA":
            # TODO: formatear bien para preguntar, split por |
            datos_externo = datos_externo.split('|')
            #print("Georreferencia a transporte externo")
            try:
                datos_externo = datos_externo[1]
                dict_dir = direccion_a_dict(datos_externo)
            except IndexError:
                datos_externo = datos_externo[0]
                dict_dir = datos_externo
        else:
            dict_dir = direccion_a_dict(direccion)

        location = geocode(dict_dir, country_codes="CL")
        
        if location is not None:
            latitud = location.latitude
            longitud = location.longitude
            latitudes.append(latitud)
            longitudes.append(longitud)
            
        else:
            # Idea sería cambiar por S/I pero da error con app_ruteo.ejecutar_modelo(), pues necesita floats
            latitud = 0.00
            longitud = 0.00
            
            latitudes.append(latitud)
            longitudes.append(longitud)
    
    # para testing, eliminar return despues    
    #return

    if test_prints:
        print(latitudes)
        print(longitudes)
        print(list(df_filtrado["VOLUMEN"]))
    
    df_filtrado["LATITUD"] = latitudes
    df_filtrado["LONGITUD"] = longitudes
    
    # Supongamos que 'df' es tu DataFrame con las coordenadas
    # Por ejemplo, df = pd.DataFrame({'Latitud': latitudes, 'Longitud': longitudes})
    
    # Nombre del archivo Excel de salida
    nombre_archivo = "test/geo_coordenadas.xlsx"
    
    # Guarda el DataFrame como un archivo Excel
    try:
        df_filtrado.to_excel(nombre_archivo, index=False)
        if test_prints:    
            print(f"El DataFrame se ha guardado en '{nombre_archivo}'")

            print(df_filtrado[["DIRECCION", "LATITUD", "LONGITUD"]])
    except PermissionError:
        print(f"No se pudo escribir '{nombre_archivo}', permiso denegado.")
    
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


def actualizar_coordenadas(df_actualizado) -> None:
    nombre_archivo = "test/geo_coordenadas.xlsx"
    try:
        df_actualizado.to_excel(nombre_archivo, index=False)
    except PermissionError:
        print(f"No se pudo escribir '{nombre_archivo}', permiso denegado.")