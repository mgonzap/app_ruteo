# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 09:57:12 2023

@author: Ignacio Carvajal
"""

from georef import *
import numpy as np
import folium
import xlsxwriter
import os
import webbrowser
import pandas as pd
from copy import deepcopy


def verificar_elemento_mayor(lista, numero):
    if len(lista) > 0:
        for elemento in lista:
            if elemento > numero:
                return False
    return True


def condicion(camiones, camion, cluster_sums, n_clusters):
    cantidad_de_entregas = verificar_elemento_mayor(
        n_clusters, camiones[camion].maximo_entregas
    )
    capacidad = len(
        [
            x
            for x in cluster_sums
            if x <= camiones[camion].capacidad and x >= camiones[camion].sub_capacidad
        ]
    ) <= camiones[camion].vueltas and verificar_elemento_mayor(
        n_clusters, camiones[camion].maximo_entregas
    )
    return capacidad and cantidad_de_entregas


def condicion_compuesta(camiones, cluster_sums, n_clusters):
    proposicion = True
    for camion in camiones.keys():
        proposicion = proposicion and condicion(
            camiones, camion, cluster_sums, n_clusters
        )
        # if proposicion == False:
        # print(proposicion, camion)
        # print(proposicion, camion)
    return proposicion


class Camion:
    def __init__(self, capacidad: int, sub_capacidad: int, vueltas: int, maximo_entregas: int):
        self.capacidad: int = capacidad
        self.sub_capacidad: int = sub_capacidad
        self.vueltas: int = vueltas
        self.maximo_entregas: int = maximo_entregas

    def __str__(self):
        return f"({self.capacidad}, {self.sub_capacidad}, {self.vueltas}, {self.maximo_entregas})"

    def __repr__(self):
        return f"({self.capacidad}, {self.sub_capacidad}, {self.vueltas}, {self.maximo_entregas})"


class Entregas:
    def __init__(self):

        # self.nombre_archivo = nombre_archivo
        self.camiones = {
            # 1 vuelta 5 puntos
            "Sinotruk": Camion(26, 17, 1, 5),
            # 1 vuelta 8 puntos
            "JAC": Camion(16, 6, 10, 5),
            # 1 vuelta 6 ptos
            "Hyundai": Camion(6, 0, 2, 6),
            #"Externo_1": Camion(17, 16, 1, 7),
            #"Externo_2": Camion(17, 16, 1, 7),
        }
        self.camiones_copia = {}
        self.cap_max_camion = 0
        self.df_original: pd.DataFrame | None = None

    def ordenar_camiones(self):
        camiones_ordenados = sorted(
            self.camiones.items(), key=(lambda x: x[1].capacidad)
        )
        sub_cap = [0, 0]
        for tupla in camiones_ordenados:
            if tupla[1].capacidad != sub_cap[0]:
                tupla[1].sub_capacidad = sub_cap[0]
                sub_cap[1] = sub_cap[0]
                sub_cap[0] = tupla[1].capacidad
            else:
                tupla[1].sub_capacidad = sub_cap[1]

        camiones_ordenados.reverse()
        self.camiones = dict(camiones_ordenados)
        self.cap_max_camion = camiones_ordenados[0][1].capacidad

    # La función ahora retorna True o False dependiendo de si se pudo agregar el camión
    def crear_camion(self, nombre, capacidad, sub_capacidad, vueltas, maximo_entregas):
        if nombre in self.camiones.keys():
            return False
        self.camiones[nombre] = Camion(
            capacidad, sub_capacidad, vueltas, maximo_entregas
        )
        return True

    def separar_entregas(self, df: pd.DataFrame):
            lista_entregas_separadas = []
            # comenzamos con el df sorteado, de mayor a menor
            df_sorted = df.sort_values(by=["VOLUMEN"], ascending=False)

            idx_bultos = df.columns.get_loc("N° BULTOS")
            idx_volumen = df.columns.get_loc("VOLUMEN")
            idx_peso = df.columns.get_loc("PESO")

            def separar_entrega(fila: pd.Series, camion: Camion):
                bultos_total: int = fila.iloc[idx_bultos]
                volumen_por_bulto: float = fila.iloc[idx_volumen] / bultos_total
                peso_por_bulto: float = fila.iloc[idx_peso] / bultos_total

                '''print(
                    "---------------bultos total:",
                    bultos_total,
                    "volumen total:",
                    volumen_por_bulto * bultos_total,
                )'''
                # Calculamos el max de bultos dentro de la capacidad maxima
                bultos_maximos = int(camion.capacidad / volumen_por_bulto)
                nueva_entrega = [
                    bultos_maximos * volumen_por_bulto,
                    bultos_maximos * peso_por_bulto,
                    bultos_maximos,
                ]

                # guardamos la nueva fila en la lista de entregas separadas
                nueva_fila = df.iloc[fila.name].copy()
                nueva_fila[["VOLUMEN", "PESO", "N° BULTOS"]] = nueva_entrega
                lista_entregas_separadas.append(nueva_fila)

                bultos_resto = bultos_total - bultos_maximos
                entrega_resto = [
                    bultos_resto * volumen_por_bulto,
                    bultos_resto * peso_por_bulto,
                    bultos_resto,
                ]
                # asignamos los valores del resto al dataframe
                df_sorted.loc[fila.name, ["VOLUMEN", "PESO", "N° BULTOS"]] = (
                    entrega_resto
                )

                # ordenamos nuevamente
                return df_sorted.sort_values(by=["VOLUMEN"], ascending=False)

            camion_max = list(self.camiones.keys())[0]
            #print("camion max inicio:", camion_max)

            # nos aseguramos que no hayan entregas con volumen mayor que cualquier capacidad
            while df_sorted.iloc[0, idx_volumen] > self.cap_max_camion:
                if len(self.camiones) <= 0:
                    break

                # obtenemos el camion con capacidad_max
                camion_max = list(self.camiones.keys())[0]
                df_sorted = separar_entrega(
                    df_sorted.iloc[0], self.camiones[camion_max]
                )

                # le restamos una vuelta al camion
                self.camiones[camion_max].vueltas -= 1
                #print(self.camiones[camion_max])
                # si camion queda sin vueltas, se elimina
                if self.camiones[camion_max].vueltas <= 0:
                    del self.camiones[camion_max]
                    if len(self.camiones) > 0:
                        camion_max = list(self.camiones.keys())[0]
                        self.cap_max_camion = self.camiones[camion_max].capacidad

            llaves = list(self.camiones.keys())
            # index del camion que estamos viendo.
            current_idx = 0
            vueltas_disponibles = 0
            while current_idx < len(self.camiones):
                camion = self.camiones[llaves[current_idx]]
                #print("revisando camion:", llaves[current_idx], camion)

                # obtenemos entregas que solo pueden entrar en este camion o mayores
                df_entregas_camion = df_sorted[
                    [
                        camion.capacidad >= vol > camion.sub_capacidad
                        for vol in df_sorted["VOLUMEN"].to_numpy()
                    ]
                ]

                '''print("filas en df_entregas_camion:", df_entregas_camion.shape[0])
                print(
                    f"vueltas disponibles: {camion.vueltas + vueltas_disponibles} ({camion.vueltas} y {vueltas_disponibles})"
                )
                print(df_entregas_camion[["N° BULTOS", "VOLUMEN"]])'''

                # si hay mas entregas que vueltas disponibles
                while df_entregas_camion.shape[0] > (
                    camion.vueltas + vueltas_disponibles
                ):
                    # revisamos si camion siguiente (menor) existe
                    if current_idx + 1 >= len(self.camiones):
                        break

                    #print("entramos a separar")
                    # usamos un threshold de 1.5 para evitar dividir entregas
                    vol_threshold = 1.5
                    # que ocuparian completamente el camion.
                    df_threshold = df_entregas_camion[
                        [
                            camion.capacidad - vol_threshold
                            > vol
                            > camion.sub_capacidad
                            for vol in df_entregas_camion["VOLUMEN"].to_numpy()
                        ]
                    ]
                    
                    row_idx = 0
                    # si todas las entregas no pasan el threshold
                    # nos quedamos con la de menor tamaño
                    if df_threshold.empty:
                        df_threshold = df_entregas_camion
                        row_idx = df_entregas_camion.shape[0] -1
                    
                    df_sorted = separar_entrega(
                        df_threshold.iloc[row_idx],
                        self.camiones[llaves[current_idx + 1]],
                    )

                    self.camiones[llaves[current_idx + 1]].vueltas -= 1
                    if self.camiones[llaves[current_idx + 1]].vueltas <= 0:
                        del self.camiones[llaves[current_idx + 1]]
                        self.ordenar_camiones()
                        llaves = list(self.camiones.keys())

                    # actualizamos df_entregas_camion
                    df_entregas_camion = df_sorted[
                        [
                            camion.capacidad >= vol > camion.sub_capacidad
                            for vol in df_sorted["VOLUMEN"].to_numpy()
                        ]
                    ]
                    #print("filas ahora:", df_entregas_camion.shape[0])

                if df_entregas_camion.shape[0] <= (
                    camion.vueltas + vueltas_disponibles
                ):
                    vueltas_disponibles += camion.vueltas - df_entregas_camion.shape[0]

                # continuamos con el siguiente camion
                current_idx += 1

            df_entregas_separadas = pd.DataFrame(
                lista_entregas_separadas, columns=df.columns
            )
            return df_sorted, df_entregas_separadas

    # Se recibe el df procesado en procesar_datos.py
    def cargar_datos(self):
        self.ordenar_camiones()
        # respaldo
        self.camiones_copia = deepcopy(self.camiones)
        # print("Keys:", self.camiones.keys())
        #print(self.camiones)
        self.df, self.df_separados = self.separar_entregas(self.df_original.copy())
        #print("after separar:", self.camiones)
        #print(self.df[["N° BULTOS", "VOLUMEN"]])
        self.fecha_filtrado = self.df["FECHA SOLICITUD DESPACHO"].iloc[0]
        latitudes = self.df["LATITUD"]
        longitudes = self.df["LONGITUD"]

        if len(latitudes) == len(longitudes) == len(list(self.df["VOLUMEN"])):
            latitudes = np.array(self.df["LATITUD"])
            longitudes = np.array(self.df["LONGITUD"])
            volumen = np.array(list(self.df["VOLUMEN"].astype(np.float64)))

            # pueden ocurrir n_servicio = ''
            df_malos: pd.DataFrame = self.df[self.df["SERVICIO"] == ""]
            # en este punto carpeta test deberia existir
            df_malos.to_excel("test/malos.xlsx", index=False)
            # print("n_servicio vacios", self.df[self.df['SERVICIO'] == ''])
            n_servicio = np.array(
                [
                    n_servicio.split(",")[0] if len(n_servicio) > 0 else -1
                    for n_servicio in self.df["SERVICIO"]
                ]
            ).astype(np.float64)

            self.array_tridimensional = np.array(
                [latitudes, longitudes, volumen, n_servicio]
            ).T

        else:
            print(
                "Las listas no tienen la misma longitud, no se pueden combinar en un array tridimensional."
            )

    def kmeans_with_constraint(self, K, max_iters=300, constraint_value=1):
        # print("constraint:", constraint_value)
        best_centroids = None
        best_labels = None

        for _ in range(max_iters):
            centroids = self.array_tridimensional[
                np.random.choice(len(self.array_tridimensional), K, replace=False)
            ]

            for _ in range(max_iters):
                distances = np.linalg.norm(
                    self.array_tridimensional[:, np.newaxis, :2] - centroids[:, :2],
                    axis=2,
                )
                ##print(distances)

                # Condición para comparar las distancias con el umbral
                # condicion = distances > 0

                # Reemplaza los valores que cumplen la condición con el valor que elijas (por ejemplo, 0)
                # valor_elegido = 10000000000.0  # Puedes cambiar este valor según tus necesidades
                # distances[condicion] = valor_elegido

                labels = np.argmin(distances, axis=1)
                cluster_sums = np.array(
                    [
                        self.array_tridimensional[labels == k][:, 2].sum()
                        for k in range(K)
                    ]
                )
                n_clusters = [
                    len(self.array_tridimensional[labels == k][:, 2]) for k in range(K)
                ]
                # factibilidad = self.condicion(cluster_sums) and self.verificar_elemento_mayor(n_clusters, 6)
                # factibilidad = condicion(camiones, "sinotrack", cluster_sums) and condicion(camiones, "jak", cluster_sums) and condicion(camiones, "hyundai", cluster_sums) and condicion(camiones, "externo_1", cluster_sums) and np.all(cluster_sums <= constraint_value)
                # factibilidad1 = condicion(self.camiones, "Sinotrack", cluster_sums, n_clusters) and condicion(self.camiones, "JAK", cluster_sums, n_clusters)  and condicion(self.camiones, "Externo_1", cluster_sums, n_clusters)
                # print(condicion(self.camiones, "Sinotrack", cluster_sums, n_clusters), condicion(self.camiones, "JAK", cluster_sums, n_clusters),""" condicion(self.camiones, "Hyundai", cluster_sums, n_clusters)""", condicion(self.camiones, "Externo_1", cluster_sums, n_clusters), np.all(cluster_sums <= constraint_value))
                # and condicion(self.camiones, "Hyundai", cluster_sums, n_clusters)
                factibilidad2 = condicion_compuesta(
                    self.camiones, cluster_sums, n_clusters
                ) and np.all(cluster_sums <= constraint_value)
                # print(factibilidad2)
                if factibilidad2:  # factibilidad:
                    best_centroids = centroids
                    best_labels = labels
                    # print(self.camiones, cluster_sums, n_clusters)

            if best_centroids is not None:
                break

        if best_centroids is None:
            print("No se encontró una clusterización que cumpla con la restricción.")
            return None, None

        return best_centroids, best_labels

    # TODO: cuando logre nueva logica div revisar aca
    def sumar_vueltas(self):
        total_vueltas = 0
        for camion in self.camiones_copia.values():
            total_vueltas += camion.vueltas
        return total_vueltas

    def crear_mapa(self, data, labels, j):
        mapa_santiago = folium.Map(location=[-33.4489, -70.6693], zoom_start=12)
        colores_clusters = [
            "red",
            "green",
            "blue",
            "darkred",
            "orange",
            "purple",
            "pink",
            "yellow",
            "brown",
            "cyan",
            "gray",
            "magenta",
            "teal",
            "lime",
            "white",
        ]

        folium.Marker(
            location=[-33.421845, -70.9183415],
            icon=folium.Icon(color="purple"),
            popup="Punto Específico",
        ).add_to(mapa_santiago)

        for i, (lat, lon, volumen, n_serv, label) in enumerate(
            zip(data[:, 0], data[:, 1], data[:, 2], data[:, 3], labels)
        ):
            color = colores_clusters[label]

            folium.Marker(
                location=[lat, lon],
                icon=folium.Icon(color=color),
                popup=f"Punto {i}, Ruta {label+1}, Volumen {np.float64(volumen).round(2)}, Numero servicio {int(n_serv)}",
            ).add_to(mapa_santiago)

        if not os.path.exists(f"mapas/{self.fecha_filtrado}"):
            os.makedirs(f"mapas/{self.fecha_filtrado}")
        map_path = f"mapas/{self.fecha_filtrado}/mapa_{j}_Rutas.html"
        mapa_santiago.save(map_path)
        # print("Mapa Creado")
        # Abrimos el mapa para mostrar
        webbrowser.open("file://" + os.path.abspath(map_path))

    def ejecutar_modelo(self):
        # print(self.camiones)
        self.cargar_datos()
        K = self.sumar_vueltas()
        # K = 15

        for i in range(2, K):
            try:
                centroids, labels = self.kmeans_with_constraint(
                    i, constraint_value=self.cap_max_camion
                )
            except Exception as e:
                print(f"{type(e).__name__}: {e}")
                return

            # Creacion de mapas
            if centroids is not None:
                for k in range(i):
                    cluster_points = self.array_tridimensional[labels == k]
                    cluster_sum = cluster_points[:, 2].sum()
                    print(f"Cluster {k + 1}:")
                    print("Centroide:", centroids[k, :2])
                    print("Puntos en el cluster:", cluster_points)
                    print(f"Suma de la columna extra en el cluster: {cluster_sum}\n")

            try:
                self.crear_mapa(self.array_tridimensional, labels, i)

            except Exception as e:
                print(e)
                print(f"No hay solución factible para {i} rutas...")

            # Modificar excel..?
            if centroids is not None:             
                directorio_actual = os.getcwd()
                if not os.path.exists(f"rutas/{self.fecha_filtrado}"):
                    os.makedirs(f"rutas/{self.fecha_filtrado}")
                workbook = xlsxwriter.Workbook(
                    directorio_actual
                    + f"/rutas/{self.fecha_filtrado}/{i}_Ruta_info.xlsx"
                )

                for k in range(i):
                    cluster_points = self.array_tridimensional[labels == k]
                    cluster_sum = cluster_points[:, 2].sum()

                    # Create a new worksheet for the cluster
                    worksheet = workbook.add_worksheet(f"Ruta_{k + 1}")

                    # Write the data to the worksheet
                    for row_num, row_data in enumerate(cluster_points):
                        worksheet.write_row(row_num, 0, row_data)

                    # Add centroid and sum information as a separate worksheet
                    info_worksheet = workbook.add_worksheet(f"Ruta_{k + 1}_Info")
                    info_worksheet.write(0, 0, "Centroide:")
                    info_worksheet.write(1, 0, centroids[k, 0])
                    info_worksheet.write(1, 1, centroids[k, 1])
                    info_worksheet.write(2, 0, "Suma de la columna extra:")
                    info_worksheet.write(2, 1, cluster_sum)

                workbook.close()

            if centroids is not None:
                # TODO: ver bien esta logica, conversar con ignacio
                # GENERAR EXCEL PARECIDO A PDF RESUMEN DESPACHOS
                # CONDUCTOR ES POR CAMION, 1 A 1
                # diccionario conductores donde llave es nombre camion
                cols = [
                    "RUTA",
                    "(m³) TOTAL RUTA",
                    "ORDEN",
                    "N° CARPETA",
                    "EJECUTIVO CUENTA",
                    "CLIENTE",
                    "N° CONTENEDOR",
                    "N° SERVICIO",
                    "(m³)",
                    "BULTOS",
                    "FECHAS",
                    "CAMIÓN",
                    "DIRECCIÓN",
                    "COMUNA",
                    "EMPRESA EXT",
                    "CONTACTO",
                    "OBSERVACIONES",
                    "CHOFER",
                    "ESTADO",
                    "FECHA PROGRAMADA",
                    "ESTADO REVISIÓN",
                ]

                lista_filas = []
                # 0 a i-1
                for k in range(i):
                    # cluster_points: [LAT, LONG, VOL, SERVICIO]
                    # SERVICIO de cluster_points corresponde a df['SERVICIO'].split(',')[0]
                    # i: N TOTAL RUTAS, k: RUTA ACTUAL
                    cluster_points = self.array_tridimensional[labels == k]
                    cluster_sum = cluster_points[:, 2].sum()

                    # print("suma cluster:", cluster_sum)

                    for point in cluster_points:
                        # obtenemos la fila correspondiente de nuestro df
                        fila_df = self.df[
                            [
                                servicios.startswith(str(int(point[3])))
                                for servicios in self.df["SERVICIO"]
                            ]
                        ].iloc[0]

                        # asignamos valores
                        ruta = k + 1
                        vol_ruta = cluster_sum.round(2)
                        orden = 0  # TODO: como se determina?
                        n_carpeta = fila_df["N° CARPETA"]
                        ejecutivo = fila_df["EJECUTIVO"]
                        cliente = fila_df["CLIENTE"]
                        contenedor = fila_df["CONTENEDOR"]
                        n_servicio = fila_df["SERVICIO"]
                        volumen = point[2].round(2)
                        bultos = fila_df["N° BULTOS"]
                        fechas_str = (
                            f"ETA: {fila_df['ETA']} "
                            + f"DESC: {fila_df['F.DESCONSOLIDADO']} "
                            + f"PROG: {fila_df['FECHA PROG DESPACHO'] if fila_df['FECHA PROG DESPACHO'] != 'S/I' else fila_df['FECHA SOLICITUD DESPACHO']} ENT: "
                        )
                        # DETERMINAR CAMION:
                        # sub capacidad <= VOL_TOTAL_CLUSTER <= capacidad
                        camion_str = "S/I"
                        for nombre, camion in self.camiones_copia.items():
                            # no vemos por el item individual, si no por la suma de su cluster
                            if camion.sub_capacidad <= cluster_sum <= camion.capacidad:
                                camion_str = nombre.upper()
                        if camion_str == "S/I":
                            # print(cluster_sum)
                            pass

                        direccion = fila_df["DIRECCION"]
                        comuna = fila_df["COMUNA"]
                        empresa_ext = fila_df["DATOS TRANSPORTE EXTERNO"]
                        contacto = fila_df["TELEF. CONTACTO"]
                        obs_cliente = (
                            fila_df["OBS.CLIENTE"]
                            if fila_df["OBS.CLIENTE"] != None
                            else ""
                        )
                        obs = (
                            fila_df["OBSERVACIONES"]
                            if fila_df["OBSERVACIONES"] != None
                            else ""
                        )
                        observaciones = ", ".join([obs_cliente, obs])
                        chofer = fila_df["CONDUCTOR"]
                        # estado = fila_df['ESTADO DE ENTREGA'].values[0] # TODO: que estado? 'ESTADO PAGO' O 'ESTADO DE ENTREGA'?
                        estado = "S/I"
                        fecha_prog = fila_df["fecha_despacho_retiro"]
                        estado_revision = ""

                        fila: pd.Series = pd.Series(
                            [
                                ruta,
                                vol_ruta,
                                orden,
                                n_carpeta,
                                ejecutivo,
                                cliente,
                                contenedor,
                                n_servicio,
                                volumen,
                                bultos,
                                fechas_str,
                                camion_str,
                                direccion,
                                comuna,
                                empresa_ext,
                                contacto,
                                observaciones,
                                chofer,
                                estado,
                                fecha_prog,
                                estado_revision,
                            ],
                            index=cols,
                        )
                        lista_filas.append(fila)

                # incluimos las rutas separadas!
                ruta += 1
                # TODO: cambiar a otra cosa, iterrows es super lento
                #print("-------DF SEPARADO-------")
                #print(self.df_separados[["SERVICIO", "N° BULTOS", "VOLUMEN"]])
                for idx, fila_df in self.df_separados.iterrows():
                    # asignamos valores (notar que algunos difieren del df normal)
                    vol_ruta = np.float64(fila_df["VOLUMEN"]).round(2)
                    orden = 0  # TODO: como se determina?
                    n_carpeta = fila_df["N° CARPETA"]
                    ejecutivo = fila_df["EJECUTIVO"]
                    cliente = fila_df["CLIENTE"]
                    contenedor = fila_df["CONTENEDOR"]
                    n_servicio = fila_df["SERVICIO"]
                    volumen = vol_ruta
                    bultos = fila_df["N° BULTOS"]
                    fechas_str = f"ETA: {fila_df['ETA']} DESC: {fila_df['F.DESCONSOLIDADO']} PROG: {fila_df['FECHA PROG DESPACHO']} ENT: "  # TODO: formatear string "ETA: DESC: PROG: ENT:"
                    # DETERMINAR CAMION:
                    # sub capacidad <= VOL_TOTAL_CLUSTER <= capacidad
                    for nombre, camion in self.camiones_copia.items():
                        # no vemos por el item individual, si no por la suma de su cluster
                        if camion.sub_capacidad <= vol_ruta <= camion.capacidad:
                            camion_str = nombre.upper()
                    direccion = fila_df["DIRECCION"]
                    comuna = fila_df["COMUNA"]
                    empresa_ext = fila_df["DATOS TRANSPORTE EXTERNO"]
                    contacto = fila_df["TELEF. CONTACTO"]
                    obs_cliente = (
                        fila_df["OBS.CLIENTE"] if fila_df["OBS.CLIENTE"] != None else ""
                    )
                    obs = (
                        fila_df["OBSERVACIONES"]
                        if fila_df["OBSERVACIONES"] != None
                        else ""
                    )
                    observaciones = ", ".join([obs_cliente, obs])
                    chofer = fila_df["CONDUCTOR"]
                    # estado = fila_df['ESTADO DE ENTREGA'].values[0] # TODO: que estado? 'ESTADO PAGO' O 'ESTADO DE ENTREGA'?
                    estado = "S/I"
                    fecha_prog = fila_df["fecha_despacho_retiro"]
                    estado_revision = ""
                    fila: pd.Series = pd.Series(
                        [
                            ruta,
                            vol_ruta,
                            orden,
                            n_carpeta,
                            ejecutivo,
                            cliente,
                            contenedor,
                            n_servicio,
                            volumen,
                            bultos,
                            fechas_str,
                            camion_str,
                            direccion,
                            comuna,
                            empresa_ext,
                            contacto,
                            observaciones,
                            chofer,
                            estado,
                            fecha_prog,
                            estado_revision,
                        ],
                        index=cols,
                    )
                    # print(fila)
                    lista_filas.append(fila)
                    ruta += 1

                df_excel = pd.DataFrame(lista_filas, columns=cols)
                try:
                    if not os.path.exists(f"resumen_despachos/{self.fecha_filtrado}"):
                        os.makedirs(f"resumen_despachos/{self.fecha_filtrado}")
                    df_excel.to_excel(
                        f"resumen_despachos/{self.fecha_filtrado}/resumen-{i}_rutas.xlsx",
                        index=False,
                    )
                except PermissionError:
                    print("No se pudo generar el excel de resumen despacho.")

                # return
