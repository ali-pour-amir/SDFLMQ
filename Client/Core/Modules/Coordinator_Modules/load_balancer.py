from Core.Modules.Coordinator_Modules.components import Cluster
from Core.Modules.Coordinator_Modules.components import Cluster_Node
from Core.Modules.Coordinator_Modules.components import Session

class Load_Balancer():
    def __init__(self):
        return
    
    def initialize_roles(self,session):
        session.set_roles([])
        return []
    
    def optimize_roles(self,session):
        session.update_roles([])
        return []

