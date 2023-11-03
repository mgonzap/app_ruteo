# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 17:01:53 2023

@author: Ignacio Carvajal
"""

# georreferenciacion

import numpy as np
import folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
"""
# Reemplaza 'nombre_del_archivo.xlsx' con el nombre real de tu archivo Excel
archivo_excel = "geo.xlsx"

# Cargar el archivo Excel en un DataFrame
df = pd.read_excel(archivo_excel)

print(df)
df = df[df["FECHA ENTREGA"] == "16-10-2023"]
# Ahora puedes trabajar con el DataFrame 'df'
# Por ejemplo, para ver las primeras


camiones = {"sinotrack": {"capacidad": 16,
                          "sub_capacidad": 6,
                          "vueltas": 1},

            "jak": {"capacidad": 26,
                    "sub_capacidad": 22,
                    "vueltas": 1},

            "hyundai":   {"capacidad": 6,
                          "sub_capacidad": 0,
                          "vueltas": 1},

            "externo_1":  {"capacidad": 22,
                           "sub_capacidad": 16,
                           "vueltas":1},

            "externo_2": {"capacidad": 22,
                          "sub_capacidad": 16,
                          "vueltas": 1}}
from geopy.geocoders import Nominatim


print("Este es el inicio del programa.")

bodega = "Camino a noviciado 1945, Bodega 19, Pudahuel, Región Metropolitana"
# Crea una instancia de Nominatim
geolocator = Nominatim(user_agent="myGeoco")

print(df["DIRECCION"])

# Define la función de limitación de velocidad
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2)

# Realiza la geocodificación
#location = geocode(f"{calle}, {ciudad}")
latitudes = []
longitudes = []
for i in df["DIRECCION"]:
    
    location = geocode(i)
    
    if location is not None:
        latitud = location.latitude
        longitud = location.longitude
        latitudes.append(latitud)
        longitudes.append(longitud)
        print(latitudes)
        print(longitudes)

        
    else:
       
        latitud = -33.464161
        longitud = -70.699524
        
        latitudes.append(latitud)
        longitudes.append(longitud)

print(latitudes)
print(longitudes)
print(list(df["VOLUMEN"]))

df["latitudes"] = latitudes

df["longitudes"] = longitudes


# Supongamos que 'df' es tu DataFrame con las coordenadas
# Por ejemplo, df = pd.DataFrame({'Latitud': latitudes, 'Longitud': longitudes})

# Nombre del archivo Excel de salida
nombre_archivo = "coordenadas.xlsx"

# Guarda el DataFrame como un archivo Excel
df.to_excel(nombre_archivo, index=False)

print(f"El DataFrame se ha guardado en '{nombre_archivo}'")



