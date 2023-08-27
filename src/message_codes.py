from enum import Enum


class MessageCodes(Enum):
    DHT_PUT = 650
    DHT_GET = 651
    DHT_SUCCESS = 652
    DHT_FAILURE = 653
    DHT_PING = 654
    DHT_PONG = 655
    DHT_FIND_NODE = 656
    DHT_NODE_REPLY = 657
    DHT_FIND_VALUE = 658
    DHT_FOUND_PEERS = 659
