import random
from typing import Union

from scripts.rabbit.history import History
from scripts.events_module.generate_events import GenerateEvents
from scripts.game_structure.game_essentials import game
from scripts.utility import event_text_adjust
from scripts.rabbit.rabbits import Rabbit
from scripts.event_class import Single_Event
from scripts.warren_resources.freshkill import (
    Freshkill_Pile, 
    MAL_PERCENTAGE , 
    STARV_PERCENTAGE, 
    FRESHKILL_ACTIVE, 
    FRESHKILL_EVENT_TRIGGER_FACTOR, 
    FRESHKILL_EVENT_ACTIVE, 
    EVENT_WEIGHT_TYPE
)

class Freshkill_Events():
    """All events with a connection to freshkill pile or the nutrition of rabbits."""

    @staticmethod
    def handle_nutrient(rabbit: Rabbit, nutrition_info: dict) -> None:
        """
        Handles gaining conditions or death for rabbits with low nutrient.
        This function should only be called if the game is in 'expanded' or 'cruel season' mode.

            Parameters
            ----------
            rabbit : Rabbit
                the rabbit which has to be checked and updated
            nutrition_info : dict
                dictionary of all nutrition information (can be found in the freshkill pile)
        """
        if not FRESHKILL_ACTIVE:
            return

        if rabbit.ID not in nutrition_info.keys():
            print(f"WARNING: Could not find rabbit with ID {rabbit.ID}({rabbit.name}) in the nutrition information.")
            return

        # get all events for a certain status of a rabbit
        rabbit_nutrition = nutrition_info[rabbit.ID]
        possible_events = GenerateEvents.possible_short_events(rabbit.status, rabbit.age, "nutrition")

        # get the other needed information and values to create a event
        possible_other_rabbits = [i for i in Rabbit.all_rabbits.values() if not (i.dead or i.outside) and i.ID != rabbit.ID]
        if len(possible_other_rabbits) <= 0:
            other_rabbit = None
        else:
            other_rabbit = random.choice(possible_other_rabbits)
        other_warren = random.choice(game.warren.all_warrens)
        other_warren_name = f'{other_warren.name}Clan'

        if other_warren_name == 'None':
            other_warren = game.warren.all_warrens[0]
            other_warren_name = f'{other_warren.name}'

        needed_tags = []
        illness = None
        heal = False

        # handle death first, if percentage is 0 or lower, the rabbit will die
        if rabbit_nutrition.percentage <= 0:
            # this statement above will prevent, that a dead rabbit will get an illness
            final_events = Freshkill_Events.get_filtered_possibilities(possible_events, ["death"], rabbit, other_rabbit)
            if len(final_events) <= 0:
                return
            chosen_event = (random.choice(final_events))

            # set up all the text's
            death_text = event_text_adjust(Rabbit, chosen_event.event_text, rabbit, other_rabbit, other_warren_name)
            history_text = 'this should not show up - history text'

            # give history to rabbit if they die
            if rabbit.status != "chief rabbit" and chosen_event.history_text[0] is not None:
                history_text = event_text_adjust(Rabbit, chosen_event.history_text[0], rabbit, other_rabbit, other_warren_name)
            elif rabbit.status == "chief rabbit" and chosen_event.history_text[1] is not None:
                history_text = event_text_adjust(Rabbit, chosen_event.history_text[1], rabbit, other_rabbit, other_warren_name)

            rabbit.die()
            History.add_death(rabbit, history_text)
            
            # if the rabbit is the chief rabbit, the illness "starving" needs to be added again

            types = ["birth_death"]
            game.cur_events_list.append(Single_Event(death_text, types, [rabbit.ID]))
            return

        # heal rabbit if percentage is high enough and rabbit is ill
        elif rabbit_nutrition.percentage > MAL_PERCENTAGE and rabbit.is_ill() and "malnourished" in rabbit.illnesses:
            needed_tags = ["malnourished_healed"]
            illness = "malnourished"
            heal = True

        # heal rabbit if percentage is high enough and rabbit is ill
        elif rabbit_nutrition.percentage > STARV_PERCENTAGE and rabbit.is_ill() and "starving" in rabbit.illnesses:
            if rabbit_nutrition.percentage < MAL_PERCENTAGE:
                if "malnourished" not in rabbit.illnesses:
                    rabbit.get_ill("malnourished")
                needed_tags = ["starving_healed"]
                illness = "starving"
                heal = True
            else:
                needed_tags = ["starving_healed"]
                illness = "starving"
                heal = True

        elif rabbit_nutrition.percentage <= MAL_PERCENTAGE and rabbit_nutrition.percentage > STARV_PERCENTAGE:
            # because of the smaller 'nutrition buffer', kitten and elder should get the starving condition.
            if rabbit.status in ["kit", "elder"]:
                needed_tags = ["starving"]
                illness = "starving"
            else:        
                needed_tags = ["malnourished"]
                illness = "malnourished"

        elif rabbit_nutrition.percentage <= STARV_PERCENTAGE:
            needed_tags = ["starving"]
            illness = "starving"

        # handle the gaining/healing illness
        if heal:
            rabbit.illnesses.pop(illness)
        elif not heal and illness:
            rabbit.get_ill(illness)

        # filter the events according to the needed tags 
        final_events = Freshkill_Events.get_filtered_possibilities(possible_events, needed_tags, rabbit, other_rabbit)        
        if len(final_events) <= 0:
            return

        chosen_event = (random.choice(final_events))
        event_text = event_text_adjust(Rabbit, chosen_event.event_text, rabbit, other_rabbit, other_warren_name)
        types = ["health"]
        game.cur_events_list.append(Single_Event(event_text, types, [rabbit.ID]))

    @staticmethod
    def handle_amount_freshkill_pile(freshkill_pile: Freshkill_Pile, living_rabbits: list) -> None:
        """
        Handles events (eg. a fox is attacking the burrow), which are related to the freshkill pile.
        This function should only be called if the game is in 'expanded' or 'cruel season' mode.

            Parameters
            ----------
            freshkill_pile : Freshkill_Pile
                the freshkill pile which is used to calculate the event
            living_rabbits : list
                a list of rabbits which have to be feed
        """

        if not living_rabbits or len(living_rabbits) == 0:
            # End if there are no living rabbits left.
            return

        # return if settings turned freshkill events off
        if not FRESHKILL_EVENT_ACTIVE:
            return

        # change the trigger factor according to the size of the warren
        trigger_factor = FRESHKILL_EVENT_TRIGGER_FACTOR
        trigger_factor = trigger_factor - ((len(living_rabbits)) / 50)
        if len(living_rabbits) > 30:
            trigger_factor = trigger_factor - ((len(living_rabbits)) / 50)
        if trigger_factor < 1.1:
            trigger_factor = 1.1

        # check if amount of the freshkill pile is too big and a event will be triggered
        needed_amount = freshkill_pile.amount_food_needed()
        trigger_value = trigger_factor * needed_amount
        print(f" -- FRESHKILL: amount {trigger_value} to trigger freshkill event. current amount {freshkill_pile.total_amount}")
        if freshkill_pile.total_amount < trigger_value:
            return

        factor = int(freshkill_pile.total_amount / needed_amount)
        chance = 10 - factor
        if chance <= 0:
            chance = 1
        print(f" -- FRESHKILL: trigger chance of 1/{chance}")
        choice = random.randint(1,chance)
        if choice != 1:
            return

        # check if there is much more prey than needed, to filter the events
        much_prey = False
        if freshkill_pile.total_amount >= (trigger_value + needed_amount) and len(living_rabbits) > 10:
            much_prey = True

        # get different resources, which are later needed
        rabbit = random.choice(living_rabbits)
        other_rabbit = None
        if len(living_rabbits) > 1:
            other_rabbit = random.choice(living_rabbits)
            while other_rabbit.ID == rabbit.ID:
                other_rabbit = random.choice(living_rabbits)

        possible_events = GenerateEvents.possible_short_events(rabbit.status, rabbit.age, "freshkill_pile")
        possible_tasks = []
        for tag_type in EVENT_WEIGHT_TYPE:
            possible_tasks.extend(tag_type * EVENT_WEIGHT_TYPE[tag_type])

        # randomly choose which tags are used for the event
        choice = random.choice(possible_tasks)
        double_event = random.choice([True, False])
        needed_tags = []
        if choice == "death":
            needed_tags.append("death")
            needed_tags.append("multi_death")
        elif choice == "injury":
            needed_tags.append("injury")
            needed_tags.append("multi_injury")
        if (double_event and choice != "reduce") or choice == "reduce":
            needed_tags.append("reduce_half")
            needed_tags.append("reduce_quarter")
            if double_event and choice == "reduce":
                injury = random.choice([True, False])
                if injury:
                    needed_tags.append("injury")
                else:
                    needed_tags.append("death")
                    needed_tags.append("multi_death")

        # remove events with the "much_prey" tag, if the condition is not fulfilled
        final_events = []
        for event in possible_events:
            if (not much_prey and "much_prey" not in event.tags) or much_prey:
                final_events.append(event)

        final_events = Freshkill_Events.get_filtered_possibilities(final_events, needed_tags, rabbit, other_rabbit)  

        # if there are no events available, return
        if len(final_events) <= 0:
            return

        # get the event and trigger certain things
        chosen_event = (random.choice(final_events))
        event_text = event_text_adjust(Rabbit, chosen_event.event_text, rabbit, other_rabbit)
        Freshkill_Events.handle_history_death(chosen_event,rabbit,other_rabbit)

        # if a food is stolen, remove the food
        reduce_amount = 0
        if "reduce_half" in chosen_event.tags:
            reduce_amount = int(freshkill_pile.total_amount / 2)
        elif "reduce_quarter" in chosen_event.tags:
            reduce_amount = int(freshkill_pile.total_amount / 4)
        elif "reduce_eighth" in chosen_event.tags:
            reduce_amount = int(freshkill_pile.total_amount / 8)
        freshkill_pile.remove_freshkill(reduce_amount, take_random=True)

        # add it to the event screens
        types = ["misc"]
        if chosen_event.injury:
            types.append("health")
        if "death" in chosen_event.tags:
            types.append("birth_death")

        if "m_c" not in chosen_event.event_text:
            game.cur_events_list.append(Single_Event(event_text, types, []))
        elif "other_rabbit" in chosen_event.tags and other_rabbit:
            game.cur_events_list.append(Single_Event(event_text, types, [rabbit.ID, other_rabbit.ID]))
        else:
            game.cur_events_list.append(Single_Event(event_text, types, [rabbit.ID]))

    # ---------------------------------------------------------------------------- #
    #                                helper function                               #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def get_filtered_possibilities(possible_events: list, needed_tags: list, rabbit: Rabbit, other_rabbit: Union[Rabbit, None]) -> list:
        """
        Returns a filtered list of possible events for a given list of tags.

            Parameters
            ----------
            possible_events : list
                a list of events to filter
            needed_tags : list
                a list of tags, which should be in the event
            rabbit : Rabbit
                the main rabbit of the provided possible event list  
            other_rabbit : Rabbit
                the other rabbit in the possible event list

            Returns
            -------
            final_events : list
                all events, which fulfill the needed tags
        """
        final_events = []
        for event in possible_events:
            if any(x in event.tags for x in needed_tags):
                if event.other_rabbit_trait and other_rabbit and \
                   other_rabbit.personality.trait in event.other_rabbit_trait:
                    final_events.append(event)
                    continue

                if event.rabbit_trait and rabbit.personality.trait in event.rabbit_trait:
                    final_events.append(event)
                    continue

                if event.other_rabbit_skill and other_rabbit and \
                   other_rabbit.skill in event.other_rabbit_skill:
                    final_events.append(event)
                    continue

                if event.rabbit_skill:
                    _flag = False
                    for _skill in event.rabbit_skill:
                        spl = _skill.split(",")
                        if len(spl) != 2:
                            continue
                        
                        if rabbit.skills.meets_skill_requirement(spl[0], spl[1]):
                            _flag = True
                    
                    if _flag:
                        final_events.append(event)
                        continue

                # if this event has no specifirabbition, but one of the needed tags, the event should be considered to be chosen
                if not event.other_rabbit_trait and not event.rabbit_trait and \
                    not event.other_rabbit_skill and not event.rabbit_skill:
                    final_events.append(event)
        return final_events

    @staticmethod
    def handle_history_death(event: Single_Event, rabbit: Rabbit, other_rabbit: Union[Rabbit, None]) -> None:
        """
        Handles death and history for a given event.

            Parameters
            ----------
            event : Single_Event
                the event which is be chosen
            rabbit : Rabbit
                the main rabbit of the provided possible event list  
            other_rabbit : Rabbit
                the other rabbit in the possible event list
        """

        if event.injury:
            scar_text = None
            history_normal = None
            history_chief_rabbit = None
            if event.history_text[0] is not None:
                scar_text = event_text_adjust(Rabbit, event.history_text[0], rabbit, other_rabbit)
            if event.history_text[1] is not None:
                history_normal = event_text_adjust(Rabbit, event.history_text[1], rabbit, other_rabbit)
            elif event.history_text[2] is not None:
                history_chief_rabbit = event_text_adjust(Rabbit, event.history_text[2], rabbit, other_rabbit)
            
            if rabbit.status == "chief rabbit":
                History.add_possible_history(rabbit, event.injury, death_text=history_chief_rabbit, scar_text=scar_text,
                                                  other_rabbit=other_rabbit)
            else:
                History.add_possible_history(rabbit, event.injury, death_text=history_normal, scar_text=scar_text,
                                                  other_rabbit=other_rabbit)


            rabbit.get_injured(event.injury, event_triggered=True)
            if "multi_injury" in event.tags and other_rabbit:
                History.add_possible_history(other_rabbit, event.injury, death_text=history_normal, 
                                                      scar_text=scar_text, other_rabbit=rabbit)

                other_rabbit.get_injured(event.injury, event_triggered=True)

        # if the length of the history text is 2, this means the event is a instant death event
        if "death" in event.tags or "multi_death" in event.tags:
            history_normal = None
            history_chief_rabbit = None
            if event.history_text[0] is not None:
                history_normal = event_text_adjust(Rabbit, event.history_text[0], rabbit, other_rabbit)
            if event.history_text[1] is not None:
                history_chief_rabbit = event_text_adjust(Rabbit, event.history_text[1], rabbit, other_rabbit)

                game.warren.chief_rabbit_lives -= 1
                History.add_death(rabbit, history_chief_rabbit, other_rabbit=other_rabbit)
            else:
                History.add_death(rabbit, history_normal, other_rabbit=other_rabbit)

            rabbit.die()
            if "multi_death" in event.tags and other_rabbit:
                History.add_death(other_rabbit, history_normal, other_rabbit=rabbit)
                other_rabbit.die()
            if "multi_death" in event.tags and not other_rabbit:
                print("WARNING: multi_death event in freshkill pile was triggered, but no other rabbit was given.")
