_ROLE_AGGREGATOR = '10'
_ROLE_TRAINER = '01'
_ROLE_TRAINER_AGGREGATOR = '11'
import datetime

class Client :
    def __init__(self,
                 client_id,
                 preferred_role,
                 memcap,
                 mdatasize,
                 pspeed) :
        
        self.client_id = client_id  
        self.preferred_role = preferred_role
        self.memcap = memcap 
        self.pspeed = pspeed
        self.mdatasize = mdatasize

class Cluster_Node():
    def __init__(self, 
                 name,
                role,
                client):
        self.name = name
        self.role = role
        self.client = client

class Cluster():

    def __init__(self,
                 cluster_id,
                 cluster_head):
        self.id = cluster_id
        self.cluster_head = cluster_head
        self.cluster_nodes = []

    def add_node(self,
                 node_name,
                 client,
                 role):
        new_node = Cluster_Node(node_name,role,client)

        if(role == _ROLE_TRAINER_AGGREGATOR or 
           role == _ROLE_AGGREGATOR):
            self.cluster_head = new_node
        else:
            self.cluster_nodes.append(new_node)


class Session():
    def __init__(self,
                session_id,
                session_time,
                session_capacity_min,
                session_capacity_max,
                waiting_time,
                model_name,
                model_spec,
                fl_rounds):
        
        self.client_list = []
        self.nodes = []
        self.clusters = []

        self.session_id = session_id
        self.session_time = session_time
        self.session_capacity_min = session_capacity_min
        self.session_capacity_max = session_capacity_max 
        self.waiting_time = waiting_time
        self.model_name = model_name
        self.model_stat = model_spec
        self.num_rounds = fl_rounds
        self.current_round_index = 0
    
        round = {'participants' : [],
                'status': '', 
                'acc':'',
                'loss':''}
        
        self.rounds  = [round]
        self.session_creation_time = datetime.datetime.now()

    def add_client(self, client):
        self.client_list.append(client)

    def set_role_dictionary(self,role_dictionary):
        self.set_role_dictionary = role_dictionary

    def set_roles(self,role_vector):
        self.role_vector = role_vector
        #TODO:Travese the nodes and place the clients according to the role_vectors. 
        #TODO:Place the remaining clients into training_only nodes.

    def update_roles(self,new_role_vector):
        old_role_vector = self.role_vector
        self.role_vector = new_role_vector
    
    def set_clusters(self,init_clusters):
        self.clusters = init_clusters

    def update_clusters(self,new_role_dictionary):
        return
    def add_cluster(self,cluster):
        return
    def remove_cluster(self,cluster):
        return
    
        
