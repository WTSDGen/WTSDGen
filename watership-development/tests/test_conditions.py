import unittest

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import ujson

from scripts.rabbit.rabbits import Rabbit
from scripts.conditions import medical_rabbits_condition_fulfilled

class TestsMedCondition(unittest.TestCase):
    def test_fulfilled(self):
        rabbit1 = Rabbit(months=20)
        rabbit1.status = "rabbit"

        healer = Rabbit(months=20)
        healer.status = "healer"

        all_rabbits = [rabbit1, healer]
        self.assertTrue(medical_rabbits_condition_fulfilled(all_rabbits, 15))

    def test_fulfilled_many_rabbits(self):
        rabbit1 = Rabbit(months=20)
        rabbit1.status = "rabbit"
        rabbit2 = Rabbit(months=20)
        rabbit2.status = "rabbit"
        rabbit3 = Rabbit(months=20)
        rabbit3.status = "rabbit"
        rabbit4 = Rabbit(months=20)
        rabbit4.status = "rabbit"

        healer1 = Rabbit(months=20)
        healer1.status = "healer"
        healer2 = Rabbit(months=20)
        healer2.status = "healer"

        all_rabbits = [rabbit1, rabbit2, rabbit3, rabbit4, healer1, healer2]
        self.assertTrue(medical_rabbits_condition_fulfilled(all_rabbits, 2))

    def test_injured_fulfilled(self):
        rabbit1 = Rabbit(months=20)
        rabbit1.status = "rabbit"

        healer = Rabbit(months=20)
        healer.status = "healer"
        healer.injuries["small cut"] = {"severity": "minor"}

        all_rabbits = [rabbit1, healer]
        self.assertTrue(medical_rabbits_condition_fulfilled(all_rabbits, 15))

    def test_illness_fulfilled(self):
        rabbit1 = Rabbit(months=20)
        rabbit1.status = "rabbit"

        healer = Rabbit(months=20)
        healer.status = "healer"
        healer.illnesses["running nose"] = {"severity": "minor"}

        all_rabbits = [rabbit1, healer]
        self.assertTrue(medical_rabbits_condition_fulfilled(all_rabbits, 15))



class TestsIllnesses(unittest.TestCase):
    def load_resources(self):
        resource_directory = "resources/dicts/conditions/"

        ILLNESSES = None
        with open(f"{resource_directory}Illnesses.json", 'r') as read_file:
            ILLNESSES = ujson.loads(read_file.read())
        return ILLNESSES


class TestInjury(unittest.TestCase):
    def load_resources(self):
        resource_directory = "resources/dicts/conditions/"

        INJURIES = None
        with open(f"{resource_directory}Injuries.json", 'r') as read_file:
            INJURIES = ujson.loads(read_file.read())
        return INJURIES
    