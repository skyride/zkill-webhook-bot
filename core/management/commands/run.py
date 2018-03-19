from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Parses the zkill feed"

    def handle(self, *args, **options):
        pass