import socket
from shared import * # import the shared stuff between server and client
from _thread import *
import sys
import helpers
import logger
import json
import secrets
import importlib

class ServerRoot:
    def __init__(self):
        self.current_id = 0
        self.network_objects = [] #all the network objects
        self.room_messages = {} # map of all the messages in the rooms
        self.current_connections = {

        } #a dictionary of connections to their corresponding player objects
        self.map = None

    def get_next_valid_id(self): #gets and returns the next valid id. the current id system is placeholder
        self.current_id = self.current_id + 1
        return self.current_id
    
    def load_map(self, filename):
        self.map = Map(0,{}).deserialize(helpers.read_json(filename))
        for key in self.map.rooms.keys():
            self.room_messages[key] = ("","...")

    def add_to_net(self,obj): #adds a newly created networkable to the network objects and assigns it a valid id, then sends it to the client
        obj.id = self.get_next_valid_id()
        self.network_objects.append(obj)
        # tell old clients that this object now exists and they should add it to their list.
        self.send_to_all_cons({
            "type":"add_object",
            "object":obj.serialize()
        })
        return obj

    def delete_net(self,obj):
        # tell old clients to remove this object from their list based off of the ID.
        self.send_to_all_cons({
            "type":"delete_object",
            "object":obj.id
        })
        self.network_objects.remove(obj)

    def send_to_all_cons(self,raw_data):
        data = str.encode(network_create_packet(raw_data))
        for key in self.current_connections.keys():
            key.sendall(data)
    
    # relay a user sent packet to all the clients that didnt get it.
    def relay_to_all_cons(self,raw_data,sender,includesender=False):
        raw_data["sender_id"] = self.current_connections[sender].id
        dat_no_encode = network_create_packet(raw_data)
        logger.log("relaying: " + dat_no_encode)
        data = str.encode(dat_no_encode)
        for key in self.current_connections.keys():
            if (key != sender) or (includesender):
                key.sendall(data)

    def actor_leave_room(self,cl_actor):
        if self.room_messages[cl_actor.room][0] == cl_actor.name:
            self.room_messages[cl_actor.room] = ("","...")
            self.send_to_all_cons({
                "type":"chat",
                "message":"...",
                "name":"",
                "room":cl_actor.room
            })

    def get_actors_in_room(self,rm_id):
        count = 0
        for obj in self.network_objects:
            if (obj.type == "playeractor"):
                if obj.room == rm_id:
                    count += 1
        return count

SR = ServerRoot()

def sanitize_text(text):
    text = text.replace("[","[[")
    return text

config = helpers.read_config("config.ini")

server = config["NETWORK"]["Address"]
port = int(config["NETWORK"]["Port"])
max_read = int(config["NETWORK"]["MaxRead"])

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)

logger.log("Loading " + config["SERVER"]["Map"] + " as map...")
SR.load_map(config["SERVER"]["Map"])

logger.log("Loaded map succesfully.")

logger.log("Attempting to load plugins...")

plugins = []

plugins_config = config["SERVER"]["Plugins"].split(",")

if (plugins_config[0] == ""):
    plugins_config = []

for name in plugins_config:
    lib = importlib.import_module("plugins." + name,".")
    plugin = lib.Plugin(SR)
    logger.log("Succesfully loaded:" + plugin.name)
    plugins.append(plugin) # create that plugins associated object

logger.log("Plugins succesfully loaded.")

