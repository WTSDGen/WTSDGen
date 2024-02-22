from .Screens import Screens
from .StartScreen import StartScreen
from .PatrolScreen import PatrolScreen
from .AllegiancesScreen import AllegiancesScreen
from .CeremonyScreen import CeremonyScreen
from .ChooseAdoptiveParentScreen import ChooseAdoptiveParentScreen
from .ProfileScreen import ProfileScreen
from .RoleScreen import RoleScreen
from .SpriteInspectScreen import SpriteInspectScreen
from .MakeWarrenScreen import MakeWarrenScreen
from .MedDenScreen import MedDenScreen
from .RelationshipScreen import RelationshipScreen
from .SettingsScreen import SettingsScreen
from .SwitchWarrenScreen import SwitchWarrenScreen
from .WarrenScreen import WarrenScreen
from .ListScreen import ListScreen
from .EventsScreen import EventsScreen
from .ChooseMateScreen import ChooseMateScreen
from .ChooseRusasirahScreen import ChooseRusasirahScreen
from .FamilyTreeScreen import FamilyTreeScreen
from .OutsideWarrenScreen import OutsideWarrenScreen
from .MediationScreen import MediationScreen
from .WarrenSettingsScreen import WarrenSettingsScreen
from .FoodScreen import FoodScreen

# ---------------------------------------------------------------------------- #
#                                  UI RULES                                    #
# ---------------------------------------------------------------------------- #
"""
SCREEN: 700 height x 800 width

MARGINS: 25px on all sides
    ~Any new buttons or text MUST be within these margins.
    ~Buttons on the edge of the screen should butt up right against the margin. 
    (i.e. the <<Main Menu button is placed 25px x 25px on most screens) 
    
BUTTONS:
    ~Buttons are 30px in height. Width can be anything, though generally try to keep to even numbers.
    ~Square icons are 34px x 34px.
    ~Generally keep text at least 5px away from the right and left /straight/ (do not count the rounded ends) edge 
    of the button (this rule is sometimes broken. the goal is to be consistent across the entire screen or button type)
    ~Generally, the vertical gap between buttons should be 5px
"""

# SCREENS
screens = Screens()

# ---------------------------------------------------------------------------- #
#                                 rabbit_screens.py                               #
# ---------------------------------------------------------------------------- #

profile_screen = ProfileScreen('profile screen')
ceremony_screen = CeremonyScreen('ceremony screen')
role_screen = RoleScreen('role screen')
sprite_inspect_screen = SpriteInspectScreen("sprite inspect screen")


make_warren_screen = MakeWarrenScreen('make warren screen')


allegiances_screen = AllegiancesScreen('allegiances screen')
burrow_screen = WarrenScreen('burrow screen')
catlist_screen = ListScreen('list screen')
med_den_screen = MedDenScreen('med den screen')
freshkill_pile_screen = FoodScreen('food screen')


events_screen = EventsScreen('events screen')


settings_screen = SettingsScreen('settings screen')
clan_settings_screen = WarrenSettingsScreen('warren settings screen')
start_screen = StartScreen('start screen')
switch_warren_screen = SwitchWarrenScreen('switch warren screen')


patrol_screen = PatrolScreen('patrol screen')


choose_mate_screen = ChooseMateScreen('choose mate screen')
choose_rusasirah_screen = ChooseRusasirahScreen('choose rusasirah screen')
choose_adoptive_parent_screen = ChooseAdoptiveParentScreen('choose adoptive parent screen')
relationship_screen = RelationshipScreen('relationship screen')
view_children_screen = FamilyTreeScreen('see kittens screen')
mediation_screen = MediationScreen("mediation screen")


outside_warren_screen = OutsideWarrenScreen('other screen')
