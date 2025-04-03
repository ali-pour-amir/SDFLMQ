from sdflmq import DFLMQ_Coordinator
import time
import sys
import argparse

def main():    
    

    parser = argparse.ArgumentParser(description="SDFLMQ Coordinator quick lunch")

    parser.add_argument('--coordinator_id', type=str, required=True, help='Coordinator id')
    parser.add_argument('--broker_ip', type=str, default="localhost", help='IP address of the broker to connect to')
    parser.add_argument('--broker_port', type=int, default=1883, help='Port number of the broker to connect to')

    args = parser.parse_args()
    
    print(args.coordinator_id)
    print(args.broker_ip)
    print(args.broker_port)
    coordinator_client = DFLMQ_Coordinator( myID            = args.coordinator_id,
                                            broker_ip       = args.broker_ip,
                                            broker_port     = args.broker_port,
                                            loop_forever    = True,
                                            plot_stats      = False)


  
#____________________________________________GUI START_____________________________________________

if __name__ == "__main__":
    main()
	
