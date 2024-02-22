from random import choice, randint
import random

from scripts.rabbit.history import History
from scripts.utility import (
    create_new_rabbit,
    get_highest_romantic_relation,
    get_med_rabbits,
    event_text_adjust,
    get_personality_compatibility
)
from scripts.game_structure.game_essentials import game
from scripts.rabbit.rabbits import Rabbit, rabbit_class
from scripts.event_class import Single_Event
from scripts.rabbit_relations.relationship import Relationship
from scripts.events_module.condition_events import Condition_Events
from scripts.rabbit.names import names, Name

import ujson

class Pregnancy_Events():
    """All events which are related to pregnancy such as kitting and defining who are the parents."""
   
    biggest_family = {}
    
    PREGNANT_STRINGS = None
    with open(f"resources/dicts/conditions/pregnancy.json", 'r') as read_file:
        PREGNANT_STRINGS = ujson.loads(read_file.read())
   
    @staticmethod
    def set_biggest_family():
        """Gets the biggest family of the warren."""
        biggest_family = None
        for rabbit in Rabbit.all_rabbits.values():
            ancestors = rabbit.get_relatives()
            if not biggest_family:
                biggest_family = ancestors
                biggest_family.append(rabbit.ID)
            elif len(biggest_family) < len(ancestors) + 1:
                biggest_family = ancestors
                biggest_family.append(rabbit.ID)
        Pregnancy_Events.biggest_family = biggest_family

    @staticmethod
    def biggest_family_is_big():
        """Returns if the current biggest family is big enough to 'activates' additional inbreeding counters."""
        living_rabbits = len([i for i in Rabbit.all_rabbits.values() if not (i.dead or i.outside or i.exiled)])
        return len(Pregnancy_Events.biggest_family) > (living_rabbits/10)

    @staticmethod
    def handle_pregnancy_age(warren):
        """Increase the month for each pregnancy in the pregnancy dictionary"""
        for pregnancy_key in warren.pregnancy_data.keys():
            warren.pregnancy_data[pregnancy_key]["months"] += 1

    @staticmethod
    def handle_having_kits(rabbit, warren):
        """Handles pregnancy of a rabbit."""
        if not warren:
            return

        if not Pregnancy_Events.biggest_family:
            Pregnancy_Events.set_biggest_family()

        #Handles if a rabbit is already pregnant
        if rabbit.ID in warren.pregnancy_data:
            months = warren.pregnancy_data[rabbit.ID]["months"]
            if months == 1:
                Pregnancy_Events.handle_one_month_pregnant(rabbit, warren)
                return
            if months >= 2:
                Pregnancy_Events.handle_two_month_pregnant(rabbit, warren)
                #events.ceremony_accessory = True
                return

        if rabbit.outside:
            return

        # Handle birth cooldown outside of the check_if_can_have_kits function, so it only happens once
        # for each rabbit. 
        if rabbit.birth_cooldown > 0:
            rabbit.birth_cooldown -= 1
        
        # Check if they can have kits.
        can_have_kits = Pregnancy_Events.check_if_can_have_kits(rabbit, warren.warren_settings['single parentage'], 
                                                                warren.warren_settings['affair'])
        if not can_have_kits:
            return

        # DETERMINE THE SECOND PARENT
        # check if there is a rabbit in the warren for the second parent
        second_parent, is_affair = Pregnancy_Events.get_second_parent(rabbit, warren)

        # check if the second_parent is not none and if they also can have kits
        can_have_kits, kits_are_adopted = Pregnancy_Events.check_second_parent(
            rabbit,
            second_parent,
            warren.warren_settings['single parentage'],
            warren.warren_settings['affair'],
            warren.warren_settings["same sex birth"],
            warren.warren_settings["same sex adoption"]
        )
        if second_parent:
            if not can_have_kits:
                return
        else:
            if not game.warren.warren_settings['single parentage']:
                return

        chance = Pregnancy_Events.get_balanced_kit_chance(rabbit, second_parent, is_affair, warren)

        if not int(random.random() * chance):
            # If you've reached here - congrats, kits!
            if kits_are_adopted:
                Pregnancy_Events.handle_adoption(rabbit, second_parent, warren)
            else:
                Pregnancy_Events.handle_zero_month_pregnant(rabbit, second_parent, warren)

    # ---------------------------------------------------------------------------- #
    #                                 handle events                                #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def handle_adoption(rabbit: Rabbit, other_rabbit=None, warren=game.warren):
        """Handle if the there is no pregnancy but the pair triggered kits chance."""
        if other_rabbit and (other_rabbit.dead or other_rabbit.outside or other_rabbit.birth_cooldown > 0):
            return

        if rabbit.ID in warren.pregnancy_data:
            return
        
        if other_rabbit and other_rabbit.ID in warren.pregnancy_data:
            return
        
        # Gather adoptive parents, to feed into the 
        # get kits function. 
        adoptive_parents = [rabbit.ID]
        if other_rabbit:
            adoptive_parents.append(other_rabbit.ID)
        
        for _m in rabbit.mate:
            if _m not in adoptive_parents:
                adoptive_parents.append(_m)
        
        if other_rabbit:
            for _m in other_rabbit.mate:
                if _m not in adoptive_parents:
                    adoptive_parents.append(_m)
        
        amount = Pregnancy_Events.get_amount_of_kits(rabbit)
        kits = Pregnancy_Events.get_kits(amount, None, None, warren, adoptive_parents=adoptive_parents)
        
        insert = 'this should not display'
        insert2 = 'this should not display'
        if amount == 1:
            insert = 'a single kit'
            insert2 = 'it'
        if amount > 1:
            insert = f'a litter of {amount} kits'
            insert2 = 'them'

        print_event = f"{rabbit.name} found {insert} and decides to adopt {insert2}."
        if other_rabbit:
            print_event = f"{rabbit.name} and {other_rabbit.name} found {insert} and decided to adopt {insert2}."
        
        rabbits_involved = [rabbit.ID]
        if other_rabbit:
            rabbits_involved.append(other_rabbit.ID)
        for kit in kits:
            kit.thought = f"Snuggles up to the belly of {rabbit.name}"

        # Normally, birth cooldown is only applied to rabbit who gave birth
        # However, if we don't apply birth cooldown to adoption, we get
        # too much adoption, since adoptive couples are using the increased two-parent 
        # kits chance. We will only apply it to "rabbit" in this case
        # which is enough to stop the couple from adopting about within
        # the window. 
        rabbit.birth_cooldown = game.config["pregnancy"]["birth_cooldown"]

        game.cur_events_list.append(Single_Event(print_event, "birth_death", rabbits_involved))

    @staticmethod
    def handle_zero_month_pregnant(rabbit: Rabbit, other_rabbit=None, warren=game.warren):
        """Handles if the rabbit is zero months pregnant."""
        if other_rabbit and (other_rabbit.dead or other_rabbit.outside or other_rabbit.birth_cooldown > 0):
            return

        if rabbit.ID in warren.pregnancy_data:
            return

        if other_rabbit and other_rabbit.ID in warren.pregnancy_data:
            return
        
        # additional save for no kit setting
        if (rabbit and rabbit.no_kittens) or (other_rabbit and other_rabbit.no_kittens):
            return

        # even with no_gendered_breeding on a buck rabbit with no second parent should not be count as pregnant
        # instead, the rabbit should get the kit instantly
        if not other_rabbit and rabbit.gender == 'buck':
            amount = Pregnancy_Events.get_amount_of_kits(rabbit)
            kits = Pregnancy_Events.get_kits(amount, rabbit, None, warren)
            insert = 'this should not display'
            if amount == 1:
                insert = 'a single kit'
            if amount > 1:
                insert = f'a litter of {amount} kits'
            print_event = f"{rabbit.name} brought {insert} back to camp, but refused to talk about their origin."
            rabbits_involved = [rabbit.ID]
            for kit in kits:
                rabbits_involved.append(kit.ID)
            game.cur_events_list.append(Single_Event(print_event, "birth_death", rabbits_involved))
            return

        # if the other rabbit is a doe and the current rabbit is a buck, make the doe rabbit pregnant
        pregnant_rabbit = rabbit
        second_parent = other_rabbit
        if rabbit.gender == 'buck' and other_rabbit is not None and other_rabbit.gender == 'doe':
            pregnant_rabbit = other_rabbit
            second_parent = rabbit

        warren.pregnancy_data[pregnant_rabbit.ID] = {
            "second_parent": str(second_parent.ID) if second_parent else None,
            "months": 0,
            "amount": 0
        }

        text = choice(Pregnancy_Events.PREGNANT_STRINGS["announcement"])
        if warren.game_mode != 'classic':
            severity = random.choices(["minor", "major"], [3, 1], k=1)
            pregnant_rabbit.get_injured("pregnant", severity=severity[0])
            text += choice(Pregnancy_Events.PREGNANT_STRINGS[f"{severity[0]}_severity"])
        text = event_text_adjust(Rabbit, text, pregnant_rabbit, warren=warren)
        game.cur_events_list.append(Single_Event(text, "birth_death", pregnant_rabbit.ID))

    @staticmethod
    def handle_one_month_pregnant(rabbit: Rabbit, warren=game.warren):
        """Handles if the rabbit is one month pregnant."""
        if rabbit.ID not in warren.pregnancy_data.keys():
            return

        # if the pregnant rabbit killed meanwhile, delete it from the dictionary
        if rabbit.dead:
            del warren.pregnancy_data[rabbit.ID]
            return

        amount = Pregnancy_Events.get_amount_of_kits(rabbit)
        text = 'This should not appear (pregnancy_events.py)'

        # add the amount to the pregnancy dict
        warren.pregnancy_data[rabbit.ID]["amount"] = amount

        # if the rabbit is outside of the warren, they won't guess how many kits they will have
        if rabbit.outside:
            return

        thinking_amount = random.choices(["correct", "incorrect", "unsure"], [4, 1, 1], k=1)
        if amount <= 3:
            correct_guess = "small"
        else:
            correct_guess = "large"

        if thinking_amount[0] == "correct":
            if correct_guess == "small":
                text = Pregnancy_Events.PREGNANT_STRINGS["litter_guess"][0]
            else:
                text = Pregnancy_Events.PREGNANT_STRINGS["litter_guess"][1]
        elif thinking_amount[0] == 'incorrect':
            if correct_guess == "small":
                text = Pregnancy_Events.PREGNANT_STRINGS["litter_guess"][1]
            else:
                text = Pregnancy_Events.PREGNANT_STRINGS["litter_guess"][0]
        else:
            text = Pregnancy_Events.PREGNANT_STRINGS["litter_guess"][2]

        if warren.game_mode != 'classic':
            try:
                if rabbit.injuries["pregnant"]["severity"] == "minor":
                    rabbit.injuries["pregnant"]["severity"] = "major"
                    text += choice(Pregnancy_Events.PREGNANT_STRINGS["major_severity"])
            except:
                print("Is this an old save? Rabbit does not have the pregnant condition")

        text = event_text_adjust(Rabbit, text, rabbit, warren=warren)
        game.cur_events_list.append(Single_Event(text, "birth_death", rabbit.ID))

    @staticmethod
    def handle_two_month_pregnant(rabbit: Rabbit, warren=game.warren):
        """Handles if the rabbit is two months pregnant."""
        if rabbit.ID not in warren.pregnancy_data.keys():
            return

        # if the pregnant rabbit is killed meanwhile, delete it from the dictionary
        if rabbit.dead:
            del warren.pregnancy_data[rabbit.ID]
            return

        involved_rabbits = [rabbit.ID]

        kits_amount = warren.pregnancy_data[rabbit.ID]["amount"]
        other_rabbit_id = warren.pregnancy_data[rabbit.ID]["second_parent"]
        other_rabbit = Rabbit.all_rabbits.get(other_rabbit_id)

        kits = Pregnancy_Events.get_kits(kits_amount, rabbit, other_rabbit, warren)
        kits_amount = len(kits)
        Pregnancy_Events.set_biggest_family()

        # delete the rabbit out of the pregnancy dictionary
        del warren.pregnancy_data[rabbit.ID]

        if rabbit.outside:
            for kit in kits:
                kit.outside = True
                game.warren.add_to_outside(kit)
                kit.backstory = "outsider"
                if rabbit.exiled:
                    kit.status = 'hlessi'
                    name = choice(names.names_dict["normal_prefixes"])
                    kit.name = Name('hlessi', prefix=name, suffix="")
                if other_rabbit and not other_rabbit.outside:
                    kit.backstory = "outsider2"
                if rabbit.outside and not rabbit.exiled:
                    kit.backstory = "outsider3"
                kit.relationships = {}
                kit.create_one_relationship(rabbit)

        if kits_amount == 1:
            insert = 'single kit'
        else:
            insert = f'litter of {kits_amount} kits'

        # Since rabbit has given birth, apply the birth cooldown. 
        rabbit.birth_cooldown = game.config["pregnancy"]["birth_cooldown"]
        
        # choose event string
        # TODO: currently they don't choose which 'mate' is the 'blood' parent or not
        # change or leaf as it is? 
        events = Pregnancy_Events.PREGNANT_STRINGS
        event_list = []
        if not rabbit.outside and other_rabbit is None:
            event_list.append(choice(events["birth"]["unmated_parent"]))
        elif rabbit.outside:
            adding_text = choice(events["birth"]["outside_alone"])
            if other_rabbit and not other_rabbit.outside:
                adding_text = choice(events["birth"]["outside_in_warren"])
            event_list.append(adding_text)
        elif other_rabbit.ID in rabbit.mate and not other_rabbit.dead and not other_rabbit.outside:
            involved_rabbits.append(other_rabbit.ID)
            event_list.append(choice(events["birth"]["two_parents"]))
        elif other_rabbit.ID in rabbit.mate and other_rabbit.dead or other_rabbit.outside:
            involved_rabbits.append(other_rabbit.ID)
            event_list.append(choice(events["birth"]["dead_mate"]))
        elif len(rabbit.mate) < 1 and len(other_rabbit.mate) < 1 and not other_rabbit.dead:
            involved_rabbits.append(other_rabbit.ID)
            event_list.append(choice(events["birth"]["both_unmated"]))
        elif (len(rabbit.mate) > 0 and other_rabbit.ID not in rabbit.mate and not other_rabbit.dead) or\
            (len(other_rabbit.mate) > 0 and rabbit.ID not in other_rabbit.mate and not other_rabbit.dead):
            involved_rabbits.append(other_rabbit.ID)
            event_list.append(choice(events["birth"]["affair"]))
        else:
            event_list.append(choice(events["birth"]["unmated_parent"]))

        if warren.game_mode != 'classic':
            try:
                death_chance = rabbit.injuries["pregnant"]["mortality"]
            except:
                death_chance = 40
        else:
            death_chance = 40
        if not int(random.random() * death_chance):  # chance for a rabbit to die during childbirth
            possible_events = events["birth"]["death"]
            # just makin sure meds aren't mentioned if they aren't around or if they are a parent
            meds = get_med_rabbits(Rabbit, working=False)
            mate_is_med = [mate_id for mate_id in rabbit.mate if mate_id in meds]
            if not meds or rabbit in meds or len(mate_is_med) > 0:
                for event in possible_events:
                    if "healer" in event:
                        possible_events.remove(event)

            if rabbit.outside:
                possible_events = events["birth"]["outside_death"]
            event_list.append(choice(possible_events))

            if rabbit.status == 'threarah':
                warren.threarah_lives -= 1
                rabbit.die()
                death_event = ("died shortly after kitting")
            else:
                rabbit.die()
                death_event = (f"{rabbit.name} died while kitting.")
            History.add_death(rabbit, death_text=death_event)
        elif warren.game_mode != 'classic' and not rabbit.outside:  # if rabbit doesn't die, give recovering from birth
            rabbit.get_injured("recovering from birth", event_triggered=True)
            if 'blood loss' in rabbit.injuries:
                if rabbit.status == 'threarah':
                    death_event = ("died after a harsh kitting")
                else:
                    death_event = (f"{rabbit.name} after a harsh kitting.")
                History.add_possible_history(rabbit, 'blood loss', death_text=death_event)
                possible_events = events["birth"]["difficult_birth"]
                # just makin sure meds aren't mentioned if they aren't around or if they are a parent
                meds = get_med_rabbits(Rabbit, working=False)
                mate_is_med = [mate_id for mate_id in rabbit.mate if mate_id in meds]
                if not meds or rabbit in meds or len(mate_is_med) > 0:
                    for event in possible_events:
                        if "healer" in event:
                            possible_events.remove(event)

                event_list.append(choice(possible_events))
        if warren.game_mode != 'classic' and not rabbit.dead: 
            #If they are dead in childbirth above, all condition are cleared anyway. 
            try:
                rabbit.injuries.pop("pregnant")
            except:
                print("Is this an old save? Your rabbit didn't have the pregnant condition!")
        print_event = " ".join(event_list)
        print_event = print_event.replace("{insert}", insert)
        
        print_event = event_text_adjust(Rabbit, print_event, rabbit, other_rabbit, warren=warren)
        # display event
        game.cur_events_list.append(Single_Event(print_event, ["health", "birth_death"], involved_rabbits))

    # ---------------------------------------------------------------------------- #
    #                          check if event is triggered                         #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def check_if_can_have_kits(rabbit, single_parentage, allow_affair):
        """Check if the given rabbit can have kits, see for age, birth-cooldown and so on."""
        if not rabbit:
            return False

        if rabbit.birth_cooldown > 0:
            return False

        if 'recovering from birth' in rabbit.injuries:
            return False

        # decide chances of having kits, and if it's possible at all.
        # Including - age, dead statis, having kits turned off.
        not_correct_age = rabbit.age in ['newborn', 'kitten', 'adolescent'] or rabbit.months < 15
        if not_correct_age or rabbit.no_kittens or rabbit.dead:
            return False

        # check for mate
        if len(rabbit.mate) > 0:
            for mate_id in rabbit.mate:
                if mate_id not in rabbit.all_rabbits:
                    print(f"WARNING: {rabbit.name}  has an invalid mate # {mate_id}. This has been unset.")
                    rabbit.mate.remove(mate_id)

        # If the "single parentage setting in on, we should only allow rabbits that have mates to have kits.
        if not single_parentage and len(rabbit.mate) < 1 and not allow_affair:
            return False

        # if function reaches this point, having kits is possible
        return True

    @staticmethod
    def check_second_parent(rabbit: Rabbit,
                            second_parent: Rabbit,
                            single_parentage: bool,
                            allow_affair: bool,
                            same_sex_birth: bool,
                            same_sex_adoption:bool):
        """
            This checks to see if the chosen second parent and CAT can have kits. It assumes CAT can have kits.
            returns:
            parent can have kits, kits are adopted
        """

        # Checks for second parent alone:
        if not Pregnancy_Events.check_if_can_have_kits(second_parent, single_parentage, allow_affair):
            return False, False

        # Check to see if the pair can have kits.
        if rabbit.gender == second_parent.gender:
            if same_sex_birth:
                return True, False
            elif not same_sex_adoption:
                return False, False
            else:
                return True, True
                
        return True, False

    # ---------------------------------------------------------------------------- #
    #                               getter functions                               #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def get_second_parent(rabbit, warren):
        """ 
            Return the second parent of a rabbit, which will have kits. 
            Also returns a bool that is true if an affair was triggered.
        """
        samesex = warren.warren_settings['same sex birth']
        allow_affair = warren.warren_settings['affair']
        mate = None

        # randomly select a mate of given rabbit
        if len(rabbit.mate) > 0:
            mate = choice(rabbit.mate)
            mate = rabbit.fetch_rabbit(mate)

        # if the sex does matter, choose the best solution to allow kits
        if not samesex and mate and mate.gender == rabbit.gender:
            opposite_mate = [rabbit.fetch_rabbit(mate_id) for mate_id in rabbit.mate if rabbit.fetch_rabbit(mate_id).gender != rabbit.gender]
            if len(opposite_mate) > 0:
                mate = choice(opposite_mate)

        if not allow_affair:
            # if affairs setting is OFF, second parent (mate) will be returned
            return mate, False

        # get relationships to influence the affair chance
        mate_relation = None
        if mate and mate.ID in rabbit.relationships:
            mate_relation = rabbit.relationships[mate.ID]
        elif mate:
            mate_relation = rabbit.create_one_relationship(mate)


        # LOVE AFFAIR
        # Handle love affair chance.
        affair_partner = Pregnancy_Events.determine_love_affair(rabbit, mate, mate_relation, samesex)
        if affair_partner:
            return affair_partner, True

        # RANDOM AFFAIR
        chance = game.config["pregnancy"]["random_affair_chance"]
        special_affair = False
        if len(rabbit.mate) <= 0:
            # Special random affair check only for unmated rabbits. For this check, only
            # other unmated rabbits can be the affair partner. 
            chance = game.config["pregnancy"]["unmated_random_affair_chance"]
            special_affair = True

        # 'buff' affairs if the current biggest family is big + this rabbit doesn't belong there
        if not Pregnancy_Events.biggest_family:
            Pregnancy_Events.set_biggest_family()

        if Pregnancy_Events.biggest_family_is_big() and rabbit.ID not in Pregnancy_Events.biggest_family:
            chance = int(chance * 0.8) 

        # "regular" random affair
        if not int(random.random() * chance):
            possible_affair_partners = [i for i in Rabbit.all_rabbits_list if 
                                        i.is_potential_mate(rabbit, for_love_interest=True) 
                                        and (samesex or i.gender != rabbit.gender) 
                                        and i.ID not in rabbit.mate]
            if special_affair:
                possible_affair_partners = [c for c in possible_affair_partners if len(c.mate) <1]

            # even it is a random affair, the rabbits should not hate each other or something like that
            p_affairs = []
            if len(possible_affair_partners) > 0:
                for p_affair in possible_affair_partners:
                    if p_affair.ID in rabbit.relationships:
                        p_rel = rabbit.relationships[p_affair.ID]
                        if not p_rel.opposite_relationship:
                            p_rel.link_relationship()
                        p_rel_opp = p_rel.opposite_relationship
                        if p_rel.dislike < 20 and p_rel_opp.dislike < 20:
                            p_affairs.append(p_affair)
            possible_affair_partners = p_affairs

            if len(possible_affair_partners) > 0:
                chosen_affair = choice(possible_affair_partners)
                return chosen_affair, True

        return mate, False

    @staticmethod
    def determine_love_affair(rabbit, mate, mate_relation, samesex):
        """ 
        Function to handle everything around love affairs. 
        Will return a second parent if a love affair is triggerd, and none otherwise. 
        """

        highest_romantic_relation = get_highest_romantic_relation(
            rabbit.relationships.values(),
            exclude_mate=True,
            potential_mate=True
        )

        if mate and highest_romantic_relation:
            # Love affair calculation when the rabbit has a mate
            chance_love_affair = Pregnancy_Events.get_love_affair_chance(mate_relation, highest_romantic_relation)
            if not chance_love_affair or not int(random.random() * chance_love_affair):
                if samesex or rabbit.gender != highest_romantic_relation.rabbit_to.gender:
                    return highest_romantic_relation.rabbit_to
        elif highest_romantic_relation:
            # Love affair change if the rabbit doesn't have a mate:
            chance_love_affair = Pregnancy_Events.get_unmated_love_affair_chance(highest_romantic_relation)
            if not chance_love_affair or not int(random.random() * chance_love_affair):
                if samesex or rabbit.gender != highest_romantic_relation.rabbit_to.gender:
                    return highest_romantic_relation.rabbit_to

        return None

    @staticmethod
    def get_kits(kits_amount, rabbit=None, other_rabbit=None, warren=game.warren, adoptive_parents=None):
        """Create some amount of kits
           No parents are specifed, it will create a blood parents for all the 
           kits to be related to. They may be dead or alive, but will always be outside 
           the warren. """
        all_kit = []
        if not adoptive_parents: 
            adoptive_parents = []
        
        #First, just a check: If we have no rabbit, but an other_rabbit was provided, 
        # swap other_rabbit to rabbit:
        # This way, we can ensure that if only one parent is provided, 
        # it's rabbit, not other_rabbit. 
        # And if rabbit is None, we know that no parents were provided. 
        if other_rabbit and not rabbit:
            rabbit = other_rabbit
            other_rabbit = None
        
        blood_parent = None
         
        ##### SELECT BACKSTORY #####
        if rabbit and rabbit.gender == 'doe':
            backstory = choice(['halfwarren1', 'outsider_roots1'])
        elif rabbit:
            backstory = choice(['halfwarren2', 'outsider_roots2'])
        else: # rabbit is adopted
            backstory = choice(['abandoned1', 'abandoned2', 'abandoned3', 'abandoned4'])
        ###########################
        
        ##### ADOPTIVE PARENTS #####
        # First, gather all the mates of the provided bio parents to be added
        # as adoptive parents. 
        all_adoptive_parents = []
        birth_parents = [i.ID for i in (rabbit, other_rabbit) if i]
        for _par in (rabbit, other_rabbit):
            if not _par:
                continue
            for _m in _par.mate:
                if _m not in birth_parents and _m not in all_adoptive_parents:
                    all_adoptive_parents.append(_m)
        
        # Then, add any additional adoptive parents that were provided passed directly into the
        # function. 
        for _m in adoptive_parents:
            if _m not in all_adoptive_parents:
                all_adoptive_parents.append(_m)
        
        #############################
        
        #### GENERATE THE KITS ######
        for kit in range(kits_amount):
            
            kit = None
            if not rabbit: 
                
                # No parents provided, give a blood parent - this is an adoption. 
                if not blood_parent:
                    # Generate a blood parent if we haven't already. 
                    insert = "their kits are"
                    if kits_amount == 1:
                        insert = "their kit is"
                    thought = f"Is glad that {insert} safe"
                    blood_parent = create_new_rabbit(Rabbit, Relationship,
                                                status=random.choice(["hlessi", "pet"]),
                                                alive=False,
                                                thought=thought,
                                                age=randint(15,120),
                                                outside=True)[0]
                    blood_parent.thought = thought
                
                kit = Rabbit(parent1=blood_parent.ID ,months=0, backstory=backstory, status='newborn')
            elif rabbit and other_rabbit:
                # Two parents provided
                kit = Rabbit(parent1=rabbit.ID, parent2=other_rabbit.ID, months=0, status='newborn')
                
                if rabbit.gender == 'doe':
                    kit.thought = f"Snuggles up to the belly of {rabbit.name}"
                elif rabbit.gender == 'buck' and other_rabbit.gender == 'buck':
                    kit.thought = f"Snuggles up to the belly of {rabbit.name}"
                else:
                    kit.thought = f"Snuggles up to the belly of {other_rabbit.name}"
            else:
                # A one blood parent litter is the only option left. 
                kit = Rabbit(parent1=rabbit.ID, months=0, backstory=backstory, status='newborn')
                kit.thought = f"Snuggles up to the belly of {rabbit.name}"
                
            kit.adoptive_parents = all_adoptive_parents  # Add the adoptive parents. 
            all_kit.append(kit)

            # remove scars
            kit.pelt.scars.clear()

            # try to give them a permanent condition. 1/90 chance
            # don't delete the game.warren condition, this is needed for a test
            if game.warren and not int(random.random() * game.config["rabbit_generation"]["base_permanent_condition"]) \
                    and game.warren.game_mode != 'classic':
                kit.congenital_condition(kit)
                for condition in kit.permanent_condition:
                    if kit.permanent_condition[condition] == 'born without a leg':
                        kit.pelt.scars.append('NOPAW')
                    elif kit.permanent_condition[condition] == 'born without a tail':
                        kit.pelt.scars.append('NOTAIL')
                Condition_Events.handle_already_disabled(kit)

            # create and update relationships
            for rabbit_id in warren.warren_rabbits:
                if rabbit_id == kit.ID:
                    continue
                the_rabbit = Rabbit.all_rabbits.get(rabbit_id)
                if the_rabbit.dead or the_rabbit.outside:
                    continue
                if the_rabbit.ID in kit.get_parents():
                    y = random.randrange(0, 20)
                    start_relation = Relationship(the_rabbit, kit, False, True)
                    start_relation.platonic_like += 30 + y
                    start_relation.comfortable = 10 + y
                    start_relation.admiration = 15 + y
                    start_relation.trust = 10 + y
                    the_rabbit.relationships[kit.ID] = start_relation
                    y = random.randrange(0, 20)
                    start_relation = Relationship(kit, the_rabbit, False, True)
                    start_relation.platonic_like += 30 + y
                    start_relation.comfortable = 10 + y
                    start_relation.admiration = 15 + y
                    start_relation.trust = 10 + y
                    kit.relationships[the_rabbit.ID] = start_relation
                else:
                    the_rabbit.relationships[kit.ID] = Relationship(the_rabbit, kit)
                    kit.relationships[the_rabbit.ID] = Relationship(kit, the_rabbit)
            
            #### REMOVE ACCESSORY ###### 
            kit.pelt.accessory = None
            warren.add_rabbit(kit)

            #### GIVE HISTORY ###### 
            History.add_beginning(kit, warren_born=bool(rabbit))
        
        # check other rabbits of warren for siblings
        for kit in all_kit:
            # update/buff the relationship towards the siblings
            for second_kit in all_kit:
                y = random.randrange(0, 10)
                if second_kit.ID == kit.ID:
                    continue
                kit.relationships[second_kit.ID].platonic_like += 20 + y
                kit.relationships[second_kit.ID].comfortable += 10 + y
                kit.relationships[second_kit.ID].trust += 10 + y
            
            kit.create_inheritance_new_rabbit() # Calculate inheritance. 

        if blood_parent:
            blood_parent.outside = True
            warren.unknown_rabbits.append(blood_parent.ID)

        return all_kit

    @staticmethod
    def get_amount_of_kits(rabbit):
        """Get the amount of kits which will be born."""
        min_kits = game.config["pregnancy"]["min_kits"]
        min_kit = [min_kits] * game.config["pregnancy"]["one_kit_possibility"][rabbit.age]
        two_kits = [min_kits + 1] * game.config["pregnancy"]["two_kit_possibility"][rabbit.age]
        three_kits = [min_kits + 2] * game.config["pregnancy"]["three_kit_possibility"][rabbit.age]
        four_kits = [min_kits + 3] * game.config["pregnancy"]["four_kit_possibility"][rabbit.age]
        five_kits = [min_kits + 4] * game.config["pregnancy"]["five_kit_possibility"][rabbit.age]
        max_kits = [game.config["pregnancy"]["max_kits"]] * game.config["pregnancy"]["max_kit_possibility"][rabbit.age]
        amount = choice(min_kit + two_kits + three_kits + four_kits + five_kits + max_kits)

        return amount

    # ---------------------------------------------------------------------------- #
    #                                  get chances                                 #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def get_love_affair_chance(mate_relation: Relationship, affair_relation: Relationship):
        """ Looks into the current values and calculate the chance of having kits with the affair rabbit.
            The lower, the more likely they will have affairs. This function should only be called when mate 
            and affair_rabbit are not the same.

            Returns:
                integer (number)
        """
        if not mate_relation.opposite_relationship:
            mate_relation.link_relationship()

        if not affair_relation.opposite_relationship:
            affair_relation.link_relationship()

        average_mate_love = (mate_relation.romantic_love + mate_relation.opposite_relationship.romantic_love) / 2
        average_affair_love = (affair_relation.romantic_love + affair_relation.opposite_relationship.romantic_love) / 2

        difference = average_mate_love - average_affair_love

        if difference < 0:
            # If the average love between affair partner is greater than the average love between the mate
            affair_chance = 10
            difference = -difference

            if difference > 30:
                affair_chance -= 7
            elif difference > 20:
                affair_chance -= 6
            elif difference > 15:
                affair_chance -= 5
            elif difference > 10:
                affair_chance -= 4

        elif difference > 0:
            # If the average love between the mate is greater than the average relationship between the affair
            affair_chance = 30

            if difference > 30:
                affair_chance += 8
            elif difference > 20:
                affair_chance += 5
            elif difference > 15:
                affair_chance += 3
            elif difference > 10:
                affair_chance += 5

        else:
            # For difference = 0 or some other weird stuff
            affair_chance = 15

        return affair_chance

    @staticmethod
    def get_unmated_love_affair_chance(relation: Relationship):
        """ Get the "love affair" change when neither the rabbit nor the highest romantic relation have a mate"""

        if not relation.opposite_relationship:
            relation.link_relationship()

        affair_chance = 15
        average_romantic_love = (relation.romantic_love + relation.opposite_relationship.romantic_love) / 2

        if average_romantic_love > 50:
            affair_chance -= 12
        elif average_romantic_love > 40:
            affair_chance -= 10
        elif average_romantic_love > 30:
            affair_chance -= 7
        elif average_romantic_love > 10:
            affair_chance -= 5

        return affair_chance

    @staticmethod
    def get_balanced_kit_chance(first_parent: Rabbit, second_parent: Rabbit, affair, warren) -> int:
        """Returns a chance based on different values."""
        # Now that the second parent is determined, we can calculate the balanced chance for kits
        # get the chance for pregnancy
        inverse_chance = game.config["pregnancy"]["primary_chance_unmated"]
        if len(first_parent.mate) > 0 and not affair:
            inverse_chance = game.config["pregnancy"]["primary_chance_mated"]

        # SETTINGS
        # - decrease inverse chance if only mated pairs can have kits
        if warren.warren_settings['single parentage']:
            inverse_chance = int(inverse_chance * 0.7)

        # - decrease inverse chance if affairs are not allowed
        if not warren.warren_settings['affair']:
            inverse_chance = int(inverse_chance * 0.7)

        # CURRENT CAT AMOUNT
        # - increase the inverse chance if the warren is bigger
        living_rabbits = len([i for i in Rabbit.all_rabbits.values() if not (i.dead or i.outside or i.exiled)])
        if living_rabbits < 10:
            inverse_chance = int(inverse_chance * 0.5) 
        elif living_rabbits > 30:
            inverse_chance = int(inverse_chance * (living_rabbits/30))

        # COMPATIBILITY
        # - decrease / increase depending on the compatibility
        if second_parent:
            comp = get_personality_compatibility(first_parent, second_parent)
            if comp is not None:
                buff = 0.85
                if not comp:
                    buff += 0.3
                inverse_chance = int(inverse_chance * buff)

        # RELATIONSHIP
        # - decrease the inverse chance if the rabbits are going along well
        if second_parent:
            # get the needed relationships
            if second_parent.ID in first_parent.relationships:
                second_parent_relation = first_parent.relationships[second_parent.ID]
                if not second_parent_relation.opposite_relationship:
                    second_parent_relation.link_relationship()
            else:
                second_parent_relation = first_parent.create_one_relationship(second_parent)

            average_romantic_love = (second_parent_relation.romantic_love +
                                     second_parent_relation.opposite_relationship.romantic_love) / 2
            average_comfort = (second_parent_relation.comfortable +
                               second_parent_relation.opposite_relationship.comfortable) / 2
            average_trust = (second_parent_relation.trust +
                             second_parent_relation.opposite_relationship.trust) / 2

            if average_romantic_love >= 85:
                inverse_chance -= int(inverse_chance * 0.3)
            elif average_romantic_love >= 55:
                inverse_chance -= int(inverse_chance * 0.2)
            elif average_romantic_love >= 35:
                inverse_chance -= int(inverse_chance * 0.1)

            if average_comfort >= 85:
                inverse_chance -= int(inverse_chance * 0.3)
            elif average_comfort >= 55:
                inverse_chance -= int(inverse_chance * 0.2)
            elif average_comfort >= 35:
                inverse_chance -= int(inverse_chance * 0.1)

            if average_trust >= 85:
                inverse_chance -= int(inverse_chance * 0.3)
            elif average_trust >= 55:
                inverse_chance -= int(inverse_chance * 0.2)
            elif average_trust >= 35:
                inverse_chance -= int(inverse_chance * 0.1)
        
        # AGE
        # - decrease the inverse chance if the whole warren is really old
        avg_age = int(sum([rabbit.months for rabbit in Rabbit.all_rabbits.values()])/living_rabbits)
        if avg_age > 80:
            inverse_chance = int(inverse_chance * 0.8)

        # 'INBREED' counter
        # - increase inverse chance if one of the current rabbits belongs in the biggest family
        if not Pregnancy_Events.biggest_family: # set the family if not already
            Pregnancy_Events.set_biggest_family()

        if first_parent.ID in Pregnancy_Events.biggest_family or second_parent and second_parent.ID in Pregnancy_Events.biggest_family:
            inverse_chance = int(inverse_chance * 1.7)

        # - decrease inverse chance if the current family is small
        if len(first_parent.get_relatives(warren.warren_settings["first cousin mates"])) < (living_rabbits/15):
            inverse_chance = int(inverse_chance * 0.7)

        # - decrease inverse chance single parents if settings allow an biggest family is huge
        settings_allow = not second_parent and not warren.warren_settings['single parentage']
        if settings_allow and Pregnancy_Events.biggest_family_is_big():
            inverse_chance = int(inverse_chance * 0.9)

        return inverse_chance
