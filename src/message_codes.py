from enum import Enum


class MessageCodes(Enum):
    DHT_PUT = 650
    DHT_GET = 651
    DHT_SUCCESS = 652
    DHT_FAILURE = 653
    DHT_PING = 654
    DHT_PONG = 655
    DHT_FIND_NODE = 656
    DHT_FIND_VALUE = 657