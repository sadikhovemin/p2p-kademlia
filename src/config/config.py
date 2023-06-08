import configparser
import os

config = configparser.ConfigParser()
dir_path = os.path.dirname(os.path.realpath(__file__))

config_path = os.path.join(dir_path, "settings.ini")
config.read(config_path)

dht_config = config["dht"]