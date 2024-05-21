class dflmq_client_app_logic():
    
    def __init__(self)-> None:
        self.executables = ['set_logic_model', 'collect_logic_data']


    def set_logic_model(self):
        return 0
    
    def collect_logic_data(self):
        return 0

    def get_model(self):
        return 0
    
    def get_data(self):
        return 0

    def _execute_on_msg(self, msg,_get_header_body_func):
        header_parts = _get_header_body_func(msg)

        # if header_parts[2] == '' : 
        #     self.()