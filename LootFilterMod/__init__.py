import unrealsdk
from .._bl2helper import bl2helper
from ..ModMenu import EnabledSaveType, Hook, SDKMod, Options, KeybindManager, Game, RegisterMod
from typing import List
from datetime import datetime


class TypeFilter(Options.Boolean):

    DefinedItemType: str

    def __init__(self, ItemType: str, ZippyFrameName: List[str], AdditionalDescription: str = ""):
        self.DefinedItemType = ItemType
        
        super().__init__(
            Caption = "Show "+self.DefinedItemType+"s",
            Description = "Toggles if ANY "+self.DefinedItemType+"s"+" are being shown. "+AdditionalDescription,
            StartingValue = True,
            Choices = ("Off", "On")
        )
        TypeFilterList.append(self)
        ItemTypesToZippyFrame[self.DefinedItemType] = ZippyFrameName

TypeFilterList : List[TypeFilter] = []
ItemTypesToZippyFrame = {}

class LootFilterMod(SDKMod):
    Name = "Loot Filter Mod"
    Description = "Ever wanted to get rid of all the non-shiny objects on your screen? This is the mod for you."
    Author = "Majüs"
    Version = "0.1"
    SaveEnabledState = EnabledSaveType.LoadWithSettings

    #Keybinds
    Keybinds: List[KeybindManager.Keybind] = [
        KeybindManager.Keybind(
            Name="Toggle Item Filter",
        ),
        KeybindManager.Keybind(
            Name="Clear Loot"
        )
    ]

    #Options
    FilterEnable: Options.Boolean
    RaritySpinner: Options.Spinner
    RaritySlider: Options.Slider
    LevelSlider: Options.Slider
    Nest_Advanced: Options.Nested
    Nest_TypeFilter: Options.Nested
    LoggingEnabled: Options.Boolean


    #Rarities
    LootRarities = {
        'White': 1,
        'Green': 2,
        'Blue': 3,
        'Purple': 4,
        'E-Tech': 6,
        'Legendary': 9,
        'Seraph/Pearl': 500,
        'Advanced': -1
    }

    #Player
    Player = bl2helper.GetPlayerActor()

    def __init__(self):
        super().__init__()

        #Options Init
        self.FilterEnable = Options.Boolean(
            Caption = "Enable Item Filter",
            Description = "Turns the item filter on or off.",
            StartingValue = True,
            Choices = ("Off", "On")
        )

        self.RaritySpinner = Options.Spinner(
            Caption = "Remove Items Below Rarity",
            Description = "Sets the rarity below items will be deleted.",
            StartingValue = list(self.LootRarities.keys())[0],
            Choices = [t for t in self.LootRarities.keys()],
        )

        self.LevelSlider = Options.Slider(
            Caption = "Remove Items Below Level",
            Description = "Also removes items of ANY rarity which are below the specified level. Each OP level counts as 1 more level. Level 0 means no loot will be deleted by this option.",
            StartingValue = 0,
            MinValue = 0,
            MaxValue = 90,
            Increment = 1
        )

        self.RaritySlider = Options.Slider(
            Caption = "Remove Items Below Rarity Level",
            Description = "Uses the set value as the filter for item rarity. Useful for mods which modify rarity levels.",
            StartingValue = 0,
            MinValue = 0,
            MaxValue = 1000,
            Increment = 1
        )

        #TypeFilters        
        self.TypeFilter_Artifact = TypeFilter("Artifact", "Artifact")
        self.TypeFilter_ClassMod = TypeFilter("Class Comm", "comm")
        self.TypeFilter_Granade = TypeFilter("Granade Mod", "Grenade")
        self.TypeFilter_Shield = TypeFilter("Shield", "Shield")
        self.TypeFilter_Pistol = TypeFilter("Pistol", "Pistol")
        self.TypeFilter_Rifle = TypeFilter("Assault Rifle", "ar")
        self.TypeFilter_SMG = TypeFilter("SMG", "SMG")
        self.TypeFilter_Shotgun = TypeFilter("Shotgun", "Shotgun")
        self.TypeFilter_Sniper = TypeFilter("Sniper Rifle", "sniper")
        self.TypeFilter_Launcher = TypeFilter("Rocket Launcher", "rocket")
        self.TypeFilter_Cosmetics = TypeFilter("Cosmetic", ["Customization_Head", "Customization_Skin"])
        self.TypeFilter_Consumables = TypeFilter("Consumable", ["Money", "Health"], "This includes any kind of Currency like Money, Eridium, Seraph Crystals.")

        self.Nest_TypeFilter = Options.Nested(
            Caption = "Item Type Filter",
            Description = "When you only want to see certain types of items.",
            Children = TypeFilterList
        )

        self.LoggingEnabled = Options.Boolean(
            Caption = "Enable Console Logging",
            Description = "Turns the console logging on or off. This can become very spammy.",
            StartingValue = False,
            Choices = ("Off", "On")
        )

        self.Nest_Advanced = Options.Nested(
            Caption = "Advanced Options",
            Description = "More filtering going on here.",
            Children = [
                self.RaritySlider,
                self.LoggingEnabled,
                self.Nest_TypeFilter
            ]
        )

        self.Options = [self.FilterEnable, self.RaritySpinner, self.LevelSlider, self.Nest_Advanced]

        self.timer = datetime.now()

    def GameInputPressed(self, bind: KeybindManager.Keybind, event: KeybindManager.InputEvent) -> None:
        if event != KeybindManager.InputEvent.Released:
            return
        
        if bind.Name == "Toggle Item Filter":
            self.FilterEnable.CurrentValue = not self.FilterEnable.CurrentValue
            if self.FilterEnable.CurrentValue:
                self.ShowNotification("Loot Filter enabled!")
            else:
                self.ShowNotification("Loot Filter disabled!")
        
        if bind.Name == "Clear Loot":
            if not self.FilterEnable:
                return
            self.RemoveLoot(self.GetValidLoot())

    @Hook("WillowGame.WillowPickup.PickupAtRest")
    def LootFilter(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if bl2helper.AmIClientPlayer() or not self.FilterEnable.CurrentValue or bl2helper.IsInMainMenu:
            return True
        
        if (datetime.now() - self.timer).total_seconds() > 0.5:
            self.RunRemoval()
            self.timer = datetime.now()

        return True
    
    def GenerateFilterSettingsMessage(self) -> str:
        outputMessage =  "Current Loot Filter:\n"

        outputMessage += "Rarity < " + str(self.RaritySpinner.CurrentValue) + "\n"
        outputMessage += "Level < " + str(self.LevelSlider.CurrentValue) + "\n"
        
        for TypeFilter in TypeFilterList:
            if not TypeFilter.CurrentValue:
                outputMessage += TypeFilter.DefinedItemType + " " + str(TypeFilter.CurrentValue) + "\n"

        return outputMessage

    def GetValidLoot(self) -> List[unrealsdk.UObject]:
        return [
            loot for loot in bl2helper.GetLootList()
            if not (loot.bIsMissionItem == True or loot.Inventory.GetZippyFrame() == "None")
        ]

    def RemoveLoot(self, Loot):
        for l in Loot:
            l.LifeSpan = 0.1

    def RunRemoval(self):
        self.RemoveWithType()
        self.RemoveWithRarity()
        self.RemoveWithLevel()

    def RemoveWithRarity(self):
        if self.LootRarities.get(self.RaritySpinner.CurrentValue) == -1:
            rarity = self.RaritySlider.CurrentValue
        else:
            rarity = self.LootRarities.get(self.RaritySpinner.CurrentValue)

        LootList = self.GetValidLoot()

        LootList = [
            loot for loot in LootList
            if loot.InventoryRarityLevel < rarity 
            and not (loot.Inventory.GetZippyFrame() == "Health" or loot.Inventory.GetZippyFrame() == "Money" or loot.InventoryRarityLevel == 0)
        ]
        
        if len(LootList) > 0:
            self.LogRemoval(LootList)
            self.RemoveLoot(LootList)
    
    def RemoveWithLevel(self):
        if self.LevelSlider.CurrentValue == 0:
            return
        
        if self.LevelSlider.CurrentValue > bl2helper.GetCurrentPlayerLevel() + bl2helper.GetMaxOverpowerLevel():
            self.LevelSlider.CurrentValue = bl2helper.GetCurrentPlayerLevel() + bl2helper.GetMaxOverpowerLevel()
            self.ShowNotification("Adjusted the Level Slider to "+str(self.LevelSlider.CurrentValue))

        LootList = self.GetValidLoot()

        LootList = [
            loot for loot in LootList
            if loot.Inventory.ExpLevel < self.LevelSlider.CurrentValue
            and loot.Inventory.GameStage < self.LevelSlider.CurrentValue
            and not (loot.Inventory.GetZippyFrame() == "Health" or loot.Inventory.GetZippyFrame() == "Money" or loot.InventoryRarityLevel == 0)
        ]

        if len(LootList) > 0:
            self.LogRemoval(LootList)
            self.RemoveLoot(LootList)
    
    def RemoveWithType(self):
        for filter in TypeFilterList:
            if not filter.CurrentValue:
                LootList = self.GetValidLoot()

                LootList = [
                    loot for loot in LootList
                    if loot.Inventory.GetZippyFrame() in ItemTypesToZippyFrame.get(filter.DefinedItemType)
                ]
                self.LogRemoval(LootList)
                self.RemoveLoot(LootList)

    def ShowNotification(self, message):
        bl2helper.ShowNotification(message, "Loot Filter Mod")

    def LogRemoval(self, LootList):
        if not self.LoggingEnabled:
            #unrealsdk.Log("Logging Disabled.")
            return
        
        unrealsdk.Log("-----The following Items will be removed-----")
        for l in LootList:
            unrealsdk.Log(
                "-EXP: " , l.Inventory.ExpLevel ,
                " GameStage: " , l.Inventory.GameStage ,
                " RarityLevel: " , l.Inventory.RarityLevel ,
                " ZippyFrame:" , l.Inventory.ZippyFrame ,
                " Value: " , l.Inventory.MonetaryValue ,
                " Serial: " , l.Inventory.GetSerialNumberString()
            )

RegisterMod(LootFilterMod())