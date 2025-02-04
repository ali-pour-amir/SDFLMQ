from Core.Modules.Coordinator_Modules.components import Cluster
from Core.Modules.Coordinator_Modules.components import Cluster_Node
from Core.Modules.Coordinator_Modules.components import Session
import math 

class Clustering_Engine():
    def __init__(self):
        return

    
    def create_2layer_topology(self,session,percentage_of_aggs): #TODO:incorporate 30,70 or 20,80 or ...
        session.role_vector = []
        session.role_dictionary = {}
        num_aggregators = math.floor(session.session_capacity_max * percentage_of_aggs)
        num_training_only = session.session_capacity_max - num_aggregators

        for i in range(num_aggregators):
            session.list
        return [[],{}]#TODO:[agg_role_vector, role_dictionary]
 
    def form_clusters(self,session):
        return []
        #TODO:check session.role_dictionary
        #TODO:form clusters of nodes (not clients) based on the above parameter 
        