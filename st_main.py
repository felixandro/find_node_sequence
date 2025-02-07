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
                                     routes_gdf, route_id_col, route_direction_col, availability_col):
    
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
                                           edges_gdf, start_node_col, end_node_col, availability_col)
        
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
node_id_col = "nodo"

#Arcos
start_node_col = "NODOA"
end_node_col = "NODOB"

#Rutas
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

inputs_are_validated = (nodes_zip is not None)*(edges_zip is not None)*(routes_zip is not None)

if inputs_are_validated:
    if "nodes_gdf" not in st.session_state:
        st.session_state["nodes_gdf"] = gpd.read_file(nodes_zip).to_crs("EPSG:32719")
    if "edges_gdf" not in st.session_state:
        st.session_state["edges_gdf"] = gpd.read_file(edges_zip).to_crs("EPSG:32719")
    if "routes_gdf" not in st.session_state:
        st.session_state["routes_gdf"] = gpd.read_file(routes_zip).to_crs("EPSG:32719")

    # División
    st.divider()
    
    # Subtítulo de Inputs
    st.header('Configuración Entradas')

    #Nodos    
    st.subheader('Nodos')
    
    fields_nodes_gdf = st.session_state["nodes_gdf"].columns.to_list()[:-1]
    
    node_id_col = st.selectbox("Identificador Nodo",
                               fields_nodes_gdf)

    #Arcos
    st.subheader('Arcos')
    
    fields_edges_gdf = st.session_state["edges_gdf"].columns.to_list()[:-1]
    
    start_node_col = st.selectbox("Identificador Nodo Inicio",
                                  fields_edges_gdf)
    end_node_col = st.selectbox("Identificador Nodo Fin",
                                fields_edges_gdf)
    availability_col = st.selectbox("Disponibilidad",
                                    ["Todos los arcos disponibles"] + fields_edges_gdf)
    if availability_col == "Todos los arcos disponibles":
        availability_col = None
                                  
    #Rutas
    st.subheader('Rutas')
    
    fields_routes_gdf = st.session_state["routes_gdf"].columns.to_list()[:-1]
    
    route_id_col = st.selectbox("Identificador Ruta",
                                fields_routes_gdf)
    route_direction_col = st.selectbox("Sentido",
                                       fields_routes_gdf)

    #Botón para ejecutar el algoritmo
    find_node_sequence_button = st.button("Encontrar Secuencia de Nodos",
                                        type = "primary",
                                        on_click = find_node_sequence_to_all_routes,
                                        args = (st.session_state["nodes_gdf"], node_id_col, 
                                                st.session_state["edges_gdf"], start_node_col, end_node_col,
                                                st.session_state["routes_gdf"], route_id_col, route_direction_col, availability_col))

    progress_bar = st.progress(0, text = "Buscando Secuencia de Nodos")
    progress_bar.empty()

    # División
    st.divider()

    # Subtítulo de Outputs
    st.header('Salidas')

    st.write(st.session_state["node_sequences_df"])