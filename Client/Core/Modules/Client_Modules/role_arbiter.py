import json
import psutil
import os

class Role_Arbiter():
    def __init__(self,client_id):
        self.is_aggregator = False
        self.client_id = client_id

    def get_resources(self):
        resources = {
            'cpu_count'     : psutil.cpu_count() ,
            # 'disk_usage'    : psutil.disk_usage("/") ,
            'cpu_frequency' : psutil.cpu_freq() ,
            # 'cpu_stats'     : psutil.cpu_stats() ,
            # 'net_stats'     : psutil.net_if_stats() ,
            'ram_usage'     : psutil.virtual_memory()[3]/1000000000 ,
            # 'net_counters'  : psutil.net_io_counters()
            }

        res_msg = json.dumps(resources)
        return res_msg
    
    def set_current_session(session_id):
        pass

    def add_role(session_id, role):
        pass

    def set_role(self,session_id,role):
        pass

    def reset_role(Self,session_id,role):
        pass
    

    def set_aggregator(self,id): #TODO: Move this to the Role Arbiter module
        if(id == self.id):
            self.aggregator.is_aggregator = True
            os.system('setterm -background blue -foreground white')
            os.system('clear')
            if(self.aggregator.current_agg_topic_r != "-1"):
                self.client.unsubscribe(self.aggregator.current_agg_topic_r)
            self.aggregator.current_agg_topic_r = "c2a_agg_"+id
            self.aggregator.current_agg_topic_s = "a2c_agg_"+id
            self.client.subscribe(self.aggregator.current_agg_topic_r)
        else:
            self.aggregator.is_aggregator = False
            os.system('setterm -background yellow -foreground black')
            os.system('clear')
            if(self.aggregator.current_agg_topic_r != "-1"):
                self.client.unsubscribe(self.aggregator.current_agg_topic_r)
            self.aggregator.current_agg_topic_s = "c2a_agg_"+id
            self.aggregator.current_agg_topic_r = "a2c_agg_"+id
            self.client.subscribe(self.aggregator.current_agg_topic_r)
        print("Aggregator topic: " + str(self.aggregator.is_aggregator))
