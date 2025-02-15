
from datetime import datetime,timedelta

from dateutil import parser 

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
                 fl_rounds,
                 memcap,
                 mdatasize,
                 pspeed) :
        
        self.client_id = client_id  
        self.preferred_role = preferred_role
        self.fl_rounds = fl_rounds
        self.memcap = memcap 
        self.pspeed = pspeed
        self.mdatasize = mdatasize
        self.is_placed = False

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
        self.cluster_nodes.append(node)

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
        
        t = datetime.strptime(session_time,"%H:%M:%S")
        delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        self.session_time = (delta)

        self.session_creation_time = datetime.now()
        self.session_termination_time = None
        self.total_processing_time = None
        self.session_capacity_min = int(session_capacity_min)
        self.session_capacity_max = int(session_capacity_max)
        self.waiting_time = parser.parse(waiting_time)
        self.model_name = model_name
        self.model_spec = model_spec
        self.num_rounds = int(fl_rounds)
        self.current_round_index = 0
        self.session_status = _SESSION_ALIVE
        round = {'participants' : [],
                'num_registered_clients' : 0,
                'status': _ROUND_READY, 
                'acc':'',
                'loss':'',
                'starting_time':datetime.now(),
                'completion_time':None,
                'processing_time':None}
        
        self.rounds  = [round]
        # self.session_creation_time = datetime.now()

    def get_current_round(self):
        return self.rounds[self.current_round_index]
    def complete_round(self,acc = 0,loss = 0):
        if(self.rounds[self.current_round_index]['status'] == _ROUND_READY):
            self.rounds[self.current_round_index]['status'] = _ROUND_COMPLETE
            self.rounds[self.current_round_index]['acc'] = acc
            self.rounds[self.current_round_index]['loss'] = loss
            self.rounds[self.current_round_index]['completion_time'] = datetime.now()
            self.rounds[self.current_round_index]['processing_time'] = self.rounds[self.current_round_index]['completion_time'] - self.rounds[self.current_round_index]['starting_time']
            self.current_round_index = self.current_round_index + 1
    
    def new_round(self):
        new_round = {'participants' : [],
                        'num_registered_clients' : 0,
                        'status': _ROUND_READY, 
                        'acc':'',
                        'loss':'',
                        'starting_time':datetime.now(),
                        'completion_time':None,
                        'processing_time':None}
        self.rounds.append(new_round)

    def get_participants(self):
        return self.rounds[self.current_round_index]['participants']
    def add_participant(self,client_id):
        if(client_id not in self.rounds[self.current_round_index]['participants']):
            self.rounds[self.current_round_index]['participants'].append(client_id)

    def add_client(self, client):
        self.client_list.append(client)
       
    def set_role_dictionary(self,role_dictionary):
        self.role_dictionary = role_dictionary

    def set_roles(self,role_vector):
        
        #Travese the nodes and place the clients according to the role_vectors. 
        #Place the remaining clients into training_only nodes.
        #all nodes that are allocated should have a pending status, and is_elected = True
        #set root node according to new_role_vector
        #in case of not hitting max capacity, some nodes are unallocated. if so, their is_elected should remain False
        
        #FIRST: Assign clients to Nodes which their role is equal to the counting agg_roles (extracted from role_dictionary key items).
        agg_roles = list(self.role_dictionary.keys())
        for i,j in enumerate(role_vector):
            for k in range(len(self.nodes)):
                # print("node role : " + str(self.nodes[k].role))
                if(agg_roles[i] == self.nodes[k].role):
                    self.nodes[k].client = self.client_list[j]
                    self.nodes[k].status = _NODE_PENDING
                    self.client_list[j].is_placed = True
                    break
        
        #SECOND: Traverse the list of clients, those that hasn't been placed yet, find a node in the list of nodes which has no clients 
        #        and also has a role name starting with 't' indicating the node accepts trainer clients, and assigns the client to the node.
        for l in range(len(self.client_list)):
            if(self.client_list[l].is_placed == False):
                for m in range(len(self.nodes)):
                    if(self.nodes[m].client == None):
                        if(self.nodes[m].role[0] == 't'):
                            self.nodes[m].client = self.client_list[l]
                            self.nodes[m].status = _NODE_PENDING
                            self.client_list[l].is_placed = True
                            break
        
        # for n in self.nodes:
            # print("node " + n.name + " role " + n.role + " status " + n.status + " client " + str(n.client))
        self.role_vector = role_vector
        
    def set_root_node(self,node):
        self.root_node = node
    
    def get_root_node(self):
        return self.root_node
    
    def confirm_role(self,role,client_id):
        for i in range(len(self.nodes)):
            if(self.nodes[i].role == role):
                if(self.nodes[i].client.client_id == client_id):
                    self.nodes[i].status = _NODE_ACTIVE
                    return 0
        return -1

    def update_roles(self,new_role_vector):
        
        old_role_vector = self.role_vector

        # print(old_role_vector)
        # print(new_role_vector)

        agg_roles = list(self.role_dictionary.keys())
        #FIRST: Traverse the new_role_vector and find the item(s) which differ compare to the old_role_vector.
        #       Then, traverse the list of nodes, and extract the node which has been assigned the client which appears to be in the new role_vector element for the updating node.
        #       After finding the node, set it's client to none, and break out of the for.
        for i,j in enumerate(new_role_vector):
            if(old_role_vector[i] != j):
                for m in range(len(self.nodes)):
                    if(self.nodes[m].status == _NODE_ACTIVE):
                        if(self.nodes[m].client.client_id == self.client_list[j].client_id):
                            self.nodes[m].client.is_placed = False
                            self.nodes[m].client = None
                            self.nodes[m].status = _NODE_PENDING
                            break
                #
                # self.client_list[old_role_vector[i]].is_placed = False

                #SECOND: Traverse the list of nodes and find the node whose role maches the counting updating role according the agg_roles set.
                #        Then, first set its client free by setting it's is_placed atribute to false. Then assign the new client to the node, and set it to pending mode and set the newly placed client as placed.
                for k in range(len(self.nodes)):
                # print("node role : " + str(self.nodes[k].role))
                    if(agg_roles[i] == self.nodes[k].role):
                        if(self.nodes[k].client != None):
                            self.nodes[k].client.is_placed = False
                            self.nodes[k].status = _NODE_PENDING
                        self.nodes[k].client = self.client_list[j]
                        self.client_list[j].is_placed = True
                        break
                        
        #THIRD: search the list of clients, and find those whose is_placed is false. When found one, search the list of nodes and find the first that has no client attached which also is trainer only, and assign the found client to it.
        for l in range(len(self.client_list)):
            if(self.client_list[l].is_placed == False):
                for m in range(len(self.nodes)):
                    if(self.nodes[m].client == None):
                        if(self.nodes[m].role[0] == 't'):
                            self.nodes[m].client = self.client_list[l]
                            self.nodes[m].status = _NODE_PENDING
                            self.client_list[l].is_placed = True
                            break

        # for n in self.nodes:
        #     print("node " + n.name + " role " + n.role + " status " + n.status + " client " + str(n.client))
        #set root node according to new_role_vector
        #revert node.status in updated nodes to _NODE_PENDING
        #for nodes not allocated, check their is_elected is false
        self.role_vector = new_role_vector

    def set_clusters(self,clusters):
        self.clusters = clusters
           
    def update_clusters(self,new_role_dictionary):
        return
    
    def add_cluster(self,cluster):
        self.clusters.append(cluster)
    
    def remove_cluster(self,cluster):
        return
    
        
