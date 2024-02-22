# pylint: disable=line-too-long
"""

TODO: Docs


"""

  # pylint: enable=line-too-long

from scripts.game_structure.game_essentials import game
from scripts.rabbit.skills import SkillPath


def medical_rabbits_condition_fulfilled(all_rabbits,
                                     amount_per_med,
                                     give_warrenmembers_covered=False):
    """
    returns True if the player has enough meds for the whole warren

    set give_warrenmembers_covered to True to return the int of warrenmembers that the meds can treat
    """
    
    fulfilled = False
    
    medical_rabbits = [i for i in all_rabbits if not i.dead and not i.outside and not
                                            i.not_working() and i.status in 
                                            ["healer", 
                                             "healer apprentice"]]
    full_med = [i for i in medical_rabbits if i.status == "healer"]
    apprentices = [i for i in medical_rabbits if i.status == "healer apprentice"]
    
    total_exp = 0
    for rabbit in medical_rabbits:
        total_exp += rabbit.experience 
    total_exp = total_exp * 0.003
    
    # Determine the total med number. Med rabbits with certain skill counts 
    # as "more" of a med rabbit.  Only full medicine rabbit can have their skills have effect
    total_med_number = len(apprentices) / 2
    for rabbit in full_med:
        if rabbit.skills.meets_skill_requirement(SkillPath.HEALER, 3):
            total_med_number += 2
        elif rabbit.skills.meets_skill_requirement(SkillPath.HEALER, 2):
            total_med_number += 1.75
        elif rabbit.skills.meets_skill_requirement(SkillPath.HEALER, 2):
            total_med_number += 1.5
        else:
            total_med_number += 1
        
    
    adjust_med_number = total_med_number + total_exp

    can_care_for = int(adjust_med_number * (amount_per_med + 1))

    relevant_rabbits = list(
        filter(lambda c: not c.dead and not c.outside, all_rabbits))

    if give_warrenmembers_covered is True:
        return can_care_for
    if can_care_for >= len(relevant_rabbits):
        fulfilled = True
    return fulfilled


def get_amount_rabbit_for_one_medic(warren):
    """Returns """
    amount = 10
    if warren and warren.game_mode == 'cruel season':
        amount = 7
    return amount


# ---------------------------------------------------------------------------- #
#                                    Illness                                   #
# ---------------------------------------------------------------------------- #


class Illness:
    """
    TODO: DOCS
    """

    def __init__(self,
                 name,
                 severity,
                 mortality,
                 infectiousness,
                 duration,
                 medicine_duration,
                 medicine_mortality,
                 risks,
                 herbs=None,
                 event_triggered=False):
        self.name = name
        self.severity = severity
        self.mortality = int(mortality)
        self.infectiousness = int(infectiousness)
        self.duration = int(duration)
        self.medicine_duration = int(medicine_duration)
        self.medicine_mortality = int(medicine_mortality)
        self.risks = risks
        self.herbs = herbs if herbs else []
        self.new = event_triggered

        self.current_duration = duration
        self.current_mortality = mortality

        amount_per_med = get_amount_rabbit_for_one_medic(game.warren)
        if medical_rabbits_condition_fulfilled(game.rabbit_class.all_rabbits.values(),
                                            amount_per_med):
            self.current_duration = medicine_duration
            self.current_mortality = medicine_mortality

    @property
    def current_duration(self):
        """
        TODO: DOCS
        """
        return self._current_duration

    @current_duration.setter
    def current_duration(self, value):
        """
        TODO: DOCS
        """
        amount_per_med = get_amount_rabbit_for_one_medic(game.warren)
        if medical_rabbits_condition_fulfilled(game.rabbit_class.all_rabbits.values(),
                                            amount_per_med):
            if value > self.medicine_duration:
                value = self.medicine_duration

        self._current_duration = value

    @property
    def current_mortality(self):
        """
        TODO: DOCS
        """
        return self._current_mortality

    @current_mortality.setter
    def current_mortality(self, value):
        """
        TODO: DOCS
        """
        amount_per_med = get_amount_rabbit_for_one_medic(game.warren)
        if medical_rabbits_condition_fulfilled(game.rabbit_class.all_rabbits.values(),
                                            amount_per_med):
            if value < self.medicine_mortality:
                value = self.medicine_mortality

        self._current_mortality = value


# ---------------------------------------------------------------------------- #
#                                   Injuries                                   #
# ---------------------------------------------------------------------------- #


class Injury:
    """
    TODO: DOCS
    """

    def __init__(self,
                 name,
                 severity,
                 duration,
                 medicine_duration,
                 mortality,
                 risks=None,
                 illness_infectiousness=None,
                 also_got=None,
                 cause_permanent=None,
                 herbs=None,
                 event_triggered=False):
        self.name = name
        self.severity = severity
        self.duration = duration
        self.medicine_duration = medicine_duration
        self.mortality = mortality
        self.risks = risks
        self.illness_infectiousness = illness_infectiousness
        self.also_got = also_got
        self.cause_permanent = cause_permanent
        self.herbs = herbs if herbs else []
        self.new = event_triggered

        self.current_duration = duration
        self.current_mortality = mortality

        amount_per_med = get_amount_rabbit_for_one_medic(game.warren)
        if medical_rabbits_condition_fulfilled(game.rabbit_class.all_rabbits.values(),
                                            amount_per_med):
            self.current_duration = medicine_duration

    @property
    def current_duration(self):
        """
        TODO: DOCS
        """
        return self._current_duration

    @current_duration.setter
    def current_duration(self, value):
        amount_per_med = get_amount_rabbit_for_one_medic(game.warren)
        if medical_rabbits_condition_fulfilled(game.rabbit_class.all_rabbits.values(),
                                            amount_per_med):
            if value > self.medicine_duration:
                value = self.medicine_duration

        self._current_duration = value

    @property
    def current_mortality(self):
        """
        TODO: DOCS
        """
        return self._current_mortality

    @current_mortality.setter
    def current_mortality(self, value):
        self._current_mortality = value


# ---------------------------------------------------------------------------- #
#                             Permanent Conditions                             #
# ---------------------------------------------------------------------------- #


class PermanentCondition:
    """
    TODO: DOCS
    """

    def __init__(self,
                 name,
                 severity,
                 months_until,
                 congenital='never',
                 mortality=0,
                 risks=None,
                 illness_infectiousness=None,
                 herbs=None,
                 event_triggered=False):
        self.name = name
        self.severity = severity
        self.congenital = congenital
        self.months_until = months_until
        self.mortality = mortality
        self.risks = risks
        self.illness_infectiousness = illness_infectiousness
        self.herbs = herbs if herbs else []
        self.new = event_triggered

        self.current_mortality = mortality

    # severity level determines retirement:
    # severe - auto retire, major - chance retire, minor - no retire
    # congenital determines if a rabbit can be born with it or not: never, sometimes, always

    # months_until is used if you want a delay between when the rabbit
    # contracts the condition and when the rabbit presents that condition

    @property
    def current_mortality(self):
        """
        TODO: DOCS
        """
        return self._current_mortality

    @current_mortality.setter
    def current_mortality(self, value):
        """
        TODO: DOCS
        """
        self._current_mortality = value
