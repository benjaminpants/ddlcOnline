from shared import *

# This plugin implements a more immersive Roleplay experience, at the cost of trusting the clients WAY TOO MUCH.
# Instead of showing player names, it shows the name of the character you are playing as.
# Actions can be done by starting a message with *
# By chatting "rp:outfit " and then a name of any ddlc asset you can manually change expressions to a more varied range then whats included in the default picker.
class Plugin:
    def __init__(self,server):
        self.name = "True Roleplay"
        self.version = "0.0.0.0"
        self.server = server
    def onCommand(self,command,parameters):
        pass
    def nameFromCharacter(self,actor,player):
        if (actor.character.startswith("mc")):
            return player.username
        return actor.character.split(" ")[0].title()
    def updateActorName(self,actor,player):
        self.server.send_to_all_cons({
            "type":"change_net",
            "id":actor.id,
            "data":{"name":self.nameFromCharacter(actor,player)}
        })
    def prePacket(self,data,sender_data): # sender_data is a tuple containing the player's player object and their actor
        if (data["type"] == "chat"):
            if data["message"].startswith("rp:outfit"):
                outfit = data["message"].replace("rp:outfit","",1).strip()
                outfit_packet = {
                    "type":"change_char",
                    "sender_id":sender_data[0].id,
                    "character":outfit
                }
                sender_data[1].character = outfit
                self.server.send_to_all_cons(outfit_packet)
                self.postPacket(outfit_packet,sender_data)
                return False
            elif data["message"].startswith("*"):
                data["message"] = data["message"].replace("*","",1) #+ "\n{i}(" + sender_data[0].username + "){/i}"
                data["name_override"] = ""
            else:
                data["message"] = "\"" + data["message"] + "\""# + "\n{i}(" + sender_data[0].username + "){/i}"
                data["name_override"] = self.nameFromCharacter(sender_data[1],sender_data[0])
        return True # return false to disable standard behavior
    def postPacket(self,data,sender_data): # set the actors name to be the name of their character
        if (data["type"] == "changeusername"):
            self.updateActorName(sender_data[1],sender_data[0])
        elif (data["type"] == "change_char"):
            self.updateActorName(sender_data[1],sender_data[0])