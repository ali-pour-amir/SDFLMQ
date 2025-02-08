from Core.Modules.Coordinator_Modules.components import Cluster
from Core.Modules.Coordinator_Modules.components import Cluster_Node
from Core.Modules.Coordinator_Modules.components import Session
import Core.Modules.Coordinator_Modules.components as components
import math 

class Clustering_Engine():
    def __init__(self):
        return

    ###DESCRIPTION: A 2-layer topology is a tree-like topology in which the root node is the roo_aggregator, 
    # and level_1 leaves are aggregators or aggregator_trainers, and the level_2 leaves are trainer-only nodes. 
    # Example::
    ##                    [AGG____0]
    ##                   /          \
    ##              [AGG_1]         [AGG_2]
    ##             /   |   \       /   |   \
    ##           [T1] [T2] [T3]  [T4] [T5] [T6]
    ###_____________________________________________________________________________________________________
    ###_____________________________________________________________________________________________________
    
    def create_2layer_topology(self,session,percentage_of_aggs): #TODO:incorporate 30,70 or 20,80 or ...
        session.role_vector = []
        session.role_dictionary = {}
        num_aggregators = math.floor(session.session_capacity_max * percentage_of_aggs)
        num_training_only = session.session_capacity_max - num_aggregators
        
        num_trainer_per_l2_cluster = math.ceil(num_training_only / (num_aggregators - 1))
        
        session.role_dictionary['agg_0'] = []
        session.role_vector.append(0)
        n_counter = 0
        for i in range(1,num_aggregators):
            session.role_dictionary['agg_0'].append('agg_' + str(i))
            session.role_vector.append(0)  
            session.role_dictionary['agg_' + str(i)] = []
            for j in range(num_trainer_per_l2_cluster):
                if(n_counter >= num_training_only):
                    break
                else:
                    session.role_dictionary['agg_' + str(i)].append('t_'+str(n_counter))
                    n_counter += 1

        return [session.role_vector,session.role_dictionary]
 
    def form_clusters(self,session):
        items = list(session.role_dictionary.items())#check session.role_dictionary
        for i in range(items):
            new_cluster = Cluster('cluster_' + str(i))

            new_node = Cluster_Node("N_" + str(len(session.nodes)),items[i][0],None) #First create the cluster head which has the role of aggregator
            session.nodes.append(new_node)#In each session, there is one root node which is the top-most aggregator. in role_dic it is 'agg_0'. If a given node is 'agg_0', then it is root node
            if(items[i][0] == "agg_0"):
                new_node.role = components._ROLE_AGGREGATOR_ROOT
                session.set_root_node(new_node)
            
            new_cluster.set_cluster_head(new_node)
            
            for j in range(1,len(items[i])):#Now form clusters of nodes (not clients) based on the list of each aggregator's items
                new_sub_node = Cluster_Node("N_" + str(len(session.nodes)),items[i][j],None)
                session.nodes.append(new_sub_node)
                if(items[i][j][0] == 't'):
                    new_sub_node.role = components._ROLE_TRAINER
                new_cluster.add_node(new_sub_node)
                
            session.add_cluster(new_cluster)
        #NOTE: All added nodes here are in pending mode. They will go to ACTIVE mode once the client they are assigned to, acknowledges the node's role.

        
        
        