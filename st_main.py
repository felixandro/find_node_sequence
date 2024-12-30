import streamlit as st
import pandas as pd
import geopandas as gpd
from find_node_sequence import find_node_sequence

###################
#### Funciones ####
###################

#find_node_sequence_to_all_routes: LineString Str GeoDataFrame Str Str GeoDataFrame Str Str -> DataFrame
#Aplica el algoritmo find_node_sequence a todas las rutas contenidas en routes_gdf
#Se obtiene un dataframe con la secuencia de nodos para cada una de las rutas
def find_node_sequence_to_all_routes(nodes_gdf, node_id_col, 
                                     edges_gdf, start_node_col, end_node_col,
                                     routes_gdf, route_id_col, route_direction_col):
    
    #Cantidad total de rutas
    n_routes = len(routes_gdf)

    #Diccionario para almacenar secuencias de nodos
    node_sequences_dict = {}

    #Ciclo for para aplicar algoritmo a cada ruta por separado
    for index, route_row in routes_gdf.iterrows():
        
        #Datos de la ruta
        route_id = route_row[route_id_col] #Identificador único de la ruta
        route_direction = route_row[route_direction_col] #Sentido de la ruta (NS o SN)        
        linestring = route_row["geometry"] #Geometría de la ruta

        #Aplicación Algoritmo
        node_sequence = find_node_sequence(linestring, route_direction,
                                           nodes_gdf, node_id_col,
                                           edges_gdf, start_node_col, end_node_col)
        
        #Almacenaje de secuencia de nodos obtenida en el diccionario
        node_sequences_dict[route_id] = node_sequence

        #Actualización de la barra de progreso
        progress = (index + 1 ) / n_routes
        progress_bar.progress(progress, text = f"Buscando Secuencia de Nodos ({index+1}/{n_routes})") 

    #Conversión de resultados de Diccionario a DataFrame
    node_sequences_df = pd.DataFrame.from_dict(node_sequences_dict, orient='index')
    node_sequences_df.columns = [f"NODO {i+1}" for i in range(node_sequences_df.shape[1])]
    node_sequences_df.fillna(0, inplace=True)

    #Almacenaje de Dataframe con resultado en variable de estado
    st.session_state["node_sequences_df"] = node_sequences_df

##################
##### Inputs #####
##################

#Nodos
#nodes_path = "Inputs/Nodos/Nodos.shp"
#nodes_gdf = gpd.read_file(nodes_path)

node_id_col = "ID"

#Arcos
#edges_path = "Inputs/Arcos/Arcos.shp"
#edges_gdf = gpd.read_file(edges_path)

start_node_col = "Nodo A"
end_node_col = "Nodo B"

#Rutas
#routes_path = "Inputs/Rutas/Rutas.shp"
#routes_gdf = gpd.read_file(routes_path)

route_id_col = "Name"
route_direction_col = "sentido"

#############################
#### Variables de Estado ####
#############################

if "node_sequences_df" not in st.session_state:
    st.session_state["node_sequences_df"] = None


##################
#### Frontend ####
##################

# Título de la página
st.title('Encontrar Secuencia de Nodos')

# Subtítulo de Inputs
st.header('Entradas')

# Subsubtítulo de Input de Nodos

nodes_zip = st.file_uploader("Nodos")
edges_zip = st.file_uploader("Arcos")
routes_zip = st.file_uploader("Rutas")

if "nodes_gdf" not in st.session_state:
    st.session_state["nodes_gdf"] = gpd.read_file(nodes_zip)

if "edges_gdf" not in st.session_state:
    st.session_state["edges_gdf"] = gpd.read_file(edges_zip)

if "routes_gdf" not in st.session_state:
    st.session_state["routes_gdf"] = gpd.read_file(routes_zip)

# División
st.divider()

#Botón para ejecutar el algoritmo

find_node_sequence_button = st.button("Encontrar Secuencia de Nodos",
                                      type = "primary",
                                      on_click = find_node_sequence_to_all_routes,
                                      args = (st.session_state["nodes_gdf"], node_id_col, 
                                              st.session_state["edges_gdf"], start_node_col, end_node_col,
                                              st.session_state["routes_gdf"], route_id_col, route_direction_col))

progress_bar = st.progress(0, text = "Buscando Secuencia de Nodos")
progress_bar.empty()

# División
st.divider()

# Subtítulo de Outputs
st.header('Salidas')

st.write(st.session_state["node_sequences_df"])