from typing import List
from scripts.utility import get_alive_warren_queens
from scripts.rabbit.rabbits import Rabbit
from scripts.rabbit.skills import SkillPath
from scripts.game_structure.game_essentials import game
from copy import deepcopy
import random

class Nutrition():
    """All the information about nutrition from one rabbit."""

    def __init__(self) -> None:
        """Initialize the class."""
        self.max_score = 1
        self.current_score = 0
        self.percentage = 0

    def __str__(self):
        this_is_a_dict_not_a_string = {
            "max_score": self.max_score,
            "current_score": self.current_score,
            "percentage": self.percentage,
        }
        return str(this_is_a_dict_not_a_string)

    @property
    def current_score(self):
        return self._current_score

    @current_score.setter
    def current_score(self, value) -> None:
        """
        When the current_score is changed, this will be handled here. It also automatically calculates the percentage of the nutrient.

            Parameters
            ----------
            value : int|float
                the value which should be set to the current score
        """
        if value > self.max_score:
            value = self.max_score
        if value < 0:
            value = 0
        self._current_score = value
        self.percentage = self._current_score / self.max_score * 100


class Freshkill_Pile():
    """Handle everything related to the freshkill pile of the warren."""

    def __init__(self, pile: dict = None) -> None:
        """
        Initialize the class.

            Parameters
            ----------
            pile : dict
                the dictionary of the loaded pile from files
        """
        # the pile could be handled as a list but this makes it more readable
        if pile:
            self.pile = pile
            total = 0
            for k,v in pile.items():
                total += v
            self.total_amount = total
        else:
            self.pile = {
                "expires_in_4": game.prey_config["start_amount"],
                "expires_in_3": 0,
                "expires_in_2": 0,
                "expires_in_1": 0,
            }
            self.total_amount = game.prey_config["start_amount"]
        self.nutrition_info = {}
        self.living_rabbits = []
        self.needed_prey = 0

    def add_freshkill(self, amount) -> None:
        """
        Add new fresh kill to the pile.

            Parameters
            ----------
            amount : int|float
                the amount which should be added to the pile
        """
        self.pile["expires_in_4"] += amount
        self.total_amount += amount

    def remove_freshkill(self, amount, take_random: bool = False) -> None:
        """
        Remove a certain amount of fresh kill from the pile.

            Parameters
            ----------
            amount : int|float
                the amount which should be removed from the pile
            take_random : bool
                if it should be taken from the different sub-piles or not
        """
        if amount == 0:
            return
        order = ["expires_in_1", "expires_in_2", "expires_in_3", "expires_in_4"]
        if take_random:
            random.shuffle(order)       
        for key in order:
            amount = self.take_from_pile(key, amount)

    def _update_needed_food(self, living_rabbits: List[Rabbit]) -> None:
        sick_rabbits = [rabbit for rabbit in living_rabbits if rabbit.not_working() and "pregnant" not in rabbit.injuries]
        queen_dict, living_kits = get_alive_warren_queens(self.living_rabbits)
        relevant_queens = []
        # kits under 3 months are feed by the queen
        for queen_id, their_kits in queen_dict.items():
            queen = Rabbit.fetch_rabbit(queen_id)
            young_kits = [kit for kit in their_kits if kit.months < 3]
            if len(young_kits) > 0:
                relevant_queens.append(queen)
        pregnant_rabbits = [rabbit for rabbit in living_rabbits if "pregnant" in rabbit.injuries and rabbit.ID not in queen_dict.keys()]

        # all normal status rabbits calculation
        needed_prey = sum([PREY_REQUIREMENT[rabbit.status] for rabbit in living_rabbits if rabbit.status not in ["newborn", "kitten"]])
        # increase the number for sick rabbits
        needed_prey += len(sick_rabbits) * CONDITION_INCREASE
        # increase the number of prey which are missing for relevant queens an pregnant rabbits
        needed_prey += (len(relevant_queens) + len(pregnant_rabbits)) * (PREY_REQUIREMENT["queen/pregnant"] - PREY_REQUIREMENT["rabbit"])
        # increase the number of prey for kits, which are not taken care by a queen
        needed_prey += sum([PREY_REQUIREMENT[rabbit.status] for rabbit in living_kits])
        
        self.needed_prey = needed_prey

    def time_skip(self, living_rabbits: list, event_list: list) -> None:
        """
        Handle the time skip for the freshkill pile, 'age' the prey and feeding the rabbits.

            Parameters
            ----------
            living_rabbits : list
                list of living rabbits which should be feed
        """
        self.living_rabbits = living_rabbits
        previous_amount = 0
        # update the freshkill pile
        for key, value in self.pile.items():
            self.pile[key] = previous_amount
            previous_amount = value
            if key == "expires_in_1" and FRESHKILL_ACTIVE and value > 0:
                event_list.append(f"Some prey expired, {value} pieces where removed from the pile.")
        self.total_amount = sum(self.pile.values())
        value_diff = self.total_amount
        self.feed_rabbits(living_rabbits)
        value_diff -= sum(self.pile.values())
        event_list.append(f"{value_diff} pieces of prey where consumed.")
        self._update_needed_food(living_rabbits)

    def feed_rabbits(self, living_rabbits: list) -> None:
        """
        Handles to feed all living warren rabbits. This happens before the aging up.

            Parameters
            ----------
            living_rabbits : list
                list of living rabbits which should be feed
        """
        self.update_nutrition(living_rabbits)
        # NOTE: this is for testing purposes
        if not game.warren:
            self.tactic_status(living_rabbits)
            return

        # NOTE: the tactics should have a own function for testing purposes
        if game.warren.warren_settings["younger first"]:
            self.tactic_younger_first(living_rabbits)
        elif game.warren.warren_settings["less nutrition first"]:
            self.tactic_less_nutrition_first(living_rabbits)
        elif game.warren.warren_settings["more experience first"]:
            self.tactic_more_experience_first(living_rabbits)
        elif game.warren.warren_settings["harvester first"]:
            self.tactic_harvester_first(living_rabbits)
        elif game.warren.warren_settings["sick/injured first"]:
            self.tactic_sick_injured_first(living_rabbits)
        elif game.warren.warren_settings["by-status"]:
            self.tactic_status(living_rabbits)
        else:
            self.tactic_status(living_rabbits)

    def amount_food_needed(self):
        """
            Returns
            -------
            needed_prey : int|float
                the amount of prey the Clan needs
        """
        living_rabbits = [rabbit for rabbit in Rabbit.all_rabbits.values() if not (rabbit.dead or rabbit.outside or rabbit.exiled)]
        self._update_needed_food(living_rabbits)
        return self.needed_prey

    def warren_has_enough_food(self) -> bool:
        """
            Returns
            -------
            _ : bool
                check if the amount of the prey is enough for one month
        """
        return self.amount_food_needed() <= self.total_amount


    # ---------------------------------------------------------------------------- #
    #                                    tactics                                   #
    # ---------------------------------------------------------------------------- #

    def tactic_status(self, living_rabbits: List[Rabbit]) -> None:
        """
        With this tactic, the rabbits will be fed after status + age.

        Parameters
        ----------
            living_rabbits : list
                the list of rabbits which should be feed
        """
        relevant_group = []
        queen_dict, kits = get_alive_warren_queens(living_rabbits)
        fed_kits = []
        relevant_queens = []
        # kits under 3 months are feed by the queen
        for queen_id, their_kits in queen_dict.items():
            queen = Rabbit.fetch_rabbit(queen_id)
            young_kits = [kit for kit in their_kits if kit.months < 3]
            if len(young_kits) > 0:
                fed_kits.extend(young_kits)
                relevant_queens.append(queen)
        
        pregnant_rabbits = [rabbit for rabbit in living_rabbits if "pregnant" in rabbit.injuries and rabbit.ID not in queen_dict.keys()]

        for feeding_status in FEEDING_ORDER:
            if feeding_status == "newborn":
                relevant_group = [
                    rabbit for rabbit in living_rabbits if rabbit.status == "newborn" and rabbit not in fed_kits
                ]
            elif feeding_status == "kitten":
                relevant_group = [
                    rabbit for rabbit in living_rabbits if rabbit.status == "kitten" and rabbit not in fed_kits
                ]
            elif feeding_status == "queen/pregnant":
                relevant_group = relevant_queens + pregnant_rabbits
            else:
                relevant_group = [rabbit for rabbit in living_rabbits if str(rabbit.status) == feeding_status]
                # remove all rabbits, which are also queens / pregnant
                relevant_group = [rabbit for rabbit in relevant_group if rabbit not in relevant_queens and rabbit not in pregnant_rabbits]

            if len(relevant_group) == 0:
                continue
        
            sorted_group = sorted(relevant_group, key=lambda x: x.months)
            if feeding_status == "queen/pregnant":
                self.feed_group(sorted_group, True)
            elif feeding_status in ["newborn", "kitten"]:
                self.feed_group(sorted_group, False, fed_kits)
            else:
                self.feed_group(sorted_group)

    def tactic_younger_first(self, living_rabbits: List[Rabbit]) -> None:
        """
        With this tactic, the youngest rabbits will be fed first.

        Parameters
        ----------
            living_rabbits : list
                the list of rabbits which should be feed
        """
        sorted_rabbits = sorted(living_rabbits, key=lambda x: x.months)
        self.feed_group(sorted_rabbits)

    def tactic_less_nutrition_first(self, living_rabbits: List[Rabbit]) -> None:
        """
        With this tactic, the rabbits with the lowest nutrition will be feed first.

        Parameters
        ----------
            living_rabbits : list
                the list of rabbits which should be feed
        """
        if len(living_rabbits) == 0:
            return
        
        # first get special groups, which need to be looked out for, when feeding
        queen_dict, kits = get_alive_warren_queens(living_rabbits)
        fed_kits = []
        relevant_queens = []
        # kits under 3 months are feed by the queen
        for queen_id, their_kits in queen_dict.items():
            queen = Rabbit.fetch_rabbit(queen_id)
            young_kits = [kit for kit in their_kits if kit.months < 3]
            if len(young_kits) > 0:
                fed_kits.extend(young_kits)
                relevant_queens.append(queen)
        pregnant_rabbits = [rabbit for rabbit in living_rabbits if "pregnant" in rabbit.injuries and rabbit.ID not in queen_dict.keys()]

        # first split nutrition information into low nutrition and satisfied
        ration_prey = game.warren.warren_settings["ration prey"] if game.warren else False

        low_nutrition = {}
        satisfied = {}
        for rabbit in living_rabbits:
            if self.nutrition_info[rabbit.ID].percentage < 100:
                low_nutrition[rabbit.ID] = self.nutrition_info[rabbit.ID]
            else:
                satisfied[rabbit.ID] = self.nutrition_info[rabbit.ID]
        # if there are no low nutrition rabbits, go back to status tactic
        if len(low_nutrition) == 0:
            self.tactic_status(living_rabbits)

        # sort the nutrition after amount
        sorted_nutrition = dict(sorted(low_nutrition.items(), key=lambda x: x[1].percentage))
        
        # use living_rabbits to fetch rabbit for testing
        fetch_rabbit = living_rabbits[0]

        # first feed the rabbits with the lowest nutrition
        for rabbit_id, v in sorted_nutrition.items():
            rabbit = Rabbit.all_rabbits[rabbit_id]
            status = str(rabbit.status)
            # check if this is a kit, if so check if they are fed by the mother
            if status in ["newborn", "kitten"] and rabbit in fed_kits:
                continue

            # check for queens / pregnant
            if rabbit.ID in queen_dict.keys() or rabbit in pregnant_rabbits:
                status = "queen/pregnant"
            feeding_amount = PREY_REQUIREMENT[status]
            needed_amount = feeding_amount

            # check for condition
            if "pregnant" not in rabbit.injuries and rabbit.not_working():
                feeding_amount += CONDITION_INCREASE
                needed_amount = feeding_amount
            else:
                if ration_prey and status == "rabbit":
                    feeding_amount = feeding_amount/2

            if self.amount_food_needed() < self.total_amount * 1.2 and self.nutrition_info[rabbit.ID].percentage < 100:
                feeding_amount += 1
            elif self.amount_food_needed() < self.total_amount and self.nutrition_info[rabbit.ID].percentage < 100:
                feeding_amount += 0.5
            self.feed_rabbit(rabbit, feeding_amount, needed_amount)

        # feed the rest according to their status
        remaining_rabbits = [fetch_rabbit.fetch_rabbit(info[0]) for info in satisfied.items()]
        self.tactic_status(remaining_rabbits)

    def tactic_more_experience_first(self, living_rabbits: List[Rabbit]) -> None:
        """
        With this tactic, the rabbits with the most experience will be fed first.

        Parameters
        ----------
            living_rabbits : list
                the list of rabbits which should be feed
        """
        sorted_rabbits = sorted(living_rabbits, key=lambda x: x.experience, reverse=True)
        self.feed_group(sorted_rabbits)

    def tactic_harvester_first(self, living_rabbits: List[Rabbit]) -> None:
        """
        With this tactic, the rabbits with the skill harvester (depending on rank) will be fed first.

        Parameters
        ----------
            living_rabbits : list
                the list of rabbits which should be feed
        """
        best_harvester = []
        for search_rank in range(1,4):
            for rabbit in living_rabbits.copy():
                if not rabbit.skills:
                    continue
                if rabbit.skills.primary and rabbit.skills.primary.path == SkillPath.HARVESTER and rabbit.skills.primary.tier == search_rank:
                    best_harvester.insert(0,rabbit)
                    living_rabbits.remove(rabbit)
                elif rabbit.skills.secondary and rabbit.skills.secondary.path == SkillPath.HARVESTER and rabbit.skills.secondary.tier == search_rank:
                    best_harvester.insert(0,rabbit)
                    living_rabbits.remove(rabbit)

        sorted_group = best_harvester + living_rabbits
        self.feed_group(sorted_group)

    def tactic_sick_injured_first(self, living_rabbits: List[Rabbit]) -> None:
        """
        With this tactic, the sick or injured rabbits will be fed first.

        Parameters
        ----------
            living_rabbits : list
                the list of rabbits which should be feed
        """
        sick_rabbits = [rabbit for rabbit in living_rabbits if rabbit.is_ill() or rabbit.is_injured()]
        healthy_rabbits = [rabbit for rabbit in living_rabbits if not rabbit.is_ill() and not rabbit.is_injured()]
        sorted_rabbits = sick_rabbits + healthy_rabbits
        self.feed_group(sorted_rabbits)

    # ---------------------------------------------------------------------------- #
    #                               helper functions                               #
    # ---------------------------------------------------------------------------- #

    def feed_group(self, group: list, queens = False, fed_kits = None) -> None:
        """
        Handle the feeding giving rabbits.

            Parameters
            ----------
            group : list
                the list of rabbits which should be feed
        """
        if len(group) == 0:
            return

        # first split nutrition information into low nutrition and satisfied
        ration_prey = game.warren.warren_settings["ration prey"] if game.warren else False

        # first feed the rabbits with the lowest nutrition
        for rabbit in group:
            status = str(rabbit.status)
            # check if this is a kit, if so check if they are fed by the mother
            if status in ["newborn", "kitten"] and fed_kits and rabbit in fed_kits:
                continue

            # check for queens / pregnant
            if queens:
                status = "queen/pregnant"
            feeding_amount = PREY_REQUIREMENT[status]
            needed_amount = feeding_amount

            # check for condition
            if "pregnant" not in rabbit.injuries and rabbit.not_working():
                feeding_amount += CONDITION_INCREASE
                needed_amount = feeding_amount
            else:
                if ration_prey and status == "rabbit":
                    feeding_amount = feeding_amount/2

            if self.amount_food_needed() < self.total_amount * 1.2 and self.nutrition_info[rabbit.ID].percentage < 100:
                feeding_amount += 1
            elif self.amount_food_needed() < self.total_amount and self.nutrition_info[rabbit.ID].percentage < 100:
                feeding_amount += 0.5
            self.feed_rabbit(rabbit, feeding_amount, needed_amount)

    def feed_rabbit(self, rabbit: Rabbit, amount, actual_needed) -> None:
        """
        Handle the feeding process.

            Parameters
            ----------
            rabbit : Rabbit
                the rabbit to feed
            amount : int|float
                the amount which will be consumed
            actual_needed : int|float
                the amount the rabbit actually needs for the month
        """
        ration = game.warren.warren_settings["ration prey"] if game.warren else False
        remaining_amount = amount
        amount_difference = actual_needed - amount
        order = ["expires_in_1", "expires_in_2", "expires_in_3", "expires_in_4"]
        for key in order:
            remaining_amount = self.take_from_pile(key, remaining_amount)

        if remaining_amount > 0 and amount_difference == 0:
            self.nutrition_info[rabbit.ID].current_score -= remaining_amount
        elif remaining_amount == 0:
            if actual_needed == 0:
                self.nutrition_info[rabbit.ID].current_score += amount
            elif amount > actual_needed:
                self.nutrition_info[rabbit.ID].current_score += (amount - actual_needed)
        elif ration and rabbit.status == "rabbit":
            feeding_amount = PREY_REQUIREMENT[rabbit.status]
            feeding_amount = feeding_amount/2
            self.nutrition_info[rabbit.ID].current_score -= feeding_amount

    def take_from_pile(self, pile_group: str, given_amount):
        """
        Take the amount from a specific pile group and returns the rest of the original needed amount.

            Parameters
            ----------
            pile_group : str
                the name of the pile group
            given_amount : int|float
                the amount which should be consumed

            Returns
            ----------
            remaining_amount : int|float
                the amount which could not be consumed from the given pile group
        """
        if given_amount == 0:
            return given_amount

        remaining_amount = given_amount
        if self.pile[pile_group] >= given_amount:
            self.pile[pile_group] -= given_amount
            self.total_amount -= given_amount
            remaining_amount = 0
        elif self.pile[pile_group] > 0:
            remaining_amount = given_amount - self.pile[pile_group]
            self.total_amount -= self.pile[pile_group]
            self.pile[pile_group] = 0

        return remaining_amount

    # ---------------------------------------------------------------------------- #
    #                              nutrition relevant                              #
    # ---------------------------------------------------------------------------- #

    def update_nutrition(self, living_rabbits: list) -> None:
        """
        Handles increasing or decreasing the max score of their nutrition depending on their age and automatically removes irrelevant rabbits.

            Parameters
            ----------
            living_rabbits : list
                the list of the current living rabbits, where the nutrition should be stored
        """
        old_nutrition_info = deepcopy(self.nutrition_info)
        self.nutrition_info = {}
        queen_dict, kits = get_alive_warren_queens(self.living_rabbits)

        for rabbit in living_rabbits:
            if str(rabbit.status) not in PREY_REQUIREMENT:
                continue
            # update the nutrition_info
            if rabbit.ID in old_nutrition_info:
                self.nutrition_info[rabbit.ID] = old_nutrition_info[rabbit.ID]
                factor = 3
                status_ = str(rabbit.status)
                if str(rabbit.status) in ["newborn", "kitten", "elder"]:
                    factor = 2
                if rabbit.ID in queen_dict.keys() or "pregnant" in rabbit.injuries:
                    status_ = "queen/pregnant"

                # check if the max_score is correct, otherwise update
                required_max = PREY_REQUIREMENT[status_] * factor
                current_score = self.nutrition_info[rabbit.ID].current_score
                if self.nutrition_info[rabbit.ID].max_score != required_max:
                    previous_max = self.nutrition_info[rabbit.ID].max_score
                    self.nutrition_info[rabbit.ID].max_score = required_max
                    self.nutrition_info[rabbit.ID].current_score = current_score / previous_max * required_max
            else:
                self.add_rabbit_to_nutrition(rabbit)

    def add_rabbit_to_nutrition(self, rabbit: Rabbit) -> None:
        """
            Parameters
            ----------
            rabbit : Rabbit
                the rabbit, which should be added to the nutrition info
        """
        nutrition = Nutrition()
        factor = 3
        if str(rabbit.status) in ["newborn", "kitten", "elder"]:
            factor = 2
        
        queen_dict, kits = get_alive_warren_queens(self.living_rabbits)
        prey_status = str(rabbit.status)
        if rabbit.ID in queen_dict.keys() or "pregnant" in rabbit.injuries:
            prey_status = "queen/pregnant"
        max_score = PREY_REQUIREMENT[prey_status] * factor
        nutrition.max_score = max_score
        nutrition.current_score = max_score
        nutrition.percentage = 100

        # adapt sickness (increase needed amount)
        if "pregnant" not in rabbit.injuries and rabbit.not_working():
            nutrition.max_score += CONDITION_INCREASE * factor
            nutrition.current_score = nutrition.max_score

        self.nutrition_info[rabbit.ID] = nutrition



# ---------------------------------------------------------------------------- #
#                                LOAD RESOURCES                                #
# ---------------------------------------------------------------------------- #


ADDITIONAL_PREY = game.prey_config["additional_prey"]
PREY_REQUIREMENT = game.prey_config["prey_requirement"]
CONDITION_INCREASE = game.prey_config["condition_increase"]
FEEDING_ORDER = game.prey_config["feeding_order"]
HARVESTER_BONUS = game.prey_config["harvester_bonus"]
HARVESTER_EXP_BONUS = game.prey_config["harvester_exp_bonus"]
FRESHKILL_EVENT_TRIGGER_FACTOR = game.prey_config["base_event_trigger_factor"]
EVENT_WEIGHT_TYPE = game.prey_config["events_weights"]
MAL_PERCENTAGE = game.prey_config["nutrition_malnourished_percentage"]
STARV_PERCENTAGE = game.prey_config["nutrition_starving_percentage"]

FRESHKILL_ACTIVE = game.prey_config["activate_death"]
FRESHKILL_EVENT_ACTIVE = game.prey_config["activate_events"]