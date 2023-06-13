from shared import *

class Plugin:
    def __init__(self,server):
        self.name = "Debug and Experimental Plugin"
        self.version = "0.0.0.0"
        self.server = server
    def onCommand(self,command,parameters):
        if command == "create_actor":
            actor = PlayerActor(0,parameters[1])
            actor.character = parameters[2]
            actor.name = parameters[3]
            self.server.add_to_net(actor)
    def prePacket(self,data,sender_data): # sender_data is a tuple containing the player's player object and their actor
        # print("Pre packet!")
        return True # return false to disable standard behavior
    def postPacket(self,data,sender_data): # same variables as prePacket
        pass