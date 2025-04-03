from sdflmq import DFLMQ_Coordinator
import time


def main(**kwargs):
    
coordinator_client = DFLMQ_Coordinator(myID      = kwargs[coordinator_id],
                                    broker_ip    = kwargs[broker_ip],
                                    broker_port  = kwargs[broker_port],
                                    loop_forever = True,
                                    plot_stats   = False)


  
#____________________________________________GUI START_____________________________________________

if __name__ == "__main__":
    main(**dict(arg.split('=') for arg in sys.argv[1:]))
	
