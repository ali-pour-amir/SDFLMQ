import executable_class

userID = input("Enter UserID: ")
print("User with ID=" + userID +" is created.")
exec_program = executable_class.PubSub_Base_Executable(myID = userID,
                                                       broker_ip = 'localhost',
                                                       broker_port = 1883,
                                                       introduction_topic='client_introduction',
                                                       controller_executable_topic='controller_executable',
                                                       controller_echo_topic="echo",
                                                       start_loop=False)
exec_program.base_loop();

