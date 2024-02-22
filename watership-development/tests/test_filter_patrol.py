import unittest

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from scripts.rabbit.rabbits import Rabbit
from scripts.rabbit_relations.relationship import Relationship
from scripts.patrol.patrol import PatrolEvent, Patrol
from scripts.warren import Warren

# TODO: redo them! Filtering is not working like this anymore but it got removed from .github/workflows/test.yml 
# so they are not failing!

class TestRelationshipConstraintPatrols(unittest.TestCase):

    def test_sibling_patrol(self):
        # given
        parent = Rabbit()
        rabbit1 = Rabbit(parent1=parent.ID)
        rabbit2 = Rabbit(parent1=parent.ID)
        rabbit1.create_inheritance_new_rabbit()
        rabbit2.create_inheritance_new_rabbit()

        # when
        self.assertTrue(rabbit1.is_sibling(rabbit2))
        self.assertTrue(rabbit2.is_sibling(rabbit1))
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["siblings"]
        no_con_patrol_event = PatrolEvent(patrol_id="test2")
        no_con_patrol_event.relationship_constraints["relationship"] = []

        test_warren = Warren(name="test")

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2, parent], test_warren)
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

    def test_mates_patrol(self):
        # given
        mate1 = Rabbit()
        mate2 = Rabbit()
        rabbit1 = Rabbit()

        mate1.mate.append(mate2.ID)
        mate2.mate.append(mate1.ID)

        # when
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["mates"]
        no_con_patrol_event = PatrolEvent(patrol_id="test2")
        no_con_patrol_event.relationship_constraints["relationship"] = []

        test_warren = Warren(name="test")

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([mate1, mate2], test_warren)
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        patrol = Patrol()
        patrol.add_patrol_rabbits([mate1, rabbit1], test_warren)
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        patrol = Patrol()
        patrol.add_patrol_rabbits([mate1, mate2, rabbit1], test_warren)
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

    def test_parent_child_patrol(self):
        # given
        parent = Rabbit()
        rabbit1 = Rabbit(parent1=parent.ID)
        rabbit2 = Rabbit(parent1=parent.ID)

        # when
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["parent/child"]
        no_con_patrol_event = PatrolEvent(patrol_id="test2")
        no_con_patrol_event.relationship_constraints["relationship"] = []

        test_warren = Warren(name="test")

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([parent, rabbit1], test_warren)
        patrol.patrol_chief_rabbit = parent
        patrol.patrol_random_rabbit = rabbit1
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        patrol = Patrol()
        patrol.add_patrol_rabbits([parent, rabbit1], test_warren)
        patrol.patrol_chief_rabbit = rabbit1
        patrol.patrol_random_rabbit = parent
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        patrol = Patrol()
        rabbit_list = [rabbit1, rabbit2, parent]
        patrol.add_patrol_rabbits(rabbit_list, test_warren)
        patrol.patrol_chief_rabbit = parent
        patrol.patrol_random_rabbit = rabbit2
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

    def test_child_parent_patrol(self):
        # given
        parent = Rabbit()
        rabbit1 = Rabbit(parent1=parent.ID)
        rabbit2 = Rabbit(parent1=parent.ID)

        # when
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["child/parent"]
        no_con_patrol_event = PatrolEvent(patrol_id="test2")
        no_con_patrol_event.relationship_constraints["relationship"] = []

        test_warren = Warren(name="test")

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([parent, rabbit1], test_warren)
        patrol.patrol_chief_rabbit = rabbit1
        patrol.patrol_random_rabbit = parent
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        patrol = Patrol()
        patrol.add_patrol_rabbits([parent, rabbit1], test_warren)
        patrol.patrol_chief_rabbit = parent
        patrol.patrol_random_rabbit = rabbit1
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        patrol = Patrol()
        rabbit_list = [rabbit1, rabbit2, parent]
        patrol.add_patrol_rabbits(rabbit_list, test_warren)
        patrol.patrol_chief_rabbit = parent
        patrol.patrol_random_rabbit = rabbit2
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

    def test_romantic_constraint_patrol(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()

        relationship1 = Relationship(rabbit1,rabbit2)
        relationship2 = Relationship(rabbit2,rabbit1)

        relationship1.romantic_love = 20
        relationship2.romantic_love = 20

        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        rabbit1.relationships[rabbit2.ID] = relationship1
        rabbit2.relationships[rabbit1.ID] = relationship2

        test_warren = Warren(name="test")

        # when - correct
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["romantic_10"]
        no_con_patrol_event = PatrolEvent(patrol_id="test2")
        no_con_patrol_event.relationship_constraints["relationship"] = []

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        # when - to high
        con_patrol_event = PatrolEvent(patrol_id="test3")
        con_patrol_event.relationship_constraints["relationship"] = ["romantic_30"]

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

    def test_platonic_constraint_patrol(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()

        relationship1 = Relationship(rabbit1,rabbit2)
        relationship2 = Relationship(rabbit2,rabbit1)

        relationship1.platonic_like = 20
        relationship2.platonic_like = 20

        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        rabbit1.relationships[rabbit2.ID] = relationship1
        rabbit2.relationships[rabbit1.ID] = relationship2

        test_warren = Warren(name="test")

        # when - correct
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["platonic_10"]
        no_con_patrol_event = PatrolEvent(patrol_id="test2")
        no_con_patrol_event.relationship_constraints["relationship"] = []

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        # when - to high
        con_patrol_event = PatrolEvent(patrol_id="test3")
        con_patrol_event.relationship_constraints["relationship"] = ["platonic_30"]
        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

    def test_dislike_constraint_patrol(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()

        relationship1 = Relationship(rabbit1,rabbit2)
        relationship2 = Relationship(rabbit2,rabbit1)

        relationship1.dislike = 20
        relationship2.dislike = 20

        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        rabbit1.relationships[rabbit2.ID] = relationship1
        rabbit2.relationships[rabbit1.ID] = relationship2

        test_warren = Warren(name="test")

        # when - correct
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["dislike_10"]
        no_con_patrol_event = PatrolEvent(patrol_id="test2")
        no_con_patrol_event.relationship_constraints["relationship"] = []

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        # when - to high
        con_patrol_event = PatrolEvent(patrol_id="test3")
        con_patrol_event.relationship_constraints["relationship"] = ["dislike_30"]

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

    def test_comfortable_constraint_patrol(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()

        relationship1 = Relationship(rabbit1,rabbit2)
        relationship2 = Relationship(rabbit2,rabbit1)

        relationship1.comfortable = 20
        relationship2.comfortable = 20

        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        rabbit1.relationships[rabbit2.ID] = relationship1
        rabbit2.relationships[rabbit1.ID] = relationship2

        test_warren = Warren(name="test")

        # when - correct
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["comfortable_10"]
        no_con_patrol_event = PatrolEvent(patrol_id="test2")
        no_con_patrol_event.relationship_constraints["relationship"] = []

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        # when - to high
        con_patrol_event = PatrolEvent(patrol_id="test3")
        con_patrol_event.relationship_constraints["relationship"] = ["comfortable_30"]

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

    def test_jealousy_patrol(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()

        relationship1 = Relationship(rabbit1,rabbit2)
        relationship2 = Relationship(rabbit2,rabbit1)

        relationship1.jealousy = 20
        relationship2.jealousy = 20

        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        rabbit1.relationships[rabbit2.ID] = relationship1
        rabbit2.relationships[rabbit1.ID] = relationship2

        test_warren = Warren(name="test")

        # when - correct
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["jealousy_10"]
        no_con_patrol_event = PatrolEvent(patrol_id="test2")
        no_con_patrol_event.relationship_constraints["relationship"] = []

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        # when - to high
        con_patrol_event = PatrolEvent(patrol_id="test3")
        con_patrol_event.relationship_constraints["relationship"] = ["jealousy_30"]

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

    def test_trust_patrol(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()

        relationship1 = Relationship(rabbit1,rabbit2)
        relationship2 = Relationship(rabbit2,rabbit1)

        relationship1.trust = 20
        relationship2.trust = 20

        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        rabbit1.relationships[rabbit2.ID] = relationship1
        rabbit2.relationships[rabbit1.ID] = relationship2

        test_warren = Warren(name="test")

        # when - correct
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["trust_10"]
        no_con_patrol_event = PatrolEvent(patrol_id="test2")
        no_con_patrol_event.relationship_constraints["relationship"] = []

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        # when - to high
        con_patrol_event = PatrolEvent(patrol_id="test3")
        con_patrol_event.relationship_constraints["relationship"] = ["trust_30"]

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

    def test_multiple_romantic_patrol(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()
        rabbit3 = Rabbit()

        relationship1_2 = Relationship(rabbit1,rabbit2)
        relationship1_3 = Relationship(rabbit1,rabbit3)
        relationship2_1 = Relationship(rabbit2,rabbit1)
        relationship2_3 = Relationship(rabbit2,rabbit3)
        relationship3_1 = Relationship(rabbit3,rabbit1)
        relationship3_2 = Relationship(rabbit3,rabbit2)

        relationship1_2.romantic_love = 20
        relationship1_3.romantic_love = 20
        relationship2_1.romantic_love = 20
        relationship2_3.romantic_love = 20
        relationship3_1.romantic_love = 20
        relationship3_2.romantic_love = 20

        relationship1_2.opposite_relationship = relationship2_1
        relationship1_3.opposite_relationship = relationship3_1
        relationship2_1.opposite_relationship = relationship1_2
        relationship2_3.opposite_relationship = relationship3_2
        relationship3_1.opposite_relationship = relationship3_1
        relationship3_2.opposite_relationship = relationship2_3

        rabbit1.relationships[rabbit2.ID] = relationship1_2
        rabbit1.relationships[rabbit3.ID] = relationship1_3
        rabbit2.relationships[rabbit1.ID] = relationship2_1
        rabbit2.relationships[rabbit3.ID] = relationship2_3
        rabbit3.relationships[rabbit1.ID] = relationship3_1
        rabbit3.relationships[rabbit2.ID] = relationship3_2

        test_warren = Warren(name="test")

        # when - all is correct
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["romantic_10"]
        no_con_patrol_event = PatrolEvent(patrol_id="test2")
        no_con_patrol_event.relationship_constraints["relationship"] = []

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2, rabbit3], test_warren)
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

        # when - to high limit
        con_patrol_event = PatrolEvent(patrol_id="test3")
        con_patrol_event.relationship_constraints["relationship"] = ["romantic_30"]

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2, rabbit3], test_warren)
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))


        # when - different relationship values
        rabbit3.relationships[rabbit2.ID].romantic_love = 5
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["romantic_10"]

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2, rabbit3], test_warren)
        self.assertFalse(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(no_con_patrol_event))

    def test_multiple_constraint_patrol(self):
        # given
        rabbit1 = Rabbit()
        rabbit2 = Rabbit()

        relationship1 = Relationship(rabbit1,rabbit2)
        relationship2 = Relationship(rabbit2,rabbit1)

        relationship1.romantic_love = 20
        relationship2.romantic_love = 20
        relationship1.platonic_like = 20
        relationship2.platonic_like = 20

        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        rabbit1.relationships[rabbit2.ID] = relationship1
        rabbit2.relationships[rabbit1.ID] = relationship2

        test_warren = Warren(name="test")

        # when - correct
        con_patrol_event = PatrolEvent(patrol_id="test1")
        con_patrol_event.relationship_constraints["relationship"] = ["romantic_10"]
        con_patrol_event2 = PatrolEvent(patrol_id="test2")
        con_patrol_event2.relationship_constraints["relationship"] = ["platonic_10"]

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertTrue(patrol._filter_relationship(con_patrol_event2))

        # when - to high
        con_patrol_event2 = PatrolEvent(patrol_id="test2")
        con_patrol_event2.relationship_constraints["relationship"] = ["platonic_30"]

        # then
        patrol = Patrol()
        patrol.add_patrol_rabbits([rabbit1, rabbit2], test_warren)
        self.assertTrue(patrol._filter_relationship(con_patrol_event))
        self.assertFalse(patrol._filter_relationship(con_patrol_event2))