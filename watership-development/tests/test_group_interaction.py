import unittest

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from scripts.rabbit.rabbits import Rabbit, Relationship
from scripts.rabbit.skills import Skill, SkillPath
from scripts.events_module.relationship.group_events import Group_Events, Group_Interaction

class MainRabbitFiltering(unittest.TestCase):
    def test_main_rabbit_status_one(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        main_rabbit.status = "rabbit"
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.status_constraint = {"m_c": ["rabbit"]}

        interaction2 = Group_Interaction("2")
        interaction2.status_constraint = {"m_c": ["healer"]}
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "Any", "Any")

        # then
        self.assertNotEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)

    def test_main_rabbit_status_all(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        main_rabbit.status = "rabbit"
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.status_constraint = {"m_c": ["rabbit"]}

        interaction2 = Group_Interaction("2")
        interaction2.status_constraint = {"m_c": ["healer", "rabbit"]}
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "Any", "Any")

        # then
        self.assertEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)
        self.assertIn(interaction2, filtered_interactions)

    def test_main_rabbit_trait_one(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        main_rabbit.personality.trait = "calm"
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.trait_constraint = {"m_c": ["calm"]}

        interaction2 = Group_Interaction("2")
        interaction2.trait_constraint = {"m_c": ["troublesome"]}
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "Any", "Any")

        # then
        self.assertNotEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)

    def test_main_rabbit_trait_all(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        main_rabbit.personality.trait = "calm"
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.trait_constraint = {"m_c": ["calm"]}

        interaction2 = Group_Interaction("2")
        interaction2.trait_constraint = {"m_c": ["troublesome", "calm"]}
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "Any", "Any")

        # then
        self.assertEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)
        self.assertIn(interaction2, filtered_interactions)

    def test_main_rabbit_skill_one(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit(moons=40)
        main_rabbit.skills.primary = Skill(SkillPath.HARVESTER, points=9)
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.skill_constraint = {"m_c": ["good harvester"]}

        interaction2 = Group_Interaction("2")
        interaction2.skill_constraint = {"m_c": ["excellent harvester"]}
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "Any", "Any")

        # then
        self.assertNotEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)

    def test_main_rabbit_skill_all(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        main_rabbit.skills.primary = Skill(SkillPath.HARVESTER, 9)
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.skill_constraint = {"m_c": ["good harvester"]}

        interaction2 = Group_Interaction("2")
        interaction2.skill_constraint = {"m_c": ["excellent harvester", "good harvester"]}
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "Any", "Any")

        # then
        self.assertEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)
        self.assertIn(interaction2, filtered_interactions)

    def test_main_rabbit_backstory_one(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        main_rabbit.backstory = "warrenborn"
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.backstory_constraint = {"m_c": ["warrenborn"]}

        interaction2 = Group_Interaction("2")
        interaction2.backstory_constraint = {"m_c": ["halfwarren1"]}
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "Any", "Any")

        # then
        self.assertNotEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)

    def test_main_rabbit_backstory_all(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        main_rabbit.backstory = "warrenborn"
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.backstory_constraint = {"m_c": ["warrenborn"]}

        interaction2 = Group_Interaction("2")
        interaction2.backstory_constraint = {"m_c": ["halfwarren1", "warrenborn"]}
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "Any", "Any")

        # then
        self.assertEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)
        self.assertIn(interaction2, filtered_interactions)


