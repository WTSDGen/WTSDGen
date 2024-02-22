import os
import random
from math import floor
from .game_essentials import game
from ..rabbit.history import History
from ..rabbit.skills import RabbitSkills
from ..housekeeping.datadir import get_save_dir

import ujson

from re import sub
from scripts.rabbit.pelts import Pelt
from scripts.rabbit.rabbits import Rabbit, Personality, BACKSTORIES
from scripts.housekeeping.version import SAVE_VERSION_NUMBER
from scripts.utility import update_sprite, is_iterable
from random import choice
from scripts.rabbit_relations.inheritance import Inheritance

import logging
logger = logging.getLogger(__name__)

def load_rabbits():
    try:
        json_load()
    except FileNotFoundError:
        try:
            csv_load(Rabbit.all_rabbits)
        except FileNotFoundError as e:
            game.switches['error_message'] = 'Can\'t find warren_rabbits.json!'
            game.switches['traceback'] = e
            raise


def json_load():
    all_rabbits = []
    rabbit_data = None
    warrenname = game.switches['warren_list'][0]
    warren_rabbits_json_path = f'{get_save_dir()}/{warrenname}/warren_rabbits.json'
    with open(f"resources/dicts/conversion_dict.json", 'r') as read_file:
        convert = ujson.loads(read_file.read())
    try:
        with open(warren_rabbits_json_path, 'r') as read_file:
            rabbit_data = ujson.loads(read_file.read())
    except PermissionError as e:
        game.switches['error_message'] = f'Can\t open {warren_rabbits_json_path}!'
        game.switches['traceback'] = e
        raise
    except ujson.JSONDecodeError as e:
        game.switches['error_message'] = f'{warren_rabbits_json_path} is malformed!'
        game.switches['traceback'] = e
        raise

    old_tortie_patches = convert["old_tortie_patches"]

    # create new rabbit objects
    for i, rabbit in enumerate(rabbit_data):
        try:
            
            new_rabbit = Rabbit(ID=rabbit["ID"],
                        prefix=rabbit["name_prefix"],
                        specsuffix_hidden=(rabbit["specsuffix_hidden"] if 'specsuffix_hidden' in rabbit else False),
                        gender=rabbit["gender"],
                        status=rabbit["status"],
                        parent1=rabbit["parent1"],
                        parent2=rabbit["parent2"],
                        months=rabbit["months"],
                        eye_colour=rabbit["eye_colour"],
                        loading_rabbit=True)
            
            if rabbit["eye_colour"] == "BLUE2":
                rabbit["eye_colour"] = "COBALT"
            if rabbit["eye_colour"] in ["BLUEYELLOW", "BLUEGREEN"]:
                if rabbit["eye_colour"] == "BLUEYELLOW":
                    rabbit["eye_colour2"] = "YELLOW"
                elif rabbit["eye_colour"] == "BLUEGREEN":
                    rabbit["eye_colour2"] = "GREEN"
                rabbit["eye_colour"] = "BLUE"
            if "eye_colour2" in rabbit:
                if rabbit["eye_colour2"] == "BLUE2":
                    rabbit["eye_colour2"] = "COBALT"
                        
            new_rabbit.pelt = Pelt(
                name=rabbit["pelt_name"],
                length=rabbit["pelt_length"],
                colour=rabbit["pelt_color"],
                eye_color=rabbit["eye_colour"],
                eye_colour2=rabbit["eye_colour2"] if "eye_colour2" in rabbit else None,
                paralyzed=rabbit["paralyzed"],
                kitten_sprite=rabbit["sprite_kitten"] if "sprite_kitten" in rabbit else rabbit["spirit_kitten"],
                adol_sprite=rabbit["sprite_adolescent"] if "sprite_adolescent" in rabbit else rabbit["spirit_adolescent"],
                adult_sprite=rabbit["sprite_adult"] if "sprite_adult" in rabbit else rabbit["spirit_adult"],
                senior_sprite=rabbit["sprite_senior"] if "sprite_senior" in rabbit else rabbit["spirit_elder"],
                para_adult_sprite=rabbit["sprite_para_adult"] if "sprite_para_adult" in rabbit else None,
                reverse=rabbit["reverse"],
                vitiligo=rabbit["vitiligo"] if "vitiligo" in rabbit else None,
                points=rabbit["points"] if "points" in rabbit else None,
                white_patches_tint=rabbit["white_patches_tint"] if "white_patches_tint" in rabbit else "offwhite",
                white_patches=rabbit["white_patches"],
                tortiebase=rabbit["tortie_base"],
                tortiecolour=rabbit["tortie_color"],
                tortiepattern=rabbit["tortie_pattern"],
                pattern=rabbit["pattern"],
                skin=rabbit["skin"],
                tint=rabbit["tint"] if "tint" in rabbit else "none",
                scars=rabbit["scars"] if "scars" in rabbit else [],
                accessory=rabbit["accessory"],
                opacity=rabbit["opacity"] if "opacity" in rabbit else 100
            )
            
            # Runs a bunch of appearence-related convertion of old stuff. 
            new_rabbit.pelt.check_and_convert(convert)
            
             # converting old specialty saves into new scar parameter
            if "specialty" in rabbit or "specialty2" in rabbit:
                if rabbit["specialty"] is not None:
                    new_rabbit.pelt.scars.append(rabbit["specialty"])
                if rabbit["specialty2"] is not None:
                    new_rabbit.pelt.scars.append(rabbit["specialty2"])
            
            new_rabbit.adoptive_parents = rabbit["adoptive_parents"] if "adoptive_parents" in rabbit else []
            
            new_rabbit.genderalign = rabbit["gender_align"]
            new_rabbit.backstory = rabbit["backstory"] if "backstory" in rabbit else None
            if new_rabbit.backstory in BACKSTORIES["conversion"]:
                new_rabbit.backstory = BACKSTORIES["conversion"][new_rabbit.backstory]
            new_rabbit.birth_cooldown = rabbit["birth_cooldown"] if "birth_cooldown" in rabbit else 0
            new_rabbit.months = rabbit["months"]
            
            
            if "facets" in rabbit:
                facets = [int(i) for i in rabbit["facets"].split(",")]
                new_rabbit.personality = Personality(trait=rabbit["trait"], kitten_trait=new_rabbit.age in ["newborn", "kitten"],
                                              lawful=facets[0], social=facets[1], 
                                              aggress=facets[2], stable=facets[3])
            else:
                new_rabbit.personality = Personality(trait=rabbit["trait"], kitten_trait=new_rabbit.age in ["newborn", "kitten"])
                
                
            new_rabbit.rusasirah = rabbit["rusasirah"]
            new_rabbit.former_rusasirah = rabbit["former_rusasirah"] if "former_rusasirah" in rabbit else []
            new_rabbit.patrol_with_rusasirah = rabbit["patrol_with_rusasirah"] if "patrol_with_rusasirah" in rabbit else 0
            new_rabbit.no_kittens = rabbit["no_kittens"]
            new_rabbit.no_mates = rabbit["no_mates"] if "no_mates" in rabbit else False
            new_rabbit.no_retire = rabbit["no_retire"] if "no_retire" in rabbit else False
            new_rabbit.exiled = rabbit["exiled"]

            if "skill_dict" in rabbit:
                new_rabbit.skills = RabbitSkills(rabbit["skill_dict"])
            elif "skill" in rabbit:
                if new_rabbit.backstory is None:
                    if "skill" == 'formerly a hlessi':
                        backstory = choice(['hlessi1', 'hlessi2', 'rogue1', 'rogue2'])
                        new_rabbit.backstory = backstory
                    elif "skill" == 'formerly a pet':
                        backstory = choice(['pet1', 'pet2'])
                        new_rabbit.backstory = backstory
                    else:
                        new_rabbit.backstory = 'warrenborn'
                new_rabbit.skills = RabbitSkills.get_skills_from_old(rabbit["skill"], new_rabbit.status, new_rabbit.months)

            new_rabbit.mate = rabbit["mate"] if type(rabbit["mate"]) is list else [rabbit["mate"]]
            if None in new_rabbit.mate:
                new_rabbit.mate = [i for i in new_rabbit.mate if i is not None]
            new_rabbit.previous_mates = rabbit["previous_mates"] if "previous_mates" in rabbit else []
            new_rabbit.dead = rabbit["dead"]
            new_rabbit.dead_for = rabbit["dead_months"]
            new_rabbit.experience = rabbit["experience"]
            new_rabbit.rusasi = rabbit["current_rusasi"]
            new_rabbit.former_rusasi = rabbit["former_rusasi"]
            new_rabbit.df = rabbit["df"] if "df" in rabbit else False

            new_rabbit.outside = rabbit["outside"] if "outside" in rabbit else False
            new_rabbit.faded_offspring = rabbit["faded_offspring"] if "faded_offspring" in rabbit else []
            new_rabbit.prevent_fading = rabbit["prevent_fading"] if "prevent_fading" in rabbit else False
            new_rabbit.favourite = rabbit["favourite"] if "favourite" in rabbit else False
            
            if "died_by" in rabbit or "scar_event" in rabbit or "rusasirah_influence" in rabbit:
                new_rabbit.convert_history(
                    rabbit["died_by"] if "died_by" in rabbit else [],
                    rabbit["scar_event"] if "scar_event" in rabbit else []
                )

            # new_rabbit.pronouns = rabbit["pronouns"] if "pronouns" in rabbit else [new_rabbit.default_pronouns[0].copy()]
            all_rabbits.append(new_rabbit)

        except KeyError as e:
            if "ID" in rabbit:
                key = f" ID #{rabbit['ID']} "
            else:
                key = f" at index {i} "
            game.switches['error_message'] = f'Rabbit{key}in warren_rabbits.json is missing {e}!'
            game.switches['traceback'] = e
            raise

    # replace rabbit ids with rabbit objects and add other needed variables
    for rabbit in all_rabbits:

        rabbit.load_conditions()

        # this is here to handle paralyzed rabbits in old saves
        if rabbit.pelt.paralyzed and "paralyzed" not in rabbit.permanent_condition:
            rabbit.get_permanent_condition("paralyzed")
        elif "paralyzed" in rabbit.permanent_condition and not rabbit.pelt.paralyzed:
            rabbit.pelt.paralyzed = True

        # load the relationships
        try:
            if not rabbit.dead:
                rabbit.load_relationship_of_rabbit()
                if rabbit.relationships is not None and len(rabbit.relationships) < 1:
                    rabbit.init_all_relationships()
            else:
                rabbit.relationships = {}
        except Exception as e:
            logger.exception(f'There was an error loading relationships for rabbit #{rabbit}.')
            game.switches['error_message'] = f'There was an error loading relationships for rabbit #{rabbit}.'
            game.switches['traceback'] = e
            raise
        
        
        rabbit.inheritance = Inheritance(rabbit)
        
        try:
            # initialization of thoughts
            rabbit.thoughts()
        except Exception as e:
            logger.exception(f'There was an error when thoughts for rabbit #{rabbit} are created.')
            game.switches['error_message'] = f'There was an error when thoughts for rabbit #{rabbit} are created.'
            game.switches['traceback'] = e
            raise

        # Save integrety checks
        if game.config["save_load"]["load_integrity_checks"]:
            save_check()


