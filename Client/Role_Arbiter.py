import json
import psutil

class Role_Arbiter():
    def __init__(self,client_id):
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
