# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 09:57:12 2023

@author: Ignacio Carvajal
"""

from georef import *
import numpy as np
import folium
import xlsxwriter
import openpyxl
import os
import webbrowser

def verificar_elemento_mayor(lista, numero):
    if len(lista) > 0:
        for elemento in lista:
            if elemento > numero:
                return False
    return True


def condicion(camiones, camion, cluster_sums, n_clusters):
    cantidad_de_entregas = verificar_elemento_mayor(n_clusters, camiones[camion].maximo_entregas)
    capacidad = len([x for x in cluster_sums if x <= camiones[camion].capacidad and x >= camiones[camion].sub_capacidad]) <= camiones[camion].vueltas and verificar_elemento_mayor(n_clusters, camiones[camion].maximo_entregas)
    return capacidad and cantidad_de_entregas

def condicion_compuesta(camiones, cluster_sums, n_clusters):
    proposicion = True
    for camion in camiones.keys():
        proposicion = proposicion and condicion(camiones, camion, cluster_sums, n_clusters)
        #if proposicion == False:
            #print(proposicion, camion)
        #print(proposicion)
        #print(camion)
    return proposicion

class Camion:
    def __init__(self, capacidad, sub_capacidad, vueltas, maximo_entregas):
        self.capacidad = capacidad
        self.sub_capacidad = sub_capacidad
        self.vueltas = vueltas
        self.maximo_entregas = maximo_entregas
    
    def __str__(self):
        return f"({self.capacidad}, {self.sub_capacidad}, {self.vueltas}, {self.maximo_entregas})"

class Entregas:
    # Ahora entregas no utiliza nombre de archivo, recibe df directamente
    def __init__(self):
        # self.nombre_archivo = nombre_archivo
        self.camiones = {"Sinotrack": Camion(28, 22, 2, 7),
                    "JAK": Camion(18, 6, 2, 7),
                    "Hyundai": Camion(8, 0, 1, 7),
                    "Externo_1": Camion(22, 18,2,7),
                    "Externo_2": Camion(22, 18,2,7)
        }

    # La función ahora retorna True o False dependiendo de si se pudo agregar el camión 
    def crear_camion(self, nombre, capacidad, sub_capacidad, vueltas, maximo_entregas):
        if nombre in self.camiones.keys():
            return False
        self.camiones[nombre] = Camion(capacidad, sub_capacidad, vueltas,maximo_entregas)
        return True

    # Por ahora trabajamos con xlsx, idealmente seria query a base de datos.
    # Se recibe solo el df ya filtrado pues el xlsx/query fue procesado en procesar_datos.py
    def cargar_datos(self, df_filtrado):
        # existe FECHA_SOLICITUD_DESPACHO y FECHA_PROG_DESPACHO
        #df = df[df["FECHA_SOLICITUD_DESPACHO"].str[:12] == fecha]

        # Ahora el DataFrame incluira latitud y longitud de acuerdo a las direcciones
        #df = pasar_a_coordenadas(df, test_prints=True)
        
        #df = df[df["latitudes"] != -33.464161]
        latitudes = df_filtrado["LATITUD"]
        longitudes = df_filtrado["LONGITUD"]

        if len(latitudes) == len(longitudes) == len(list(df_filtrado["VOLUMEN"])):
            latitudes = np.array(df_filtrado["LATITUD"])
            longitudes = np.array(df_filtrado["LONGITUD"])
            volumen = np.array(list(df_filtrado["VOLUMEN"].astype(np.float64)))
            indices_eliminar = np.where(latitudes == 999)[0]

            latitudes = [latitudes[i] for i in range(len(latitudes)) if i not in indices_eliminar]
            longitudes = [longitudes[i] for i in range(len(longitudes)) if i not in indices_eliminar]
            volumen = [volumen[i] for i in range(len(volumen)) if i not in indices_eliminar]
            n_servicio = df_filtrado["SERVICIO"].astype(np.float64)

            self.array_tridimensional = np.array([latitudes, longitudes, volumen, n_servicio]).T
            
        else:
            print("Las listas no tienen la misma longitud, no se pueden combinar en un array tridimensional.")

       

    def kmeans_with_constraint(self, K, max_iters=300, constraint_value=28):
        best_centroids = None
        best_labels = None

        for _ in range(max_iters):
            
            centroids = self.array_tridimensional[np.random.choice(len(self.array_tridimensional), K, replace=False)]

            for _ in range(max_iters):
                distances = np.linalg.norm(self.array_tridimensional[:, np.newaxis, :2] - centroids[:, :2], axis=2)
                suma = sum(sum(distances))

                labels = np.argmin(distances, axis=1)
                cluster_sums = np.array([self.array_tridimensional[labels == k][:, 2].sum() for k in range(K)])
                n_clusters = [len(self.array_tridimensional[labels == k][:, 2]) for k in range(K)]
                #factibilidad = self.condicion(cluster_sums) and self.verificar_elemento_mayor(n_clusters, 6)
                #factibilidad = condicion(camiones, "sinotrack", cluster_sums) and condicion(camiones, "jak", cluster_sums) and condicion(camiones, "hyundai", cluster_sums) and condicion(camiones, "externo_1", cluster_sums) and np.all(cluster_sums <= constraint_value)
                #factibilidad = condicion(self.camiones, "Sinotrack", cluster_sums, n_clusters) and condicion(self.camiones, "JAK", cluster_sums, n_clusters) and condicion(self.camiones, "Hyundai", cluster_sums, n_clusters) and condicion(self.camiones, "Externo_1", cluster_sums, n_clusters) and np.all(cluster_sums <= constraint_value)
                factibilidad = condicion_compuesta(self.camiones, cluster_sums, n_clusters) and np.all(cluster_sums <= constraint_value)
                if factibilidad:
                    best_centroids = centroids
                    best_labels = labels

            if best_centroids is not None:
                break

        if best_centroids is None:
            print("No se encontró una clusterización que cumpla con la restricción.")
            return None, None

        return best_centroids, best_labels

    #def condicion(self, cluster_sums):
      #  return all(cluster_sums <= 26)

    def sumar_vueltas(self):
        total_vueltas = 0
        for camion in self.camiones.values():
            total_vueltas += camion.vueltas
        return total_vueltas

    def crear_mapa(self, data, labels, j):
        mapa_santiago = folium.Map(location=[-33.4489, -70.6693], zoom_start=12)
        colores_clusters = ['red', 'green', 'blue', 'white', 'darkred', 'orange', 'purple', 'pink', 'yellow', 'brown', 'cyan', 'gray', 'magenta', 'teal', 'lime']

        folium.Marker(
            location=[-33.421845,-70.9183415],
            icon=folium.Icon(color='purple'),
            popup="Punto Específico"
        ).add_to(mapa_santiago)

        for i, (lat, lon, volumen, n_serv, label) in enumerate(zip(data[:, 0], data[:, 1], data[:, 2], data[:, 3], labels)):
            color = colores_clusters[label]

            folium.Marker(
                location=[lat, lon],
                icon=folium.Icon(color=color),
                popup=f'Punto {i}, Cluster {label}, Volumen {volumen}, Numero servicio {n_serv}'
            ).add_to(mapa_santiago)

        mapa_santiago.save(f"mapas/mapa_{j}_Rutas.html")
        print("Mapa Creado")

    def ejecutar_modelo(self):
        K = self.sumar_vueltas()
        K = 10
        
        for i in range(3, K):
            centroids, labels = self.kmeans_with_constraint(i)

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
                
            except:
                print(f"No hay solución factible para {i} rutas...")

            
            if centroids is not None:
                directorio_actual = os.getcwd()
                workbook = xlsxwriter.Workbook(directorio_actual + f'/rutas/{i}_Ruta_info.xlsx')
            
                for k in range(i):
                    cluster_points = self.array_tridimensional[labels == k]
                    cluster_sum = cluster_points[:, 2].sum()
            
                    # Create a new worksheet for the cluster
                    worksheet = workbook.add_worksheet(f'Ruta_{k + 1}')
            
                    # Write the data to the worksheet
                    for row_num, row_data in enumerate(cluster_points):
                        worksheet.write_row(row_num, 0, row_data)
            
                    # Add centroid and sum information as a separate worksheet
                    info_worksheet = workbook.add_worksheet(f'Ruta_{k + 1}_Info')
                    info_worksheet.write(0, 0, "Centroide:")
                    info_worksheet.write(1, 0, centroids[k, 0])
                    info_worksheet.write(1, 1, centroids[k, 1])
                    info_worksheet.write(2, 0, "Suma de la columna extra:")
                    info_worksheet.write(2, 1, cluster_sum)
            
                workbook.close()
            
            if centroids is not None:
                # Primero, crea el archivo Excel para guardar los datos del cluster.
                workbook = xlsxwriter.Workbook(directorio_actual + f'/rutas/{i}_ruta_info.xlsx')
                for k in range(i):
                    cluster_points = self.array_tridimensional[labels == k]
                    cluster_sum = cluster_points[:, 2].sum()
                    
                    # Formatting para el archivo
                    bold = workbook.add_format({
                        'bold': True,
                        'align': 'center',
                    })
            
                    # Crea una nueva hoja para el cluster
                    worksheet = workbook.add_worksheet(f'Ruta_{k + 1}')
            
                    # Escribe los datos del cluster en la hoja
                    nombres_columnas = ["LATITUD", "LONGITUD", "VOLUMEN", "N_SERVICIO"]
                    worksheet.write_row(0, 0, nombres_columnas, bold)
                    for row_num, row_data in enumerate(cluster_points):
                        # Formato es (fila, columna, datos)
                        worksheet.write_row(row_num + 1, 0, row_data)
            
                    # Abre el archivo Excel "coordenadas.xlsx"
                    wb = openpyxl.load_workbook(directorio_actual + f'/pedidos/coordenadas.xlsx')
                    sheet = wb.active
            
                    # Crea una nueva hoja en "coordenadas.xlsx" para los registros específicos del cluster
                    cluster_sheet = wb.create_sheet(title=f'Ruta_{k + 1}')
            
                    # Itera a través de las filas de "coordenadas.xlsx" y copia las que pertenecen al cluster
                    for row in sheet.iter_rows(min_row=2, values_only=True):
                        servicio = row[3]  # Suponiendo que la columna de servicio está en la posición 4 (columna D)
                        if labels[k] == servicio:
                            cluster_sheet.append(row)
            
                    # Guarda el archivo "coordenadas.xlsx"
                    wb.save(directorio_actual + f'/pedidos/coordenadas6.xlsx')
            
                    # Agrega la información del centroide y suma al archivo Excel original
                    info_worksheet = workbook.add_worksheet(f'Ruta_{k + 1}_Info')
                    info_worksheet.write(0, 0, "Centroide:")
                    info_worksheet.write(1, 0, centroids[k, 0])
                    info_worksheet.write(1, 1, centroids[k, 1])
                    info_worksheet.write(2, 0, "Suma de la columna extra:")
                    info_worksheet.write(2, 1, cluster_sum)
            
                workbook.close()

