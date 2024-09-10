import unrealsdk
from unrealsdk import *
from ..ModMenu import Hook

class _bl2helper(unrealsdk.BL2MOD):
    Name = "bl2helper"
    Description = "Provides functionality for my other mods."
    Author = "Majüs"
    Version = "0.1"
    Types = unrealsdk.ModTypes.Utility
    Status = "Enabled"
    SettingsInputs = {}

def GetPlayerActor() -> unrealsdk.UObject:
    return unrealsdk.GetEngine().GamePlayers[0].Actor

def AmIClientPlayer() -> bool:
    return unrealsdk.GetEngine().GetCurrentWorldInfo().NetMode == 3

def GetGameInfo() -> unrealsdk.UObject:
    return unrealsdk.GetEngine().GetCurrentWorldInfo().Game

def GetCurrentPlayerLevel() -> int:
    return GetPlayerActor().GetExpLevelLoadedFromSavedGame()

def GetMaxOverpowerLevel() -> int:
    return GetPlayerActor().GetMaximumPossibleOverpowerModifier()

def ShowNotification(message : str, owner : str):
    HudMovie = GetPlayerActor().GetHUDMovie()
    if HudMovie is None:
        return
    HudMovie.ClearTrainingText()
    HudMovie.AddTrainingText(message, owner, 4.0, (), "", False, 0, GetPlayerActor().PlayerReplicationInfo, True)

def GetWillowGlobals():
    return GetPlayerActor().GetWillowGlobals()

def GetLootList():
    return GetWillowGlobals().PickupList

@Hook("WillowGame.FrontendGFxMovie.OnTick")
def _MainMenuHook(self, caller: UObject, function: UFunction, params: FStruct) -> None:
    self.IsInMainMenu = True
    return True

@Hook("WillowGame.WillowHUD.CreateWeaponScopeMovie")
def _IngameHook(self, caller: UObject, function: UFunction, params: FStruct) -> None:
    self.IsInMainMenu = False
    return True

IsInMainMenu : bool = None
unrealsdk.RegisterMod(_bl2helper())