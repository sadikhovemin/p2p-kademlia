import configparser

config = configparser.ConfigParser()
config.read('settings.ini')

dht_config = config["dht"]