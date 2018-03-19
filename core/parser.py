import requests

from sde.models import System


# Parses a redisq object
class Parser:
    filters = {}

    def __init__(self, config):
        # Webhooks should be a list of URLs
        self.name = config.get("name", "")
        self.webhooks = config.get("webhooks", [])

        # Normalise filters as lists
        for key, values in config.get("filters", {}).items():
            if isinstance(values, list):
                self.filters[key] = values
            else:
                self.filters[key] = [values]


    def parse(self, package):
        # Return False if we find a filter it doesn't pass
        for filter in self.filters.keys():
            filter = getattr(self, filter)
            if not filter(package):
                return False

        return True


    def region_id(self, package):
        values = self.filters.get("region_id")
        system = System.objects.get(id=package['killmail']['solar_system_id'])
        return system.region_id in values