class OtherFiltering(unittest.TestCase):
    def test_season_one(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.season = ["spring"]

        interaction2 = Group_Interaction("2")
        interaction2.season = ["summer"]
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "Any", "spring")

        # then
        self.assertNotEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)

    def test_season_multiple(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.season = ["spring"]

        interaction2 = Group_Interaction("2")
        interaction2.season = ["spring", "summer"]
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "Any", "spring")

        # then
        self.assertEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)
        self.assertIn(interaction2, filtered_interactions)

    def test_season_any(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.season = ["spring"]

        interaction2 = Group_Interaction("2")
        interaction2.season = ["Any"]
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "Any", "spring")

        # then
        self.assertEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)
        self.assertIn(interaction2, filtered_interactions)

    def test_biome_one(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.biome = ["forest"]

        interaction2 = Group_Interaction("2")
        interaction2.biome = ["beach"]
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "forest", "Any")

        # then
        self.assertNotEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)

    def test_biome_multiple(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.biome = ["forest"]

        interaction2 = Group_Interaction("2")
        interaction2.biome = ["beach", "forest"]
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "forest", "Any")

        # then
        self.assertEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)
        self.assertIn(interaction2, filtered_interactions)

    def test_biome_any(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        group_events.abbreviations_rabbit_id={"m_c": main_rabbit.ID}

        interaction1 = Group_Interaction("1")
        interaction1.biome = ["forest"]

        interaction2 = Group_Interaction("2")
        interaction1.biome = ["Any"]
        
        # when
        all_interactions = [interaction1, interaction2]
        filtered_interactions = group_events.get_main_rabbit_interactions(all_interactions, "forest", "Any")

        # then
        self.assertEqual(len(filtered_interactions), len(all_interactions))
        self.assertIn(interaction1, filtered_interactions)
        self.assertIn(interaction2, filtered_interactions)


class Abbreviations(unittest.TestCase):
    def test_get_abbreviation_possibilities_all(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        main_rabbit.status = "rabbit"
        group_events.abbreviations_rabbit_id={
            "m_c": main_rabbit.ID,
            "r_c1": None,
            "r_c2": None
        }

        random1 = Rabbit()
        random1.status = "rabbit"
        random2 = Rabbit()
        random2.status = "rabbit"
        random3 = Rabbit()
        random3.status = "rabbit"

        interaction1 = Group_Interaction("1")
        interaction1.status_constraint = {"r_c1": ["rabbit"]}

        interaction2 = Group_Interaction("2")
        interaction2.status_constraint = {"r_c1": ["healer", "rabbit"]}
        
        # when
        all_interactions = [interaction1, interaction2]
        interaction_rabbits = [random1, random2]
        abbreviations_possibilities = group_events.get_abbreviations_possibilities(
            all_interactions, 3, interaction_rabbits
        )

        # then
        self.assertEqual(len(abbreviations_possibilities), 2)
        # all rabbits would fit in
        self.assertEqual(len(abbreviations_possibilities["1"]), 3)
        self.assertEqual(len(abbreviations_possibilities["2"]), 3)

    def test_get_abbreviation_possibilities_not_all(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        main_rabbit.status = "rabbit"
        group_events.abbreviations_rabbit_id={
            "m_c": main_rabbit.ID,
            "r_c1": None,
            "r_c2": None
        }

        random1 = Rabbit()
        random1.status = "rabbit"
        random2 = Rabbit()
        random2.status = "rabbit"
        random3 = Rabbit()
        random3.status = "healer"

        interaction1 = Group_Interaction("1")
        interaction1.status_constraint = {"r_c1": ["rabbit"]}

        interaction2 = Group_Interaction("2")
        interaction2.status_constraint = {"r_c1": ["healer"]}
        
        # when
        all_interactions = [interaction1, interaction2]
        interaction_rabbits = [random1, random2, random3]
        abbreviations_possibilities = group_events.get_abbreviations_possibilities(
            all_interactions, 3, interaction_rabbits
        )

        # then
        self.assertEqual(len(abbreviations_possibilities), 2)
        # all rabbits would fit in
        self.assertEqual(len(abbreviations_possibilities["1"]["r_c1"]), 2)
        self.assertEqual(len(abbreviations_possibilities["2"]["r_c1"]), 1)

    def test_remove_abbreviations_missing_rabbits(self):
        # given
        group_events = Group_Events()
        abbreviations_possibilities = {
            "1": {
                "r_c1": ["1", "2"],
                "r_c2": ["1", "2"],
            },
            "2": {
                "r_c1": ["1", "2"],
                "r_c2": [],
            },
        }
        
        # when
        new_possibilities = group_events.remove_abbreviations_missing_rabbits(
            abbreviations_possibilities
        )

        # then
        self.assertNotEqual(len(abbreviations_possibilities), len(new_possibilities))
        self.assertIn("1", new_possibilities)
        self.assertNotIn("2", new_possibilities)

    def test_set_abbreviations_rabbits(self):
        # given
        group_events = Group_Events()
        main_rabbit = Rabbit()
        main_rabbit.status = "rabbit"
        group_events.abbreviations_rabbit_id={
            "m_c": main_rabbit.ID,
            "r_c1": None,
            "r_c2": None
        }

        random1 = Rabbit()
        random1.status = "rabbit"
        random2 = Rabbit()
        random2.status = "rabbit"
        random3 = Rabbit()
        random3.status = "healer"

        interaction1 = Group_Interaction("1")
        interaction1.status_constraint = {"r_c1": ["rabbit"]}

        interaction2 = Group_Interaction("2")
        interaction2.status_constraint = {"r_c1": ["healer", "rabbit"]}

        # when
        interaction_rabbits = [random1, random2, random3]
        group_events.rabbit_abbreviations_counter = {
            random1.ID: {
                "r_c1": 2,
                "r_c2": 2
            },
            random2.ID: {
                "r_c1": 2,
                "r_c2": 2
            },
            random3.ID: {
                "r_c1": 1,
                "r_c2": 2
            }
        }
        group_events.set_abbreviations_rabbits(interaction_rabbits)

        # then
        self.assertIsNotNone(group_events.abbreviations_rabbit_id["r_c1"])
        self.assertIsNotNone(group_events.abbreviations_rabbit_id["r_c2"])
        self.assertIn(group_events.abbreviations_rabbit_id["r_c1"], [random1.ID, random2.ID])
        self.assertNotIn(group_events.abbreviations_rabbit_id["r_c1"], [random3.ID])


class OtherRabbitsFiltering(unittest.TestCase):
    def test_relationship_allow_true(self):
        # given
        group_events = Group_Events()
        parent = Rabbit()
        main_rabbit = Rabbit(parent1=parent.ID)
        main_rabbit.status = "rabbit"
        random1 = Rabbit(parent1=parent.ID)
        random1.status = "rabbit"
        random2 = Rabbit()
        random2.status = "rabbit"
        group_events.abbreviations_rabbit_id={
            "m_c": main_rabbit.ID,
            "r_c1": random1.ID,
            "r_c2": random2.ID
        }
        # given - relationships
        # order: romantic, platonic, dislike, admiration, comfortable, jealousy, trust
        main_rabbit.relationships[random1.ID] = Relationship(
            main_rabbit, random1, False, False, 50, 50, 0, 50, 50, 0, 50
        )
        random1.relationships[main_rabbit.ID] = Relationship(
            random1, main_rabbit, False, False, 50, 50, 0, 50, 50, 0, 50
        )

        main_rabbit.relationships[random2.ID] = Relationship(
            main_rabbit, random2, False, True, 0, 0, 50, 0, 0, 50, 0
        )
        random2.relationships[main_rabbit.ID] = Relationship(
            random2, main_rabbit, False, True, 0, 0, 50, 0, 0, 50, 0
        )


        random1.mate.append(random2.ID)
        random2.mate.append(random1.ID)
        random1.relationships[random2.ID] = Relationship(
            random1, random2, True, False, 50, 50, 0, 0, 0, 0, 50
        )
        random2.relationships[random1.ID] = Relationship(
            random2, random1, True, False, 50, 50, 0, 0, 0, 0, 0
        )

        # summary: 
        #    - random1 and random2 are mates
        #    - random2 and main_rabbit are siblings
        #    - main_rabbit has a crush on the siblings mate (random1) + vise versa
        #    - main_rabbit don't like their sibling because of the crush (random2)
        #    - random2 don't trust their mate (random1) because of sibling (main_rabbit)
        

        # given - interactions
        # first all true
        interaction1 = Group_Interaction("test")

        interaction2 = Group_Interaction("test")
        interaction2.relationship_constraint = {
            "r_c1_to_r_c2": ["mates"]
        }

        interaction3 = Group_Interaction("test")
        interaction3.relationship_constraint = {
            "m_c_to_r_c1": ["siblings"]
        }

        interaction4 = Group_Interaction("test")
        interaction4.relationship_constraint = {
            "m_c_to_r_c1": ["romantic_40"]
        }

        interaction5 = Group_Interaction("test")
        interaction5.relationship_constraint = {
            "m_c_to_r_c1": ["comfortable_40"]
        }

        interaction6 = Group_Interaction("test")
        interaction6.relationship_constraint = {
            "m_c_to_r_c1": ["comfortable_40", "romantic_40"]
        }

        interaction7 = Group_Interaction("test")
        interaction7.relationship_constraint = {
            "m_c_to_r_c1": ["romantic_60_lower"]
        }

        interaction8 = Group_Interaction("test")
        interaction8.relationship_constraint = {
            "m_c_to_r_c1": ["comfortable_60_lower"]
        }

        interaction9 = Group_Interaction("test")
        interaction9.relationship_constraint = {
            "m_c_to_r_c2": ["dislike_40"]
        }

        interaction10 = Group_Interaction("test")
        interaction10.relationship_constraint = {
            "r_c2_to_m_c": ["dislike_40"]
        }

        # then
        self.assertTrue(group_events.relationship_allow_interaction(interaction1))
        self.assertTrue(group_events.relationship_allow_interaction(interaction2))
        self.assertTrue(group_events.relationship_allow_interaction(interaction3))
        self.assertTrue(group_events.relationship_allow_interaction(interaction4))
        self.assertTrue(group_events.relationship_allow_interaction(interaction5))
        self.assertTrue(group_events.relationship_allow_interaction(interaction6))
        self.assertTrue(group_events.relationship_allow_interaction(interaction7))
        self.assertTrue(group_events.relationship_allow_interaction(interaction8))
        self.assertTrue(group_events.relationship_allow_interaction(interaction9))
        self.assertTrue(group_events.relationship_allow_interaction(interaction10))

    def test_relationship_allow_false(self):
        # given
        group_events = Group_Events()
        parent = Rabbit()
        main_rabbit = Rabbit(parent1=parent.ID)
        main_rabbit.status = "rabbit"
        random1 = Rabbit(parent1=parent.ID)
        random1.status = "rabbit"
        random2 = Rabbit()
        random2.status = "rabbit"
        group_events.abbreviations_rabbit_id={
            "m_c": main_rabbit.ID,
            "r_c1": random1.ID,
            "r_c2": random2.ID
        }
        # given - relationships
        # order: romantic, platonic, dislike, admiration, comfortable, jealousy, trust
        main_rabbit.relationships[random1.ID] = Relationship(
            main_rabbit, random1, False, False, 50, 50, 0, 50, 50, 0, 50
        )
        random1.relationships[main_rabbit.ID] = Relationship(
            random1, main_rabbit, False, False, 50, 50, 0, 50, 50, 0, 50
        )

        main_rabbit.relationships[random2.ID] = Relationship(
            main_rabbit, random2, False, True, 0, 0, 50, 0, 0, 50, 0
        )
        random2.relationships[main_rabbit.ID] = Relationship(
            random2, main_rabbit, False, True, 0, 0, 50, 0, 0, 50, 0
        )


        random1.mate.append(random2.ID)
        random2.mate.append(random1.ID)
        random1.relationships[random2.ID] = Relationship(
            random1, random2, True, False, 50, 50, 0, 0, 0, 0, 50
        )
        random2.relationships[random1.ID] = Relationship(
            random2, random1, True, False, 50, 50, 0, 0, 0, 0, 0
        )

        # summary: 
        #    - random1 and random2 are mates
        #    - random2 and main_rabbit are siblings
        #    - main_rabbit has a crush on the siblings mate (random1) + vise versa
        #    - main_rabbit don't like their sibling because of the crush (random2)
        #    - random2 don't trust their mate (random1) because of sibling (main_rabbit)

        # given - interactions
        interaction1 = Group_Interaction("test")
        interaction1.relationship_constraint = {
            "r_c1_to_m_c": ["dislike_40"]
        }

        interaction2 = Group_Interaction("test")
        interaction2.relationship_constraint = {
            "r_c1_to_r_c2": ["not_mates"]
        }

        interaction3 = Group_Interaction("test")
        interaction3.relationship_constraint = {
            "r_c1_to_r_c2": ["romantic_40_lower"]
        }

        interaction4 = Group_Interaction("test")
        interaction4.relationship_constraint = {
            "r_c1_to_r_c2": ["romantic_40_lower"]
        }

        interaction5 = Group_Interaction("test")
        interaction5.relationship_constraint = {
            "r_c1_to_r_c2": ["trust_40_lower"]
        }

        interaction6 = Group_Interaction("test")
        interaction6.relationship_constraint = {
            "r_c1_to_m_c": ["mates"]
        }

        interaction7 = Group_Interaction("test")
        interaction7.relationship_constraint = {
            "m_c_to_r_c1": ["comfortable_60"]
        }

        interaction8 = Group_Interaction("test")
        interaction8.relationship_constraint = {
            "m_c_to_r_c1": ["romantic_40_lower"]
        }

        interaction9 = Group_Interaction("test")
        interaction9.relationship_constraint = {
            "m_c_to_r_c1": ["comfortable_40_lower"]
        }

        interaction10 = Group_Interaction("test")
        interaction10.relationship_constraint = {
            "r_c2_to_r_c1": ["trust_40"]
        }

        # then
        self.assertFalse(group_events.relationship_allow_interaction(interaction1))
        self.assertFalse(group_events.relationship_allow_interaction(interaction2))
        self.assertFalse(group_events.relationship_allow_interaction(interaction3))
        self.assertFalse(group_events.relationship_allow_interaction(interaction4))
        self.assertFalse(group_events.relationship_allow_interaction(interaction5))
        self.assertFalse(group_events.relationship_allow_interaction(interaction6))
        self.assertFalse(group_events.relationship_allow_interaction(interaction7))
        self.assertFalse(group_events.relationship_allow_interaction(interaction8))
        self.assertFalse(group_events.relationship_allow_interaction(interaction9))
        self.assertFalse(group_events.relationship_allow_interaction(interaction10))
