#!/usr/bin/env python3
# -*- coding: ascii -*-
import random

import ujson
from scripts.game_structure.game_essentials import game

resource_directory = "resources/dicts/events/"


# ---------------------------------------------------------------------------- #
#                Tagging Guidelines can be found at the bottom                 #
# ---------------------------------------------------------------------------- #

class GenerateEvents:
    loaded_events = {}
    
    INJURY_DISTRIBUTION = None
    with open(f"resources/dicts/conditions/event_injuries_distribution.json", 'r') as read_file:
        INJURY_DISTRIBUTION = ujson.loads(read_file.read())

    INJURIES = None
    with open(f"resources/dicts/conditions/injuries.json", 'r') as read_file:
        INJURIES = ujson.loads(read_file.read())

    @staticmethod
    def get_short_event_dicts(file_path):
        try:
            with open(
                    file_path,
                    "r",
            ) as read_file:
                events = ujson.loads(read_file.read())
        except:
            print(f"ERROR: Unable to load {file_path}.")
            return None

        return events

    @staticmethod
    def get_ongoing_event_dicts(file_path):
        events = None
        try:
            with open(
                    file_path,
                    "r",
            ) as read_file:
                events = ujson.loads(read_file.read())
        except:
            print(f"ERROR: Unable to load events from biome {file_path}.")

        return events

    @staticmethod
    def get_death_reaction_dicts(family_relation, rel_value):
        try:
            file_path = f"{resource_directory}/death/death_reactions/{family_relation}/{family_relation}_{rel_value}.json"
            with open(
                    file_path,
                    "r",
            ) as read_file:
                events = ujson.loads(read_file.read())
        except:
            events = None
            print(f"ERROR: Unable to load death reaction events for {family_relation}_{rel_value}.")
        return events

    @staticmethod
    def clear_loaded_events():
        GenerateEvents.loaded_events = {}

    @staticmethod
    def generate_short_events(event_triggered, rabbit_type, biome):

        if rabbit_type and not biome:
            file_path = f"{resource_directory}{event_triggered}/{rabbit_type}.json"
        elif not rabbit_type and biome:
            file_path = f"{resource_directory}{event_triggered}/{biome}.json"
        else:
            file_path = f"{resource_directory}{event_triggered}/{biome}/{rabbit_type}.json"

        if file_path in GenerateEvents.loaded_events:
            return GenerateEvents.loaded_events[file_path]
        else:
            events_dict = GenerateEvents.get_short_event_dicts(file_path)

            event_list = []
            if not events_dict:
                return event_list
            for event in events_dict:
                event_text = event["event_text"] if "event_text" in event else None
                if not event_text:
                    event_text = event["death_text"] if "death_text" in event else None

                if not event_text:
                    print(f"WARNING: some events resources which are used in generate_events. Have no 'event_text'.")
                event = ShortEvent(
                    burrow=event["burrow"] if "burrow" in event else "any",
                    tags=event["tags"],
                    event_text=event_text,
                    history_text=event["history_text"] if "history_text" in event else {},
                    rabbit_trait= event["rabbit_trait"] if "rabbit_trait" in event else [],
                    rabbit_skill=event["rabbit_skill"] if "rabbit_skill" in event else [],
                    other_rabbit_trait=event["other_rabbit_trait"] if "other_rabbit_trait" in event else [],
                    other_rabbit_skill=event["other_rabbit_skill"] if "other_rabbit_skill" in event else [],
                    rabbit_negate_trait=event["rabbit_negate_trait"] if "rabbit_negate_trait" in event else [],
                    rabbit_negate_skill=event["rabbit_negate_skill"] if "rabbit_negate_skill" in event else [],
                    other_rabbit_negate_trait=event[
                        "other_rabbit_negate_trait"] if "other_rabbit_negate_trait" in event else [],
                    other_rabbit_negate_skill=event[
                        "other_rabbit_negate_skill"] if "other_rabbit_negate_skill" in event else [],
                    backstory_constraint=event["backstory_constraint"] if "backstory_constraint" in event else [],

                    # injury event only
                    injury=event["injury"] if "injury" in event else None,

                    # new rabbit event only
                    loner=event["loner"] if "loner" in event else False,
                    pet=event["pet"] if "pet" in event else False,
                    other_warren=event["other_warren"] if "other_warren" in event else False,
                    kitten=event["kitten"] if "kitten" in event else False,
                    new_name=event["new_name"] if "new_name" in event else False,
                    litter=event["litter"] if "litter" in event else False,
                    backstory=event["backstory"] if "backstory" in event else None,
                    reputation=event["reputation"] if "reputation" in event else None,

                    # for misc events only
                    accessories=event["accessories"] if "accessories" in event else None
                )
                event_list.append(event)

            # Add to loaded events.
            GenerateEvents.loaded_events[file_path] = event_list
            return event_list

    @staticmethod
    def generate_ongoing_events(event_type, biome, specific_event=None):

        file_path = f"resources/dicts/events/{event_type}/{biome}.json"

        if file_path in GenerateEvents.loaded_events:
            return GenerateEvents.loaded_events[file_path]
        else:
            events_dict = GenerateEvents.get_ongoing_event_dicts(file_path)

            if not specific_event:
                event_list = []
                for event in events_dict:
                    event = OngoingEvent(
                        event=event["event"],
                        burrow=event["burrow"],
                        season=event["season"],
                        tags=event["tags"],
                        priority=event["priority"],
                        duration=event["duration"],
                        current_duration=0,
                        rarity=event["rarity"],
                        trigger_events=event["trigger_events"],
                        progress_events=event["progress_events"],
                        conclusion_events=event["conclusion_events"],
                        secondary_disasters=event["secondary_disasters"],
                        collateral_damage=event["collateral_damage"]
                    )
                    event_list.append(event)
                return event_list
            else:
                event = None
                for event in events_dict:
                    if event["event"] != specific_event:
                        #print(event["event"], 'is not', specific_event)
                        continue
                    #print(event["event"], "is", specific_event)
                    event = OngoingEvent(
                        event=event["event"],
                        burrow=event["burrow"],
                        season=event["season"],
                        tags=event["tags"],
                        priority=event["priority"],
                        duration=event["duration"],
                        current_duration=0,
                        progress_events=event["progress_events"],
                        conclusion_events=event["conclusion_events"],
                        collateral_damage=event["collateral_damage"]
                    )
                    break
                return event

    @staticmethod
    def possible_short_events(rabbit_type=None, age=None, event_type=None):
        event_list = []
        biome = None

        excluded_from_general = []
        rabbit_adjacent_ranks = []

        if event_type == 'death':
            rabbit_adjacent_ranks.extend(["captain", "rusasi"])
            excluded_from_general.extend(["kitten", "threarah", "newborn"])
        elif event_type in ['injury', 'nutrition', 'misc_events', 'new_rabbit']:
            rabbit_adjacent_ranks.extend(["captain", "rusasi", "threarah"])
            excluded_from_general.extend(["kitten", "threarah", "newborn"])

        if rabbit_type in ["healer", "healer rusasi"]:
            rabbit_type = "medicine"
        elif rabbit_type in ["owsla", "owsla rusasi"]:
            rabbit_type = "owsla"

        # skip the rest of the loading if there is an unrecognised rabbit type
        if rabbit_type not in game.warren.RABBIT_TYPES:
            print(
                f"WARNING: unrecognised rabbit status {rabbit_type} in generate_events. Have you added it to RABBIT_TYPES in "
                f"warren.py?")

        elif game.warren.biome not in game.warren.BIOME_TYPES:
            print(
                f"WARNING: unrecognised biome {game.warren.biome} in generate_events. Have you added it to BIOME_TYPES "
                f"in warren.py?")

        # NUTRITION this needs biome to be None so is handled separately
        elif event_type == 'nutrition':
            event_list.extend(
                GenerateEvents.generate_short_events(event_type, rabbit_type, biome))

            if rabbit_type in rabbit_adjacent_ranks:
                event_list.extend(
                    GenerateEvents.generate_short_events(event_type, "rabbit", biome))

            if rabbit_type not in excluded_from_general:
                event_list.extend(
                    GenerateEvents.generate_short_events(event_type, "general", biome))

        else:
            biome = game.warren.biome.lower()

            # RANK SPECIFIC
            # biome specific rank specific events
            event_list.extend(
                GenerateEvents.generate_short_events(event_type, rabbit_type, biome))

            # any biome rank specific events
            event_list.extend(
                GenerateEvents.generate_short_events(event_type, rabbit_type, "general"))

            # WARRIOR-LIKE
            if rabbit_type in rabbit_adjacent_ranks:
                # biome specific rabbit events for "rabbit-like" ranks
                event_list.extend(
                    GenerateEvents.generate_short_events(event_type, "rabbit", biome))

                # any biome rabbit events for "rabbit-like" ranks
                event_list.extend(
                    GenerateEvents.generate_short_events(event_type, "rabbit", "general"))

            # GENERAL
            if rabbit_type not in excluded_from_general:
                # biome specific general rank events
                event_list.extend(
                    GenerateEvents.generate_short_events(event_type, "general", biome))

                # any biome general rank events
                event_list.extend(
                    GenerateEvents.generate_short_events(event_type, "general", "general"))

        return event_list

    @staticmethod
    def filter_possible_short_events(possible_events, rabbit, other_rabbit, war, enemy_warren, other_warren, alive_kits, murder=False, murder_reveal=False):
        final_events = []

        minor = []
        major = []
        severe = []
        
        # Chance to bypass the skill or trait requirements. 
        trait_skill_bypass = 15

        if war and random.randint(1, 10) != 1 and other_warren == enemy_warren:
            war_event = True
        else:
            war_event = False

        for event in possible_events:
            
            # Normally, there is a chance to bypass skill and trait requirments. 
            # the "skill_trait_required" tags turns this off. Lets grab this tag once, for simplicity. 
            prevent_bypass = "skill_trait_required" in event.tags
            
            if war_event and ("war" not in event.tags and "hostile" not in event.tags):
                continue
            if not war and "war" in event.tags:
                continue

            # some events are classic only
            if game.warren.game_mode in ["expanded", "cruel season"] and "classic" in event.tags:
                continue

            if "other_rabbit" in event.tags and not other_rabbit:
                continue

            if event.backstory_constraint and rabbit.backstory not in event.backstory_constraint:
                continue

            if murder and "murder" not in event.tags:
                continue
            if not murder and "murder" in event.tags:
                continue

            if murder_reveal and "murder_reveal" not in event.tags:
                continue
            if not murder_reveal and "murder_reveal" in event.tags:
                continue

            # make complete threarah death less likely until the threarah is over 150 months
            if "all_lives" in event.tags:
                if int(rabbit.months) < 150 and int(random.random() * 5):
                    continue

            # make sure that 'some lives' events don't show up if the threarah doesn't have multiple lives to spare
            if "some_lives" in event.tags and game.warren.threarah_lives <= 3:
                continue

            if "low_lives" in event.tags:
                if game.warren.threarah_lives > 3:
                    continue

            # check season
            if game.warren.current_season not in event.tags:
                continue

            if event.reputation:
                reputation = game.warren.reputation
                # hostile
                if 1 <= reputation <= 30 and "hostile" not in event.reputation:
                    continue
                # neutral
                elif 31 <= reputation <= 70 and "neutral" not in event.reputation:
                    continue
                # welcoming
                elif 71 <= reputation <= 100 and "welcoming" not in event.reputation:
                    continue

            # check that injury is possible
            if event.injury in GenerateEvents.INJURIES:

                if event.injury == 'mangled tail' and ('NOTAIL' in rabbit.pelt.scars or 'HALFTAIL' in rabbit.pelt.scars):
                    continue

                if event.injury == 'torn ear' and 'NOEAR' in rabbit.pelt.scars:
                    continue

            # check meddie tags
            if "medicine_rabbit" in event.tags and rabbit.status != "healer":
                continue
            elif "medicine_rabbit_app" in event.tags and rabbit.status != "healer rusasi":
                continue

            # other Warren related checks
            if "other_warren" in event.tags:
                if "war" in event.tags and not war:
                    continue
                if "ally" in event.tags and int(other_warren.relations) < 17:
                    continue
                elif "neutral" in event.tags and (int(other_warren.relations) <= 7 or int(other_warren.relations) >= 17):
                    continue
                elif "hostile" in event.tags and int(other_warren.relations) > 7:
                    continue

            # check if Warren has kits
            if "warren_kits" in event.tags and not alive_kits:
                continue
            
            if "adoption" in event.tags:
                # If the rabbit or any of their mates have "no kits" toggled, forgo the adoption event.
                if rabbit.no_kits:
                    continue
                if any(rabbit.fetch_rabbit(i).no_kits for i in rabbit.mate):
                    continue
            
            # check for old age
            if "old_age" in event.tags and rabbit.months < game.config["death_related"]["old_age_death_start"]:
                continue
            # remove some non-old age events to encourage elders to die of old age more often
            if "old_age" not in event.tags and rabbit.months > game.config["death_related"]["old_age_death_start"] \
                    and int(random.random() * 3):
                continue

            # check other_rabbit status and other identifiers
            if other_rabbit:
                if "other_rabbit_threarah" in event.tags and other_rabbit.status != "threarah":
                    continue
                if "other_rabbit_dep" in event.tags and other_rabbit.status != "captain":
                    continue
                if "other_rabbit_med" in event.tags and other_rabbit.status != "healer":
                    continue
                if "other_rabbit_med_app" in event.tags and other_rabbit.status != "healer rusasi":
                    continue
                if "other_rabbit_rabbit" in event.tags and other_rabbit.status != "rabbit":
                    continue
                if "other_rabbit_app" in event.tags and other_rabbit.status != "apprentice":
                    continue
                if "other_rabbit_elder" in event.tags and other_rabbit.status != "elder":
                    continue
                if "other_rabbit_adult" in event.tags and other_rabbit.age in ["senior", "kitten", "newborn"]:
                    continue
                if "other_rabbit_kit" in event.tags and other_rabbit.status not in ['newborn', 'kitten']:
                    continue

                if "other_rabbit_mate" in event.tags and other_rabbit.ID not in rabbit.mate:
                    continue
                if "other_rabbit_child" in event.tags and other_rabbit.ID not in rabbit.get_children():
                    continue
                if "other_rabbit_parent" in event.tags and other_rabbit.ID not in rabbit.get_parents():
                    continue

                if "other_rabbit_own_app" in event.tags and other_rabbit.ID not in rabbit.apprentice:
                    continue
                if "other_rabbit_rusasirah" in event.tags and other_rabbit.ID != rabbit.rusasirah:
                    continue
                
                # check other rabbit trait and skill
                has_trait = False
                if event.other_rabbit_trait:
                    if other_rabbit.personality.trait in event.other_rabbit_trait:
                        has_trait = True
                
                has_skill = False
                if event.other_rabbit_skill:
                    for _skill in event.other_rabbit_skill:
                        split = _skill.split(",")
                        
                        if len(split) < 2:
                            print("Rabbit skill incorrectly formatted", _skill)
                            continue
                        
                        if other_rabbit.skills.meets_skill_requirement(split[0], int(split[1])):
                            has_skill = True
                            break
                    
                # There is a small chance to bypass the skill or trait requirments.  
                if event.other_rabbit_trait and event.other_rabbit_skill:
                    if not (has_trait or has_skill) and (prevent_bypass or int(random.random() * trait_skill_bypass)):
                        continue
                elif event.other_rabbit_trait:
                    if not has_trait and (prevent_bypass or int(random.random() * trait_skill_bypass)):
                        continue
                elif event.other_rabbit_skill:
                    if not has_skill and (prevent_bypass or int(random.random() * trait_skill_bypass)):
                        continue
                
                
                # check rabbit negate trait and skill
                has_trait = False
                if event.other_rabbit_negate_trait:
                    if other_rabbit.personality.trait in event.other_rabbit_negate_trait:
                        has_trait = True
                
                has_skill = False
                if event.other_rabbit_negate_trait:
                    for _skill in event.other_rabbit_negate_trait:
                        split = _skill.split(",")
                        
                        if len(split) < 2:
                            print("Rabbit skill incorrectly formatted", _skill)
                            continue
                        
                        if other_rabbit.skills.meets_skill_requirement(split[0], int(split[1])):
                            has_skill = True
                            break
                    
                # There is a small chance to bypass the skill or trait requirments.  
                if (has_trait or has_skill) and int(random.random() * trait_skill_bypass):
                    continue

            else:
                if "other_rabbit" in event.tags or "multi_death" in event.tags:
                    continue

            # check for mate if the event requires one
            if "mate" in event.tags and len(rabbit.mate) < 1:
                continue


            # check rabbit trait and skill
            has_trait = False
            if event.rabbit_trait:
                if rabbit.personality.trait in event.rabbit_trait:
                    has_trait = True
            else:
                has_trait = None
            
            has_skill = False
            if event.rabbit_skill:
                for _skill in event.rabbit_skill:
                    split = _skill.split(",")
                    
                    if len(split) < 2:
                        print("Rabbit skill incorrectly formatted", _skill)
                        continue
                    
                    if rabbit.skills.meets_skill_requirement(split[0], int(split[1])):
                        has_skill = True
                        break
            
            # There is a small chance to bypass the skill or trait requirments.  
            if event.rabbit_trait and event.rabbit_skill:
                if not (has_trait or has_skill) and (prevent_bypass or int(random.random() * trait_skill_bypass)):
                    continue
            elif event.rabbit_trait:
                if not has_trait and (prevent_bypass or int(random.random() * trait_skill_bypass)):
                    continue
            elif event.rabbit_skill:
                if not has_skill and (prevent_bypass or int(random.random() * trait_skill_bypass)):
                    continue
            
            
            # check rabbit negate trait and skill
            has_trait = False
            if event.rabbit_negate_trait:
                if rabbit.personality.trait in event.rabbit_negate_trait:
                    has_trait = True
            
            has_skill = False
            if event.rabbit_negate_skill:
                for _skill in event.rabbit_negate_skill:
                    split = _skill.split(",")
                    
                    if len(split) < 2:
                        print("Rabbit skill incorrectly formatted", _skill)
                        continue
                    
                    if rabbit.skills.meets_skill_requirement(split[0], int(split[1])):
                        has_skill = True
                        break
                
            # There is a small chance to bypass the skill or trait requirments.  
            if (has_trait or has_skill) and int(random.random() * trait_skill_bypass):
                continue

            # determine injury severity chance
            if event.injury:
                injury = GenerateEvents.INJURIES[event.injury]
                severity = injury['severity']

                if severity == 'minor':
                    minor.append(event)
                elif severity == 'major':
                    major.append(event)
                else:
                    severe.append(event)

            else:
                final_events.append(event)

        # determine which injury severity list will be used
        if minor or major or severe:
            if rabbit.status in GenerateEvents.INJURY_DISTRIBUTION:
                minor_chance = GenerateEvents.INJURY_DISTRIBUTION[rabbit.status]['minor']
                major_chance = GenerateEvents.INJURY_DISTRIBUTION[rabbit.status]['major']
                severe_chance = GenerateEvents.INJURY_DISTRIBUTION[rabbit.status]['severe']
                severity_chosen = random.choices(["minor", "major", "severe"], [minor_chance, major_chance, severe_chance], k=1)
                if severity_chosen[0] == 'minor':
                    final_events = minor
                elif severity_chosen[0] == 'major':
                    final_events = major
                else:
                    final_events = severe

        return final_events

    @staticmethod
    def possible_ongoing_events(event_type=None, specific_event=None):
        event_list = []

        if game.warren.biome not in game.warren.BIOME_TYPES:
            print(
                f"WARNING: unrecognised biome {game.warren.biome} in generate_events. Have you added it to BIOME_TYPES in warren.py?")

        else:
            biome = game.warren.biome.lower()
            if not specific_event:
                event_list.extend(
                    GenerateEvents.generate_ongoing_events(event_type, biome)
                )
                """event_list.extend(
                    GenerateEvents.generate_ongoing_events(event_type, "general", specific_event)
                )"""
                return event_list
            else:
                #print(specific_event)
                event = (
                    GenerateEvents.generate_ongoing_events(event_type, biome, specific_event)
                )
                return event

    @staticmethod
    def possible_death_reactions(family_relation, rel_value, trait, body_status):
        possible_events = []
        # grab general events first, since they'll always exist
        events = GenerateEvents.get_death_reaction_dicts("general", rel_value)
        possible_events.extend(events["general"][body_status])
        if trait in events:
            possible_events.extend(events[trait][body_status])

        # grab family events if they're needed. Family events should not be romantic. 
        if family_relation != 'general' and rel_value != "romantic":
            events = GenerateEvents.get_death_reaction_dicts(family_relation, rel_value)
            possible_events.extend(events["general"][body_status])
            if trait in events:
                possible_events.extend(events[trait][body_status])

        # print(possible_events)

        return possible_events


