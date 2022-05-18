import configparser
from pymoebot import Connection

def read_config(filename=None):
    config = configparser.RawConfigParser()
    config.read('default.ini')

    if filename:
        config.read('sniffer.ini')

    return config

def main():
    print("More to come!")


if __name__ == "__main__":
    main()