def csv_load(all_rabbits):
    if game.switches['warren_list'][0].strip() == '':
        rabbit_data = ''
    else:
        if os.path.exists(get_save_dir() + '/' + game.switches['warren_list'][0] +
                          'rabbits.csv'):
            with open(get_save_dir() + '/' + game.switches['warren_list'][0] + 'rabbits.csv',
                      'r') as read_file:
                rabbit_data = read_file.read()
        else:
            with open(get_save_dir() + '/' + game.switches['warren_list'][0] + 'rabbits.txt',
                      'r') as read_file:
                rabbit_data = read_file.read()
    if len(rabbit_data) > 0:
        rabbit_data = rabbit_data.replace('\t', ',')
        for i in rabbit_data.split('\n'):
            # CAT: ID(0) - prefix:suffix(1) - gender(2) - status(3) - age(4) - trait(5) - parent1(6) - parent2(7) - rusasirah(8)
            # PELT: pelt(9) - colour(10) - white(11) - length(12)
            # SPRITE: kitten(13) - rusasi(14) - warrior(15) - elder(16) - eye colour(17) - reverse(18)
            # - white patches(19) - pattern(20) - tortiebase(21) - tortiepattern(22) - tortiecolour(23) - skin(24) - skill(25) - NONE(26) - spec(27) - accessory(28) -
            # spec2(29) - months(30) - mate(31)
            # dead(32) - SPRITE:dead(33) - exp(34) - dead for _ months(35) - current rusasi(36)
            # (BOOLS, either TRUE OR FALSE) paralyzed(37) - no kittens(38) - exiled(39)
            # genderalign(40) - former rusasis list (41)[FORMER APPS SHOULD ALWAYS BE MOVED TO THE END]
            if i.strip() != '':
                attr = i.split(',')
                for x in range(len(attr)):
                    attr[x] = attr[x].strip()
                    if attr[x] in ['None', 'None ']:
                        attr[x] = None
                    elif attr[x].upper() == 'TRUE':
                        attr[x] = True
                    elif attr[x].upper() == 'FALSE':
                        attr[x] = False
                game.switches[
                    'error_message'] = '1There was an error loading rabbit # ' + str(
                        attr[0])
                the_pelt = Pelt(
                    colour=attr[2],
                    name = attr[11],
                    length=attr[9],
                    eye_color=attr[17]
                )
                game.switches[
                    'error_message'] = '2There was an error loading rabbit # ' + str(
                    attr[0])
                the_rabbit = Rabbit(ID=attr[0],
                              prefix=attr[1].split(':')[0],
                              gender=attr[2],
                              status=attr[3],
                              pelt=the_pelt,
                              parent1=attr[6],
                              parent2=attr[7],
                            )
                
                
                game.switches[
                    'error_message'] = '3There was an error loading rabbit # ' + str(
                    attr[0])
                the_rabbit.age, the_rabbit.rusasirah = attr[4], attr[8]
                game.switches[
                    'error_message'] = '4There was an error loading rabbit # ' + str(
                        attr[0])
                the_rabbit.pelt.rabbit_sprites['kitten'], the_rabbit.pelt.rabbit_sprites[
                    'adolescent'] = int(attr[13]), int(attr[14])
                game.switches[
                    'error_message'] = '5There was an error loading rabbit # ' + str(
                        attr[0])
                the_rabbit.pelt.rabbit_sprites['adult'], the_rabbit.pelt.rabbit_sprites[
                    'elder'] = int(attr[15]), int(attr[16])
                game.switches[
                    'error_message'] = '6There was an error loading rabbit # ' + str(
                        attr[0])
                the_rabbit.pelt.rabbit_sprites['young adult'], the_rabbit.pelt.rabbit_sprites[
                    'senior adult'] = int(attr[15]), int(attr[15])
                game.switches[
                    'error_message'] = '7There was an error loading rabbit # ' + str(
                        attr[0])
                the_rabbit.pelt.reverse, the_rabbit.pelt.white_patches, the_rabbit.pelt.pattern = attr[
                    18], attr[19], attr[20]
                game.switches[
                    'error_message'] = '8There was an error loading rabbit # ' + str(
                        attr[0])
                the_rabbit.pelt.tortiebase, the_rabbit.pelt.tortiepattern, the_rabbit.pelt.tortiecolour = attr[
                    21], attr[22], attr[23]
                game.switches[
                    'error_message'] = '9There was an error loading rabbit # ' + str(
                        attr[0])
                the_rabbit.trait, the_rabbit.pelt.skin, the_rabbit.specialty = attr[5], attr[
                    24], attr[27]
                game.switches[
                    'error_message'] = '10There was an error loading rabbit # ' + str(
                    attr[0])
                the_rabbit.skill = attr[25]
                if len(attr) > 28:
                    the_rabbit.pelt.accessory = attr[28]
                if len(attr) > 29:
                    the_rabbit.specialty2 = attr[29]
                else:
                    the_rabbit.specialty2 = None
                game.switches[
                    'error_message'] = '11There was an error loading rabbit # ' + str(
                    attr[0])
                if len(attr) > 34:
                    the_rabbit.experience = int(attr[34])
                    experiencelevels = [
                        'very low', 'low', 'slightly low', 'average',
                        'somewhat high', 'high', 'very high', 'master', 'max'
                    ]
                    the_rabbit.experience_level = experiencelevels[floor(
                        int(the_rabbit.experience) / 10)]
                else:
                    the_rabbit.experience = 0
                game.switches[
                    'error_message'] = '12There was an error loading rabbit # ' + str(
                    attr[0])
                if len(attr) > 30:
                    # Attributes that are to be added after the update
                    the_rabbit.months = int(attr[30])
                    if len(attr) >= 31:
                        # assigning mate to rabbit, if any
                        the_rabbit.mate = [attr[31]]
                    if len(attr) >= 32:
                        # Is the rabbit dead
                        the_rabbit.dead = attr[32]
                        the_rabbit.pelt.rabbit_sprites['dead'] = attr[33]
                game.switches[
                    'error_message'] = '13There was an error loading rabbit # ' + str(
                    attr[0])
                if len(attr) > 35:
                    the_rabbit.dead_for = int(attr[35])
                game.switches[
                    'error_message'] = '14There was an error loading rabbit # ' + str(
                    attr[0])
                if len(attr) > 36 and attr[36] is not None:
                    the_rabbit.rusasi = attr[36].split(';')
                game.switches[
                    'error_message'] = '15There was an error loading rabbit # ' + str(
                    attr[0])
                if len(attr) > 37:
                    the_rabbit.pelt.paralyzed = bool(attr[37])
                if len(attr) > 38:
                    the_rabbit.no_kittens = bool(attr[38])
                if len(attr) > 39:
                    the_rabbit.exiled = bool(attr[39])
                if len(attr) > 40:
                    the_rabbit.genderalign = attr[40]
                if len(attr
                       ) > 41 and attr[41] is not None:  # KEEP THIS AT THE END
                    the_rabbit.former_rusasis = attr[41].split(';')
        game.switches[
            'error_message'] = 'There was an error loading this warren\'s rusasirah, rusasis, relationships, or sprite info.'
        for inter_rabbit in all_rabbits.values():
            # Load the rusasirah and rusasis after all rabbits have been loaded
            game.switches[
                'error_message'] = 'There was an error loading this warren\'s rusasirah/rusasis. Last rabbit read was ' + str(
                inter_rabbit)
            inter_rabbit.rusasirah = Rabbit.all_rabbits.get(inter_rabbit.rusasirah)
            apps = []
            former_apps = []
            for app_id in inter_rabbit.rusasi:
                app = Rabbit.all_rabbits.get(app_id)
                # Make sure if rabbit isn't an rusasi, they're a former rusasi
                if 'rusasi' in app.status:
                    apps.append(app)
                else:
                    former_apps.append(app)
            for f_app_id in inter_rabbit.former_rusasis:
                f_app = Rabbit.all_rabbits.get(f_app_id)
                former_apps.append(f_app)
            inter_rabbit.rusasi = [a.ID for a in apps]  # Switch back to IDs. I don't want to risk breaking everything.
            inter_rabbit.former_rusasis = [a.ID for a in former_apps]
            if not inter_rabbit.dead:
                game.switches[
                    'error_message'] = 'There was an error loading this warren\'s relationships. Last rabbit read was ' + str(
                    inter_rabbit)
                inter_rabbit.load_relationship_of_rabbit()
            game.switches[
                'error_message'] = 'There was an error loading a rabbit\'s sprite info. Last rabbit read was ' + str(
                inter_rabbit)
            # update_sprite(inter_rabbit)
        # generate the relationship if some is missing
        if not the_rabbit.dead:
            game.switches[
                'error_message'] = 'There was an error when relationships where created.'
            for id in all_rabbits.keys():
                the_rabbit = all_rabbits.get(id)
                game.switches[
                    'error_message'] = f'There was an error when relationships for rabbit #{the_rabbit} are created.'
                if the_rabbit.relationships is not None and len(the_rabbit.relationships) < 1:
                    the_rabbit.create_all_relationships()
        game.switches['error_message'] = ''


