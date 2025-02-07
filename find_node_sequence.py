########################
#####  Frameworks  #####
########################

import networkx as nx
from shapely.geometry import Point

##################################
#####  Funciones Auxiliares ######
##################################

#prepare_nodes_gdf: GeoDataFrame Str -> GeoDataFrame
#Configura los id de los nodos como los indices del GeoDataFrame
def prepare_nodes_gdf(nodes_gdf, node_id_col):
    nodes_gdf_copy = nodes_gdf.copy()
    return nodes_gdf_copy.set_index(node_id_col)

#add_distance_between_nodes_and_linestring: LineString GeoDataFrame -> GeoDataFrame
#Se agrega la distancia entre los nodos y la línea de referencia
#como una columna adicional al GeoDataFrame de nodos
def add_distance_col_to_nodes(linestring, nodes_gdf):
    nodes_gdf_copy = nodes_gdf.copy()    
    nodes_gdf_copy["d_to_ls"] = nodes_gdf_copy.geometry.distance(linestring) 
    #d_to_ls es abreviación de distance_to_linestring
    return nodes_gdf_copy

#prepare_edges_gdf: GeoDataFrame Str -> GeoDataFrame
#Filtra los arcos conservando solo los disponibles según la columna indicada
def prepare_edges_gdf(edges_gdf, availability_col):
    edges_gdf_copy = edges_gdf.copy()
    if availability_col:
        return edges_gdf_copy[edges_gdf_copy[availability_col] == 1]
    return edges_gdf_copy

#add_weight_col_to_edges: GeoDataFrame GeoDataFrame Str Str -> GeoDataFrame
#A cada arco le agrega su peso como el promedio de las distancias 
#entre la línea de referencia y los nodos que lo definen
def add_weight_col_to_edges(nodes_gdf, 
                            edges_gdf, start_node_col, end_node_col):    
    weight_list = []
    for _, row in edges_gdf.iterrows():
        #Identificadores Nodos de inicio y fin
        start_node = row[start_node_col]
        end_node = row[end_node_col]
        #Distancia desde linea de referencia a Nodos de inicio y fin
        start_node_distance = nodes_gdf.loc[start_node,"d_to_ls"] #Distancia Nodo Inicio a Linea de Referencia
        end_node_distance = nodes_gdf.loc[end_node,"d_to_ls"] #Distancia Nodo Fin a Linea de Referencia
        #Peso Arco
        weight = (start_node_distance + end_node_distance) / 2
        weight_list.append(weight)
    edges_gdf_copy = edges_gdf.copy()
    edges_gdf_copy["weight"] = weight_list
    return edges_gdf_copy        

#build_network: GeoDataFrame Str Str Str -> nx.DiGraph
#Construye el grafo dirigido referente a edges_gdf, el cual debe tener una columna con pesos
def build_network(edges_gdf, start_node_col, end_node_col, available_col = None):
    network = nx.DiGraph() #Grafo Dirigido Vacío
    for _, row in edges_gdf.iterrows():
        start_node = row[start_node_col]
        end_node = row[end_node_col]
        weight = row["weight"]
        network.add_edge(start_node, end_node, weight = weight)
    return network

#first_last_point: LineString Str -> Point Point
def first_last_point(linestring,direction):
    #Validar variables de entrada
    assert linestring.geom_type == "LineString" 
    assert direction == "NS" or direction == "SN"
    first_point_tuple = list(linestring.coords)[0]
    last_point_tuple = list(linestring.coords)[-1]
    if first_point_tuple[1] > last_point_tuple[1]: #CASO DIBUJO NS 
        if direction == "SN":
            first_point_tuple, last_point_tuple = (last_point_tuple, first_point_tuple)
    else: #CASO DIBUJO SN 
        if direction == "NS":
            first_point_tuple, last_point_tuple = (last_point_tuple, first_point_tuple)
    first_point = Point(first_point_tuple)
    last_point = Point(last_point_tuple)
    return first_point, last_point

#find_nearest_node_id: Point GeoDataFrame -> Int
#Entrega el id del punto más cercano a otro de referencia
def find_nearest_node_id(point, nodes_gdf):
   geometry_serie = nodes_gdf.geometry
   distance_to_point_serie = geometry_serie.distance(point)
   nearest_node_id = distance_to_point_serie.idxmin()
   return nearest_node_id

#get_min_route: nx.DiGraph Str int int -> list[int]
#Entrega la secuencia de nodos respectiva a la ruta mínima 
#en la red de arcos ponderados desde un nodo fuente a otro sumidero
def get_min_route(network, source_node, sink_node):
    if nx.has_path(network, source = source_node , target = sink_node):
      node_sequence = nx.shortest_path(network, source = source_node, target = sink_node, weight = "weight")
    else:
      node_sequence = []
    return node_sequence


#######################################
#######  Función Consolidadada  #######
#######        Pipeline         #######
#######################################

#find_node_sequence: LineString GeoDataFrame Str Str Str Str Str Str -> list[int]
#Encuentra la secuencia de nodos que minimiza la distancia entre la línea de referencia y los nodos
def find_node_sequence(linestring, route_direction,
                       nodes_gdf, node_id_col,
                       edges_gdf, start_node_col, end_node_col, availability_col):
    #Preparar GeoDataFrame de Nodos
    nodes_gdf_prepared = prepare_nodes_gdf(nodes_gdf, node_id_col)
    #Agregar Distancia entre Nodos y Linea de Referencia
    nodes_gdf_with_distance = add_distance_col_to_nodes(linestring, nodes_gdf_prepared)
    
    #Preparar GeoDataFrame de Arcos
    edges_gdf_availables = prepare_edges_gdf(edges_gdf, availability_col)
    #Agregar Peso a los Arcos
    edges_gdf_with_weight = add_weight_col_to_edges(nodes_gdf_with_distance, 
                                                    edges_gdf_availables, start_node_col, end_node_col)
    #Construir Red
    network = build_network(edges_gdf_with_weight, start_node_col, end_node_col)
    #Puntos Iniciales y Finales
    first_point, last_point = first_last_point(linestring, route_direction)
    #Nodos Iniciales y Finales
    source_node_id = find_nearest_node_id(first_point, nodes_gdf_with_distance)
    sink_node_id = find_nearest_node_id(last_point, nodes_gdf_with_distance)
    #Secuencia de Nodos
    node_sequence = get_min_route(network, source_node_id, sink_node_id)
    return node_sequence