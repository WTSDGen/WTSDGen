from scripts.rabbit.names import names
from scripts.rabbit_relations.relationship import Relationship

import random

from scripts.rabbit.rabbits import Rabbit, INJURIES, BACKSTORIES
from scripts.events_module.generate_events import GenerateEvents
from scripts.utility import event_text_adjust, change_warren_relations, change_relationship_values, create_new_rabbit
from scripts.game_structure.game_essentials import game
from scripts.event_class import Single_Event
from scripts.rabbit.names import Name
from scripts.rabbit.history import History


# ---------------------------------------------------------------------------- #
#                               New Rabbit Event Class                              #
# ---------------------------------------------------------------------------- #

class NewRabbitEvents:
    """All events with a connection to new rabbits."""

    @staticmethod
    def handle_new_rabbits(rabbit: Rabbit, other_rabbit, war, enemy_warren, alive_kittens):
        """ 
        This function handles the new rabbits
        """
        if war:
            other_warren = enemy_warren
        else:
            other_warren = random.choice(game.warren.all_warrens)
        other_warren_name = f'{other_warren.name}'

        if other_warren_name == 'None':
            other_warren = game.warren.all_warrens[0]
            other_warren_name = f'{other_warren.name}'

        
        #Determine
        if NewRabbitEvents.has_outside_rabbit():
            if random.randint(1, 3) == 1:
                outside_rabbit = NewRabbitEvents.select_outside_rabbit()
                backstory = outside_rabbit.status
                outside_rabbit = NewRabbitEvents.update_rabbit_properties(outside_rabbit)
                event_text = f"A {backstory} named {outside_rabbit.name} waits on the border, asking to join the warren."
                name_change = random.choice([1, 2])
                if name_change == 1 or backstory == 'defector':
                    event_text = event_text + f" They decide to keep their name."
                elif name_change == 2 and backstory != 'defector':
                    outside_rabbit.name = Name(outside_rabbit.status, 
                                            colour=outside_rabbit.pelt.colour,
                                            eyes=outside_rabbit.pelt.eye_colour,
                                            pelt=outside_rabbit.pelt.name,
                                            tortiepattern=outside_rabbit.pelt.tortiepattern,
                                            biome=game.warren.biome)
                    
                    event_text = event_text + f" They decide to take a new name, {outside_rabbit.name}."
                outside_rabbit.thought = "Is sniffing around the burrow"
                involved_rabbits = [outside_rabbit.ID]
                game.cur_events_list.append(Single_Event(event_text, ["misc"], involved_rabbits))

                # add them 
                for the_rabbit in outside_rabbit.all_rabbits.values():
                    if the_rabbit.dead or the_rabbit.outside or the_rabbit.ID == outside_rabbit.ID:
                        continue
                    the_rabbit.create_one_relationship(outside_rabbit)
                    outside_rabbit.create_one_relationship(the_rabbit)

                # takes rabbit out of the outside rabbit list
                game.warren.add_to_warren(outside_rabbit)
                history = History()
                history.add_beginning(outside_rabbit)

                return [outside_rabbit]

        
        # ---------------------------------------------------------------------------- #
        #                                rabbit creation                                  #
        # ---------------------------------------------------------------------------- #
        possible_events = GenerateEvents.possible_short_events(rabbit.status, rabbit.age, "new_rabbit")
        final_events = GenerateEvents.filter_possible_short_events(possible_events, rabbit, other_rabbit, war,
                                                                        enemy_warren,
                                                                        other_warren, alive_kittens)
        if not final_events:
            print('ERROR: no new rabbit month events available')
            return
        else:
            new_rabbit_event = (random.choice(final_events))

        involved_rabbits = []
        created_rabbits = []
        if "m_c" in new_rabbit_event.tags:
            involved_rabbits = [rabbit.ID]

        if "other_rabbit" in new_rabbit_event.tags:
            involved_rabbits = [other_rabbit.ID]
        else:
            other_rabbit = None

        status = None
        if "new_rabbit" in new_rabbit_event.tags:
            status = "rabbit"
        elif "new_app" in new_rabbit_event.tags:
            status = "rusasi"
        elif "new_med_app" in new_rabbit_event.tags:
            status = "healer rusasi"
        elif "new_med" in new_rabbit_event.tags:
            status = "healer"


        created_rabbits = create_new_rabbit(Rabbit,
                                      Relationship,
                                      new_rabbit_event.new_name,
                                      new_rabbit_event.hlessi,
                                      new_rabbit_event.pet,
                                      new_rabbit_event.kitten,
                                      new_rabbit_event.litter,
                                      new_rabbit_event.other_warren,
                                      new_rabbit_event.backstory,
                                      status
                                      )
        
        blood_parent = None
        if new_rabbit_event.litter:
            # If we have a litter joining, assign them a blood parent for
            # relation-tracking purposes
            thought = "Is happy their kittens are safe"
            blood_parent = create_new_rabbit(Rabbit, Relationship,
                                          status=random.choice(["hlessi", "pet"]),
                                          alive=False,
                                          thought=thought,
                                          age=random.randint(15,120),
                                          outside=True)[0]
            
            
        for new_rabbit in created_rabbits:
            
            involved_rabbits.append(new_rabbit.ID)
            
            # Set the blood parent, if one was created.
            # Also set adoptive parents if needed. 
            new_rabbit.parent1 = blood_parent.ID if blood_parent else None
            if "adoption" in new_rabbit_event.tags and rabbit.ID not in new_rabbit.adoptive_parents:
                new_rabbit.adoptive_parents.append(rabbit.ID)
                if len(rabbit.mate) > 0:
                    for mate_id in rabbit.mate:
                        if mate_id not in new_rabbit.adoptive_parents:
                            new_rabbit.adoptive_parents.extend(rabbit.mate)
            
            # All parents have been added now, we now create the inheritance. 
            new_rabbit.create_inheritance_new_rabbit()

            if "m_c" in new_rabbit_event.tags:
                # print('month event new rabbit rel gain')
                rabbit.create_one_relationship(new_rabbit)
                new_rabbit.create_one_relationship(rabbit)
                
                new_to_warren_rabbit = game.config["new_rabbit"]["rel_buff"]["new_to_warren_rabbit"]
                warren_rabbit_to_new = game.config["new_rabbit"]["rel_buff"]["warren_rabbit_to_new"]
                change_relationship_values(
                    rabbits_to=[rabbit.ID],
                    rabbits_from=[new_rabbit],
                    romantic_love=new_to_warren_rabbit["romantic"],
                    platonic_like=new_to_warren_rabbit["platonic"],
                    dislike=new_to_warren_rabbit["dislike"],
                    admiration=new_to_warren_rabbit["admiration"],
                    comfortable=new_to_warren_rabbit["comfortable"],
                    jealousy=new_to_warren_rabbit["jealousy"],
                    trust=new_to_warren_rabbit["trust"]
                )
                change_relationship_values(
                    rabbits_to=[new_rabbit.ID],
                    rabbits_from=[rabbit],
                    romantic_love=warren_rabbit_to_new["romantic"],
                    platonic_like=warren_rabbit_to_new["platonic"],
                    dislike=warren_rabbit_to_new["dislike"],
                    admiration=warren_rabbit_to_new["admiration"],
                    comfortable=warren_rabbit_to_new["comfortable"],
                    jealousy=warren_rabbit_to_new["jealousy"],
                    trust=warren_rabbit_to_new["trust"]
                )

        if "adoption" in new_rabbit_event.tags:
            if new_rabbit_event.litter:
                for new_rabbit in created_rabbits:
                    # giving relationships for siblings
                    siblings = new_rabbit.get_siblings()
                    for sibling in siblings:
                        sibling = Rabbit.fetch_rabbit(sibling)
                        
                        sibling.create_one_relationship(new_rabbit)
                        new_rabbit.create_one_relationship(sibling)
                        
                        rabbit1_to_rabbit2 = game.config["new_rabbit"]["sib_buff"]["rabbit1_to_rabbit2"]
                        rabbit2_to_rabbit1 = game.config["new_rabbit"]["sib_buff"]["rabbit2_to_rabbit1"]
                        change_relationship_values(
                            rabbits_to=[sibling.ID],
                            rabbits_from=[new_rabbit],
                            romantic_love=rabbit1_to_rabbit2["romantic"],
                            platonic_like=rabbit1_to_rabbit2["platonic"],
                            dislike=rabbit1_to_rabbit2["dislike"],
                            admiration=rabbit1_to_rabbit2["admiration"],
                            comfortable=rabbit1_to_rabbit2["comfortable"],
                            jealousy=rabbit1_to_rabbit2["jealousy"],
                            trust=rabbit1_to_rabbit2["trust"]
                        )
                        change_relationship_values(
                            rabbits_to=[new_rabbit.ID],
                            rabbits_from=[sibling],
                            romantic_love=rabbit2_to_rabbit1["romantic"],
                            platonic_like=rabbit2_to_rabbit1["platonic"],
                            dislike=rabbit2_to_rabbit1["dislike"],
                            admiration=rabbit2_to_rabbit1["admiration"],
                            comfortable=rabbit2_to_rabbit1["comfortable"],
                            jealousy=rabbit2_to_rabbit1["jealousy"],
                            trust=rabbit2_to_rabbit1["trust"]
                        )

        # give injuries to other rabbit if tagged as such
        if "injured" in new_rabbit_event.tags and game.warren.game_mode != "classic":
            major_injuries = []
            if "major_injury" in new_rabbit_event.tags:
                for injury in INJURIES:
                    if INJURIES[injury]["severity"] == "major" and injury not in ["pregnant", "recovering from birth"]:
                        major_injuries.append(injury)
            for new_rabbit in created_rabbits:
                for tag in new_rabbit_event.tags:
                    if tag in INJURIES:
                        new_rabbit.get_injured(tag)
                    elif tag == "major_injury":
                        injury = random.choice(major_injuries)
                        new_rabbit.get_injured(injury)

        if "rel_down" in new_rabbit_event.tags:
            difference = -1
            change_warren_relations(other_warren, difference=difference)

        elif "rel_up" in new_rabbit_event.tags:
            difference = 1
            change_warren_relations(other_warren, difference=difference)

        event_text = event_text_adjust(Rabbit, new_rabbit_event.event_text, rabbit, other_rabbit, other_warren_name,
                                       new_rabbit=created_rabbits[0])

        types = ["misc"]
        if "other_warren" in new_rabbit_event.tags:
            types.append("other_warrens")
        game.cur_events_list.append(Single_Event(event_text, types, involved_rabbits))

        return created_rabbits

    @staticmethod
    def has_outside_rabbit():
        outside_rabbits = [i for i in Rabbit.all_rabbits.values() if i.status in ["pet", "hlessi", "rogue", "defector"] and not i.dead and i.outside]
        return any(outside_rabbits)

    @staticmethod
    def select_outside_rabbit():
        outside_rabbits = [i for i in Rabbit.all_rabbits.values() if i.status in ["pet", "hlessi", "rogue", "defector"] and not i.dead and i.outside]
        if outside_rabbits:
            return random.choice(outside_rabbits)
        else:
            return None
        

    @staticmethod
    def update_rabbit_properties(rabbit):
        if rabbit.backstory in BACKSTORIES["backstory_categories"]['healer_backstories']:
                rabbit.status = 'healer'
        else:
            rabbit.status = "rabbit"
        rabbit.outside = False
        return rabbit
