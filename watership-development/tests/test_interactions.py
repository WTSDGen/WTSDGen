import unittest
from scripts.rabbit.rabbits import Rabbit, Relationship
from scripts.rabbit.skills import SkillPath, Skill

from scripts.rabbit_relations.interaction import (
    Single_Interaction, 
    rel_fulfill_rel_constraints,
    rabbits_fulfill_single_interaction_constraints
)

class RelationshipConstraints(unittest.TestCase):
    def test_siblings(self):
        # given
        parent = Rabbit()
        rabbit_from = Rabbit(parent1=parent.ID)
        rabbit_to = Rabbit(parent1=parent.ID)
        rel = Relationship(rabbit_from, rabbit_to, False, True)
    
        # then
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["sibling"], "test"))
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["not_mates"], "test"))

    def test_mates(self):
        # given
        rabbit_from = Rabbit()
        rabbit_to = Rabbit()
        rabbit_from.mate.append(rabbit_to.ID)
        rabbit_to.mate.append(rabbit_from.ID)
        rel = Relationship(rabbit_from, rabbit_to, True, False)
    
        # then
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["mates"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(rel, ["not_mates"], "test"))

    def test_parent_child_combo(self):
        # given
        parent = Rabbit()
        child = Rabbit(parent1=parent.ID)

        child_parent_rel = Relationship(child, parent, False, True)
        parent_child_rel = Relationship(parent, child, False, True)
    
        # then
        self.assertTrue(rel_fulfill_rel_constraints(child_parent_rel, ["child/parent"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(child_parent_rel, ["parent/child"], "test"))
        self.assertTrue(rel_fulfill_rel_constraints(parent_child_rel, ["parent/child"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(parent_child_rel, ["child/parent"], "test"))

    def test_rel_values_above(self):
        # given
        rabbit_from = Rabbit()
        rabbit_to = Rabbit()
        rel = Relationship(rabbit_from, rabbit_to)
        rel.romantic_love = 50
        rel.platonic_like = 50
        rel.dislike = 50
        rel.comfortable = 50
        rel.jealousy = 50
        rel.trust = 50
    
        # then
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["romantic_50"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(rel, ["romantic_60"], "test"))
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["platonic_50"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(rel, ["platonic_60"], "test"))
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["comfortable_50"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(rel, ["comfortable_60"], "test"))
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["jealousy_50"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(rel, ["jealousy_60"], "test"))
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["trust_50"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(rel, ["trust_60"], "test"))

    def test_rel_values_under(self):
        # given
        rabbit_from = Rabbit()
        rabbit_to = Rabbit()
        rel = Relationship(rabbit_from, rabbit_to)
        rel.romantic_love = 50
        rel.platonic_like = 50
        rel.dislike = 50
        rel.comfortable = 50
        rel.jealousy = 50
        rel.trust = 50
    
        # then
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["romantic_50_lower"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(rel, ["romantic_30_lower"], "test"))
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["platonic_50_lower"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(rel, ["platonic_30_lower"], "test"))
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["comfortable_50_lower"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(rel, ["comfortable_30_lower"], "test"))
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["jealousy_50_lower"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(rel, ["jealousy_30_lower"], "test"))
        self.assertTrue(rel_fulfill_rel_constraints(rel, ["trust_50_lower"], "test"))
        self.assertFalse(rel_fulfill_rel_constraints(rel, ["trust_30_lower"], "test"))

class SingleInteractionRabbitConstraints(unittest.TestCase):
    def test_status(self):
        # given
        rabbit = Rabbit()
        rabbit.status = "rabbit"
        medicine = Rabbit()
        medicine.status = "healer"

        # when
        rabbit_to_all = Single_Interaction("test")
        rabbit_to_all.main_status_constraint = ["rabbit"]
        rabbit_to_all.random_status_constraint = ["rabbit", "healer"]

        rabbit_to_rabbit = Single_Interaction("test")
        rabbit_to_rabbit.main_status_constraint = ["rabbit"]
        rabbit_to_rabbit.random_status_constraint = ["rabbit"]

        medicine_to_rabbit = Single_Interaction("test")
        medicine_to_rabbit.main_status_constraint = ["healer"]
        medicine_to_rabbit.random_status_constraint = ["rabbit"]

        # then
        for game_mode in ["classic", "expanded", "cruel season"]:
            self.assertTrue(rabbits_fulfill_single_interaction_constraints(rabbit, rabbit, rabbit_to_all, game_mode))
            self.assertTrue(rabbits_fulfill_single_interaction_constraints(rabbit, rabbit, rabbit_to_rabbit, game_mode))
            self.assertFalse(rabbits_fulfill_single_interaction_constraints(rabbit, rabbit, medicine_to_rabbit, game_mode))

            self.assertTrue(rabbits_fulfill_single_interaction_constraints(rabbit, medicine, rabbit_to_all, game_mode))
            self.assertFalse(rabbits_fulfill_single_interaction_constraints(rabbit, medicine, rabbit_to_rabbit, game_mode))
            self.assertFalse(rabbits_fulfill_single_interaction_constraints(rabbit, medicine, medicine_to_rabbit, game_mode))

            self.assertFalse(rabbits_fulfill_single_interaction_constraints(medicine, rabbit, rabbit_to_all, game_mode))
            self.assertFalse(rabbits_fulfill_single_interaction_constraints(medicine, rabbit, rabbit_to_rabbit, game_mode))
            self.assertTrue(rabbits_fulfill_single_interaction_constraints(medicine, rabbit, medicine_to_rabbit, game_mode))

    def test_trait(self):
        # given
        calm = Rabbit()
        calm.personality.trait = "calm"
        troublesome = Rabbit()
        troublesome.personality.trait = "troublesome"

        # when
        calm_to_all = Single_Interaction("test")
        calm_to_all.main_trait_constraint = ["calm"]
        calm_to_all.random_trait_constraint = []

        all_to_calm = Single_Interaction("test")
        all_to_calm.main_trait_constraint = ["troublesome", "calm"]
        all_to_calm.random_trait_constraint = ["calm"]


        # then
        for game_mode in ["classic", "expanded", "cruel season"]:
            self.assertTrue(rabbits_fulfill_single_interaction_constraints(calm, troublesome, calm_to_all, game_mode))
            self.assertFalse(rabbits_fulfill_single_interaction_constraints(calm, troublesome, all_to_calm, game_mode))

            self.assertFalse(rabbits_fulfill_single_interaction_constraints(troublesome, calm, calm_to_all, game_mode))
            self.assertTrue(rabbits_fulfill_single_interaction_constraints(troublesome, calm, all_to_calm, game_mode))

            self.assertTrue(rabbits_fulfill_single_interaction_constraints(calm, calm, calm_to_all, game_mode))
            self.assertTrue(rabbits_fulfill_single_interaction_constraints(calm, calm, all_to_calm, game_mode))

    def test_skill(self):
        # given
        hunter = Rabbit()
        hunter.skills.primary = Skill(SkillPath.HARVESTER, points=9)
        fighter = Rabbit()
        fighter.skills.primary = Skill(SkillPath.FIGHTER, points=9)

        # when
        hunter_to_all = Single_Interaction("test")
        hunter_to_all.main_skill_constraint = ["good hunter"]
        hunter_to_all.random_skill_constraint = []

        all_to_hunter = Single_Interaction("test")
        all_to_hunter.main_skill_constraint = ["good fighter", "good hunter"]
        all_to_hunter.random_skill_constraint = ["good hunter"]


        # then
        for game_mode in ["classic", "expanded", "cruel season"]:
            self.assertTrue(rabbits_fulfill_single_interaction_constraints(hunter, fighter, hunter_to_all, game_mode))
            self.assertFalse(rabbits_fulfill_single_interaction_constraints(hunter, fighter, all_to_hunter, game_mode))

            self.assertFalse(rabbits_fulfill_single_interaction_constraints(fighter, hunter, hunter_to_all, game_mode))
            self.assertTrue(rabbits_fulfill_single_interaction_constraints(fighter, hunter, all_to_hunter, game_mode))

            self.assertTrue(rabbits_fulfill_single_interaction_constraints(hunter, hunter, hunter_to_all, game_mode))
            self.assertTrue(rabbits_fulfill_single_interaction_constraints(hunter, hunter, all_to_hunter, game_mode))

    def test_background(self):
        # given
        warren = Rabbit()
        warren.backstory = "warrenborn"
        half = Rabbit()
        half.backstory = "halfwarren1"

        # when
        warren_to_all = Single_Interaction("test")
        warren_to_all.backstory_constraint = {
            "m_c": ["warrenborn"]
        }

        all_to_warren = Single_Interaction("test")
        all_to_warren.backstory_constraint = {
            "m_c": ["halfwarren1", "warrenborn"],
            "r_r": ["warrenborn"]
        }

        # then
        for game_mode in ["classic", "expanded", "cruel season"]:
            self.assertTrue(rabbits_fulfill_single_interaction_constraints(warren, half, warren_to_all, game_mode))
            self.assertFalse(rabbits_fulfill_single_interaction_constraints(warren, half, all_to_warren, game_mode))

            self.assertFalse(rabbits_fulfill_single_interaction_constraints(half, warren, warren_to_all, game_mode))
            self.assertTrue(rabbits_fulfill_single_interaction_constraints(half, warren, all_to_warren, game_mode))

            self.assertTrue(rabbits_fulfill_single_interaction_constraints(warren, warren, warren_to_all, game_mode))
            self.assertTrue(rabbits_fulfill_single_interaction_constraints(warren, warren, all_to_warren, game_mode))
