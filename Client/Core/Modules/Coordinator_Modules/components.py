import datetime

_ROLE_AGGREGATOR_ROOT = '00'
_ROLE_AGGREGATOR = '10'
_ROLE_TRAINER = '01'
_ROLE_TRAINER_AGGREGATOR = '11'

_NODE_PENDING = '00'
_NODE_ACTIVE = '01'

_SESSION_ALIVE = '00'
_SESSION_ACTIVE = '01'
_SESSION_TIMEOUT = '10'
_SESSION_TERMINATED = '11'

_ROUND_READY = '00'
_ROUND_COMPLETE = '01'


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
        self.is_settled = False

class Cluster_Node():
    def __init__(self, 
                 name,
                role,
                client):
        self.name = name
        self.role = role
        self.client = client
        self.status = _NODE_PENDING
        self.is_elected = False

class Cluster():

    def __init__(self,
                 cluster_id):
        self.id = cluster_id
        self.cluster_head = None
        self.cluster_nodes = []

    def add_node(self,node):
        self.cluster_head.append(node)

    def set_cluster_head(self,node):
        self.cluster_head = node

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
        self.root_node = None #This is the client which has the __ROLE_AGGREGATOR_ROOT

        self.role_vector = []
        self.role_dictionary = {}
        self.session_id = session_id
        self.session_time = session_time
        self.session_creation_time = datetime.datetime.now()
        self.session_capacity_min = session_capacity_min
        self.session_capacity_max = session_capacity_max 
        self.waiting_time = waiting_time
        self.model_name = model_name
        self.model_stat = model_spec
        self.num_rounds = fl_rounds
        self.current_round_index = 0
        self.session_status = _SESSION_ALIVE
        round = {'participants' : [],
                'status': _ROUND_READY, 
                'acc':'',
                'loss':'',
                'starting_time':datetime.datetime.now(),
                'completion_time':None,
                'processing_time':None}
        
        self.rounds  = [round]
        self.session_creation_time = datetime.datetime.now()

    def complete_round(self):
        if(self.rounds[self.current_round_index]['status'] == _ROUND_READY):
            self.rounds[self.current_round_index]['status'] = _ROUND_COMPLETE
            self.rounds[self.current_round_index]['completion_time'] = datetime.datetime.now()
            self.rounds[self.current_round_index]['processing_time'] = self.rounds[self.current_round_index]['completion_time'] - self.rounds[self.current_round_index]['starting_time']
            self.current_round_index = self.current_round_index + 1
    
    def new_round(self):
        new_round = {'participants' : [],
                        'status': _ROUND_READY, 
                        'acc':'',
                        'loss':'',
                        'starting_time':datetime.datetime.now(),
                        'completion_time':None,
                        'processing_time':None}
        self.rounds.append(new_round)
            
            
    def add_client(self, client):
        self.client_list.append(client)
       

    def set_role_dictionary(self,role_dictionary):
        self.role_dictionary = role_dictionary

    def set_roles(self,role_vector):
        self.role_vector = role_vector
        #TODO:Travese the nodes and place the clients according to the role_vectors. 
        #TODO:Place the remaining clients into training_only nodes.
        #TODO: all nodes that are allocated should have a pending status, and is_elected = True
        #TODO: set root node according to new_role_vector
        #TODO: in case of not hitting max capacity, some nodes are unallocated. if so, their is_elected should remain False
    
    def get_root_node(self,node):
        self.root_node = node
    def set_root_node(self):
        return self.root_node
    
    def confirm_role(self,role,client_id):
        for i in range(len(self.nodes)):
            if(self.nodes[i].role == role):
                if(self.nodes[i].client.id == client_id):
                    self.nodes[i].status = _NODE_ACTIVE

    def update_roles(self,new_role_vector):
        old_role_vector = self.role_vector
        self.role_vector = new_role_vector
        #TODO: set root node according to new_role_vector
        #TODO: revert node.status in updated nodes to _NODE_PENDING
        #TODO: for nodes not allocated, check their is_elected is false
    
    # def set_clusters(self,init_clusters):
    #     self.clusters = init_clusters

    def update_clusters(self,new_role_dictionary):
        return
    
    def add_cluster(self,cluster):
        self.cluster.append(cluster)
    
    def remove_cluster(self,cluster):
        return
    
        
