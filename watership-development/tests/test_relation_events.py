import unittest
from unittest.mock import patch

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from scripts.rabbit_relations.relationship import Relationship
from scripts.events_module.relationship.pregnancy_events import Pregnancy_Events
from scripts.events_module.relationship.romantic_events import Romantic_Events
from scripts.rabbit.rabbits import Rabbit
from scripts.warren import Warren

class CanHaveKits(unittest.TestCase):
    def test_prevent_kits(self):
        # given
        rabbit = Rabbit()
        rabbit.no_kits = True

        # then
        self.assertFalse(Pregnancy_Events.check_if_can_have_kits(rabbit,single_parentage=True, allow_affair=True))

    @patch('scripts.events_module.relationship.pregnancy_events.Pregnancy_Events.check_if_can_have_kits')
    def test_no_kit_setting(self, check_if_can_have_kits):
        # given
        test_warren = Warren(name="warren")
        test_warren.pregnancy_data = {}
        rabbit1 = Rabbit(gender = 'doe')
        rabbit1.no_kittens = True
        rabbit2 = Rabbit(gender = 'buck')

        rabbit1.mate.append(rabbit2.ID)
        rabbit2.mate.append(rabbit1.ID)
        relation1 = Relationship(rabbit1, rabbit2,mates=True,family=False,romantic_love=100)
        relation2 = Relationship(rabbit2, rabbit1,mates=True,family=False,romantic_love=100)
        rabbit1.relationships[rabbit2.ID] = relation1
        rabbit2.relationships[rabbit1.ID] = relation2

        # when
        check_if_can_have_kits.return_value = True
        Pregnancy_Events.handle_having_kits(rabbit=rabbit1,warren=test_warren)

        # then
        self.assertNotIn(rabbit1.ID, test_warren.pregnancy_data.keys())

class SameSexAdoptions(unittest.TestCase):
    def test_kits_are_adopted(self):
        # given

        rabbit1 = Rabbit(gender = 'doe', age = "adult", moons=40)
        rabbit2 = Rabbit(gender = 'doe', age = "adult", moons=40)
        rabbit1.mate.append(rabbit2.ID)
        rabbit2.mate.append(rabbit1.ID)

        # when
        single_parentage = False
        allow_affair = False
        self.assertTrue(Pregnancy_Events.check_if_can_have_kits(rabbit1, single_parentage, allow_affair))
        self.assertTrue(Pregnancy_Events.check_if_can_have_kits(rabbit2, single_parentage, allow_affair))

        can_have_kits, kits_are_adopted = Pregnancy_Events.check_second_parent(
            rabbit=rabbit1,
            second_parent=rabbit2,
            single_parentage=single_parentage,
            allow_affair=allow_affair,
            same_sex_birth=False,
            same_sex_adoption=True
        )
        self.assertTrue(can_have_kits)
        self.assertTrue(kits_are_adopted)

class Pregnancy(unittest.TestCase):
    @patch('scripts.events_module.relationship.pregnancy_events.Pregnancy_Events.check_if_can_have_kits')
    def test_single_rabbit_doe(self, check_if_can_have_kits):
        # given
        warren = Warren(name="warren")
        rabbit = Rabbit(gender = 'doe')
        warren.pregnancy_data = {}

        # when
        check_if_can_have_kits.return_value = True
        Pregnancy_Events.handle_zero_month_pregnant(rabbit,None,warren)

        # then
        self.assertIn(rabbit.ID, warren.pregnancy_data.keys())

    @patch('scripts.events_module.relationship.pregnancy_events.Pregnancy_Events.check_if_can_have_kits')
    def test_pair(self, check_if_can_have_kits):
        # given
        warren = Warren(name="warren")
        rabbit1 = Rabbit(gender = 'doe')
        rabbit2 = Rabbit(gender = 'buck')

        warren.pregnancy_data = {}

        # when
        check_if_can_have_kits.return_value = True
        Pregnancy_Events.handle_zero_month_pregnant(rabbit1,rabbit2,warren)

        # then
        self.assertIn(rabbit1.ID, warren.pregnancy_data.keys())
        self.assertEqual(warren.pregnancy_data[rabbit1.ID]["second_parent"], rabbit2.ID)

class Mates(unittest.TestCase):
    def test_platonic_kitten_mating(self):
        # given
        rabbit1 = Rabbit(moons=3)
        rabbit2 = Rabbit(moons=3)

        relationship1 = Relationship(rabbit1,rabbit2)
        relationship2 = Relationship(rabbit2,rabbit1)
        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        rabbit1.relationships[rabbit2.ID] = relationship1
        rabbit2.relationships[rabbit1.ID] = relationship2

        # when
        relationship1.platonic_like = 100
        relationship2.platonic_like = 100

        # then
        self.assertFalse(Romantic_Events.check_if_new_mate(rabbit1,rabbit2)[0])

    def test_platonic_rusasi_mating(self):
        # given
        rabbit1 = Rabbit(moons=6)
        rabbit2 = Rabbit(moons=6)

        relationship1 = Relationship(rabbit1,rabbit2)
        relationship2 = Relationship(rabbit2,rabbit1)
        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        rabbit1.relationships[rabbit2.ID] = relationship1
        rabbit2.relationships[rabbit1.ID] = relationship2

        # when
        relationship1.platonic_like = 100
        relationship2.platonic_like = 100

        # then
        self.assertFalse(Romantic_Events.check_if_new_mate(rabbit1,rabbit2)[0])

    def test_romantic_kitten_mating(self):
        # given
        rabbit1 = Rabbit(moons=3)
        rabbit2 = Rabbit(moons=3)

        relationship1 = Relationship(rabbit1,rabbit2)
        relationship2 = Relationship(rabbit2,rabbit1)
        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        rabbit1.relationships[rabbit2.ID] = relationship1
        rabbit2.relationships[rabbit1.ID] = relationship2

        # when
        relationship1.romantic_love = 100
        relationship2.romantic_love = 100

        # then
        self.assertFalse(Romantic_Events.check_if_new_mate(rabbit1,rabbit2)[0])

    def test_romantic_rusasi_mating(self):
        # given
        rabbit1 = Rabbit(moons=6)
        rabbit2 = Rabbit(moons=6)

        relationship1 = Relationship(rabbit1,rabbit2)
        relationship2 = Relationship(rabbit2,rabbit1)
        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        rabbit1.relationships[rabbit2.ID] = relationship1
        rabbit2.relationships[rabbit1.ID] = relationship2

        # when
        relationship1.romantic_love = 100
        relationship2.romantic_love = 100

        # then
        self.assertFalse(Romantic_Events.check_if_new_mate(rabbit1,rabbit2)[0])
