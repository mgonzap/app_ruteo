import os
import pandas as pd
import numpy as np
from datetime import date
from base_datos import *
import georef
import pytz

# Para procesar datos de query / xlsx
def obtener_dataframe_datos(fecha: str):
    """Procesa datos desde query, realizando un filtro por fecha
    para obtener las filas donde 'FECHA SOLICITUD DESPACHO' corresponda al día de mañana.
    Luego se entregan los datos como DataFrame a georef, quien añade columnas de latitud y longitud.

    Args:
        filename (_type_, opcional): El nombre del archivo xlsx a procesar. Si no hay nombre, es None y se revisa por query.

    Returns:
        pd.DataFrame: Un DataFrame que incluye las columnas de latitud y longitud georreferenciadas.
    """
    
    print("Fecha de hoy:", date.today().strftime('%d-%m-%Y'))
    print("Fecha a filtrar:", fecha)
    
    df = obtener_datos(fecha)
    
    if df.empty:
        return df
    
    try:
        df.to_excel('test/excel_procesado.xlsx', index=False)
    except PermissionError:
        print("No se pudo escribir 'test/excel_procesado.xlsx', permiso denegado.")
    
    # retiros directamente en bodega, por lo tanto no lo georreferenciamos
    # Filtrar y guardar en su propio DataFrame
    df_retiros = df[df["TIPO DE ENTREGA"].isin(['RETIRA TRANS.EXTERNO', 'RETIRA CLIENTE'])]
    try:
        if not os.path.exists('retiros'):
            os.makedirs('retiros')
        df_retiros.to_excel(f"retiros/retiros-{fecha}.xlsx", index=False)
    except PermissionError:
        print(f"No se pudo escribir 'retiros/retiros-{fecha}.xlsx', permiso denegado.")
    
    df = df[~df["TIPO DE ENTREGA"].isin(['RETIRA TRANS.EXTERNO', 'RETIRA CLIENTE'])]
    
    # para poder concatenar los n de SERVICIO de las entregas agrupadas.
    df.to_excel('test/pre_agrupar.xlsx', index=False)
    df['SERVICIO'] = df['SERVICIO'].astype(str)
    df = agrupar_entregas(df)
    df.to_excel('test/post_agrupar.xlsx', index=False)
    
    # Procesamos los datos mediante georef
    # obteniendo un DataFrame que incluye coordenadas asociadas a direccion
    df.reset_index(drop=True, inplace=True)
    df = georef.pasar_a_coordenadas(df)
    return df

def obtener_dataframe_entregas_clientes(fecha: str, lista_clientes: list[str], df_principal: pd.DataFrame):
    """Procesa datos desde query, realizando un filtro por fecha
    para obtener las filas donde 'FECHA SOLICITUD DESPACHO' corresponda al día de mañana.
    Luego se entregan los datos como DataFrame a georef, quien añade columnas de latitud y longitud.

    Args:
        filename (_type_, opcional): El nombre del archivo xlsx a procesar. Si no hay nombre, es None y se revisa por query.

    Returns:
        pd.DataFrame: Un DataFrame que incluye las columnas de latitud y longitud georreferenciadas.
    """
    
    print("Fecha de hoy:", date.today().strftime('%d-%m-%Y'))
    print("Fecha a filtrar:", fecha)
    print("Lista de clientes:", lista_clientes)
    
    df = obtener_entregas_clientes(fecha, lista_clientes, df_principal)
    
    if df.empty:
        return df
    
    try:
        df.to_excel('test/excel_procesado_clientes.xlsx', index=False)
    except PermissionError:
        print("No se pudo escribir 'test/excel_procesado_clientes.xlsx', permiso denegado.")
    
    # retiros directamente en bodega, por lo tanto no lo georreferenciamos
    # Filtrar y guardar en su propio DataFrame
    df_retiros = df[df["TIPO DE ENTREGA"].isin(['RETIRA TRANS.EXTERNO', 'RETIRA CLIENTE'])]
    try:
        if not os.path.exists('retiros'):
            os.makedirs('retiros')
        df_retiros.to_excel(f"retiros/retiros-{fecha}-clientes.xlsx", index=False)
    except PermissionError:
        print(f"No se pudo escribir 'retiros/retiros-{fecha}-clientes.xlsx', permiso denegado.")
    
    df = df[~df["TIPO DE ENTREGA"].isin(['RETIRA TRANS.EXTERNO', 'RETIRA CLIENTE'])]
    
    # para poder concatenar los n de SERVICIO de las entregas agrupadas.
    df.to_excel('test/pre_agrupar_clientes.xlsx', index=False)
    df['SERVICIO'] = df['SERVICIO'].astype(str)
    df = agrupar_entregas(df)
    df.to_excel('test/post_agrupar_clientes.xlsx', index=False)
    
    # Procesamos los datos mediante georef
    # obteniendo un DataFrame que incluye coordenadas asociadas a direccion
    df.reset_index(drop=True, inplace=True)
    df = georef.pasar_a_coordenadas(df)
    return df

