from copy import deepcopy
import unittest
from unittest.mock import patch

import os


os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from scripts.rabbit.rabbits import Rabbit
from scripts.rabbit_relations.relationship import Relationship


class TestCreationAge(unittest.TestCase):

    def test_kitten(self):
        test_rabbit = Rabbit(moons=5)
        self.assertEqual(test_rabbit.age,"kit")

    def test_adolescent(self):
        test_rabbit = Rabbit(moons=6)
        self.assertEqual(test_rabbit.age,"adolescent")

    def test_young_adult(self):
        test_rabbit = Rabbit(moons=12)
        self.assertEqual(test_rabbit.age,"young adult")
    
    def test_adult(self):
        test_rabbit = Rabbit(moons=48)
        self.assertEqual(test_rabbit.age,"adult")

    def test_senior_adult(self):
        test_rabbit = Rabbit(moons=96)
        self.assertEqual(test_rabbit.age,"senior adult")

    def test_elder(self):
        test_rabbit = Rabbit(moons=120)
        self.assertEqual(test_rabbit.age,"senior")

class TestRelativesFunction(unittest.TestCase):

    def test_is_parent(self):
        parent = Rabbit()
        kit = Rabbit(parent1=parent.ID)
        self.assertFalse(kit.is_parent(kit))
        self.assertFalse(kit.is_parent(parent))
        self.assertTrue(parent.is_parent(kit))

    def test_is_sibling(self):
        parent = Rabbit()
        kit1 = Rabbit(parent1=parent.ID)
        kit2 = Rabbit(parent1=parent.ID)
        self.assertFalse(parent.is_sibling(kit1))
        self.assertFalse(kit1.is_sibling(parent))
        self.assertTrue(kit2.is_sibling(kit1))
        self.assertTrue(kit1.is_sibling(kit2))

    def test_is_uncle_aunt(self):
        grand_parent = Rabbit()
        sibling1 = Rabbit(parent1=grand_parent.ID)
        sibling2 = Rabbit(parent1=grand_parent.ID)
        kit = Rabbit(parent1=sibling1.ID)
        self.assertFalse(sibling1.is_uncle_aunt(kit))
        self.assertFalse(sibling1.is_uncle_aunt(sibling2))
        self.assertFalse(kit.is_uncle_aunt(sibling2))
        self.assertTrue(sibling2.is_uncle_aunt(kit))

    def test_is_grandparent(self):
        grand_parent = Rabbit()
        sibling1 = Rabbit(parent1=grand_parent.ID)
        sibling2 = Rabbit(parent1=grand_parent.ID)
        kit = Rabbit(parent1=sibling1.ID)
        self.assertFalse(sibling1.is_grandparent(kit))
        self.assertFalse(sibling1.is_grandparent(sibling2))
        self.assertFalse(kit.is_grandparent(sibling2))
        self.assertFalse(sibling2.is_grandparent(kit))
        self.assertFalse(kit.is_grandparent(grand_parent))
        self.assertTrue(grand_parent.is_grandparent(kit))