class ShortEvent:
    def __init__(
            self,
            burrow="any",
            tags=None,
            event_text="",
            history_text=None,
            rabbit_trait=None,
            rabbit_skill=None,
            other_rabbit_trait=None,
            other_rabbit_skill=None,
            rabbit_negate_trait=None,
            rabbit_negate_skill=None,
            other_rabbit_negate_trait=None,
            other_rabbit_negate_skill=None,
            backstory_constraint=None,
            injury=None,
            loner=False,
            new_name=False,
            pet=False,
            kitten=False,
            litter=False,
            backstory=None,
            other_warren=None,
            reputation=None,
            accessories=None
    ):
        self.burrow = burrow
        self.tags = tags
        self.event_text = event_text
        self.history_text = history_text
        self.rabbit_trait = rabbit_trait if rabbit_trait else []
        self.rabbit_skill = rabbit_skill if rabbit_skill else []
        self.other_rabbit_trait = other_rabbit_trait if other_rabbit_trait else []
        self.other_rabbit_skill = other_rabbit_skill if other_rabbit_skill else []
        self.rabbit_negate_trait = rabbit_negate_trait if rabbit_negate_trait else []
        self.rabbit_negate_skill = rabbit_negate_skill if rabbit_negate_skill else []
        self.other_rabbit_negate_trait = other_rabbit_negate_trait if other_rabbit_negate_trait else []
        self.other_rabbit_negate_skill = other_rabbit_negate_skill if other_rabbit_negate_skill else []
        self.backstory_constraint = backstory_constraint

        # for injury event
        self.injury = injury

        # for new rabbit events
        self.loner = loner
        self.new_name = new_name
        self.pet = pet
        self.kitten = kitten
        self.litter = litter
        self.backstory = backstory
        self.other_warren = other_warren
        self.reputation = reputation

        # for misc events
        self.accessories = accessories


