import socket
import threading
import json
import ctypes


class Network:
    def __init__(self, addr, packet_handler_func):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = addr[0]
        self.port = addr[1]
        self.addr = addr
        self.greetingpacket = self.connect()
        self.last_data = None
        self.connect_thread = None
        self.phf = packet_handler_func
        self.connected = True
        self.begin_consistent_connection()
    
    def pop_last_data(self):
        if (self.last_data == None):
            return None
        else:
            to_return = self.last_data
            self.last_data = None
            return to_return

    def wait_til_data(self):
        data_to_return = None
        while data_to_return == None:
            data_to_return = self.pop_last_data()
        return data_to_return

    def data_thread(self):
        data = None
        while self.connected:
            try:
                try:
                    data = self.client.recv(4096)
                    if not self.connected:
                        raise Exception("God damn disconnect from the server already fuck my life.")
                except:
                    data = None
                if data == None:
                    break
                # This is a working theory, if I'm correct, this should resolve any potential mishaps.
                data_lines = []
                try:
                    data_lines = data.decode().split("\n")
                except:
                    print("Error while attempted to decode server message.")
                    continue
                for l in data_lines:
                    if (l.strip() == ""):
                        continue
                    self.last_data = l
                    
                    decoded_data = json.loads(self.last_data)
                    packet_type = decoded_data["type"]
                    if self.phf(self,packet_type,decoded_data):
                        self.last_data = None
            except Exception as e:
                print(e)
        print("Connection closed or otherwise ended.")
        self.disconnect()


    def connect(self):
        try:
            self.client.connect(self.addr)
            return self.client.recv(4096).decode()
        except:
            print("Connection failed!")
            pass

    def begin_consistent_connection(self):
        self.connect_thread = threading.Thread(target=self.data_thread)
        self.connect_thread.daemon = True
        self.connect_thread.start()

    def send(self, data, wait_for_response):
        try:
            self.client.send(str.encode(str(data)))
            if wait_for_response:
                return self.wait_til_data()
            else:
                return True
        except socket.error as e:
            print(e)
            if wait_for_response:
                return None
            else:
                return False

    def disconnect(self):
        self.client.close()
        self.connected = False