import os
import pickle

def save_file(dir,filename, data):
    
    if(os.path.isdir(dir) == False):
        os.mkdir(dir)
    filename_ = dir + "/" + filename
     
    if(os.path.isfile(filename_)):
        print("File exists. Replacing file...")
        f = open(filename_, "wb")
        pickle.dump(data,f)
    else:
        print("Saving " + filename + " as a new file...")
        f = open(filename_, "wb")
        pickle.dump(data,f)


def load_file(dir,filename):
    
    if(os.path.isdir(dir) == False):
        print("directory does not exist!")
        return -1
    
    filename_ = dir + "/" + filename 
    if(os.path.isfile(filename_)):
        print("Openning file...")
        f = open(filename_, "rb")
        data = pickle.load(f)
        return data
    else:
        print("File " + filename + " does not exist!")
        return -1