from Core.Modules.Coordinator_Modules.components import Cluster
from Core.Modules.Coordinator_Modules.components import Cluster_Node
from Core.Modules.Coordinator_Modules.components import Session

class Clustering_Engine():
    def __init__(self):
        return

    
    def create_topology(self,session): #TODO:incorporate 30,70 or 20,80 or ...
        session.role_vector = []
        session.role_dictionary = {}
        return [[],{}]#TODO:[agg_role_vector, role_dictionary]
 
    def form_clusters(self,session):
        return []
        #TODO:check session.role_dictionary
        #TODO:form clusters of nodes (not clients) based on the above parameter 
        