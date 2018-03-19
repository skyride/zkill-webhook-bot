import requests

from sde.models import System, Group, Category


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


    # Filters
    def region_id(self, package):
        values = self.filters.get("region_id")
        system = System.objects.get(id=package['killmail']['solar_system_id'])
        return system.region_id in values

    def constellation_id(self, package):
        values = self.filters.get("constellation_id")
        system = System.objects.get(id=package['killmail']['solar_system_id'])
        return system.constellation_id in values

    def system_id(self, package):
        return package['killmail']['solar_system_id'] in self.filters.get("system_id")

    def isk(self, package):
        return package['zkb']['totalValue'] > self.filters.get("isk")[0]

    def attacker_type_id(self, package):
        values = self.filters.get("attacker_type_id")
        return len(
            set(
                self.attacker_property(package, "ship_type_id")
            ).intersection(
                set(values)
            )
        )

    def attacker_group_id(self, package):
        values = self.filters.get("attacker_group_id")
        return Group.objects.filter(
            types__id__in=self.attacker_property(package, "ship_type_id"),
            id__in=values
        ).exists()

    def attacker_category_id(self, package):
        values = self.filters.get("attacker_category_id")
        return Category.objects.filter(
            groups__types__id__in=self.attacker_property(package, "ship_type_id"),
            id__in=values
        ).exists()

    def attacker_corporation_id(self, package):
        values = self.filters.get("attacker_corporation_id")
        return len(
            set(
                self.attacker_property(package, "alliance_id")
            ).intersection(
                set(values)
            )
        )

    def attacker_alliance_id(self, package):
        values = self.filters.get("attacker_alliance_id")
        return len(
            set(
                self.attacker_property(package, "alliance_id")
            ).intersection(
                set(values)
            )
        )
        

    # Gets a specific property from the attackers
    def attacker_property(self, package, key):
        return list(
            filter(
                lambda x: x != None,
                map(
                    lambda x: x.get(key),
                    package['killmail']['attackers']
                )
            )
        )