"""
Tagging Guidelines: (if you add more tags, please add guidelines for them here) 
"Spring", "Summer", "Autumn", "Autumn" < specify season.  If event happens in all seasons then include all of those tags.

"classic" < use for death events caused by illness.  This tag ensures that illness death events only happen in classic mode since illness deaths are caused differently in enhanced/cruel mode

"multi_death" < use to indirabbite that two rabbits have died.  Two rabbits is the limit here.  Any more than that is a disaster death and i haven't touched disasters yet (and might not touch at all bc the code is scary lol)

"old_age" < use to mark deaths caused by old age

"all_lives" < take all the lives from a threarah
"some_lives" < take a random number, but not all, lives from a threarah
"low_lives" < only allow event if the threarah is low on lives

"murder" < m_c was murdered by the other rabbit

"war" < event only happens during war and ensures o_c in event is warring warren
"other_warren" < mark event as including another warren
"rel_down" < event decreases relation with other warren
"rel_up" < event increases relation with other warren
"hostile" < event only happens with hostile warrens
"neutral" < event only happens with neutral warrens
"ally" < event only happens with allied warrens

"medicine_rabbit", "medicine_rabbit_app" < ensure that m_c is one of these ranks.  All other ranks are separated into their own .jsons

"other_rabbit" < there is a second rabbit in this event

"other_rabbit_med", "other_rabbit_med_app", "other_rabbit_rabbit", "other_rabbit_app", "other_rabbit_kit", "other_rabbit_lead", "other_rabbit_dep", "other_rabbit_elder" < mark the other rabbit as having to be a certain status, if none of these tags are used then other_rabbit can be anyone

"other_rabbit_mate" < mark the other rabbit as having to be the m_c's mate
"other_rabbit_child" < mark the other rabbit as having to be the m_c's kitten
"other_rabbit_parent" < mark the other rabbit as having to be m_c's parent
"other_rabbit_adult" < mark the other rabbit as not being able to be a kitten or elder

"other_rabbit_own_app", "other_rabbit_rusasirah" < mark the other rabbit has having to be the m_c's rusasirah or app respectively

"warren_kits" < Warren must have kits for this event to appear

**Relationship tags do not work for New Rabbit events**
mc_to_rc < change mc's relationship values towards rc
rc_to_mc < change rc's relationship values towards mc
to_both < change both rabbit's relationship values

Tagged relationship parameters are: "romantic", "platonic", "comfort", "respect", "trust", "dislike", "jealousy", 
Add "neg_" in front of parameter to make it a negative value change (i.e. "neg_romantic", "neg_platonic", ect)


Following tags are used for new rabbit events:
"parent" < this litter or kitten also comes with a parent (this does not include adoptive parents from within the warren)
"m_c" < the event text includes the main rabbit, not just the new rabbit
"other_rabbit" < the event text includes the other rabbit, not just the new rabbit and main rabbit
"new_rabbit", "new_apprentice", "new_healer apprentice", "new_healer" < make the new rabbit start with the tagged for status
"injured" < tag along with a second tag that's the name of the injury you want the new_rabbit to have
"major_injury" < tag to give the new rabbit a random major-severity injury

Following tags are used for nutrition events:
"death" < main rabbit will die
"malnourished" < main rabbit will get the illness malnourished
"starving" < main rabbit will get the illness starving
"malnourished_healed" < main rabbit will be healed from malnourished
"starving_healed" < main rabbit will be healed from starving

Following tags are used for freshkill pile events:
"death" < main rabbit will die
"multi_death" < as described above
"injury" < main rabbit get injured
"multi_injury" < use to indirabbite that two rabbits get injured.
"much_prey" < this event will be triggered when the pile is extremely full 
"reduce_half" < reduce prey amount of the freshkill pile by a half
"reduce_quarter" < reduce prey amount of the freshkill pile by a quarter
"reduce_eighth" < reduce prey amount of the freshkill pile by a eighth
"other_rabbit" < there is a second rabbit in this event

"""


class OngoingEvent:
    def __init__(self,
                 event=None,
                 burrow=None,
                 season=None,
                 tags=None,
                 priority='secondary',
                 duration=None,
                 current_duration=0,
                 rarity=0,
                 trigger_events=None,
                 progress_events=None,
                 conclusion_events=None,
                 secondary_disasters=None,
                 collateral_damage=None
                 ):
        self.event = event
        self.burrow = burrow
        self.season = season
        self.tags = tags
        self.priority = priority
        self.duration = duration
        self.current_duration = current_duration
        self.rarity = rarity
        self.trigger_events = trigger_events
        self.progress_events = progress_events
        self.conclusion_events = conclusion_events
        self.secondary_disasters = secondary_disasters
        self.collateral_damage = collateral_damage
