import os
import pandas as pd
from datetime import date, timedelta
from base_datos import *
import georef

# Para procesar datos de query / xlsx
# Funcion temporal para cargar excel, idealmente se manejaria por query
def procesar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Procesa datos desde query o archivo xlsx, realizando un filtro por fecha
    para obtener las filas donde 'FECHA SOLICITUD DESPACHO' corresponda al día de mañana.
    Luego se entregan los datos como DataFrame a georef, quien añade columnas de latitud y longitud.

    Args:
        filename (_type_, opcional): El nombre del archivo xlsx a procesar. Si no hay nombre, es None y se revisa por query.

    Returns:
        pd.DataFrame: Un DataFrame que incluye las columnas de latitud y longitud georreferenciadas.
    """
    
    fecha = (date.today() + timedelta(days=-14)).strftime('%d-%m-%Y')
    print("fecha a filtrar:", fecha)

    # existe FECHA_SOLICITUD_DESPACHO y FECHA_PROG_DESPACHO
    df = df[df["FECHA SOLICITUD DESPACHO"].str[:12] == fecha]
    
    # TODO: no solo TVP, si no que cuando tipo de despacho es 
    # TVP retira directamente en bodega, por lo tanto no lo georreferenciamos
    # Filtrar y guardar en su propio DataFrame
    df_tvp = df[df["DATOS TRANSPORTE EXTERNO"] == "TVP"]
    print(df_tvp)
    
    df_tvp.to_excel("retiros_tvp.xlsx", index=False)
    
    # Procesamos los datos mediante georef
    # obteniendo un DataFrame que incluye coordenadas asociadas a direccion
    df = georef.pasar_a_coordenadas(df[df["DATOS TRANSPORTE EXTERNO"] != "TVP"], test_prints=True)
    
    capacidad_maxima_por_camion = 18
    
    for index, row in df.iterrows():
        volumen_total = float(row['VOLUMEN'])
        if volumen_total > capacidad_maxima_por_camion:
            
            bultos = int(row["N° BULTOS"])
            peso_total = float(row["PESO"])
            volumen_unidad_teorica = volumen_total/bultos
            print(volumen_unidad_teorica)
            peso_unidad_teorica = peso_total/bultos
            
            for bulto in range(bultos):
                
                if bulto*volumen_unidad_teorica > capacidad_maxima_por_camion:
                    
                    bultos_primera_entrega = bulto - 1
                    
                    volumen_primera_entrega = bultos_primera_entrega*volumen_unidad_teorica
                   
                    peso_primera_entrega = bultos_primera_entrega*peso_unidad_teorica
                    
                    
                    df.loc[index, 'VOLUMEN'] = volumen_primera_entrega
                    df.loc[index, "PESO"] = peso_primera_entrega
                    df.loc[index, "N° BULTOS"] = bultos_primera_entrega 
                
                    
                    
                    bultos_segunda_entrega = bultos - bultos_primera_entrega
                    #print(bultos, bultos_primera_entrega )
                    volumen_segunda_entrega = bultos_segunda_entrega*volumen_unidad_teorica
                    print(volumen_total, bultos_segunda_entrega*volumen_unidad_teorica)
                    peso_segunda_entrega = bultos_segunda_entrega*peso_unidad_teorica
                    break
                
            df.loc[index, 'VOLUMEN'] = volumen_segunda_entrega
            df.loc[index, "PESO"] = peso_segunda_entrega
            df.loc[index, "N° BULTOS"] = bultos_segunda_entrega
            
            entregas_de_un_camion = df.copy()
            
            nueva_fila = df.loc[index].copy()
            
            nueva_fila["VOLUMEN"]  = volumen_primera_entrega
            nueva_fila["PESO"] = peso_primera_entrega
            nueva_fila["N° BULTOS"] = bultos_primera_entrega 
            """
            nueva_fila["VOLUMEN"] = volumen_segunda_entrega
            nueva_fila["PESO"] = peso_segunda_entrega
            nueva_fila["N° BULTOS"] = bultos_segunda_entrega
            """
            nueva_fila["LATITUD"] = float(nueva_fila["LATITUD"]) 
            nueva_fila["LONGITUD"] = float(nueva_fila["LONGITUD"]) 
            
            print(peso_primera_entrega)
            print(peso_segunda_entrega)
            print()
            print(volumen_primera_entrega)
            print(volumen_segunda_entrega)
            print()
            print(bultos_primera_entrega)
            print(bultos_segunda_entrega)
       
            
      
            # Agregar la nueva fila al final del DataFrame usando loc
            entregas_de_un_camion.loc[1] = nueva_fila
        
    print(df)
    return df, entregas_de_un_camion

def procesar_query() -> pd.DataFrame:
    """Ejecuta la query a la base de datos y la procesa en un DataFrame similar a los excel de despacho

    Returns:
        pd.DataFrame: un DataFrame conteniendo los datos procesados de la query
    """  
    # Realizamos la query y la recibimos en forma de DataFrame
    df_query = query_datos()
    
    # fecha entrega se guarda (por alguna razon) como objetos datetime.datetime con -03:00, por lo que al pasarlos a
    # pd.datetime resultan como 03:00:00 en vez de 00:00:00. por eso aplicamos el timedelta para corregir                   
    df_query['fecha_entrega'] = pd.to_datetime(df_query['fecha_entrega'].apply(lambda x: x+timedelta(hours=-3) if pd.notna(x) else x), utc=True)
        
    # para poder pasar a excel el DataFrame a futuro sin problemas
    for col in df_query.select_dtypes(include=['datetime64[ns, UTC]']).columns:
      df_query[col] = df_query[col].apply(lambda x: x.tz_localize(None))

    # no generamos el DataFrame hasta que tengamos la lista realizada, pues
    # utilizar concat repetidamente es demasiado lento.
    columnas = df_query.columns.tolist()
    agrupado = []
    
    # queremos agrupar los elementos que coincidan en 'fk_consolidado', 'fk_proforma' y 'fk_cliente'
    # sumando los bultos, el peso y el volumen en una sola fila.
    while not df_query.empty:
        fila = df_query.iloc[0].copy()
        # queremos todos los elementos que tengan 'fk_consolidado', 'fk_proforma' y 'fk_cliente'
        # con el mismo valor que el elemento en grouped que estamos revisando.
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
      else 'REVISAR DESPACHO GRATUITO NO INCLUIDO'
    , axis=1)
    
    '''if(grouped[i]['empresa_ext_despacho']!=null){
                    tipo='DESPACHO TRANS.EXTERNO';
                  }else if(grouped[i]['empresa_ext_retiro']!=null){
                    tipo='RETIRA TRANS.EXTERNO';
                  }else if(grouped[i]['fk_bodega']!=null){
                    tipo='RETIRA CLIENTE';
                  }else if(grouped[i]['fk_region']==null){
                    tipo='SIN ESPECIFICAR';
                  }else if(grouped[i]['fk_region']==12){
                    let findIndex=ComunasNoIncluidasStgo.findIndex(x=>x==grouped[i]['fk_comuna']);
                    if(findIndex>=0){
                        tipo='REVISAR DESPACHO GRATUITO NO INCLUIDO';
                    }else{
                     tipo='DESPACHO GRATIS INCLUIDO';
                    }
                  }else{
                    tipo='REVISAR DESPACHO GRATUITO NO INCLUIDO';
                  }'''
    
    # 'QUIEN PROGRAMA'
    df_agrupado['quien'] = df_agrupado[['fk_usuario_despacho_retiro_nombre', 'fk_usuario_despacho_retiro_apellidos']].apply(
      lambda fila: f"{fila['fk_usuario_despacho_retiro_nombre'].strip()} {fila['fk_usuario_despacho_retiro_apellidos'].strip()}" 
      if pd.notna(fila['fk_usuario_despacho_retiro_apellidos']) and pd.notna(fila['fk_usuario_despacho_retiro_nombre'])
      else f"{fila['fk_usuario_despacho_retiro_nombre'].strip()}" if pd.notna(fila['fk_usuario_despacho_retiro_nombre'])
      else 'S/I'
    , axis=1)
    '''let quien='';
                  if(grouped[i]['fk_usuario_despacho_retiro']!=null){
                    if(grouped[i]['fk_usuario_despacho_retiro_nombre']!=null){
                      quien+=grouped[i]['fk_usuario_despacho_retiro_nombre'];
                    }
                    if(grouped[i]['fk_usuario_despacho_retiro_apellidos']!=null){
                      quien+=' '+grouped[i]['fk_usuario_despacho_retiro_apellidos'];
                    }
                  }else{
                   quien='S/I';
                  }'''
    
    # CLIENTE
    # formato es "('fk_cliente') 'fk_cliente_razon_social'"
    df_agrupado['cliente'] = df_agrupado[['fk_cliente', 'fk_cliente_razon_social']].apply(
      lambda fila: f"({fila['fk_cliente']}) {fila['fk_cliente_razon_social'].strip()}"
    , axis=1)
    
    
    # TODO: FECHA SOLICITUD DESPACHO (?)
    df_agrupado['fecha_solicitud'] = df_agrupado[['fecha_despacho_retiro', 'fecha_fin_despacho_retiro']].apply(
      lambda fila: f"{fila['fecha_despacho_retiro'].strftime('%d-%m-%Y %H:%M')} / {fila['fecha_fin_despacho_retiro'].strftime('%H:%M')}" 
      if pd.notna(fila['fecha_fin_despacho_retiro']) and pd.notna(fila['fecha_despacho_retiro'])
      else f"{fila['fecha_despacho_retiro'].strftime('%d-%m-%Y')}" if pd.notna(fila['fecha_despacho_retiro'])
      else "S/I"
    , axis=1)
    '''let fecha_solicitud='S/I';
                  if(grouped[i]['fecha_despacho_retiro']!=null){
                    fecha_solicitud=moment(grouped[i]['fecha_despacho_retiro']).utc().format('DD-MM-YYYY HH:mm');
                    if(grouped[i]['fecha_fin_despacho_retiro']!=null){
                      let fin =moment(grouped[i]['fecha_fin_despacho_retiro']).utc().format('HH:mm');
                      fecha_solicitud+=' / '+fin;
                    }else{
                        fecha_solicitud=moment(grouped[i]['fecha_despacho_retiro']).utc().format('DD-MM-YYYY');
                    }
                  }else{
                    fecha_solicitud='S/I';
                  }
    '''
    # FECHA PROG DESPACHO (?)
    df_agrupado['fecha_programada'] = df_agrupado['fecha_programada'].apply(
      lambda fecha: fecha.strftime('%d-%m-%Y %H:%M') if pd.notna(fecha)
      else 'S/I'
    )
    '''let fecha_programada='S/I';
                  if(grouped[i]['fk_bodega']!=null){
                    if(grouped[i]['fecha_programada']!=null){
                      fecha_programada=moment(grouped[i]['fecha_programada']).format('DD-MM-YYYY HH:mm');
                    }else{
                        fecha_programada='S/I';
                    }
                    
                  }else if(grouped[i]['empresa_ext_retiro']==null){
                  if(grouped[i]['fecha_programada']!=null){
                    fecha_programada=moment(grouped[i]['fecha_programada']).format('DD-MM-YYYY HH:mm');
                  }else{
                    fecha_programada='S/I';
                  }
                }else{
                  if(grouped[i]['fecha_programada']!=null){
                    fecha_programada=moment(grouped[i]['fecha_programada']).format('DD-MM-YYYY HH:mm');
                  }else{
                    fecha_programada='S/I';
                  }
                }'''
    
    # DATOS CONTACTO RETIRO
    df_agrupado['retiro'] = df_agrupado[['rut_retiro', 'nombre_retiro', 'patente_retiro']].apply(
      lambda fila: f"{fila['rut_retiro'].strip()}, {fila['nombre_retiro'].strip()}, {fila['patente_retiro'].strip()}"
      if pd.notna(fila['rut_retiro']) or pd.notna(fila['nombre_retiro']) or pd.notna(fila['patente_retiro']) # se aplica or para que solo no printee
      else "NO APLICA"                                                                                       # en caso de que no haya ningun dato
    , axis=1)
    '''let retiro='';
                if(grouped[i]['rut_retiro']==null && grouped[i]['nombre_retiro']==null && grouped[i]['patente_retiro']==null){
                    retiro='NO APLICA';
                }else{
                    if(grouped[i]['rut_retiro']!=null && grouped[i]['rut_retiro'].length>0){
                        retiro+=grouped[i]['rut_retiro'];
                    }

                    if(grouped[i]['nombre_retiro']!=null && grouped[i]['nombre_retiro'].length>0){
                        retiro+=', '+grouped[i]['nombre_retiro'];
                    }

                    if(grouped[i]['patente_retiro']!=null && grouped[i]['patente_retiro'].length>0){
                        retiro+=', '+grouped[i]['patente_retiro'];
                    }
                    if(retiro.length>0){
                        
                    }else{
                        retiro='NO APLICA';
                    }
                }'''
    
    # DATOS TRANSPORTE EXTERNO
    df_agrupado['emp_ext'] = df_agrupado[['empresa_ext_despacho', 'fk_direccion_empresa_ext', 'empresa_ext_retiro']].apply(
      lambda fila: f"{fila['empresa_ext_despacho']} | {fila['fk_direccion_empresa_ext']}" if pd.notna(fila['empresa_ext_despacho'])
      else fila['empresa_ext_retiro'] if pd.notna(fila['empresa_ext_retiro'])
      else 'NO APLICA'
    , axis=1)
    
    '''let emp_ext='NO APLICA';
                if(grouped[i]['empresa_ext_despacho']!=null){
                    emp_ext=grouped[i]['empresa_ext_despacho']+' | '+grouped[i]['fk_direccion_empresa_ext'];
                }else if(grouped[i]['empresa_ext_retiro']!=null){
                    emp_ext=grouped[i]['empresa_ext_retiro'];
                }else{
                    emp_ext='NO APLICA';
                }'''
    
    # FECHA ENTREGA
    df_agrupado['fecha_entrega'] = df_agrupado['fecha_entrega'].apply(
      lambda x: x.strftime('%d-%m-%Y') if pd.notna(x)
      else 'S/I'
    )
    '''let fecha_entrega='S/I';
                if(grouped[i]['fecha_entrega']!=null){
                    fecha_entrega=moment(grouped[i]['fecha_entrega']).format('DD-MM-YYYY');
                }
    '''
    
    # CONDUCTOR
    # conductor_nombre, conductor_apellido
    df_agrupado['conductor'] = df_agrupado[['conductor_nombre', 'conductor_apellido']].apply(
      lambda fila: f"{fila['conductor_nombre'].strip()} {fila['conductor_apellido'].strip()}" if pd.notna(fila['conductor_nombre']) and pd.notna(fila['conductor_apellido'])
      else f"{fila['conductor_nombre'].strip()}" if pd.notna(fila['conductor_nombre'])
      else 'S/I'
    , axis=1)
    '''
                let conductor='S/I';
                if(grouped[i]['conductor_nombre']!=null){
                    conductor=grouped[i]['conductor_nombre'];
                    if(grouped[i]['conductor_apellido']!=null){
                        conductor+=' '+grouped[i]['conductor_apellido'];
                    }
                }
    '''
    '''
                let volumen='S/I';
                if(grouped[i]['volumen']!=null){
                    volumen=parseFloat(grouped[i]['volumen']).toFixed(2);
                }
    '''
    '''
                let peso='S/I';
                if(grouped[i]['peso']!=null){
                    peso=parseFloat(grouped[i]['peso']).toFixed(2);
                }'''
    
    # al final queremos un DataFrame igual al excel de programacion de despacho que se está generando actualmente
    
    # NAVE = 'nave_nombre'
    df_final = pd.DataFrame()
    columnas_final = ['NAVE', 'CONTENEDOR', 'ETA', 'F.DESCONSOLIDADO',
                      'N° CARPETA', 'ESTADO PAGO', 'TIPO DE ENTREGA', 'SERVICIO', 
                      'EJECUTIVO', 'N° BULTOS', 'VOLUMEN', 'PESO', 
                      'QUIEN PROGRAMA', 'DIRECCION', 'COMUNA', 'CONTACTO', 
                      'TELEF. CONTACTO', 'CLIENTE', 'FECHA SOLICITUD DESPACHO', 'FECHA PROG DESPACHO', 
                      'FECHA ENTREGA', 'DATOS CONTACTO RETIRO', 'DATOS TRANSPORTE EXTERNO', 'OBS.CLIENTE', 
                      'ESTADO DE ENTREGA', 'OBSERVACIONES', 'CONDUCTOR']
    
    columnas_agrupado = ['nave_nombre', 'contenedor', 'fecha_llegada', 'fecha_desconsolidado', 
                         'n_carpeta', 'estado_pago', 'tipo_de_entrega', 'fk_consolidado',
                         'fk_comercial_nombre', 'cantidad_bultos', 'volumen', 'peso', 
                         'quien', 'fk_direccion_completa', 'fk_comuna_nombre', 'nombre_contacto', 
                         'telefono_contacto', 'cliente', 'fecha_solicitud', 'fecha_programada',
                         'fecha_entrega', 'retiro', 'emp_ext', 'obs_cliente', 
                         'estado_entrega', 'observaciones', 'conductor']
    
    df_final[columnas_final] = df_agrupado[columnas_agrupado]
    # sólo para comprobar, el excel se debería generar después de la georreferenciación y la corrección
    df_final.to_excel('excel_test.xlsx', index=False)
    
    return df_final


if __name__ == "__main__":
    import pandas as pd
    file = pd.read_excel('test_query2.xlsx')
    procesar_query(file)