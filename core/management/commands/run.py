import time
import json
import requests

from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from core.parser import Parser


class Command(BaseCommand):
    help = "Parses the zkill feed"

    def add_arguments(self, parser):
        parser.add_argument("config", type=str)

    def handle(self, *args, **options):
        # Load config
        with open("%s.json" % options['config'], "r") as config_file:
            configs = json.load(config_file)

        # Set up parsers
        parsers = []
        for config in configs:
            parsers.append(Parser(config))

        queue_id = get_random_string(length=32)
        while True:
            # Fetch killmail
            r = requests.get("https://redisq.zkillboard.com/listen.php?queueID=%s" % queue_id)

            if r.status_code == 429:
                print("Received an HTTP 429, waiting 60 seconds before trying for another killmail")
                time.sleep(60)
            elif r.status_code == 200:
                r = r.json()
                package = r.get("package")
                if package is not None:
                    for parser in parsers:
                        print(package.get('killID'), parser.name, parser.parse(package))
            else:
                print("We get a strange HTTP Error %s, so lets chill for 60 seconds" % r.status_code)