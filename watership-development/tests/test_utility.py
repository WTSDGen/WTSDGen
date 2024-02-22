import unittest

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from scripts.rabbit.rabbits import Rabbit
from scripts.rabbit_relations.relationship import Relationship
from scripts.utility import (
    get_highest_romantic_relation, 
    get_personality_compatibility, 
    get_amount_of_rabbits_with_relation_value_towards,
    get_alive_warren_queens
)

class TestPersonalityCompatibility(unittest.TestCase):

    current_traits = [
        'adventurous', 'altruistic', 'ambitious', 'bloodthirsty', 'bold',
        'calm', 'careful', 'charismatic', 'childish', 'cold', 'compassionate',
        'confident', 'daring', 'empathetic', 'faithful', 'fierce', 'insecure',
        'lonesome', 'loving', 'loyal', 'nervous', 'patient', 'playful',
        'responsible', 'righteous', 'shameless', 'sneaky', 'strange', 'strict',
        'thoughtful', 'troublesome', 'vengeful', 'wise'
    ]

    def test_some_neutral_combinations(self):
        # TODO: the one who updated the personality should update the tests!!
        pass
        #rabbit1 = Rabbit()
        #rabbit2 = Rabbit()
#
        #rabbit1.personality.trait = self.current_traits[0]
        #rabbit2.personality.trait = self.current_traits[1]
        #self.assertIsNone(get_personality_compatibility(rabbit1,rabbit2))
        #self.assertIsNone(get_personality_compatibility(rabbit2,rabbit1))
#
        #rabbit1.personality.trait = self.current_traits[3]
        #rabbit2.personality.trait = self.current_traits[5]
        #self.assertIsNone(get_personality_compatibility(rabbit1,rabbit2))
        #self.assertIsNone(get_personality_compatibility(rabbit2,rabbit1))
#
        #rabbit1.personality.trait = self.current_traits[7]
        #rabbit2.personality.trait = self.current_traits[10]
        #self.assertIsNone(get_personality_compatibility(rabbit1,rabbit2))
        #self.assertIsNone(get_personality_compatibility(rabbit2,rabbit1))

    def test_some_positive_combinations(self):
        # TODO: the one who updated the personality should update the tests!!
        pass
        #rabbit1 = Rabbit()
        #rabbit2 = Rabbit()
#
        #rabbit1.personality.trait = self.current_traits[1]
        #rabbit2.personality.trait = self.current_traits[18]
        #self.assertTrue(get_personality_compatibility(rabbit1,rabbit2))
        #self.assertTrue(get_personality_compatibility(rabbit2,rabbit1))
#
        #rabbit1.personality.trait = self.current_traits[3]
        #rabbit2.personality.trait = self.current_traits[4]
        #self.assertTrue(get_personality_compatibility(rabbit1,rabbit2))
        #self.assertTrue(get_personality_compatibility(rabbit2,rabbit1))
#
        #rabbit1.personality.trait = self.current_traits[5]
        #rabbit2.personality.trait = self.current_traits[17]
        #self.assertTrue(get_personality_compatibility(rabbit1,rabbit2))
        #self.assertTrue(get_personality_compatibility(rabbit2,rabbit1))

    def test_some_negative_combinations(self):
        # TODO: the one who updated the personality should update the tests!!
        pass
        #rabbit1 = Rabbit()
        #rabbit2 = Rabbit()
#
        #rabbit1.personality.trait = self.current_traits[1]
        #rabbit2.personality.trait = self.current_traits[2]
        #self.assertFalse(get_personality_compatibility(rabbit1,rabbit2))
        #self.assertFalse(get_personality_compatibility(rabbit2,rabbit1))
#
        #rabbit1.personality.trait = self.current_traits[3]
        #rabbit2.personality.trait = self.current_traits[6]
        #self.assertFalse(get_personality_compatibility(rabbit1,rabbit2))
        #self.assertFalse(get_personality_compatibility(rabbit2,rabbit1))
#
        #rabbit1.personality.trait = self.current_traits[8]
        #rabbit2.personality.trait = self.current_traits[9]
        #self.assertFalse(get_personality_compatibility(rabbit1,rabbit2))
        #self.assertFalse(get_personality_compatibility(rabbit2,rabbit1))

    def test_false_trait(self):
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()
        rabbit1.personality.trait = None
        rabbit2.personality.trait = None
        self.assertIsNone(get_personality_compatibility(rabbit1,rabbit2))
        self.assertIsNone(get_personality_compatibility(rabbit2,rabbit1))

