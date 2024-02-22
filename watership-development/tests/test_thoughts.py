import unittest

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from scripts.rabbit.thoughts import Thoughts

import ujson

from scripts.rabbit.rabbits import Rabbit

class TestsGetStatusThought(unittest.TestCase):

    def test_healer_thought(self):
        # given
        healer = Rabbit()
        rabbit = Rabbit()
        healer.status = "healer"
        rabbit.status = "rabbit"
        healer.trait = "bold"
        biome = "Forest"
        season = "Spring"
        burrow = "burrow2"

        # load thoughts
        thoughts = Thoughts.load_thoughts(healer, rabbit, "expanded", biome, season, burrow)

        # when
        function_thoughts = thoughts

    def test_exiled_thoughts(self):
        # given
        rabbit = Rabbit(status="exiled", moons=40)
        rabbit.exiled = True
        rabbit.outside = True
        biome = "Forest"
        season = "Spring"
        burrow = "burrow2"

        # load thoughts
        thoughts = Thoughts.load_thoughts(rabbit, None, "expanded", biome, season, burrow)
        """Prints can be turned back on if testing is needed"""
        #print("Exiled Thoughts: " + str(thoughts))

    def test_lost_thoughts(self):
        # given
        rabbit = Rabbit(status="rabbit", moons=40)
        rabbit.outside = True
        biome = "Forest"
        season = "Spring"
        burrow = "burrow2"

        # load thoughts
        thoughts = Thoughts.load_thoughts(rabbit, None, "expanded", biome, season, burrow)
        """Prints can be turned back on if testing is needed"""
        #print("Lost Thoughts: " + str(thoughts))

class TestFamilyThoughts(unittest.TestCase):

    def test_family_thought_young_children(self):
        # given
        parent = Rabbit(moons=40)
        kit = Rabbit(parent1=parent.ID, moons=4)
        biome = "Forest"
        season = "Spring"
        burrow = "burrow2"

        # when
        function_thoughts1 = Thoughts.load_thoughts(parent, kit, "expanded", biome, season, burrow)
        function_thoughts2 = Thoughts.load_thoughts(kit, parent, "expanded", biome, season, burrow)

        # then
        '''
        self.assertTrue(all(t in own_collection_thoughts for t in function_thoughts1))
        self.assertFalse(all(t in not_collection_thoughts for t in function_thoughts1))
        self.assertEqual(function_thoughts2,[])
        '''
    
    def test_family_thought_unrelated(self):
        # given
        rabbit1 = Rabbit(moons=40)
        rabbit2 = Rabbit(moons=40)

        # when

        # then

