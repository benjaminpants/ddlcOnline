import json
import configparser

def read_json(file):
    return json.loads(open(file,"r").read())

def read_config(file):
    config = configparser.ConfigParser()
    config.read(file)
    return config