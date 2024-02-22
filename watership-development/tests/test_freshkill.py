import unittest
import ujson
from scripts.rabbit.rabbits import Rabbit
from scripts.rabbit.skills import Skill, SkillPath
from scripts.warren import Warren
from scripts.warren_resources.freshkill import Freshkill_Pile
from scripts.utility import get_alive_warren_queens


class FreshkillPile(unittest.TestCase):

    def setUp(self) -> None:
        self.prey_config = None
        with open("resources/prey_config.json", 'r') as read_file:
            self.prey_config = ujson.loads(read_file.read())
        self.amount = self.prey_config["start_amount"]
        self.prey_requirement = self.prey_config["prey_requirement"]
        self.condition_increase = self.prey_config["condition_increase"]

    def test_add_freshkill(self) -> None:
        # given
        freshkill_pile = Freshkill_Pile()
        self.assertEqual(freshkill_pile.pile["expires_in_4"], self.amount)
        self.assertEqual(freshkill_pile.pile["expires_in_3"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_2"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_1"], 0)

        # then
        freshkill_pile.add_freshkill(1)
        self.assertEqual(freshkill_pile.pile["expires_in_4"], self.amount + 1)
        self.assertEqual(freshkill_pile.pile["expires_in_3"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_2"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_1"], 0)

    def test_remove_freshkill(self) -> None:
        # given
        freshkill_pile1 = Freshkill_Pile()
        freshkill_pile1.pile["expires_in_1"] = 10
        self.assertEqual(freshkill_pile1.pile["expires_in_1"], 10)
        freshkill_pile1.remove_freshkill(5)

        freshkill_pile2 = Freshkill_Pile()
        freshkill_pile2.remove_freshkill(5, True)

        # then
        self.assertEqual(freshkill_pile1.pile["expires_in_4"], self.amount)
        self.assertEqual(freshkill_pile1.pile["expires_in_1"], 5)
        self.assertEqual(freshkill_pile2.total_amount, self.amount - 5)

    def test_time_skip(self) -> None:
        # given
        freshkill_pile = Freshkill_Pile()
        self.assertEqual(freshkill_pile.pile["expires_in_4"], self.amount)
        self.assertEqual(freshkill_pile.pile["expires_in_3"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_2"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_1"], 0)

        # then
        freshkill_pile.time_skip([], [])
        self.assertEqual(freshkill_pile.pile["expires_in_4"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_3"], self.amount)
        self.assertEqual(freshkill_pile.pile["expires_in_2"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_1"], 0)
        freshkill_pile.time_skip([], [])
        self.assertEqual(freshkill_pile.pile["expires_in_4"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_3"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_2"], self.amount)
        self.assertEqual(freshkill_pile.pile["expires_in_1"], 0)
        freshkill_pile.time_skip([], [])
        self.assertEqual(freshkill_pile.pile["expires_in_4"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_3"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_2"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_1"], self.amount)
        freshkill_pile.time_skip([], [])
        self.assertEqual(freshkill_pile.pile["expires_in_4"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_3"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_2"], 0)
        self.assertEqual(freshkill_pile.pile["expires_in_1"], 0)

    def test_feed_rabbits(self) -> None:
        # given
        test_warren = Warren(name="Test",
                         chief_rabbit=None,
                         captain=None,
                         healer=None,
                         biome='Forest',
                         burrow_bg=None,
                         game_mode='expanded',
                         starting_members=[],
                         starting_season='Spring')
        test_rabbit = Rabbit()
        test_rabbit.status = "rabbit"
        test_warren.add_rabbit(test_rabbit)

        # then
        self.assertEqual(test_warren.freshkill_pile.total_amount, self.amount)
        test_warren.freshkill_pile.feed_rabbits([test_rabbit])
        self.assertEqual(test_warren.freshkill_pile.total_amount,
                         self.amount - self.prey_requirement["rabbit"])

    def test_tactic_younger_first(self) -> None:
        # given
        freshkill_pile = Freshkill_Pile()
        current_amount = self.prey_requirement["rabbit"] * 2
        freshkill_pile.pile["expires_in_4"] = current_amount
        freshkill_pile.total_amount = current_amount

        youngest_rabbit = Rabbit()
        youngest_rabbit.status = "rabbit"
        youngest_rabbit.months = 20
        middle_rabbit = Rabbit()
        middle_rabbit.status = "rabbit"
        middle_rabbit.months = 30
        oldest_rabbit = Rabbit()
        oldest_rabbit.status = "rabbit"
        oldest_rabbit.months = 40

        freshkill_pile.add_rabbit_to_nutrition(youngest_rabbit)
        freshkill_pile.add_rabbit_to_nutrition(middle_rabbit)
        freshkill_pile.add_rabbit_to_nutrition(oldest_rabbit)
        self.assertEqual(
            freshkill_pile.nutrition_info[youngest_rabbit.ID].percentage, 100)
        self.assertEqual(
            freshkill_pile.nutrition_info[middle_rabbit.ID].percentage, 100)
        self.assertEqual(
            freshkill_pile.nutrition_info[oldest_rabbit.ID].percentage, 100)

        # when
        freshkill_pile.tactic_younger_first(
            [oldest_rabbit, middle_rabbit, youngest_rabbit])

        # then
        self.assertEqual(
            freshkill_pile.nutrition_info[youngest_rabbit.ID].percentage, 100)
        self.assertEqual(
            freshkill_pile.nutrition_info[middle_rabbit.ID].percentage, 100)
        self.assertNotEqual(
            freshkill_pile.nutrition_info[oldest_rabbit.ID].percentage, 100)

    def test_tactic_less_nutrition_first(self) -> None:
        # given
        freshkill_pile = Freshkill_Pile()
        current_amount = self.prey_requirement["rabbit"] * 2
        freshkill_pile.pile["expires_in_4"] = current_amount
        freshkill_pile.total_amount = current_amount

        lowest_rabbit = Rabbit()
        lowest_rabbit.status = "rabbit"
        lowest_rabbit.months = 20
        middle_rabbit = Rabbit()
        middle_rabbit.status = "rabbit"
        middle_rabbit.months = 30
        highest_rabbit = Rabbit()
        highest_rabbit.status = "rabbit"
        highest_rabbit.months = 40

        freshkill_pile.add_rabbit_to_nutrition(lowest_rabbit)
        max_score = freshkill_pile.nutrition_info[lowest_rabbit.ID].max_score
        give_score =  max_score - self.prey_requirement["rabbit"]
        freshkill_pile.nutrition_info[lowest_rabbit.ID].current_score = give_score

        freshkill_pile.add_rabbit_to_nutrition(middle_rabbit)
        give_score = max_score - (self.prey_requirement["rabbit"] / 2)
        freshkill_pile.nutrition_info[middle_rabbit.ID].current_score = give_score

        freshkill_pile.add_rabbit_to_nutrition(highest_rabbit)
        self.assertLessEqual(
            freshkill_pile.nutrition_info[lowest_rabbit.ID].percentage, 70)
        self.assertLessEqual(
            freshkill_pile.nutrition_info[middle_rabbit.ID].percentage, 90)
        self.assertEqual(
            freshkill_pile.nutrition_info[highest_rabbit.ID].percentage, 100)

        # when
        living_rabbits = [highest_rabbit, middle_rabbit, lowest_rabbit]
        freshkill_pile.living_rabbits = living_rabbits
        freshkill_pile.tactic_less_nutrition_first(living_rabbits)

        # then
        self.assertEqual(freshkill_pile.total_amount,0)
        self.assertGreaterEqual(
            freshkill_pile.nutrition_info[lowest_rabbit.ID].percentage, 60)
        self.assertGreaterEqual(
            freshkill_pile.nutrition_info[middle_rabbit.ID].percentage, 80)
        self.assertLess(
            freshkill_pile.nutrition_info[highest_rabbit.ID].percentage, 70)

    def test_tactic_sick_injured_first(self) -> None:
        # given
        # young enough kid
        injured_rabbit = Rabbit()
        injured_rabbit.status = "rabbit"
        injured_rabbit.injuries["test_injury"] = {
            "severity": "major"
        }
        sick_rabbit = Rabbit()
        sick_rabbit.status = "rabbit"
        sick_rabbit.illnesses["test_illness"] = {
            "severity": "major"
        }
        healthy_rabbit = Rabbit()
        healthy_rabbit.status = "rabbit"


        freshkill_pile = Freshkill_Pile()
        # be able to feed one queen and some of the rabbit
        current_amount = self.prey_requirement["rabbit"] * 2 + self.condition_increase * 2
        freshkill_pile.pile["expires_in_4"] = current_amount
        freshkill_pile.total_amount = current_amount

        freshkill_pile.add_rabbit_to_nutrition(injured_rabbit)
        freshkill_pile.add_rabbit_to_nutrition(sick_rabbit)
        freshkill_pile.add_rabbit_to_nutrition(healthy_rabbit)
        self.assertEqual(freshkill_pile.nutrition_info[injured_rabbit.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[sick_rabbit.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[healthy_rabbit.ID].percentage, 100)

        # when
        freshkill_pile.tactic_sick_injured_first([healthy_rabbit, sick_rabbit, injured_rabbit])

        # then
        self.assertEqual(freshkill_pile.nutrition_info[injured_rabbit.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[sick_rabbit.ID].percentage, 100)
        self.assertLess(freshkill_pile.nutrition_info[healthy_rabbit.ID].percentage, 70)

    def test_more_experience_first(self) -> None:
        # given
        freshkill_pile = Freshkill_Pile()
        current_amount = self.prey_requirement["rabbit"]
        freshkill_pile.pile["expires_in_4"] = current_amount
        freshkill_pile.total_amount = current_amount

        lowest_rabbit = Rabbit()
        lowest_rabbit.status = "rabbit"
        lowest_rabbit.experience = 20
        middle_rabbit = Rabbit()
        middle_rabbit.status = "rabbit"
        middle_rabbit.experience = 30
        highest_rabbit = Rabbit()
        highest_rabbit.status = "rabbit"
        highest_rabbit.experience = 40

        freshkill_pile.add_rabbit_to_nutrition(lowest_rabbit)
        freshkill_pile.add_rabbit_to_nutrition(middle_rabbit)
        freshkill_pile.add_rabbit_to_nutrition(highest_rabbit)
        self.assertEqual(
            freshkill_pile.nutrition_info[lowest_rabbit.ID].percentage, 100)
        self.assertEqual(
            freshkill_pile.nutrition_info[middle_rabbit.ID].percentage, 100)
        self.assertEqual(
            freshkill_pile.nutrition_info[highest_rabbit.ID].percentage, 100)

        # when
        freshkill_pile.tactic_more_experience_first(
            [lowest_rabbit, middle_rabbit, highest_rabbit])

        # then
        #self.assertEqual(freshkill_pile.total_amount,0)
        self.assertLess(
            freshkill_pile.nutrition_info[lowest_rabbit.ID].percentage, 70)
        self.assertLess(
            freshkill_pile.nutrition_info[middle_rabbit.ID].percentage, 90)
        self.assertEqual(
            freshkill_pile.nutrition_info[highest_rabbit.ID].percentage, 100)

    def test_harvester_first(self) -> None:
        # check also different ranks of hunting skill
        # given
        freshkill_pile = Freshkill_Pile()
        current_amount = self.prey_requirement["rabbit"] + (self.prey_requirement["rabbit"]/2)
        freshkill_pile.pile["expires_in_4"] = current_amount
        freshkill_pile.total_amount = current_amount

        best_harvester_rabbit = Rabbit()
        best_harvester_rabbit.status = "rabbit"
        best_harvester_rabbit.skills.primary = Skill(SkillPath.HARVESTER, 25)
        self.assertEqual(best_harvester_rabbit.skills.primary.tier, 3)
        harvester_rabbit = Rabbit()
        harvester_rabbit.status = "rabbit"
        harvester_rabbit.skills.primary = Skill(SkillPath.HARVESTER, 0)
        self.assertEqual(harvester_rabbit.skills.primary.tier, 1)
        no_harvester_rabbit = Rabbit()
        no_harvester_rabbit.status = "rabbit"
        no_harvester_rabbit.skills.primary = Skill(SkillPath.MEDIATOR, 0, True)

        freshkill_pile.add_rabbit_to_nutrition(best_harvester_rabbit)
        freshkill_pile.add_rabbit_to_nutrition(harvester_rabbit)
        freshkill_pile.add_rabbit_to_nutrition(no_harvester_rabbit)
        self.assertEqual(freshkill_pile.nutrition_info[best_harvester_rabbit.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[harvester_rabbit.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[no_harvester_rabbit.ID].percentage, 100)

        # when
        living_rabbits = [harvester_rabbit, no_harvester_rabbit, best_harvester_rabbit]
        freshkill_pile.tactic_harvester_first(living_rabbits)

        # then
        # this harvester should be fed completely
        self.assertEqual(freshkill_pile.nutrition_info[best_harvester_rabbit.ID].percentage, 100)
        # this harvester should be fed partially
        self.assertLess(freshkill_pile.nutrition_info[harvester_rabbit.ID].percentage, 90)
        self.assertGreater(freshkill_pile.nutrition_info[harvester_rabbit.ID].percentage, 70)
        # this rabbit should not be fed
        self.assertLess(freshkill_pile.nutrition_info[no_harvester_rabbit.ID].percentage, 70)

    def test_queen_handling(self) -> None:
        # given
        # young enough kid
        mother = Rabbit()
        mother.gender = "female"
        mother.status = "rabbit"
        father = Rabbit()
        father.gender = "male"
        father.status = "rabbit"
        kid = Rabbit()
        kid.status = "kitten"
        kid.months = 2
        kid.parent1 = father
        kid.parent2 = mother

        no_parent = Rabbit()
        no_parent.status = "rabbit"

        freshkill_pile = Freshkill_Pile()
        # be able to feed one queen and some of the rabbit
        current_amount = self.prey_requirement["queen/pregnant"] + (self.prey_requirement["rabbit"] / 2)
        freshkill_pile.pile["expires_in_4"] = current_amount
        freshkill_pile.total_amount = current_amount

        freshkill_pile.add_rabbit_to_nutrition(mother)
        freshkill_pile.add_rabbit_to_nutrition(father)
        freshkill_pile.add_rabbit_to_nutrition(kid)
        freshkill_pile.add_rabbit_to_nutrition(no_parent)
        self.assertEqual(freshkill_pile.nutrition_info[kid.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[mother.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[father.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[no_parent.ID].percentage, 100)

        # when
        living_rabbits = [no_parent, father, kid, mother]
        self.assertEqual([mother.ID], list(get_alive_warren_queens(living_rabbits)[0].keys()))
        freshkill_pile.tactic_status(living_rabbits)

        # then
        self.assertEqual(freshkill_pile.nutrition_info[kid.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[mother.ID].percentage, 100)
        self.assertLess(freshkill_pile.nutrition_info[no_parent.ID].percentage, 90)
        self.assertGreater(freshkill_pile.nutrition_info[no_parent.ID].percentage, 70)
        self.assertLess(freshkill_pile.nutrition_info[father.ID].percentage, 70)

    def test_pregnant_handling(self) -> None:
        # given
        # young enough kid
        pregnant_rabbit = Rabbit()
        pregnant_rabbit.status = "rabbit"
        pregnant_rabbit.injuries["pregnant"] = {
            "severity": "minor"
        }
        rabbit2 = Rabbit()
        rabbit2.status = "rabbit"
        rabbit3 = Rabbit()
        rabbit3.status = "rabbit"


        freshkill_pile = Freshkill_Pile()
        # be able to feed one queen and some of the rabbit
        current_amount = self.prey_requirement["queen/pregnant"]
        freshkill_pile.pile["expires_in_4"] = current_amount
        freshkill_pile.total_amount = current_amount

        freshkill_pile.add_rabbit_to_nutrition(pregnant_rabbit)
        freshkill_pile.add_rabbit_to_nutrition(rabbit2)
        freshkill_pile.add_rabbit_to_nutrition(rabbit3)
        self.assertEqual(freshkill_pile.nutrition_info[pregnant_rabbit.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[rabbit2.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[rabbit3.ID].percentage, 100)

        # when
        freshkill_pile.feed_rabbits([rabbit2, rabbit3, pregnant_rabbit])

        # then
        self.assertEqual(freshkill_pile.nutrition_info[pregnant_rabbit.ID].percentage, 100)
        self.assertLess(freshkill_pile.nutrition_info[rabbit2.ID].percentage, 70)
        self.assertLess(freshkill_pile.nutrition_info[rabbit3.ID].percentage, 70)

    def test_sick_handling(self) -> None:
        # given
        # young enough kid
        injured_rabbit = Rabbit()
        injured_rabbit.status = "rabbit"
        injured_rabbit.injuries["claw-wound"] = {
            "severity": "major"
        }
        sick_rabbit = Rabbit()
        sick_rabbit.status = "rabbit"
        sick_rabbit.illnesses["diarrhea"] = {
            "severity": "major"
        }
        healthy_rabbit = Rabbit()
        healthy_rabbit.status = "rabbit"


        freshkill_pile = Freshkill_Pile()
        # be able to feed one queen and some of the rabbit
        current_amount = self.prey_requirement["rabbit"] * 2 + self.condition_increase * 2
        freshkill_pile.pile["expires_in_4"] = current_amount
        freshkill_pile.total_amount = current_amount

        freshkill_pile.add_rabbit_to_nutrition(injured_rabbit)
        freshkill_pile.add_rabbit_to_nutrition(sick_rabbit)
        freshkill_pile.add_rabbit_to_nutrition(healthy_rabbit)
        self.assertEqual(freshkill_pile.nutrition_info[injured_rabbit.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[sick_rabbit.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[healthy_rabbit.ID].percentage, 100)

        # when
        freshkill_pile.feed_rabbits([sick_rabbit, injured_rabbit, healthy_rabbit])

        # then
        self.assertEqual(freshkill_pile.nutrition_info[injured_rabbit.ID].percentage, 100)
        self.assertEqual(freshkill_pile.nutrition_info[sick_rabbit.ID].percentage, 100)
        self.assertLess(freshkill_pile.nutrition_info[healthy_rabbit.ID].percentage, 70)