class TestCountRelation(unittest.TestCase):
    def test_2_rabbits_jealousy(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()
        rabbit3 = Rabbit()
        rabbit4 = Rabbit()

        relation_1_2 = Relationship(rabbit_from=rabbit1,rabbit_to=rabbit2)
        relation_3_2 = Relationship(rabbit_from=rabbit3,rabbit_to=rabbit2)
        relation_4_2 = Relationship(rabbit_from=rabbit4,rabbit_to=rabbit2)
        rabbit1.relationships[rabbit2.ID] = relation_1_2
        rabbit3.relationships[rabbit2.ID] = relation_3_2
        rabbit4.relationships[rabbit2.ID] = relation_4_2
        relation_1_2.link_relationship()
        relation_3_2.link_relationship()
        relation_4_2.link_relationship()

        # when
        relation_1_2.jealousy += 20
        relation_3_2.jealousy += 20
        relation_4_2.jealousy += 10

        #then
        relation_dict = get_amount_of_rabbits_with_relation_value_towards(rabbit2,20,[rabbit1,rabbit2,rabbit3,rabbit4])

        self.assertEqual(relation_dict["romantic_love"],0)
        self.assertEqual(relation_dict["platonic_like"],0)
        self.assertEqual(relation_dict["dislike"],0)
        self.assertEqual(relation_dict["admiration"],0)
        self.assertEqual(relation_dict["comfortable"],0)
        self.assertEqual(relation_dict["jealousy"],2)
        self.assertEqual(relation_dict["trust"],0)

class TestHighestRomance(unittest.TestCase):
    def test_exclude_mate(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()
        rabbit3 = Rabbit()
        rabbit4 = Rabbit()

        # when
        rabbit1.mate.append(rabbit2.ID)
        rabbit2.mate.append(rabbit1.ID)
        relation_1_2 = Relationship(rabbit_from=rabbit1,rabbit_to=rabbit2, mates=True)
        relation_1_3 = Relationship(rabbit_from=rabbit1,rabbit_to=rabbit3)
        relation_1_4 = Relationship(rabbit_from=rabbit1,rabbit_to=rabbit4)
        relation_1_2.romantic_love = 60
        relation_1_3.romantic_love = 50
        relation_1_4.romantic_love = 40

        relations = [relation_1_2, relation_1_3, relation_1_4]

        #then
        self.assertNotEqual(relation_1_2, get_highest_romantic_relation(relations, exclude_mate=True))
        self.assertEqual(relation_1_3, get_highest_romantic_relation(relations, exclude_mate=True))
        self.assertNotEqual(relation_1_4, get_highest_romantic_relation(relations, exclude_mate=True))

    def test_include_mate(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()
        rabbit3 = Rabbit()
        rabbit4 = Rabbit()

        # when
        rabbit1.mate.append(rabbit2.ID)
        rabbit2.mate.append(rabbit1.ID)
        relation_1_2 = Relationship(rabbit_from=rabbit1,rabbit_to=rabbit2, mates=True)
        relation_1_3 = Relationship(rabbit_from=rabbit1,rabbit_to=rabbit3)
        relation_1_4 = Relationship(rabbit_from=rabbit1,rabbit_to=rabbit4)
        relation_1_2.romantic_love = 60
        relation_1_3.romantic_love = 50
        relation_1_4.romantic_love = 40

        relations = [relation_1_2, relation_1_3, relation_1_4]

        #then
        self.assertEqual(relation_1_2, get_highest_romantic_relation(relations, exclude_mate=False))
        self.assertNotEqual(relation_1_3, get_highest_romantic_relation(relations, exclude_mate=False))
        self.assertNotEqual(relation_1_4, get_highest_romantic_relation(relations, exclude_mate=False))

class TestGetQueens(unittest.TestCase):

    def setUp(self) -> None:
        self.test_rabbit1 = Rabbit()
        self.test_rabbit1.status = "rabbit"
        self.test_rabbit2 = Rabbit()
        self.test_rabbit2.status = "rabbit"
        self.test_rabbit3 = Rabbit()
        self.test_rabbit3.status = "rabbit"
        self.test_rabbit4 = Rabbit()
        self.test_rabbit4.status = "rabbit"
        self.test_rabbit5 = Rabbit()
        self.test_rabbit5.status = "rabbit"
        self.test_rabbit6 = Rabbit()
        self.test_rabbit6.status = "rabbit"

    def tearDown(self) -> None:
        del self.test_rabbit1
        del self.test_rabbit2
        del self.test_rabbit3
        del self.test_rabbit4
        del self.test_rabbit5
        del self.test_rabbit6

    def test_single_mother(self):
        # given
        # young enough kid
        self.test_rabbit1.gender = "doe"

        self.test_rabbit2.status = "kitten"
        self.test_rabbit2.parent1 = self.test_rabbit1.ID

        # too old kid
        self.test_rabbit3.gender = "doe"

        self.test_rabbit4.status = "rusasi"
        self.test_rabbit4.parent1 = self.test_rabbit3.ID

        # then
        living_rabbits = [self.test_rabbit1, self.test_rabbit2, self.test_rabbit3, self.test_rabbit4]
        self.assertEqual([self.test_rabbit1.ID], list(get_alive_warren_queens(living_rabbits)[0].keys()))

    def test_single_father(self):
        # given
        # young enough kid
        self.test_rabbit1.gender = "buck"

        self.test_rabbit2.status = "kitten"
        self.test_rabbit2.parent1 = self.test_rabbit1.ID

        # too old kid
        self.test_rabbit3.gender = "buck"

        self.test_rabbit4.status = "rusasi"
        self.test_rabbit4.parent1 = self.test_rabbit3.ID

        # then
        living_rabbits = [self.test_rabbit1, self.test_rabbit2, self.test_rabbit3, self.test_rabbit4]
        self.assertEqual([self.test_rabbit1.ID], list(get_alive_warren_queens(living_rabbits)[0].keys()))

    def tests_hetero_pair(self):
        # given
        # young enough kid
        self.test_rabbit1.gender = "doe"

        self.test_rabbit2.gender = "buck"

        self.test_rabbit3.status = "kitten"
        self.test_rabbit3.parent1 = self.test_rabbit2.ID
        self.test_rabbit3.parent2 = self.test_rabbit1.ID

        # too old kid
        self.test_rabbit4.gender = "doe"

        self.test_rabbit5.gender = "buck"

        self.test_rabbit6.status = "rusasi"
        self.test_rabbit6.parent1 = self.test_rabbit5.ID
        self.test_rabbit6.parent2 = self.test_rabbit4.ID

        # then
        living_rabbits = [self.test_rabbit1, self.test_rabbit2, self.test_rabbit3, self.test_rabbit4, self.test_rabbit5, self.test_rabbit6]
        self.assertEqual([self.test_rabbit1.ID], list(get_alive_warren_queens(living_rabbits)[0].keys()))

    def test_gay_pair(self):
        # given
        # young enough kid
        self.test_rabbit1.gender = "buck"

        self.test_rabbit2.gender = "buck"

        self.test_rabbit3.status = "kitten"
        self.test_rabbit3.parent1 = self.test_rabbit2.ID
        self.test_rabbit3.parent2 = self.test_rabbit1.ID

        # too old kid
        self.test_rabbit4.gender = "buck"

        self.test_rabbit5.gender = "buck"

        self.test_rabbit6.status = "rusasi"
        self.test_rabbit6.parent1 = self.test_rabbit5.ID
        self.test_rabbit6.parent2 = self.test_rabbit4.ID

        # then
        living_rabbits = [self.test_rabbit1, self.test_rabbit2, self.test_rabbit3, self.test_rabbit4, self.test_rabbit5, self.test_rabbit6]
        self.assertTrue(
            [self.test_rabbit1.ID] == list(get_alive_warren_queens(living_rabbits)[0].keys()) or [self.test_rabbit2.ID] == list(get_alive_warren_queens(living_rabbits)[0].keys())
        )

    def test_lesbian_pair(self):
        # given
        # young enough kid
        self.test_rabbit1.gender = "doe"

        self.test_rabbit2.gender = "doe"

        self.test_rabbit3.status = "kitten"
        self.test_rabbit3.parent1 = self.test_rabbit2.ID
        self.test_rabbit3.parent2 = self.test_rabbit1.ID

        # too old kid
        self.test_rabbit4.gender = "doe"

        self.test_rabbit5.gender = "doe"

        self.test_rabbit6.status = "rusasi"
        self.test_rabbit6.parent1 = self.test_rabbit5.ID
        self.test_rabbit6.parent2 = self.test_rabbit4.ID

        # then
        living_rabbits = [self.test_rabbit1, self.test_rabbit2, self.test_rabbit3, self.test_rabbit4, self.test_rabbit5, self.test_rabbit6]
        self.assertTrue(
            [self.test_rabbit1.ID] == list(get_alive_warren_queens(living_rabbits)[0].keys()) or [self.test_rabbit2.ID] == list(get_alive_warren_queens(living_rabbits)[0].keys())
        )

    def test_poly_pair(self):
        # given
        # young enough kid
        self.test_rabbit1.gender = "doe"

        self.test_rabbit2.gender = "doe"

        self.test_rabbit3.gender = "buck"

        self.test_rabbit4.status = "kitten"
        self.test_rabbit4.parent1 = self.test_rabbit2.ID
        self.test_rabbit4.parent2 = self.test_rabbit1.ID
        self.test_rabbit4.adoptive_parents.append(self.test_rabbit3.ID)

        # then
        living_rabbits = [self.test_rabbit1, self.test_rabbit2, self.test_rabbit3, self.test_rabbit4, self.test_rabbit5, self.test_rabbit6]
        self.assertEqual([self.test_rabbit2.ID], list(get_alive_warren_queens(living_rabbits)[0].keys()))
