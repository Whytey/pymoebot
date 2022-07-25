import asyncio
import configparser
import logging
import os

from pymoebot import MoeBot


def read_config(filename=None):
    config = configparser.RawConfigParser()
    config.read('default.ini')

    if filename:
        if os.path.exists(filename):
            logging.debug("Reading extra config from '%s'", filename)
            config.read('sniffer.ini')
        else:
            logging.warning("config file '%s' doesn't exist, ignoring.", filename)

    return config


def listener(msg):
    print(msg)


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
                        level=logging.INFO)
    logging.info("Started sniffer")

    config = read_config("sniffer.ini")

    moebot = MoeBot(config["MOEBOT"]["DEVICE_ID"],
                    config["MOEBOT"]["IP"],
                    config["MOEBOT"]["LOCAL_KEY"])
    logging.info("Got a MoeBot: %s" % moebot)

    moebot.add_listener(listener)
    # await moebot.listen()


if __name__ == "__main__":
    # asyncio.run(main())
    main()