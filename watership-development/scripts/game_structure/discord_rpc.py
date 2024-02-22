"""
This file is used to connect to Discord's Rich Presence API.
This allows the game to show up on your Discord profile.

Discord RPC is not required for the game to run.
If you do not have the pypresence module installed,
this file will not be used, and the game will run as normal.
"""
from time import time
from scripts.game_structure.game_essentials import game
import threading
import asyncio

status_dict = {
    "start screen": "At the start screen",
    "make warren screen": "Making a warren",
    "mediation screen": "Mediating a dispute",
    "patrol screen": "On a patrol",
    "profile screen": "Viewing a rabbit's profile",
    "ceremony screen": "Holding a ceremony",
    "inle screen": "Viewing Inlé",
    "lightless screen": "Viewing the lightless lands",
    "med den screen": "In the healing den",
    }

class _DiscordRPC(threading.Thread):
    def __init__(self, client_id: str, daemon: bool):
        super().__init__(daemon=daemon)
        self._rpc = None
        self._client_id = client_id
        self._connected = False
        self._start_time = round(time()*1000)
        self._rpc_supported = False
        self._event_loop = asyncio.new_event_loop()

        self.start_rpc = threading.Event()
        self.update_rpc = threading.Event()
        self.close_rpc = threading.Event()
            
    def run(self):
        self.start_rpc.wait()
        self.get_rpc()
        self.connect()
        while not self.close_rpc.is_set():
            self.update_rpc.wait()
            self.update()
        self.close()

    def get_rpc(self):
        # Check if pypresence is available.
        if not game.settings["discord"]:
            return
        try:
            # raise ImportError # uncomment this line to disable rpc without uninstalling pypresence
            from pypresence import Presence, DiscordNotFound
            print("Discord RPC is supported")
        except ImportError:
            print("Pypresence not installed, Discord RPC isn't supported.")
            print("To enable rpc, run 'pip install pypresence' in your terminal.")
            return
        # Check if Discord is running.
        try:
            self._rpc = Presence(client_id=self._client_id,
                                 loop=self._event_loop)
            print("Discord found!")
        except DiscordNotFound:
            print("Discord not running.")
            return
        # Try to connect.
        try:
            self._rpc_supported = True
            self.connect()
            print("Connected to discord!")
        except ConnectionError as e:
            print(f"Failed to connect to Discord: {e}")

    def connect(self):
        if self._rpc_supported:
            try:
                self._rpc.connect()
            except BaseException as e:
                self._rpc_supported = False
                print(f"Failed to connect to Discord: {e}")
                return
            self._connected = True
            self.update()

    def update(self):
        if self._connected:
            try:
                state_text = status_dict[game.switches['cur_screen']]
            except KeyError:
                state_text = "Leading the warren"

            try:
                img_str = f"{game.warren.biome}_{game.warren.current_season.replace('-', '')}_{game.warren.camp_bg}_{'dark' if game.settings['dark mode'] else 'light'}"
                img_text = game.warren.biome
            except AttributeError:
                print("Failed to get image string, game may not be fully loaded yet. Dont worry, it will fix itself. Hopefully.")
                img_str = "discord" # fallback incase the game isn't loaded yet
                img_text = "watership!!"
            
            # Example: beach_greenleaf_camp1_dark

            warren_name = 'Loading...'
            rabbits_amount = 0
            if game.warren:
                warren_name =  f"{game.warren.name}"
                rabbits_amount = len(game.warren.warren_rabbits)
                warren_age = game.warren.age
            else:
                warren_name = 'Loading...'
                rabbits_amount = 0
                warren_age = 0
            try:
                self._rpc.update(
                    state=state_text,
                    details=f"Managing {warren_name} for {warren_age} months" ,
                    large_image=img_str.lower(),
                    large_text=img_text,
                    small_image="discord",
                    small_text=f"Managing {rabbits_amount} rabbits",
                    start=self._start_time,
                    buttons=[{"label": "Join The ClanGen Server", "url": "https://discord.gg/clangen"}],
                )
            except BaseException: # pylint: disable=broad-except
                print("Discord rpc had issue updating, disabling...")
                self._rpc_supported = False
                self._connected = False
                self._rpc = None
        self.update_rpc.clear()

    def close(self):
        if self._connected:
            self._rpc.close()
            self._connected = False
            
