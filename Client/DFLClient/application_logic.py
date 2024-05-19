class dflmq_client_app_logic():
    
    def __init__(self):
        self.executables = []
        return 0

    def set_model(self):
        return 0
    
    def collect_data(self):
        return 0

    def get_model(self):
        return 0
    
    def get_data(self):
        return 0

    def _execute_on_msg(self, msg,_get_header_body_func):
        header_parts = _get_header_body_func(msg)

        # if header_parts[2] == '' : 
        #     self.()