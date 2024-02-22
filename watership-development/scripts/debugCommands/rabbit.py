from typing import List

from scripts.debugCommands.command import Command

from scripts.debugCommands.utils import add_output_line_to_log

from scripts.game_structure.game_essentials import game
from scripts.rabbit.rabbits import Rabbit

class addRabbitCommand(Command):
    name = "add"
    description = "Add a rabbit"
    aliases = ["a"]

    def callback(self, args: List[str]):
        rabbit = Rabbit()
        game.clan.add_rabbit(rabbit)
        add_output_line_to_log(f"Added {rabbit.name} with ID {rabbit.ID}")

class removeRabbitCommand(Command):
    name = "remove"
    description = "Remove a rabbit"
    aliases = ["r"]
    usage = "<rabbit name|id>"

    def callback(self, args: List[str]):
        if len(args) == 0:
            add_output_line_to_log("Please specify a rabbit name or ID")
            return
        for rabbit in Rabbit.all_rabbits_list:
            if str(rabbit.name).lower() == args[0].lower() or rabbit.ID == args[0]:
                game.clan.remove_rabbit(rabbit.ID)
                add_output_line_to_log(f"Removed {rabbit.name} with ID {rabbit.ID}")
                return
        add_output_line_to_log(f"Could not find rabbit with name or ID {args[0]}")

class listRabbitsCommand(Command):
    name = "list"
    description = "List all rabbits"
    aliases = ["l"]

    def callback(self, args: List[str]):
        for rabbit in Rabbit.all_rabbits_list:
            add_output_line_to_log(f"{rabbit.ID} - {rabbit.name}, {rabbit.status}, {rabbit.moons} moons old")

class ageRabbitsCommand(Command):
    name = "age"
    description = "Age a rabbit"
    aliases = ["a"]
    usage = "<rabbit name|id> [number]"

    def callback(self, args: List[str]):
        if len(args) == 0:
            add_output_line_to_log("Please specify a rabbit name or ID")
            return
        for rabbit in Rabbit.all_rabbits_list:
            if str(rabbit.name).lower() == args[0].lower() or rabbit.ID == args[0]:
                if len(args) == 1:
                    add_output_line_to_log(f"{rabbit.name} is {rabbit.moons} moons old")
                    return
                else:
                    if args[1].startswith("+"):
                        rabbit.moons += int(args[1][1:])
                    elif args[1].startswith("-"):
                        rabbit.moons -= int(args[1][1:])
                    else:
                        rabbit.moons = int(args[1])
                    add_output_line_to_log(f"{rabbit.name} is now {rabbit.moons} moons old")



class RabbitsCommand(Command):
    name = "rabbits"
    description = "Manage Rabbits"
    aliases = ["rabbit"]

    subCommands = [
        addRabbitCommand(),
        removeRabbitCommand(),
        listRabbitsCommand(),
        ageRabbitsCommand()
    ]

    def callback(self, args: List[str]):
        add_output_line_to_log("Please specify a subcommand")