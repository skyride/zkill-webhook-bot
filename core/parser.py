import requests

from sde.models import System, Type, Group, Category


# Parses a redisq object
class Parser:
    def __init__(self, config):
        # Webhooks should be a list of URLs
        self.name = config.get("name", "")
        self.webhooks = config.get("webhooks", [])

        # Normalise filters as lists
        self.filters = {}
        for key, values in config["filters"].items():
            if isinstance(values, list):
                self.filters[key] = values
            else:
                self.filters[key] = [values]


    def parse(self, package):
        # Return False if we find a filter it doesn't pass
        for f in self.filters.keys():
            f = getattr(self, f)
            if not f(package):
                return False

        self.send(package)
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

    def attacker_type_id(self, package, values=None):
        values = values or self.filters.get("attacker_type_id")
        return len(
            set(
                self.attacker_property(package, "ship_type_id")
            ).intersection(
                set(values)
            )
        )

    def attacker_group_id(self, package, values=None):
        values = values or self.filters.get("attacker_group_id")
        return Group.objects.filter(
            types__id__in=self.attacker_property(package, "ship_type_id"),
            id__in=values
        ).exists()

    def attacker_category_id(self, package, values=None):
        values = values or self.filters.get("attacker_category_id")
        return Category.objects.filter(
            groups__types__id__in=self.attacker_property(package, "ship_type_id"),
            id__in=values
        ).exists()

    def attacker_corporation_id(self, package, values=None):
        values = values or self.filters.get("attacker_corporation_id")
        return len(
            set(
                self.attacker_property(package, "alliance_id")
            ).intersection(
                set(values)
            )
        )

    def attacker_alliance_id(self, package, values=None):
        values = values or self.filters.get("attacker_alliance_id")
        return len(
            set(
                self.attacker_property(package, "alliance_id")
            ).intersection(
                set(values)
            )
        )

    def victim_type_id(self, package, values=None):
        values = values or self.filters.get("victim_type_id")
        return package['killmail']['victim'].get("ship_type_id") in values

    def victim_group_id(self, package, values=None):
        values = values or self.filters.get("victim_group_id")
        return Type.objects.filter(
            id=package['killmail']['victim'].get("ship_type_id"),
            group_id__in=values
        ).exists()

    def victim_category_id(self, package, values=None):
        values = values or self.filters.get("victim_category_id")
        return Type.objects.filter(
            id=package['killmail']['victim'].get("ship_type_id"),
            group__category_id__in=values
        ).exists()

    def victim_corporation_id(self, package, values=None):
        values = values or self.filters.get("victim_corporation_id")
        return package['killmail']['victim'].get("corporation_id") in values

    def victim_alliance_id(self, package, values=None):
        values = values or self.filters.get("victim_alliance_id")
        return package['killmail']['victim'].get("alliance_id") in values

    def wspace(self, package):
        wspace = self.filters.get("wspace")[0]
        if wspace:
            return package['killmail']['solar_system_id'] > 31000000
        else:
            return not package['killmail']['solar_system_id'] > 31000000


    # Combined
    def type_id(self, package):
        values = self.filters.get("type_id")
        return self.attacker_type_id(package, values) or self.victim_type_id(package, values)

    def group_id(self, package):
        values = self.filters.get("group_id")
        return self.attacker_group_id(package, values) or self.victim_group_id(package, values)

    def category_id(self, package):
        values = self.filters.get("category_id")
        return self.attacker_category_id(package, values) or self.victim_category_id(package, values)

    def corporation_id(self, package):
        values = self.filters.get("corporation_id")
        return self.attacker_corporation_id(package, values) or self.victim_corporation_id(package, values)

    def alliance_id(self, package):
        values = self.filters.get("alliance_id")
        return self.attacker_alliance_id(package, values) or self.victim_alliance_id(package, values)


    # Send webhook
    def send(self, package):
        for webhook in self.webhooks:
            requests.post(
                webhook.get("url"),
                json={
                    "content": "%s https://zkillboard.com/kill/%s/" % (
                        webhook.get("prefix", ""),
                        package['killID']
                    )
                }
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