class TestPossibleMateFunction(unittest.TestCase):

    def test_relation(self):
        grand_parent = Rabbit()
        sibling1 = Rabbit(parent1=grand_parent.ID)
        sibling2 = Rabbit(parent1=grand_parent.ID)
        kit = Rabbit(parent1=sibling1.ID)
        self.assertFalse(kit.is_potential_mate(grand_parent))
        self.assertFalse(kit.is_potential_mate(sibling1))
        self.assertFalse(kit.is_potential_mate(sibling2))
        self.assertFalse(kit.is_potential_mate(kit))
        self.assertFalse(sibling1.is_potential_mate(grand_parent))
        self.assertFalse(sibling1.is_potential_mate(sibling1))
        self.assertFalse(sibling1.is_potential_mate(sibling2))
        self.assertFalse(sibling1.is_potential_mate(kit))

    def test_relation_love_interest(self):
        grand_parent = Rabbit()
        sibling1 = Rabbit(parent1=grand_parent.ID)
        sibling2 = Rabbit(parent1=grand_parent.ID)
        kit = Rabbit(parent1=sibling1.ID)
        self.assertFalse(kit.is_potential_mate(grand_parent,for_love_interest = True))
        self.assertFalse(kit.is_potential_mate(sibling1,for_love_interest = True))
        self.assertFalse(kit.is_potential_mate(sibling2,for_love_interest = True))
        self.assertFalse(kit.is_potential_mate(kit,for_love_interest = True))
        self.assertFalse(sibling1.is_potential_mate(grand_parent,for_love_interest = True))
        self.assertFalse(sibling1.is_potential_mate(sibling1,for_love_interest = True))
        self.assertFalse(sibling1.is_potential_mate(sibling2,for_love_interest = True))
        self.assertFalse(sibling1.is_potential_mate(kit,for_love_interest = True))
        self.assertFalse(sibling2.is_potential_mate(sibling1,for_love_interest = True))

    def test_age_mating(self):
        kitten_rabbit2 = Rabbit(moons=1)
        kitten_rabbit1 = Rabbit(moons=1)
        adolescent_rabbit1 = Rabbit(moons=6)
        adolescent_rabbit2 = Rabbit(moons=6)
        too_young_adult_rabbit1 = Rabbit(moons=12)
        too_young_adult_rabbit2 = Rabbit(moons=12)
        young_adult_rabbit1 = Rabbit(moons=20)
        young_adult_rabbit2 = Rabbit(moons=20)
        adult_rabbit_in_range1 = Rabbit(moons=60)
        adult_rabbit_in_range2 = Rabbit(moons=60)
        adult_rabbit_out_range1 = Rabbit(moons=65)
        adult_rabbit_out_range2 = Rabbit(moons=65)
        senior_adult_rabbit1 = Rabbit(moons=96)
        senior_adult_rabbit2 = Rabbit(moons=96)
        elder_rabbit1 = Rabbit(moons=120)
        elder_rabbit2 = Rabbit(moons=120)

        self.assertFalse(kitten_rabbit1.is_potential_mate(kitten_rabbit1))

		# check for setting
        self.assertFalse(senior_adult_rabbit1.is_potential_mate(young_adult_rabbit1,for_love_interest=False,age_restriction=True))
        self.assertTrue(senior_adult_rabbit1.is_potential_mate(young_adult_rabbit1,for_love_interest=False,age_restriction=False))

        # check invalid constellations
        self.assertFalse(kitten_rabbit1.is_potential_mate(kitten_rabbit2))
        self.assertFalse(kitten_rabbit1.is_potential_mate(adolescent_rabbit1))
        self.assertFalse(kitten_rabbit1.is_potential_mate(young_adult_rabbit1))
        self.assertFalse(kitten_rabbit1.is_potential_mate(adult_rabbit_in_range1))
        self.assertFalse(kitten_rabbit1.is_potential_mate(senior_adult_rabbit1))
        self.assertFalse(kitten_rabbit1.is_potential_mate(elder_rabbit1))

        self.assertFalse(adolescent_rabbit1.is_potential_mate(kitten_rabbit2))
        self.assertFalse(adolescent_rabbit1.is_potential_mate(adolescent_rabbit2))
        self.assertFalse(adolescent_rabbit1.is_potential_mate(too_young_adult_rabbit2))
        self.assertFalse(adolescent_rabbit1.is_potential_mate(young_adult_rabbit1))
        self.assertFalse(adolescent_rabbit1.is_potential_mate(adult_rabbit_in_range1))
        self.assertFalse(adolescent_rabbit1.is_potential_mate(senior_adult_rabbit1))
        self.assertFalse(adolescent_rabbit1.is_potential_mate(elder_rabbit1))

        self.assertFalse(too_young_adult_rabbit1.is_potential_mate(too_young_adult_rabbit2))

        self.assertFalse(young_adult_rabbit1.is_potential_mate(kitten_rabbit2))
        self.assertFalse(young_adult_rabbit1.is_potential_mate(adolescent_rabbit1))
        self.assertFalse(young_adult_rabbit1.is_potential_mate(adult_rabbit_out_range1))
        self.assertFalse(young_adult_rabbit1.is_potential_mate(senior_adult_rabbit1))
        self.assertFalse(young_adult_rabbit1.is_potential_mate(elder_rabbit1))

        self.assertFalse(adult_rabbit_out_range1.is_potential_mate(kitten_rabbit2))
        self.assertFalse(adult_rabbit_out_range1.is_potential_mate(adolescent_rabbit1))
        self.assertFalse(adult_rabbit_out_range1.is_potential_mate(young_adult_rabbit1))
        self.assertFalse(adult_rabbit_out_range1.is_potential_mate(elder_rabbit1))

        self.assertFalse(senior_adult_rabbit1.is_potential_mate(kitten_rabbit1))
        self.assertFalse(senior_adult_rabbit1.is_potential_mate(adolescent_rabbit1))
        self.assertFalse(senior_adult_rabbit1.is_potential_mate(young_adult_rabbit1))
		
        # check valid constellations
        self.assertTrue(young_adult_rabbit1.is_potential_mate(young_adult_rabbit2))
        self.assertTrue(young_adult_rabbit1.is_potential_mate(adult_rabbit_in_range1))
        self.assertTrue(adult_rabbit_in_range1.is_potential_mate(young_adult_rabbit1))
        self.assertTrue(adult_rabbit_in_range1.is_potential_mate(adult_rabbit_in_range2))
        self.assertTrue(adult_rabbit_in_range1.is_potential_mate(adult_rabbit_out_range1))
        self.assertTrue(adult_rabbit_out_range1.is_potential_mate(adult_rabbit_out_range2))
        self.assertTrue(adult_rabbit_out_range1.is_potential_mate(senior_adult_rabbit1))
        self.assertTrue(senior_adult_rabbit1.is_potential_mate(adult_rabbit_out_range1))
        self.assertTrue(senior_adult_rabbit1.is_potential_mate(senior_adult_rabbit2))
        self.assertTrue(senior_adult_rabbit1.is_potential_mate(elder_rabbit1))
        self.assertTrue(elder_rabbit1.is_potential_mate(senior_adult_rabbit1))
        self.assertTrue(elder_rabbit1.is_potential_mate(elder_rabbit2))

    def test_age_love_interest(self):
        kitten_rabbit2 = Rabbit(moons=1)
        kitten_rabbit1 = Rabbit(moons=1)
        adolescent_rabbit1 = Rabbit(moons=6)
        adolescent_rabbit2 = Rabbit(moons=6)
        young_adult_rabbit1 = Rabbit(moons=12)
        young_adult_rabbit2 = Rabbit(moons=12)
        adult_rabbit_in_range1 = Rabbit(moons=52)
        adult_rabbit_in_range2 = Rabbit(moons=52)
        adult_rabbit_out_range1 = Rabbit(moons=65)
        adult_rabbit_out_range2 = Rabbit(moons=65)
        senior_adult_rabbit1 = Rabbit(moons=96)
        senior_adult_rabbit2 = Rabbit(moons=96)
        elder_rabbit1 = Rabbit(moons=120)
        elder_rabbit2 = Rabbit(moons=120)

        self.assertFalse(kitten_rabbit1.is_potential_mate(kitten_rabbit1,True))

        # check invalid constellations
        self.assertFalse(kitten_rabbit1.is_potential_mate(adolescent_rabbit1,True))
        self.assertFalse(kitten_rabbit1.is_potential_mate(young_adult_rabbit1,True))
        self.assertFalse(kitten_rabbit1.is_potential_mate(adult_rabbit_in_range1,True))
        self.assertFalse(kitten_rabbit1.is_potential_mate(senior_adult_rabbit1,True))
        self.assertFalse(kitten_rabbit1.is_potential_mate(elder_rabbit1,True))

        self.assertFalse(adolescent_rabbit1.is_potential_mate(kitten_rabbit2,True))
        self.assertFalse(adolescent_rabbit1.is_potential_mate(young_adult_rabbit1,True))
        self.assertFalse(adolescent_rabbit1.is_potential_mate(adult_rabbit_in_range1,True))
        self.assertFalse(adolescent_rabbit1.is_potential_mate(senior_adult_rabbit1,True))
        self.assertFalse(adolescent_rabbit1.is_potential_mate(elder_rabbit1,True))

        self.assertFalse(young_adult_rabbit1.is_potential_mate(kitten_rabbit2,True))
        self.assertFalse(young_adult_rabbit1.is_potential_mate(adolescent_rabbit1,True))
        self.assertFalse(young_adult_rabbit1.is_potential_mate(adult_rabbit_out_range1,True))
        self.assertFalse(young_adult_rabbit1.is_potential_mate(senior_adult_rabbit1,True))
        self.assertFalse(young_adult_rabbit1.is_potential_mate(elder_rabbit1,True))

        self.assertFalse(adult_rabbit_out_range1.is_potential_mate(kitten_rabbit2,True))
        self.assertFalse(adult_rabbit_out_range1.is_potential_mate(adolescent_rabbit1,True))
        self.assertFalse(adult_rabbit_out_range1.is_potential_mate(young_adult_rabbit1,True))
        self.assertFalse(adult_rabbit_out_range1.is_potential_mate(elder_rabbit1,True))

        self.assertFalse(senior_adult_rabbit1.is_potential_mate(kitten_rabbit1,True))
        self.assertFalse(senior_adult_rabbit1.is_potential_mate(adolescent_rabbit1,True))
        self.assertFalse(senior_adult_rabbit1.is_potential_mate(young_adult_rabbit1,True))

        # check valid constellations
        self.assertTrue(kitten_rabbit1.is_potential_mate(kitten_rabbit2,True))
        self.assertTrue(adolescent_rabbit1.is_potential_mate(adolescent_rabbit2,True))
        self.assertTrue(young_adult_rabbit1.is_potential_mate(young_adult_rabbit2,True))
        self.assertTrue(young_adult_rabbit1.is_potential_mate(adult_rabbit_in_range1,True))
        self.assertTrue(adult_rabbit_in_range1.is_potential_mate(young_adult_rabbit1,True))
        self.assertTrue(adult_rabbit_in_range1.is_potential_mate(adult_rabbit_in_range2,True))
        self.assertTrue(adult_rabbit_in_range1.is_potential_mate(adult_rabbit_out_range1,True))
        self.assertTrue(adult_rabbit_out_range1.is_potential_mate(adult_rabbit_out_range2,True))
        self.assertTrue(adult_rabbit_out_range1.is_potential_mate(senior_adult_rabbit1,True))
        self.assertTrue(senior_adult_rabbit1.is_potential_mate(adult_rabbit_out_range1,True))
        self.assertTrue(senior_adult_rabbit1.is_potential_mate(senior_adult_rabbit2,True))
        self.assertTrue(senior_adult_rabbit1.is_potential_mate(elder_rabbit1,True))
        self.assertTrue(elder_rabbit1.is_potential_mate(senior_adult_rabbit1,True))
        self.assertTrue(elder_rabbit1.is_potential_mate(elder_rabbit2,True))

    def test_dead_exiled(self):
        exiled_rabbit = Rabbit()
        exiled_rabbit.exiled = True
        dead_rabbit = Rabbit()
        dead_rabbit.dead = True
        normal_rabbit = Rabbit()
        self.assertFalse(exiled_rabbit.is_potential_mate(normal_rabbit))
        self.assertFalse(normal_rabbit.is_potential_mate(exiled_rabbit))
        self.assertFalse(dead_rabbit.is_potential_mate(normal_rabbit))
        self.assertFalse(normal_rabbit.is_potential_mate(dead_rabbit))


    @patch('scripts.game_structure.game_essentials.game.settings')
    def test_possible_setting(self, settings):
        rusasirah = Rabbit(moons=50)
        former_rusasi = Rabbit(moons=20)
        rusasirah.former_rusasis.append(former_rusasi.ID)

		# TODO: check how this mocking is working
        settings["romantic with former rusasirah"].return_value = False
        #self.assertFalse(rusasirah.is_potential_mate(former_rusasi,False,False))
        #self.assertFalse(former_rusasi.is_potential_mate(rusasirah,False,False))
        #self.assertTrue(rusasirah.is_potential_mate(former_rusasi,False,True))
        #self.assertTrue(former_rusasi.is_potential_mate(rusasirah,False,True))

        #self.assertFalse(rusasirah.is_potential_mate(former_rusasi,True,False))
        #self.assertFalse(former_rusasi.is_potential_mate(rusasirah,True,False))
        #self.assertTrue(rusasirah.is_potential_mate(former_rusasi,True,True))
        #self.assertTrue(former_rusasi.is_potential_mate(rusasirah,True,True))

