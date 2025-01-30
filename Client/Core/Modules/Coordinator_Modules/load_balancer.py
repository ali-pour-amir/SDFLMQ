from Core.Modules.Coordinator_Modules.components import Cluster
from Core.Modules.Coordinator_Modules.components import Cluster_Node
from Core.Modules.Coordinator_Modules.components import Session

class Load_Balancer():
    def __init__(self):
        return
    
    def initialize_roles(self,session):
        #TODO: Look into the list of nodes, and the list of clients, and associate the clients to the roles.
        #For the assignment, the input argument to the set_roles should be built, which is the role_vector.
        #Based on the policy, the assigments can varry. The basic policy is that a client who has agreed to be aggregator should be assigned to agg or agg_t nodes.
        
        session.set_roles([])
        return []
    
    def optimize_roles(self,session):
        #TODO: Read the calculated cost of FL in the previous round, and accordingly build a new role_vector, and feed it to the update_roles.
        session.update_roles([])
        return []