def save_check():
    """Checks through loaded rabbits, checks and attempts to fix issues 
    NOT currently working. """
    return
    
    for rabbit in Rabbit.all_rabbits:
        rabbit_ob = Rabbit.all_rabbits[rabbit]

        # Not-mutural mate relations
        # if rabbit_ob.mate:
        #    _temp_ob = Rabbit.all_rabbits.get(rabbit_ob.mate)
        #    if _temp_ob:
        #        # Check if the mate's mate feild is set to none
        #        if not _temp_ob.mate:
        #            _temp_ob.mate = rabbit_ob.ID 
        #    else:
        #        # Invalid mate
        #        rabbit_ob.mate = None


def version_convert(version_info):
    """Does all save-conversion that require referencing the saved version number.
    This is a separate function, since the version info is stored in warren.json, but most conversion needs to be
    done on the rabbits. Warren data is loaded in after rabbits, however."""

    if version_info is None:
        return

    if version_info["version_name"] == SAVE_VERSION_NUMBER:
        # Save was made on current version
        return

    if version_info["version_name"] is None:
        version = 0
    else:
        version = version_info["version_name"]

    if version < 1:
        # Save was made before version number storage was implemented.
        # (ie, save file version 0)
        # This means the EXP must be adjusted. 
        for c in Rabbit.all_rabbits.values():
            c.experience = c.experience * 3.2
            
    if version < 2:
        for c in Rabbit.all_rabbits.values():
            for con in c.injuries:
                months_with = 0
                if "months_with" in c.injuries[con]:
                    months_with = c.injuries[con]["months_with"]
                    c.injuries[con].pop("months_with")
                c.injuries[con]["month_start"] = game.warren.age - months_with
        
            for con in c.illnesses:
                months_with = 0
                if "months_with" in c.illnesses[con]:
                    months_with = c.illnesses[con]["months_with"]
                    c.illnesses[con].pop("months_with")
                c.illnesses[con]["month_start"] = game.warren.age - months_with
                
            for con in c.permanent_condition:
                months_with = 0
                if "months_with" in c.permanent_condition[con]:
                    months_with = c.permanent_condition[con]["months_with"]
                    c.permanent_condition[con].pop("months_with")
                c.permanent_condition[con]["month_start"] = game.warren.age - months_with
            
    if version < 3 and game.warren.freshkill_pile:
        # freshkill start for older warrens
        add_prey = game.warren.freshkill_pile.amount_food_needed() * 2
        game.warren.freshkill_pile.add_freshkill(add_prey)