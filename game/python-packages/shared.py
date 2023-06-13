# the code here is shared by the server and the client, i use a sym-link to keep the files insync but you can also just copyn them manually
import json

# networkables store an ID and that is about it.
# networkables allow objects to simply reference a network ID instead of an actual object reference.
class Networkable:
    def __init__(self, my_id):
        self.type = "invalid"
        self.id = int(my_id)
    def serialize(self):
        raise Exception("Attempt to call undefined serialize!")
    def deserialize(self,data): #data is a ALREADY DESERIALIZED DICTIONARY
        raise Exception("Attempt to call undefined deserialize!")
    def __str__(self):
        return self.serialize()

# the class that allows a player to actually exist. privkey is a server given identifier
class Player(Networkable):
    def __init__(self, id, actor_id, priv_key):
        Networkable.__init__(self, id) # define my network ID
        self.type = "player"
        self.actor_id = actor_id # object reference to my actor
        self.priv_key = priv_key
        self.username = ""
    def serialize(self):
        data_out = {
            "type":self.type,
            "id":self.id,
            "actor_id":self.actor_id,
            "username":self.username
        }
        return json.dumps(data_out)
    def deserialize(self,data):
        if (self.id == 0): #only change ID if our current ID is unknown
            self.id = data["id"]
        self.actor_id = data["actor_id"]
        self.username = data["username"]
        return self

def network_create_packet(dat):
    return json.dumps(dat) + "\n"
def network_create_class_fstring(string):
    if string == "player":
        return Player(0,0,"")
    elif string == "playeractor":
        return PlayerActor(0)
    raise Exception("Unknown class string" + str(string))
def network_serialize_objects(obj_list):
    ser_net = []
    for obj in obj_list:
        ser_net.append(obj.serialize())
    return json.dumps(ser_net)
def network_deserialize_object_no_base(data): #create a class without a base, relying on the "type" field
    return network_create_class_fstring(data["type"]).deserialize(data)
def network_deserialize_objects(string):
    data = json.loads(string)
    ser_net = []
    for obj in data:
        deserdat = json.loads(obj) #the actual json data
        ser_net.append(network_create_class_fstring(deserdat["type"]).deserialize(deserdat))
    return ser_net


# player actors are a players actual "data." they are seperated from players themselves.
class PlayerActor(Networkable):
    def __init__(self, id, room="void"):
        Networkable.__init__(self, id)
        self.type = "playeractor"
        self.room = room
        self.character = "mc 1c"
        self.name = ""
    
    def serialize(self):
        data_out = {
            "type":self.type,
            "id":self.id,
            "room":self.room,
            "character":self.character,
            "name":self.name # name is the name this character responds to
        }
        return json.dumps(data_out)
    def deserialize(self, data):
        self.character = data["character"]
        if (self.id == 0): #only change ID if our current ID is unknown
            self.id = data["id"]
        self.room = data["room"]
        self.name = data["name"]
        return self
        


# rooms are places actors can go
class Room:
    def __init__(self,name,asset,cap):
        self.name = name
        # asset tuples are simple. The first value was initially designed to designate if its a custom asset, but its now unused.
        # the second value is the actual asset filename itself. this is not ideal as mod custom assets do not work properly with this system.
        # if someone can fix this please let me know
        self.asset = asset # (False,"club")
        self.cap = cap

# map is simply a collection of rooms to be sent to the client, or if this is a client, this is to simply be stored on the client for easy access.
class Map(Networkable):
    def __init__(self, id, rooms):
        Networkable.__init__(self, id)
        self.type = "map"
        self.rooms = rooms
    def serialize(self):
        data_out = {
            "type":self.type,
            "id":self.id
        }
        rooms_out = {}
        for key in self.rooms.keys():
            rm = self.rooms[key]
            rooms_out[key] = {
                "name":rm.name,
                "asset":rm.asset,
                "cap":rm.cap
            }
        data_out["rooms"] = rooms_out
        return json.dumps(data_out)
    def deserialize(self,data):
        if (self.id == 0): #only change ID if our current ID is unknown
            self.id = data["id"]
        self.rooms = {}
        for key in data["rooms"].keys():
            elm = data["rooms"][key]
            curR = Room(elm["name"],tuple(elm["asset"]),elm["cap"])
            self.rooms[key] = curR
        return self