"""

# Nombre del archivo Excel que deseas abrir
nombre_archivo = "coordenadas.xlsx"

# Abre el archivo Excel como un DataFrame
df = pd.read_excel(nombre_archivo)
df = df[df["FECHA ENTREGA"] == "16-10-2023"]
df = df[df["latitudes"] != -33.464161]
latitudes = df["latitudes"]
longitudes = df["longitudes"]
# Ahora 'df' contiene los datos del a

# Asegúrate de que todas las listas tengan la misma longitud
if len(latitudes) == len(longitudes) == len(list(df["VOLUMEN"])):
    # Convierte las listas en arrays de una dimensión
    latitudes = np.array(df["latitudes"])
    longitudes = np.array(df["longitudes"])
    volumen = np.array(list(df["VOLUMEN"]))
    indices_eliminar = np.where(latitudes == 999)[0]
    indices_eliminar = []
    # Usando una comprensión de lista para eliminar los índices
    latitudes = [latitudes[i]
                 for i in range(len(latitudes)) if i not in indices_eliminar]
    longitudes = [longitudes[i]
                  for i in range(len(longitudes)) if i not in indices_eliminar]
    volumen = [volumen[i]
               for i in range(len(volumen)) if i not in indices_eliminar]

    # Combina los arrays en un array tridimensional
    array_tridimensional = np.array([latitudes, longitudes, volumen]).T

    print(array_tridimensional)
else:
    print("Las listas no tienen la misma longitud, no se pueden combinar en un array tridimensional.")


def condicion(camiones, camion, cluster_sums):
    return len([x for x in cluster_sums if x <= camiones[camion]["capacidad"] and x >= camiones[camion]["sub_capacidad"]]) <= camiones[camion]["vueltas"]


def condicion2(camiones, camion, cluster_sums):
    return len([x for x in cluster_sums if x <= camiones[camion]["capacidad"] and x >= camiones[camion]["sub_capacidad"]]) <= camiones[camion]["vueltas"]


def sumar_vueltas(camiones):
    total_vueltas = 0
    for camion in camiones.values():
        total_vueltas += camion["vueltas"]
    return total_vueltas


######################################################################################################################


def kmeans_with_constraint(X, K, camiones, max_iters=100, constraint_value=26):
    best_centroids = None
    best_labels = None
    best_sum = 110010000000

    #K = sumar_vueltas(camiones)


    for _ in range(max_iters):
        # Inicializar los centroides de manera aleatoria
        centroids = X[np.random.choice(len(X), K, replace=False)]

        for _ in range(max_iters):
            # Calcular las distancias entre cada punto y los centroides
            distances = np.linalg.norm(
                X[:, np.newaxis, :2] - centroids[:, :2], axis=2)
            suma = sum(sum(distances))
            # Asignar cada punto al cluster del centroide más cercano
            labels = np.argmin(distances, axis=1)

            # Calcular la suma de la columna extra para cada cluster
            cluster_sums = np.array(
                [X[labels == k][:, 2].sum() for k in range(K)])

            # Verificar si la suma supera la restricción y ajustar los centroides si es necesario
            # if np.all(cluster_sums <= constraint_value) and np.all(cluster_sums >= 8) :
            factibilidad = condicion(camiones, "sinotrack", cluster_sums) and condicion(camiones, "jak", cluster_sums) and condicion(camiones, "hyundai", cluster_sums) and condicion(camiones, "externo_1", cluster_sums) and np.all(cluster_sums <= constraint_value)

            #len([x for x in cluster_sums if x >= 6 and x <= 16]) <=2 and len([x for x in cluster_sums if x >= 16 and x <= 22]) <=2 and len([x for x in cluster_sums if x <= 6]) <=1 and len([x for x in cluster_sums if (x >= 22 and x <= constraint_value)]) <=1 and np.all(cluster_sums <= constraint_value)

            # np.any(cluster_sums <= constraint_value) and np.any(cluster_sums <= 7) and np.any(cluster_sums <= 16) and np.all(cluster_sums <= constraint_value):
            # print(factibilidad)
            if factibilidad:
                best_centroids = centroids
                best_labels = labels

        if best_centroids is not None:
            break

    if best_centroids is None:
        print("No se encontró una clusterización que cumpla con la restricción.")
        return None, None

    return best_centroids, best_labels


camiones = {"sinotrack": {"capacidad": 16,
                          "sub_capacidad": 6,
                          "vueltas": 3},

            "jak": {"capacidad": 26,
                    "sub_capacidad": 16,
                    "vueltas": 3},

            "hyundai":   {"capacidad": 6,
                          "sub_capacidad": 0,
                          "vueltas": 1},

            "externo_1":  {"capacidad": 22,
                           "sub_capacidad": 16,
                           "vueltas": 2}}


# Ejemplo de uso
if __name__ == "__main__":
    # Generar datos de ejemplo con una columna extra
    np.random.seed(0)
    data = array_tridimensional

    # Aplicar K-Means con restricción
    #K = 3
    K = sumar_vueltas(camiones)
    K = 4
    constraint_value = 26
    centroids, labels = kmeans_with_constraint(data, K, camiones, constraint_value=constraint_value)

    if centroids is not None:
        # Imprimir resultados
        for k in range(K):
            cluster_points = data[labels == k]
            cluster_sum = cluster_points[:, 2].sum()
            print(f"Cluster {k + 1}:")
            print("Centroide:", centroids[k, :2])
            print("Puntos en el cluster:", cluster_points)
            print(f"Suma de la columna extra en el cluster: {cluster_sum}")
            print("\n")


# Crear un mapa centrado en Santiago, Chile


# Supongamos que ya tienes los resultados de K-Means con restricciones en 'centroids' y 'labels'

# Crear un mapa centrado en Santiago, Chile
mapa_santiago = folium.Map(location=[-33.4489, -70.6693], zoom_start=12)

# Colores para los marcadores de los clusters
colores_clusters = ['red', 'green', 'blue',
                    'white', 'darkred', 'orange', 'purple', 'pink']


# Agregar un marcador para el punto específico con otro color
folium.Marker(
    location=[-33.4116806, -70.9097788],
    icon=folium.Icon(color='purple'),  # Cambia el color aquí
    popup="Punto Específico"
).add_to(mapa_santiago)

# Crear marcadores para cada punto y agregarlos al mapa
for i, (lat, lon, label) in enumerate(zip(data[:, 0], data[:, 1], labels)):
    # Obtener el color del cluster actual
    color = colores_clusters[label]

    # Crear un marcador en el mapa
    folium.Marker(
        location=[lat, lon],
        icon=folium.Icon(color=color),
        popup=f'Punto {i}, Cluster {label}'
    ).add_to(mapa_santiago)

# Guardar el mapa como un archivo HTML
mapa_santiago.save("mapa_clusters.html")
