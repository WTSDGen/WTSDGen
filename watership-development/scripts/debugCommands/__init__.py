from scripts.debugCommands.command import Command
from scripts.debugCommands.help import HelpCommand
from scripts.debugCommands.settings import ToggleCommand, SetCommand, GetCommand
from scripts.debugCommands.eval import EvalCommand, UnderstandRisksCommand
from scripts.debugCommands.clear import ClearCommand
from scripts.debugCommands.fps import FpsCommand
from scripts.debugCommands.rabbit import RabbitsCommand
from typing import List

commandList: List[Command] = [
    ToggleCommand(),
    SetCommand(),
    GetCommand(),
    EvalCommand(),
    UnderstandRisksCommand(),
    ClearCommand(),
    FpsCommand(),
    RabbitsCommand()
]

helpCommand = HelpCommand(commandList)
commandList.append(helpCommand)