def agrupar_entregas(df: pd.DataFrame):
    # TODO: ahora agruparemos por DIRECCIÓN y CLIENTE, concatenamos todo lo q no sea BULTOS VOLUMEN PESO

    # La entrega que tenga N° CARPETA != None es la 'principal'.
    # Las demas deberian coincidir en direccion, comuna, cliente
    cuenta_repeticiones = df['DIRECCION'].value_counts()
  
    direcciones_repetidas = cuenta_repeticiones.loc[cuenta_repeticiones > 1].index.tolist()
    #print("direcciones repetidas:", direcciones_repetidas)
    if len(direcciones_repetidas) == 0:
      return df
    
    df_duplicados = df[df['DIRECCION'].isin(direcciones_repetidas)]
    print(df_duplicados)
    df_con_carpeta = df_duplicados[df_duplicados['N° CARPETA'].notna()]
    print(df_con_carpeta)
    
    filas = []
    # Mantenemos la fila que tenga su N° CARPETA, los otros se agrupan a el, mientras coincidan en direccion, etc
    # TODO: no usar iterrows, muy lento
    idx_eliminados = []
    for idx, fila in df_con_carpeta.iterrows():
        if idx in idx_eliminados:
            continue
        # Elementos pueden estar duplicados
        # queremos todos los elementos que tengan 'DIRECCION', 'COMUNA' y 'CLIENTE'
        # con el mismo valor que el elemento que estamos revisando.
        similares = df[(df['DIRECCION'] == fila['DIRECCION'])
                       & (df['COMUNA'] == fila['COMUNA'])
                       & (df['CLIENTE'] == fila['CLIENTE'])]
        
        if similares.empty:
            continue

        # si se encuentran elementos así, se suma 'N° BULTOS', 'PESO' y 'VOLUMEN'
        # similares no debería ser empty nunca, puesto que siempre estará el elemento mismo
        # para evitar duplicados:
        # TODO: quizas hacer cat y split es innecesario
        lista_carpetas = ','.join(list(set(similares['N° CARPETA'].str.cat(sep=',').split(','))))
        lista_ejecutivos = ','.join(list(set(similares['EJECUTIVO'].str.cat(sep=',').split(','))))
        lista_servicios = ','.join(list(set(similares['SERVICIO'].str.cat(sep=',').split(','))))
        
        fila['N° CARPETA'] = lista_carpetas
        fila['EJECUTIVO'] = lista_ejecutivos
        fila['SERVICIO'] = lista_servicios
        fila['N° BULTOS'] = similares['N° BULTOS'].sum()
        fila['VOLUMEN'] = similares['VOLUMEN'].sum()
        fila['PESO'] = similares['PESO'].sum()
        
        df = df.drop(similares.index)
        idx_eliminados += similares.index.tolist()
        filas.append(fila)
  
    df_filas = pd.DataFrame(filas, columns=df.columns)
    df = pd.concat([df, df_filas])
    return df

def obtener_datos(fecha_filtrado: str) -> pd.DataFrame:
    df_query = query_datos(fecha_filtrado)
    
    return procesar_query(df_query)