class TestMateFunctions(unittest.TestCase):

    def test_set_mate(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()

        # when
        rabbit1.set_mate(rabbit2)
        rabbit2.set_mate(rabbit1)

        # then
        self.assertEqual(rabbit1.mate[0],rabbit2.ID)
        self.assertEqual(rabbit2.mate[0],rabbit1.ID)

    def test_unset_mate(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()
        rabbit1.mate.append(rabbit2.ID)
        rabbit2.mate.append(rabbit1.ID)

        # when
        rabbit1.unset_mate(rabbit2)
        rabbit2.unset_mate(rabbit1)

        # then
        self.assertNotIn(rabbit2, rabbit1.mate)
        self.assertNotIn(rabbit1, rabbit2.mate)
        self.assertEqual(len(rabbit1.mate),0)
        self.assertEqual(len(rabbit2.mate),0)

    def test_set_mate_relationship(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()
        relation1 = Relationship(rabbit1,rabbit2)
        old_relation1 = deepcopy(relation1)
        relation2 = Relationship(rabbit2,rabbit1)
        old_relation2 = deepcopy(relation1)
        
        rabbit1.relationships[rabbit2.ID] = relation1
        rabbit2.relationships[rabbit1.ID] = relation2

        # when
        rabbit1.set_mate(rabbit2)
        rabbit2.set_mate(rabbit1)

        # then
        # TODO: maybe not correct check
        self.assertLess(old_relation1.romantic_love, relation1.romantic_love)
        self.assertLessEqual(old_relation1.platonic_like, relation1.platonic_like)
        self.assertLessEqual(old_relation1.dislike, relation1.dislike)
        self.assertLess(old_relation1.comfortable, relation1.comfortable)
        self.assertLess(old_relation1.trust, relation1.trust)
        self.assertLessEqual(old_relation1.admiration, relation1.admiration)
        self.assertLessEqual(old_relation1.jealousy, relation1.jealousy)

        self.assertLess(old_relation2.romantic_love, relation2.romantic_love)
        self.assertLessEqual(old_relation2.platonic_like, relation2.platonic_like)
        self.assertLessEqual(old_relation2.dislike, relation2.dislike)
        self.assertLess(old_relation2.comfortable, relation2.comfortable)
        self.assertLess(old_relation2.trust, relation2.trust)
        self.assertLessEqual(old_relation2.admiration, relation2.admiration)
        self.assertLessEqual(old_relation2.jealousy, relation2.jealousy)

    def test_unset_mate_relationship(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()
        relation1 = Relationship(rabbit1,rabbit2, family=False, mates=True, romantic_love=40, platonic_like=40, dislike=0, comfortable=40, trust=20, admiration=20,jealousy=20)
        old_relation1 = deepcopy(relation1)
        relation2 = Relationship(rabbit2,rabbit1, family=False, mates=True, romantic_love=40, platonic_like=40, dislike=0, comfortable=40, trust=20, admiration=20,jealousy=20)
        old_relation2 = deepcopy(relation2)
        rabbit1.mate.append(rabbit2.ID)
        rabbit2.mate.append(rabbit1.ID)
        rabbit1.relationships[rabbit2.ID] = relation1
        rabbit2.relationships[rabbit1.ID] = relation2

        # when
        rabbit1.unset_mate(rabbit2, breakup=True)
        rabbit2.unset_mate(rabbit2, breakup=True)

        # then
        # TODO: maybe not correct check
        self.assertGreater(old_relation1.romantic_love, relation1.romantic_love)
        self.assertGreaterEqual(old_relation1.platonic_like, relation1.platonic_like)
        self.assertGreaterEqual(old_relation1.dislike, relation1.dislike)
        self.assertGreater(old_relation1.comfortable, relation1.comfortable)
        self.assertGreater(old_relation1.trust, relation1.trust)
        self.assertGreaterEqual(old_relation1.admiration, relation1.admiration)
        self.assertGreaterEqual(old_relation1.jealousy, relation1.jealousy)

        self.assertGreater(old_relation2.romantic_love, relation2.romantic_love)
        self.assertGreaterEqual(old_relation2.platonic_like, relation2.platonic_like)
        self.assertGreaterEqual(old_relation2.dislike, relation2.dislike)
        self.assertGreater(old_relation2.comfortable, relation2.comfortable)
        self.assertGreater(old_relation2.trust, relation2.trust)
        self.assertGreaterEqual(old_relation2.admiration, relation2.admiration)
        self.assertGreaterEqual(old_relation2.jealousy, relation2.jealousy)  

class TestUpdateMentor(unittest.TestCase):
    def test_exile_rusasi(self):
        # given
        app = Rabbit(moons=7, status="rusasi")
        rusasirah = Rabbit(moons=20, status="rabbit")
        app.update_rusasirah(rusasirah.ID)

        # when
        self.assertTrue(app.ID in rusasirah.rusasi)
        self.assertFalse(app.ID in rusasirah.former_rusasis)
        self.assertEqual(app.rusasirah, app.ID)
        app.exiled = True
        app.update_rusasirah()

        # then
        self.assertFalse(app.ID in rusasirah.rusasi)
        self.assertTrue(app.ID in rusasirah.former_rusasis)
        self.assertIsNone(app.rusasirah)
