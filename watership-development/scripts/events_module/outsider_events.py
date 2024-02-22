import random

from scripts.rabbit.rabbits import Rabbit
from scripts.events_module.generate_events import GenerateEvents
from scripts.game_structure.game_essentials import game
from scripts.event_class import Single_Event


# ---------------------------------------------------------------------------- #
#                               New Rabbit Event Class                              #
# ---------------------------------------------------------------------------- #

class OutsiderEvents:
    """All events with a connection to outsiders."""

    @staticmethod
    def killing_outsiders(rabbit: Rabbit):
        # killing outside rabbits
        if rabbit.outside:
            if random.getrandbits(6) == 1 and not rabbit.dead:
                if rabbit.exiled:
                    text = f'Rumors reach your warren that the exiled {rabbit.name} has died recently.'
                elif rabbit.status in ['pet', 'hlessi', 'rogue', 'defector']:
                    text = f'Rumors reach your warren that the {rabbit.status} ' \
                           f'{rabbit.name} has died recently.'
                else:
                    rabbit.outside = False
                    text = f"Will the black rabbit find them, even so far away? {rabbit.name} isn't sure, " \
                           f"but as they drift away, they hope to see " \
                           f"familiar dark fur on the other side."
                
                rabbit.die()
                game.cur_events_list.append(
                    Single_Event(text, "birth_death", rabbit.ID))
                
    @staticmethod
    def lost_rabbit_become_outsider(rabbit: Rabbit):
        """ 
        this will be for lost rabbits becoming pets/hlessis/etc
        TODO: need to make a unique backstory for these rabbits so they still have thoughts related to their warren
        """
        if random.getrandbits(7) == 1 and not rabbit.dead:
            OutsiderEvents.become_pet(rabbit)

    @staticmethod
    def become_pet(rabbit: Rabbit):
        # TODO: Make backstory for all of these + for exiled rabbits
        rabbit.status = 'pet'

    @staticmethod
    def become_hlessi(rabbit: Rabbit):
        rabbit.status = 'hlessi'

    @staticmethod
    def become_rogue(rabbit: Rabbit):
        """Rabbits will probably only become rogues if they were exiled formerly"""
        rabbit.status = 'rogue'