def obtener_entregas_clientes(fecha_filtrado: str, lista_clientes: list[str], df_original) -> pd.DataFrame:
    df_query = query_despachos_clientes(fecha_filtrado, lista_clientes)

    df = procesar_query(df_query)
    
    if df.empty:
        return df
    
    # obtenemos filas sin direccion ni datos transporte externo.
    filas_sin_direccion = df[(df['DIRECCION'] == ' , , ') & (df['DATOS TRANSPORTE EXTERNO'] == 'NO APLICA')]
    
    # TODO: lento, cambiar a algo mas eficiente
    for idx, row in filas_sin_direccion.iterrows():
        # buscamos la direccion asociada a otros despachos del mismo cliente
        mismo_cliente = df_original[df_original['CLIENTE'] == row['CLIENTE']]
        row[['TIPO DE ENTREGA', 'DIRECCION', 'COMUNA', 'DATOS TRANSPORTE EXTERNO']] = mismo_cliente.iloc[0][['TIPO DE ENTREGA', 'DIRECCION', 'COMUNA', 'DATOS TRANSPORTE EXTERNO']]
        # la aplicamos
        df.iloc[idx] = row
    
    return df
    
def procesar_query(df_query: pd.DataFrame) -> pd.DataFrame:
    """Recibe un DataFrame construido desde una query a la base de datos y la procesa.

    Returns:
        pd.DataFrame: un DataFrame conteniendo los datos procesados de la query
    """  
    
    # timezone Chile
    tz_chile = pytz.timezone('Chile/Continental')
    
    def convertir_a_tz_chile(x):
        if pd.notna(x):
            return x.astimezone(tz_chile).tz_localize(None)
        else:
            return x
    # al recibir las fechas están en UTC, por lo que hay que pasarlas
    # a timezone chileno (generalmente -03:00) para convertir df a excel
    lista_columnas_fecha = [
        'fecha_llegada', 
        'fecha_desconsolidado',
        'fecha_despacho_retiro', 
        'fecha_fin_despacho_retiro', 
        'fecha_entrega', 
        'fecha_programada',
        'fecha_registro'
    ]
    
    for col in lista_columnas_fecha:
        if (df_query[col].dtype != np.dtype('datetime64[ns]')):
            df_query[col] = pd.to_datetime(df_query[col], utc=True)
    
    for col in df_query.select_dtypes(include=['datetime64[ns, UTC]']).columns:
        df_query[col] = df_query[col].apply(convertir_a_tz_chile)
    
    if df_query.empty:
        return df_query
      
    try:
        query_excel_path = 'test/excel_query.xlsx'
        if not os.path.exists(query_excel_path):
            os.makedirs(query_excel_path)
        df_query.to_excel(query_excel_path, index=False)
    except PermissionError:
        print("No se pudo acceder a test/excel_query.xlsx, permiso denegado.")

    # no generamos el DataFrame hasta que tengamos la lista realizada, pues
    # utilizar concat repetidamente es lento.
    columnas = df_query.columns.tolist()
    agrupado = []
    
    # nos deshacemos de duplicados. criterio es igualdad de n_servicio, ctidad bultos, peso y volumen
    df_query = df_query.sort_values(by='fecha_despacho_retiro', ascending=False)
    df_query = df_query.drop_duplicates(subset=['cantidad_bultos', 'peso', 
                                                'volumen', 'fk_consolidado'], keep='first')
    while not df_query.empty:
        fila = df_query.iloc[0].copy()
        # todos los elementos que tengan 'fk_consolidado', 'fk_proforma' y 'fk_cliente'
        # con el mismo valor que el elemento que estamos revisando.
        
        # TODO: similares puede contener posibles duplicados
        similares = df_query[(df_query['fk_consolidado'] == fila['fk_consolidado'])
                            & (df_query['fk_proforma'] == fila['fk_proforma'])
                            & (df_query['fk_cliente'] == fila['fk_cliente'])]

        # si se encuentran elementos así, se suma 'cantidad_bultos', 'peso' y 'volumen'
        # similares no debería ser empty nunca, puesto que siempre estará el elemento mismo
        fila['cantidad_bultos'] = similares['cantidad_bultos'].sum()
        fila['peso'] = similares['peso'].sum()
        fila['volumen'] = similares['volumen'].sum()
            
        df_query = df_query.drop(similares.index)
            
        agrupado.append(fila)

    # Ahora sí generamos el DataFrame
    df_agrupado = pd.DataFrame(agrupado, columns=columnas)
    
    # ciertas columnas necesitan procesamiento
    
    # ETA
    df_agrupado['fecha_llegada'] = df_agrupado['fecha_llegada'].apply(
        lambda fecha: fecha.strftime('%d-%m-%Y') if pd.notna(fecha)
        else "S/I"
    )
    
    # F.DESCONSOLIDADO
    df_agrupado['fecha_desconsolidado'] = df_agrupado['fecha_desconsolidado'].apply(
        lambda fecha: fecha.strftime('%d-%m-%Y') if pd.notna(fecha)
        else "S/I"
    )
    
    # estado_entrega (1 = 'TOTAL', 2 = 'PARCIAL', otro = 'S/I')
    df_agrupado['estado_entrega'] = df_agrupado['estado_entrega'].apply(
        lambda x: 'TOTAL' if x == 1 
        else 'PARCIAL' if x == 2 
        else 'S/I'
    )
    
    # estado_pago ('OK', 'NO', 'PENDIENTE FINANZAS')
    df_agrupado['estado_pago'] = df_agrupado['estado_pago'].apply(
        lambda x: 'PENDIENTE FINANZAS' if pd.isna(x)
        else 'OK' if x.upper() == 'SI'
        else 'NO' if x.upper() == 'NO'
        else x
    )
    
    comunas_no_incluidas_stgo = [49, 50, 51, 53, 57, 59, 61, 62, 64, 65, 66, 69, 71, 72, 76, 82, 88, 91]
    # generamos nueva columna llamada tipo_de_entrega
    df_agrupado['tipo_de_entrega'] = df_agrupado[['empresa_ext_despacho', 'empresa_ext_retiro', 'fk_bodega', 'fk_region', 'fk_comuna']].apply(
      lambda fila: 'DESPACHO TRANS.EXTERNO' if pd.notna(fila['empresa_ext_despacho']) # != null
        else 'RETIRA TRANS.EXTERNO' if pd.notna(fila['empresa_ext_retiro']) # != null
        else 'RETIRA CLIENTE' if pd.notna(fila['fk_bodega']) # != null
        else 'SIN ESPECIFICAR' if pd.isna(fila['fk_region']) # == null
        else 'DESPACHO GRATIS INCLUIDO' if (fila['fk_region'] == 12 and fila['fk_comuna'] not in comunas_no_incluidas_stgo) # == 12
        else 'REVISAR DESPACHO GRATUITO NO INCLUIDO' if (fila['fk_region'] == 12 and fila['fk_comuna'] in comunas_no_incluidas_stgo)
        else 'SIN ESPECIFICAR'
    , axis=1)
    
    # 'QUIEN PROGRAMA'
    df_agrupado['quien'] = df_agrupado[['fk_usuario_despacho_retiro_nombre', 'fk_usuario_despacho_retiro_apellidos']].apply(
        lambda fila: f"{fila['fk_usuario_despacho_retiro_nombre'].strip()} {fila['fk_usuario_despacho_retiro_apellidos'].strip()}" 
        if pd.notna(fila['fk_usuario_despacho_retiro_apellidos']) and pd.notna(fila['fk_usuario_despacho_retiro_nombre'])
        else f"{fila['fk_usuario_despacho_retiro_nombre'].strip()}" if pd.notna(fila['fk_usuario_despacho_retiro_nombre'])
        else 'S/I'
    , axis=1)
    
    # CLIENTE
    df_agrupado['cliente'] = df_agrupado[['fk_cliente', 'fk_cliente_razon_social']].apply(
        lambda fila: f"({fila['fk_cliente']}) {fila['fk_cliente_razon_social'].strip()}"
    , axis=1)
    
    
    # FECHA SOLICITUD DESPACHO
    df_agrupado['fecha_solicitud'] = df_agrupado[['fecha_despacho_retiro', 'fecha_fin_despacho_retiro']].apply(
        lambda fila: f"{fila['fecha_despacho_retiro'].strftime('%d-%m-%Y %H:%M')} / {fila['fecha_fin_despacho_retiro'].strftime('%H:%M')}" 
        if pd.notna(fila['fecha_fin_despacho_retiro']) and pd.notna(fila['fecha_despacho_retiro'])
        else f"{fila['fecha_despacho_retiro'].strftime('%d-%m-%Y')}" if pd.notna(fila['fecha_despacho_retiro'])
        else "S/I"
    , axis=1)

    # FECHA PROG DESPACHO
    df_agrupado['fecha_programada'] = df_agrupado['fecha_programada'].apply(
        lambda fecha: fecha.strftime('%d-%m-%Y %H:%M') if pd.notna(fecha)
        else 'S/I'
    )
    
    # DATOS CONTACTO RETIRO
    df_agrupado['retiro'] = df_agrupado[['rut_retiro', 'nombre_retiro', 'patente_retiro']].apply(
        lambda fila: f"{fila['rut_retiro'].strip()}, {fila['nombre_retiro'].strip()}, {fila['patente_retiro'].strip()}"
        if pd.notna(fila['rut_retiro']) or pd.notna(fila['nombre_retiro']) or pd.notna(fila['patente_retiro']) # se aplica or para que solo no printee
        else "NO APLICA"                                                                                       # en caso de que no haya ningun dato
    , axis=1)
    
    # DATOS TRANSPORTE EXTERNO
    df_agrupado['emp_ext'] = df_agrupado[['empresa_ext_despacho', 'fk_direccion_empresa_ext', 'empresa_ext_retiro']].apply(
        lambda fila: f"{fila['empresa_ext_despacho']} | {fila['fk_direccion_empresa_ext']}" if pd.notna(fila['empresa_ext_despacho'])
        else fila['empresa_ext_retiro'] if pd.notna(fila['empresa_ext_retiro'])
        else 'NO APLICA'
    , axis=1)
    
    # FECHA ENTREGA
    df_agrupado['fecha_entrega'] = df_agrupado['fecha_entrega'].apply(
        lambda x: x.strftime('%d-%m-%Y') if pd.notna(x)
        else 'S/I'
    )
    
    # CONDUCTOR
    # conductor_nombre, conductor_apellido
    df_agrupado['conductor'] = df_agrupado[['conductor_nombre', 'conductor_apellido']].apply(
        lambda fila: f"{fila['conductor_nombre'].strip()} {fila['conductor_apellido'].strip()}" if pd.notna(fila['conductor_nombre']) and pd.notna(fila['conductor_apellido'])
        else f"{fila['conductor_nombre'].strip()}" if pd.notna(fila['conductor_nombre'])
        else 'S/I'
    , axis=1)
    
    # al final queremos un DataFrame igual al excel de programacion de despacho que se está generando actualmente
    
    
    df_final = pd.DataFrame()
    columnas_final = ['NAVE', 'CONTENEDOR', 'ETA', 'F.DESCONSOLIDADO',
                      'N° CARPETA', 'ESTADO PAGO', 'TIPO DE ENTREGA', 'SERVICIO', 
                      'EJECUTIVO', 'N° BULTOS', 'VOLUMEN', 'PESO', 
                      'QUIEN PROGRAMA', 'DIRECCION', 'COMUNA', 'CONTACTO', 
                      'TELEF. CONTACTO', 'CLIENTE', 'FECHA SOLICITUD DESPACHO', 'FECHA PROG DESPACHO', 
                      'FECHA ENTREGA', 'DATOS CONTACTO RETIRO', 'DATOS TRANSPORTE EXTERNO', 'OBS.CLIENTE', 
                      'ESTADO DE ENTREGA', 'OBSERVACIONES', 'CONDUCTOR', 'FECHA INGRESO', 'fecha_despacho_retiro', 'fk_cliente']
    
    columnas_agrupado = ['nave_nombre', 'contenedor', 'fecha_llegada', 'fecha_desconsolidado', 
                         'n_carpeta', 'estado_pago', 'tipo_de_entrega', 'fk_consolidado',
                         'fk_comercial_nombre', 'cantidad_bultos', 'volumen', 'peso', 
                         'quien', 'fk_direccion_completa', 'fk_comuna_nombre', 'nombre_contacto', 
                         'telefono_contacto', 'cliente', 'fecha_solicitud', 'fecha_programada',
                         'fecha_entrega', 'retiro', 'emp_ext', 'obs_cliente', 
                         'estado_entrega', 'observaciones', 'conductor', 'fecha_registro', 'fecha_despacho_retiro', 'fk_cliente']
    
    df_final[columnas_final] = df_agrupado[columnas_agrupado]
    
    return df_final
