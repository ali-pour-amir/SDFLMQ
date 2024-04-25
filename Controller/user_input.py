import threading
import time

class user_input:

    def __init__(self):
        while(True):
            user_input = input("What message you want to send: ")
            checked_input = self.check_input(user_input) 
            

    def input_parser(self, input_text):
        user_params = input_text.split(' ')

    def check_input(self, input_text):
        return input_text