def threaded_client(conn):
    # time to create the player object and send it to the player
    cl_actor = SR.add_to_net(PlayerActor(0,"club"))
    cl_player = SR.add_to_net(Player(0,cl_actor.id,secrets.token_urlsafe(16)))
    logger.log("Player with net id:" + str(cl_player.id) + " joined, sending greeting packet.")

    SR.current_connections[conn] = cl_player #add connection to connection list
    conn.send(str.encode(
        network_create_packet({
            #"type":"" # the client already knows what type of packet this is we dont need to specify
            "secret":cl_player.priv_key,
            "player":cl_player.id,
            "map":SR.map.serialize(),
            "netobjs":network_serialize_objects(SR.network_objects),
            "room_messages":json.dumps(SR.room_messages)
        })
    ))

    reply = ""
    while True:
        try:
            data = conn.recv(max_read)
            reply = data.decode("utf-8")

            if not data:
                logger.log("Disconnected")
                break
            else:
                # logger.log("Received: ", reply)
                # attempt to decode data
                pack_dat = {}
                try:
                    pack_dat = json.loads(reply)
                except:
                    continue
                packet_type = pack_dat["type"]
                # run plugin stuff
                skip_execution = False
                for plug in plugins:
                    if skip_execution:
                        continue
                    skip_execution = not plug.prePacket(pack_dat,(cl_player,cl_actor))
                if skip_execution:
                    continue

                if packet_type == "changeusername":
                    cl_player.username = pack_dat["username"]
                    cl_actor.name = pack_dat["username"]
                    logger.log(str(cl_player.id) + " changed name to: " + cl_player.username)
                    SR.relay_to_all_cons(pack_dat,conn,True)
                elif packet_type == "chat":
                    pack_dat["message"] = sanitize_text(pack_dat["message"])
                    SR.room_messages[cl_actor.room] = (cl_player.username,pack_dat["message"])
                    logger.log(str(cl_player.username) + " chatted in " + cl_actor.room + ":" + pack_dat["message"])
                    if pack_dat.get("name_override") == None:
                        pack_dat["name"] = cl_player.username
                    else:
                        pack_dat["name"] = pack_dat["name_override"]
                        pack_dat.pop("name_override")
                    if pack_dat.get("room_override") == None:
                        pack_dat["room"] = cl_actor.room
                    else:
                        pack_dat["room"] = pack_dat["room_override"]
                        pack_dat.pop("room_override")
                    SR.relay_to_all_cons(pack_dat,conn,True)
                elif packet_type == "change_char":
                    cl_actor.character = pack_dat["character"]
                    logger.log(str(cl_player.username) + " changed character to: " + pack_dat["character"])
                    SR.relay_to_all_cons(pack_dat,conn,True)
                elif packet_type == "change_room":
                    if SR.get_actors_in_room(pack_dat["room"]) < SR.map.rooms[pack_dat["room"]].cap:
                        cl_actor.room = pack_dat["room"]
                        logger.log(str(cl_player.username) + " changed room to: " + pack_dat["room"])
                        SR.relay_to_all_cons(pack_dat,conn,True)
                        SR.actor_leave_room(cl_actor)
                    else:
                        logger.log(str(cl_player.username) + " attempted to change room to : " + pack_dat["room"] + " but room was full.")
                    
                for plug in plugins:
                    plug.postPacket(pack_dat,(cl_player,cl_actor))
        except Exception as e:
            logger.log(e)
            break
    
    SR.current_connections.pop(conn) #remove connection to connection list

    SR.actor_leave_room(cl_actor)

    # bug, don't know if its client exclusive but leaving players dont get their actors deleted properly
    logger.log("Lost connection with PLAYER ID " + str(cl_player.id) + "...")
    SR.delete_net(cl_actor)
    SR.delete_net(cl_player)
    conn.close()


def server_loop():
    while True:
        conn, addr = s.accept()
        # print("Connected to:", addr)

        start_new_thread(threaded_client, (conn,))

start_new_thread(server_loop, tuple())

while True:
    command_raw = input("")
    parameters_unsanitized = command_raw.split(" ")
    parameters = []
    string_reads = 0
    current_parm = ""
    # this currently has some failure/bug cases. such as ""hey"" or " hey " "
    for pm in parameters_unsanitized:
        if (pm.startswith("\"")):
            if string_reads == 0:
                pm = pm.lstrip("\"")
            string_reads += 1
        if (pm.endswith("\"")):
            if string_reads == 1:
                pm = pm.rstrip("\"")
            string_reads -= 1
        current_parm += pm + " "
        if (string_reads == 0):
            parameters.append(current_parm.strip())
            current_parm = ""
    command = parameters.pop(0)
    if command == "list":
        if parameters[0] == "all":
            for obj in SR.network_objects:
                logger.log(str(obj))
        else:
            for obj in SR.network_objects:
                if obj.type == parameters[0]:
                    logger.log(str(obj))
    else:
        for plug in plugins:
            plug.onCommand(command,parameters)
        
    
        
        