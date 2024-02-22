import os
import ujson
from copy import deepcopy
from random import choice

from scripts.utility import change_relationship_values, event_text_adjust
from scripts.game_structure.game_essentials import game
from scripts.event_class import Single_Event
from scripts.rabbit.rabbits import Rabbit

class Welcoming_Events():
    """All events which are related to welcome a new rabbit in the warren."""
    
    @staticmethod    
    def welcome_rabbit(warren_rabbit: Rabbit, new_rabbit: Rabbit) -> None:
        """Checks and triggers the welcome event from the warren rabbit to the new rabbit.

            Parameters
            ----------
            warren_rabbit : Rabbit
                the warren rabbit which welcome the new rabbit
            new_rabbit : Rabbit
                new rabbit which will be welcomed

            Returns
            -------
        """
        if new_rabbit.ID == warren_rabbit.ID:
            return

        # setup the status as "key" to use it
        status = warren_rabbit.status
        if status == "healer" or status == "healer rusasi":
            status = "medicine"

        if status == "owsla rusasi":
            status = "owsla"

        # collect all events
        possible_events = deepcopy(GENERAL_WELCOMING)
        if status not in WELCOMING_MASTER_DICT:
            print(f"ERROR: there is no welcoming json for the status {status}")
        else:
            possible_events.extend(WELCOMING_MASTER_DICT[status])
        filtered_events = Welcoming_Events.filter_welcome_interactions(possible_events, new_rabbit)

        # choose which interaction will be displayed
        random_interaction = choice(filtered_events)
        interaction_str = choice(random_interaction.interactions)

        # prepare string for display
        interaction_str = event_text_adjust(Rabbit, interaction_str, warren_rabbit, new_rabbit)

        # influence the relationship
        new_to_warren_rabbit = game.config["new_rabbit"]["rel_buff"]["new_to_warren_rabbit"]
        warren_rabbit_to_new = game.config["new_rabbit"]["rel_buff"]["warren_rabbit_to_new"]
        change_relationship_values(
            rabbits_to=        [warren_rabbit.ID], 
            rabbits_from=      [new_rabbit],
            romantic_love=  new_to_warren_rabbit["romantic"],
            platonic_like=  new_to_warren_rabbit["platonic"],
            dislike=        new_to_warren_rabbit["dislike"],
            admiration=     new_to_warren_rabbit["admiration"],
            comfortable=    new_to_warren_rabbit["comfortable"],
            jealousy=       new_to_warren_rabbit["jealousy"],
            trust=          new_to_warren_rabbit["trust"]
        )
        change_relationship_values(
            rabbits_to=        [new_rabbit.ID], 
            rabbits_from=      [warren_rabbit],
            romantic_love=  warren_rabbit_to_new["romantic"],
            platonic_like=  warren_rabbit_to_new["platonic"],
            dislike=        warren_rabbit_to_new["dislike"],
            admiration=     warren_rabbit_to_new["admiration"],
            comfortable=    warren_rabbit_to_new["comfortable"],
            jealousy=       warren_rabbit_to_new["jealousy"],
            trust=          warren_rabbit_to_new["trust"]
        )

        # add it to the event list
        game.cur_events_list.append(Single_Event(
            interaction_str, ["relation", "interaction"], [new_rabbit.ID, warren_rabbit.ID]))

        # add to relationship logs
        if new_rabbit.ID in warren_rabbit.relationships:
            if warren_rabbit.age == 1:
                warren_rabbit.relationships[new_rabbit.ID].log.append(interaction_str + f" - {warren_rabbit.name} was {warren_rabbit.months} months old")
            else:
                warren_rabbit.relationships[new_rabbit.ID].log.append(interaction_str + f" - {warren_rabbit.name} was {warren_rabbit.months} months old")

            new_rabbit.relationships[warren_rabbit.ID].link_relationship()

        if warren_rabbit.ID in new_rabbit.relationships:
            if new_rabbit.age == 1:
                new_rabbit.relationships[warren_rabbit.ID].log.append(interaction_str + f" - {new_rabbit.name} was {new_rabbit.months} month old")
            else:
                new_rabbit.relationships[warren_rabbit.ID].log.append(interaction_str + f" - {new_rabbit.name} was {new_rabbit.months} months old")

    @staticmethod
    def filter_welcome_interactions(welcome_interactions : list, new_rabbit: Rabbit) -> list:
        """Filter welcome events based on states.
    
            Parameters
            ----------
            welcome_interactions : list
                a list of welcome interaction
            new_rabbit : Rabbit
                new rabbit which will be welcomed

            Returns
            -------
            filtered list of welcome interactions
        """
        filtered = []
        for interaction in welcome_interactions:
            if interaction.background and new_rabbit.backstory not in interaction.background:
                continue

            if interaction.new_rabbit_months:
                threshold_month = interaction.new_rabbit_months.split('_')
                threshold_month = int(threshold_month[len(threshold_month) - 1])

                if "over" in interaction.new_rabbit_months and new_rabbit.months < threshold_month:
                    continue
                if "under" in interaction.new_rabbit_months and new_rabbit.months > threshold_month:
                    continue
                if "over" not in interaction.new_rabbit_months and "under" not in interaction.new_rabbit_months:
                    print(f"ERROR: The new rabbit welcoming event {interaction.id} has a not valid month restriction for the new rabbit.")
                    continue

            filtered.append(interaction)
        return filtered


class Welcome_Interaction():

    def __init__(self,
                 id,
                 interactions=None,
                 background=None,
                 new_rabbit_months=None
                 ):
        self.id = id
        self.background = background
        self.new_rabbit_months = new_rabbit_months
        
        if interactions:
            self.interactions = interactions
        else:
            self.interactions = ["m_c is welcoming r_r."]

# ---------------------------------------------------------------------------- #
#                   build master dictionary for interactions                   #
# ---------------------------------------------------------------------------- #

def create_welcome_interaction(inter_list) -> list:
    created_list = []

    for inter in inter_list:
        created_list.append(Welcome_Interaction(
            id=inter["id"],
            interactions=inter["interactions"] if "interactions" in inter else None,
            background=inter["background"] if "background" in inter else None,
            new_rabbit_months=inter["new_rabbit_months"] if "new_rabbit_months" in inter else None
            )
        )

    return created_list


base_path = os.path.join(
    "resources",
    "dicts",
    "relationship_events",
    "welcoming_events"
)

WELCOMING_MASTER_DICT = {}
for file in os.listdir(base_path):
    if "general.json" == file:
        continue
    status = file.split(".")[0]
    with open(os.path.join(base_path, file), 'r') as read_file:
        welcome_list = ujson.load(read_file)
        WELCOMING_MASTER_DICT[status] = create_welcome_interaction(welcome_list)

GENERAL_WELCOMING = []
with open(os.path.join(base_path, "general.json"), 'r') as read_file:
    loaded_list = ujson.loads(read_file.read())
    GENERAL_WELCOMING = create_welcome_interaction(loaded_list)