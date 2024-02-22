# pylint: disable=line-too-long
"""

This file is the file which contains information about the inheritance of a rabbit.
Each rabbit has one instance of the inheritance class.
The inheritance class has a dictionary for all instances of the inheritance class, to easily manipulate and update the inheritance.
This class will be used to check for relations while mating and for the display of the family tree screen.

"""  # pylint: enable=line-too-long
from enum import Enum  # pylint: disable=no-name-in-module
from scripts.game_structure.game_essentials import game

class RelationType(Enum):
    """An enum representing the possible age groups of a rabbit"""

    BLOOD = ''                  	# direct blood related - do not need a special print
    ADOPTIVE = 'adoptive'       	# not blood related but close (parents, kits, siblings)
    HALF_BLOOD = 'half sibling'   	# only one blood parent is the same (siblings only)
    NOT_BLOOD = 'not blood related'	# not blood related for parent siblings
    RELATED = 'blood related'   	# related by blood (different mates only)

BLOOD_RELATIVE_TYPES = [RelationType.BLOOD, RelationType.HALF_BLOOD, RelationType.RELATED]

class Inheritance():
    all_inheritances = {}  # ID: object

    def __init__(self, rabbit, born=False):
        self.parents = {}
        self.kits = {}
        self.kits_mates = {}
        self.siblings = {}
        self.siblings_mates = {}
        self.siblings_kits = {}
        self.parents_siblings = {}
        self.cousins = {}
        self.grand_parents = {}
        self.grand_kits = {}
        self.all_involved = []
        self.all_but_cousins = []

        self.rabbit = rabbit
        self.update_inheritance()

        # if the rabbit is newly born, update all the related rabbits
        if born:
            self.update_all_related_inheritance()

        # SAVE INHERITANCE INTO ALL_INHERITANCES DICTIONARY
        self.all_inheritances[rabbit.ID] = self

    def update_inheritance(self):
        """Update inheritance of the given rabbit."""
        self.parents = {}
        self.mates = {}
        self.kits = {}
        self.kits_mates = {}
        self.siblings = {}
        self.siblings_mates = {}
        self.siblings_kits = {}
        self.parents_siblings = {}
        self.cousins = {}
        self.grand_parents = {}
        self.grand_kits = {}
        self.all_involved = []
        self.all_but_cousins = []
        self.other_mates = []

        # helping variables
        self.need_update = []

        # parents
        self.init_parents()

        # grand parents
        self.init_grand_parents()

        # mates
        self.init_mates()

        for inter_id, inter_rabbit in self.rabbit.all_rabbits.items():
            if inter_id == self.rabbit.ID:
                continue

            # kits + their mates
            self.init_kits(inter_id, inter_rabbit)

            # siblings + their mates
            self.init_siblings(inter_id, inter_rabbit)

            # parents_siblings
            self.init_parents_siblings(inter_id, inter_rabbit)

            # cousins
            self.init_cousins(inter_id, inter_rabbit)

        # since grand kits depending on kits, ALL KITS HAVE TO BE SET FIRST!
        for inter_id, inter_rabbit in self.rabbit.all_rabbits.items():
            if inter_id == self.rabbit.ID:
                continue

            # grand kits
            self.init_grand_kits(inter_id, inter_rabbit)

        # relations to faded rabbits - these must occur after all non-faded 
        # rabbits have been handled, and in the following order. 
        self.init_faded_kits()
        
        self.init_faded_siblings()
        
        self.init_faded_parents_siblings()
        
        self.init_faded_grandkits()
        
        self.init_faded_cousins()

        if len(self.need_update) > 1:
            for update_id in self.need_update:
                if update_id in self.all_inheritances:
                    self.all_inheritances[update_id].update_inheritance()
                    # if the inheritance is updated, remove the id of the need_update list
                    self.need_update.remove(update_id)

    def update_all_related_inheritance(self):
        """Update all the inheritances of the rabbits, which are related to the current rabbit."""
        # only adding/removing parents or kits will use this function, because all inheritances are based on parents
        for rabbit_id in self.all_involved:
             # Don't update the inheritance of faded rabbits - they are not viewable by the player and won't be used in any checks. 
            if rabbit_id in self.all_inheritances and not self.rabbit.fetch_rabbit(rabbit_id).faded:
                self.all_inheritances[rabbit_id].update_inheritance()

    def update_all_mates(self):
        """ 
        This function should be called, when the rabbit breaks up. 
        It renews all inheritances, where this rabbit is listed as a mate of a kit or sibling.
        """
        self.update_inheritance()
        for inter_inheritances in self.all_inheritances.values():
            if self.rabbit.ID in inter_inheritances.other_mates or self.rabbit.ID in inter_inheritances.all_involved:
                inter_inheritances.update_inheritance()

    def get_rabbit_info(self, rabbit_id) -> list:
        """Returns a list of the additional information of the given rabbit id."""
        info = {
            "additional": [],
            "type": [],
        }
        if rabbit_id in self.parents:
            info["type"].append(self.parents[rabbit_id]["type"])
            info["additional"].extend(self.parents[rabbit_id]["additional"])
        if rabbit_id in self.kits:
            info["type"].append(self.kits[rabbit_id]["type"])
            info["additional"].extend(self.kits[rabbit_id]["additional"])
        if rabbit_id in self.siblings:
            info["type"].append(self.siblings[rabbit_id]["type"])
            info["additional"].extend(self.siblings[rabbit_id]["additional"])
        if rabbit_id in self.parents_siblings:
            info["type"].append(self.parents_siblings[rabbit_id]["type"])
            info["additional"].extend(self.parents_siblings[rabbit_id]["additional"])
        if rabbit_id in self.cousins:
            info["type"].append(self.cousins[rabbit_id]["type"])
            info["additional"].extend(self.cousins[rabbit_id]["additional"])
        if rabbit_id in self.grand_parents:
            info["type"].append(self.grand_parents[rabbit_id]["type"])
            info["additional"].extend(self.grand_parents[rabbit_id]["additional"])
        if rabbit_id in self.grand_kits:
            info["type"].append(self.grand_kits[rabbit_id]["type"])
            info["additional"].extend(self.grand_kits[rabbit_id]["additional"])
        if rabbit_id in self.siblings_kits:
            info["type"].append(self.siblings_kits[rabbit_id]["type"])
            info["additional"].extend(self.siblings_kits[rabbit_id]["additional"])
        if rabbit_id in self.siblings_mates:
            info["type"].append(self.siblings_mates[rabbit_id]["type"])
            info["additional"].extend(self.siblings_mates[rabbit_id]["additional"])
        if rabbit_id in self.kits_mates:
            info["type"].append(self.kits_mates[rabbit_id]["type"])
            info["additional"].extend(self.kits_mates[rabbit_id]["additional"])
        if rabbit_id in self.mates:
            info["type"].append(self.mates[rabbit_id]["type"])
            info["additional"].extend(self.mates[rabbit_id]["additional"])
        return info

    def remove_parent(self, rabbit):
        """Remove the rabbit the parent dictionary - used to 'update' the adoptive parents."""
        if rabbit.ID in self.parents:
            del self.parents[rabbit.ID]
            self.update_all_related_inheritance()

    def add_parent(self, parent, rel_type = RelationType.ADOPTIVE):
        """Adding a parent entry with the given rel_type - used to add adoptive parents, if the parent gets a new mate."""
        # the default is adoptive, because the there should only be 2 blood parents per default
        self.parents[parent.ID] = {
            "type": rel_type,
            "additional": []
        }
        if rel_type == RelationType.ADOPTIVE and parent.ID not in self.rabbit.adoptive_parents:
            self.rabbit.adoptive_parents.append(parent.ID)
        self.all_involved.append(parent.ID)
        self.all_but_cousins.append(parent.ID)
        self.update_all_related_inheritance()

    # ---------------------------------------------------------------------------- #
    #                            different init function                           #
    # ---------------------------------------------------------------------------- #

    def init_faded_kits(self):
        
        for inter_id in self.rabbit.faded_offspring:
            inter_rabbit = self.rabbit.fetch_rabbit(inter_id)
            self.init_kits(inter_id, inter_rabbit)

    def init_faded_siblings(self):
      
        for inter_id in self.get_blood_parents() + self.rabbit.adoptive_parents:
            inter_rabbit = self.rabbit.fetch_rabbit(inter_id)
            for inter_sibling_id in inter_rabbit.faded_offspring:
                inter_sibling = self.rabbit.fetch_rabbit(inter_sibling_id)
                self.init_siblings(inter_sibling_id, inter_sibling)
             
    def init_faded_parents_siblings(self):
        
        for inter_id in self.get_blood_parents() + self.rabbit.adoptive_parents:
            inter_parent = self.rabbit.fetch_rabbit(inter_id)
            for inter_grand_id in self.get_blood_parents(inter_parent) + inter_parent.adoptive_parents:
                inter_grand = self.rabbit.fetch_rabbit(inter_grand_id)
                for inter_parent_sibling_id in inter_grand.faded_offspring:
                    inter_parent_sibling = self.rabbit.fetch_rabbit(inter_parent_sibling_id)
                    self.init_parents_siblings(inter_parent_sibling_id, inter_parent_sibling)
    
    def init_faded_grandkits(self):
        """This must occur after all kits, faded and otherwise, have been gathered. """
        
        for inter_id in self.get_children():
            inter_rabbit = self.rabbit.fetch_rabbit(inter_id)
            for inter_grandkit_id in inter_rabbit.faded_offspring:
                inter_grandkit = self.rabbit.fetch_rabbit(inter_grandkit_id)
                self.init_grand_kits(inter_grandkit_id, inter_grandkit)
        
    def init_faded_cousins(self):
        """This must occur after all parent's siblings, faded and otherwise, have been gathered."""
        
        for inter_id in self.get_parents_siblings():
            inter_rabbit = self.rabbit.fetch_rabbit(inter_id)
            for inter_cousin_id in inter_rabbit.faded_offspring:
                inter_cousin = self.rabbit.fetch_rabbit(inter_cousin_id)
                self.init_cousins(inter_cousin_id, inter_cousin)
            
        
        
    def init_parents(self):
        """Initial the class, with the focus of the parent relation."""
        # by blood
        current_parent_ids = self.get_blood_parents()
        for relevant_id in current_parent_ids:
            relevant_rabbit = self.rabbit.fetch_rabbit(relevant_id)
            if not relevant_rabbit:
                continue
            self.parents[relevant_id] = {
                "type": RelationType.BLOOD,
                "additional": []
            }
            self.all_involved.append(relevant_id)
            self.all_but_cousins.append(relevant_id)

        # adoptive
        current_parent_ids = self.get_no_blood_parents()
        for relevant_id in current_parent_ids:
            # if the rabbit is already a parent, continue
            if relevant_id in self.parents.keys():
                continue
            relevant_rabbit =self.rabbit.fetch_rabbit(relevant_id)
            self.parents[relevant_id] = {
                "type": RelationType.ADOPTIVE,
                "additional": []
            }
            self.all_involved.append(relevant_id)
            self.all_but_cousins.append(relevant_id)

    def init_mates(self):
        """Initial the class, with the focus of the mates relation."""
        for relevant_id in self.rabbit.mate:
            mate_rel = RelationType.NOT_BLOOD if relevant_id not in self.all_involved else RelationType.RELATED
            self.mates[relevant_id] = {
                "type": mate_rel,
                "additional": ["current mate"]
            }
            self.other_mates.append(relevant_id)

        for relevant_id in self.rabbit.previous_mates:
            mate_rel = RelationType.NOT_BLOOD if relevant_id not in self.all_involved else RelationType.RELATED
            self.mates[relevant_id] = {
                "type": mate_rel,
                "additional": ["previous mate"]
            }
            self.other_mates.append(relevant_id)

    def init_grand_parents(self):
        """Initial the class, with the focus of the grand parent relation."""
        for parent_id, value in self.parents.items():
            parent_rabbit = self.rabbit.fetch_rabbit(parent_id)
            grandparents = self.get_parents(parent_rabbit)
            for grand_id in grandparents:
                grand_type = RelationType.BLOOD if value["type"] == RelationType.BLOOD else RelationType.NOT_BLOOD
                if grand_id not in self.grand_parents:
                    self.grand_parents[grand_id] = {
                        "type": grand_type,
                        "additional": []
                    }
                    self.all_involved.append(grand_id)
                    self.all_but_cousins.append(grand_id)
                self.grand_parents[grand_id]["additional"].append(f"parent of {str(parent_rabbit.name)}")

    def init_kits(self, inter_id, inter_rabbit):
        """Initial the class, with the focus of the kits relation."""
        # kits - blood
        inter_blood_parents = self.get_blood_parents(inter_rabbit)
        if self.rabbit.ID in inter_blood_parents:
            self.kits[inter_id] = {
                "type": RelationType.BLOOD,
                "additional": []
            }
            self.all_involved.append(inter_id)
            self.all_but_cousins.append(inter_id)
            if len(inter_blood_parents) > 1:
                inter_blood_parents.remove(self.rabbit.ID)
                other_id = inter_blood_parents.pop()
                other_rabbit = self.rabbit.fetch_rabbit(other_id)
                self.kits[inter_id]["additional"].append(f"second parent: {str(other_rabbit.name)}")

        # kit - adoptive
        if self.rabbit.ID in inter_rabbit.adoptive_parents:
            self.kits[inter_id] = {
                "type": RelationType.ADOPTIVE,
                "additional": []
            }
            self.all_involved.append(inter_id)
            self.all_but_cousins.append(inter_id)
            if len(inter_blood_parents) > 0:
                name = []
                for blood_parent_id in inter_blood_parents:
                    blood_parent_rabbit = self.rabbit.fetch_rabbit(blood_parent_id)
                    if blood_parent_rabbit is None:
                        print(f"ERROR: the blood_parent of {str(inter_rabbit.name)}")
                    else:
                        name.append(blood_parent_rabbit.name)
                if len(name) > 0 and len(name) < 2:
                    self.kits[inter_id]["additional"].append(f"blood parent: {name[0]}")
                elif len(name) > 0 and len(name) < 3:
                    self.kits[inter_id]["additional"].append(f"blood parent: {name[0]}, {name[1]}")

        # check for mates
        if inter_id in self.kits:
            for mate_id in inter_rabbit.mate:
                self.kits_mates[mate_id] = {
                    "type": RelationType.NOT_BLOOD if mate_id not in self.all_involved else RelationType.RELATED,
                    "additional": [f"mate of {str(inter_rabbit.name)}"]
                }

    def init_siblings(self, inter_id, inter_rabbit):
        """Initial the class, with the focus of the siblings relation."""
        # blood / half-blood
        current_parent_ids = self.get_blood_parents()
        inter_parent_ids = self.get_blood_parents(inter_rabbit)
        blood_parent_overlap = set(current_parent_ids) & set(inter_parent_ids)

        # adopt
        adoptive_overlap1 = set(current_parent_ids) & set(inter_rabbit.adoptive_parents)
        adoptive_overlap2 = set(self.rabbit.adoptive_parents) & set(inter_parent_ids)
        adoptive_overlap3 = set(self.rabbit.adoptive_parents) & set(inter_rabbit.adoptive_parents)

        siblings = False
        rel_type = RelationType.BLOOD
        additional_info = []
        if len(blood_parent_overlap) == 2:
            siblings = True
            if inter_rabbit.months + inter_rabbit.dead_for == self.rabbit.months + self.rabbit.dead_for:
                additional_info.append("litter mates")
        elif len(blood_parent_overlap) == 1 and len(inter_parent_ids) == 1 and len(current_parent_ids) == 1:
            siblings = True
            if inter_rabbit.months + inter_rabbit.dead_for == self.rabbit.months + self.rabbit.dead_for:
                additional_info.append("litter mates")
        elif len(blood_parent_overlap) == 1 and (len(inter_parent_ids) > 1 or len(current_parent_ids) > 1):
            siblings = True
            rel_type = RelationType.HALF_BLOOD
        elif len(adoptive_overlap1) > 0 or len(adoptive_overlap2) > 0 or len(adoptive_overlap3) > 0:
            siblings = True
            rel_type = RelationType.ADOPTIVE

        if siblings:
            self.siblings[inter_id] = {
                "type": rel_type,
                "additional": additional_info
            }
            self.all_involved.append(inter_id)
            self.all_but_cousins.append(inter_id)

            for mate_id in inter_rabbit.mate:
                mate_rel = RelationType.NOT_BLOOD if mate_id not in self.all_involved else RelationType.RELATED
                self.siblings_mates[mate_id] = {
                    "type": mate_rel,
                    "additional": [f"mate of {str(inter_rabbit.name)}"]
                }
                self.other_mates.append(mate_id)

            # iterate over all rabbits, to get the children of the sibling
            for _c in self.rabbit.all_rabbits.values():
                _c_parents = self.get_parents(_c)
                _c_adoptive = self.get_no_blood_parents(_c)
                if inter_id in _c_parents:
                    parents_rabbits = [self.rabbit.fetch_rabbit(c_id) for c_id in _c_parents]
                    parent_rabbits_names = [str(c.name) for c in parents_rabbits]
                    kit_rel_type = RelationType.BLOOD if rel_type in BLOOD_RELATIVE_TYPES else RelationType.NOT_BLOOD
                    if inter_id in _c_adoptive:
                        kit_rel_type = RelationType.ADOPTIVE

                    add_info = ""
                    if len(parent_rabbits_names) > 0:
                        add_info = f"child of " + ", ".join(parent_rabbits_names)
                    self.siblings_kits[_c.ID] = {
                        "type": kit_rel_type,
                        "additional": [add_info]
                    }
                    self.all_involved.append(_c.ID)
                    self.all_but_cousins.append(_c.ID)

    def init_parents_siblings(self, inter_id, inter_rabbit):
        """Initial the class, with the focus of the parents siblings relation."""
        inter_parent_ids = self.get_parents(inter_rabbit)
        for inter_parent_id in inter_parent_ids:
            # check if the parent of the inter rabbit is the grand parent of the relevant rabbit
            if inter_parent_id in self.grand_parents.keys() and inter_id not in self.parents.keys():
                # the inter rabbit is an uncle/aunt of the current rabbit
                # only create a new entry if there is no entry for this rabbit - should no be but safety check
                if inter_id not in self.parents_siblings:
                    # get the relation type of the grandparent to assume how they are related
                    rel_type = RelationType.BLOOD

                    # create new entity
                    self.parents_siblings[inter_id] = {
                        "type": rel_type,
                        "additional": []
                    }
                    self.all_involved.append(inter_id)
                    self.all_but_cousins.append(inter_id)

                grand_parent_rabbit = self.rabbit.fetch_rabbit(inter_parent_id)
                if len(self.parents_siblings[inter_id]["additional"]) > 0:
                    add_info = self.parents_siblings[inter_id]["additional"][0]
                    self.parents_siblings[inter_id]["additional"][0] = add_info + ", " + str(grand_parent_rabbit.name)
                else:
                    self.parents_siblings[inter_id]["additional"].append(f"child of {str(grand_parent_rabbit.name)}")

    def init_cousins(self, inter_id, inter_rabbit):
        """Initial the class, with the focus of the cousin relation."""
        # the parent siblings already set
        # so it is only needed to check if the inter rabbit has a parent which is also in the parents_siblings dict
        inter_parent_ids = self.get_parents(inter_rabbit)
        parents_rabbits = [self.rabbit.fetch_rabbit(c_id) for c_id in inter_parent_ids]
        parent_rabbits_names = [str(c.name) for c in parents_rabbits]

        for inter_parent_id in inter_parent_ids:
            if inter_parent_id in self.parents_siblings.keys():
                rel_type = RelationType.BLOOD 
                if self.parents_siblings[inter_parent_id]["type"] not in BLOOD_RELATIVE_TYPES:
                    rel_type = RelationType.NOT_BLOOD
                add_info = ""
                if len(parent_rabbits_names) > 0:
                    add_info = f"child of " + ", ".join(parent_rabbits_names)
                        
                self.cousins[inter_id] = {
                    "type": rel_type,
                    "additional": [add_info]
                }
                self.all_involved.append(inter_id)

    def init_grand_kits(self, inter_id, inter_rabbit):
        """Initial the class, with the focus of the grand kits relation."""
        # the kits of this rabbit are already set
        # so it we only need to check if the inter rabbit has a parent which is in the kits dict
        inter_parent_ids = self.get_parents(inter_rabbit)
        parents_rabbits = [self.rabbit.fetch_rabbit(c_id) for c_id in inter_parent_ids]
        parent_rabbits_names = [str(c.name) for c in parents_rabbits if c]

        add_info = ""
        if len(parent_rabbits_names) > 0:
            add_info = f"child of " + ", ".join(parent_rabbits_names)

        for inter_parent_id in inter_parent_ids:
            if inter_parent_id in self.kits.keys():
                rel_type = RelationType.BLOOD if self.kits[inter_parent_id]["type"] in BLOOD_RELATIVE_TYPES else RelationType.NOT_BLOOD

                if inter_id not in self.grand_kits:
                    self.grand_kits[inter_id] = {
                        "type": rel_type,
                        "additional": [add_info]
                    }
                    self.all_but_cousins.append(inter_rabbit)
                    self.all_involved.append(inter_id)
                

    # ---------------------------------------------------------------------------- #
    #                             all getter functions                             #
    # ---------------------------------------------------------------------------- #

    def get_blood_relatives(self, dict):
        """Returns the keys (ids) of the dictionary entries with a blood relation."""
        return [key for key, value in dict.items() if value["type"] in BLOOD_RELATIVE_TYPES]

    def get_no_blood_relatives(self, dict):
        """Returns the keys (ids) of the dictionary entries without a blood relation."""
        return [key for key, value in dict.items() if value["type"] not in BLOOD_RELATIVE_TYPES]

    # ---------------------------------------------------------------------------- #
    #                                    parents                                   #
    # ---------------------------------------------------------------------------- #

    def get_blood_parents(self, rabbit = None) -> list:
        """Returns a list of id's which are the blood parents of the current rabbit."""
        relevant_rabbit = self.rabbit
        if rabbit:
            relevant_rabbit = rabbit
        if relevant_rabbit.parent1:
            if relevant_rabbit.parent2:
                return [relevant_rabbit.parent1, relevant_rabbit.parent2]
            return [relevant_rabbit.parent1]
        return []

    def get_no_blood_parents(self, rabbit = None) -> list:
        """Returns a list of id's which are adoptive parents of the current rabbit."""
        relevant_rabbit = rabbit if rabbit else self.rabbit
        return relevant_rabbit.adoptive_parents

    def get_parents(self, rabbit = None) -> list:
        """Returns a list of id's which are parents to the rabbit, according to the inheritance hierarchy."""
        relevant_rabbit = self.rabbit
        if rabbit:
            relevant_rabbit = rabbit
        blood_parents = self.get_blood_parents(relevant_rabbit)
        no_blood_parents = self.get_no_blood_parents(relevant_rabbit)
        return blood_parents + no_blood_parents

    # ---------------------------------------------------------------------------- #
    #                                     kits                                     #
    # ---------------------------------------------------------------------------- #

    def get_blood_kits(self) -> list:
        """Returns a list of blood related kits id's."""
        return self.get_blood_relatives(self.kits)

    def get_not_blood_kits(self) -> list:
        """Returns a list of id's of kits, which are not related by blood to the rabbit."""
        return self.get_no_blood_relatives(self.kits)

    def get_children(self) -> list:
        """Returns a list of id's which are kits to the rabbit, according to the inheritance hierarchy."""
        return self.get_blood_relatives(self.kits) + self.get_no_blood_relatives(self.kits)

    # ---------------------------------------------------------------------------- #
    #                                   siblings                                   #
    # ---------------------------------------------------------------------------- #

    def get_blood_siblings(self) -> list:
        """Returns a list of id's of blood related siblings."""
        return self.get_blood_relatives(self.siblings)

    def get_no_blood_siblings(self) -> list:
        """Returns a list of id's of siblings, which are not directly related to the rabbit."""
        return self.get_no_blood_relatives(self.siblings)

    def get_siblings(self) -> list:
        """Returns a list of id's which are siblings to the rabbit, according to the inheritance hierarchy."""
        return self.get_blood_relatives(self.siblings) + self.get_no_blood_relatives(self.siblings)

    # ---------------------------------------------------------------------------- #
    #                                parents_siblings                               #
    # ---------------------------------------------------------------------------- #

    def get_blood_parents_siblings(self) -> list:
        """Returns a list of blood related parents_siblings id's."""
        return self.get_blood_relatives(self.parents_siblings)

    def get_not_blood_parents_siblings(self) -> list:
        """Returns a list of id's of parents_siblings, which are not related by blood to the rabbit."""
        return self.get_no_blood_relatives(self.parents_siblings)

    def get_parents_siblings(self) -> list:
        """Returns a list of id's which are parents_siblings to the rabbit, according to the inheritance hierarchy."""
        return self.get_blood_relatives(self.parents_siblings) + self.get_no_blood_relatives(self.parents_siblings)

    # ---------------------------------------------------------------------------- #
    #                                    cousins                                   #
    # ---------------------------------------------------------------------------- #

    def get_blood_cousins(self) -> list:
        """Returns a list of id's of blood related cousins."""
        return self.get_blood_relatives(self.cousins)

    def get_no_blood_cousins(self) -> list:
        """Returns a list of id's of cousins, which are not directly related to the rabbit."""
        return self.get_no_blood_relatives(self.cousins)

    def get_cousins(self) -> list:
        """Returns a list of id's which are cousins to the rabbit, according to the inheritance hierarchy."""
        return self.get_blood_relatives(self.cousins) + self.get_no_blood_relatives(self.cousins)

    # ---------------------------------------------------------------------------- #
    #                                 grand_parents                                #
    # ---------------------------------------------------------------------------- #

    def get_blood_grand_parents(self) -> list:
        """Returns a list of blood related grand_parents id's."""
        return self.get_blood_relatives(self.grand_parents)

    def get_not_blood_grand_parents(self) -> list:
        """Returns a list of id's of grand_parents, which are not related by blood to the rabbit."""
        return self.get_no_blood_relatives(self.grand_parents)

    def get_grand_parents(self) -> list:
        """Returns a list of id's which are grand_parents to the rabbit, according to the inheritance hierarchy."""
        return self.get_blood_relatives(self.grand_parents) + self.get_no_blood_relatives(self.grand_parents)

    # ---------------------------------------------------------------------------- #
    #                                  grand_kits                                  #
    # ---------------------------------------------------------------------------- #

    def get_blood_grand_kits(self) -> list:
        """Returns a list of id's of blood related grand_kits."""
        return self.get_blood_relatives(self.grand_kits)

    def get_no_blood_grand_kits(self) -> list:
        """Returns a list of id's of grand_kits, which are not directly related to the rabbit."""
        return self.get_no_blood_relatives(self.grand_kits)

    def get_grand_kits(self) -> list:
        """Returns a list of id's which are grand_kits to the rabbit, according to the inheritance hierarchy."""
        return self.get_blood_relatives(self.grand_kits) + self.get_no_blood_relatives(self.grand_kits)


    # ---------------------------------------------------------------------------- #
    #                                 other related                                #
    # ---------------------------------------------------------------------------- #

    def get_kits_mates(self) -> list:
        """Returns a list of id's which are mates of a kit, according to the inheritance hierarchy."""
        return [key for key in self.kits_mates.keys()]

    def get_siblings_mates(self) -> list:
        """Returns a list of id's which are mates of a sibling, according to the inheritance hierarchy."""
        return [key for key in self.siblings_mates.keys()]

    def get_siblings_kits(self) -> list:
        """Returns a list of id's which are kits of a sibling, according to the inheritance hierarchy."""
        return [key for key in self.siblings_kits.keys()]

    def get_mates(self) -> list:
        """Returns a list of id's which are kits of a sibling, according to the inheritance hierarchy."""
        return [key for key in self.mates.keys()]