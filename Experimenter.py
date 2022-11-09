import Mutators, Shrines, Level, Consumables

primary_shrine_option = [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Dark, Level.Tags.Arcane, Level.Tags.Nature, Level.Tags.Holy, Level.Tags.Ice]
secondary_shrine_option = [Level.Tags.Sorcery, Level.Tags.Enchantment, Level.Tags.Conjuration]
tertiary_shrine_option = [Level.Tags.Word, Level.Tags.Dragon, Level.Tags.Translocation, Level.Tags.Eye, Level.Tags.Chaos, Level.Tags.Orb, Level.Tags.Metallic]

class Experimenter1(Mutators.Mutator):

    def __init__(self):
        Mutators.Mutator.__init__(self)
        self.description = ("Realms 1 and 2 contain no enemies or gates\n"
                            "Realm 2 always contains a circle\n"
                            "Realm 3 always contains a shrine")
        self.all_valid = primary_shrine_option + secondary_shrine_option + tertiary_shrine_option
    
    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty <= 2:
            levelgen.num_generators = 0
            levelgen.num_monsters = 0
            levelgen.bosses = []
        if levelgen.game and levelgen.difficulty == 2:
            levelgen.shrine = Shrines.library(levelgen.game.p1)
        if levelgen.game and levelgen.difficulty == 3:
            levelgen.shrine = Shrines.shrine(levelgen.game.p1)

class Experimenter2(Mutators.Mutator):

    def __init__(self):
        Mutators.Mutator.__init__(self)
        self.description = ("Realms 1 and 2 contain no enemies or gates\n"
                            "Realm 1 contains one rift for each circle\n"
                            "Realm 2 contains one rift for each shrine\n")
        self.all_valid = primary_shrine_option + secondary_shrine_option + tertiary_shrine_option
    
    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty <= 2:
            levelgen.num_generators = 0
            levelgen.num_monsters = 0
            levelgen.bosses = []
            levelgen.num_exits = len(self.all_valid) if levelgen.difficulty != 2 else len(Shrines.new_shrines)
        if levelgen.game and levelgen.difficulty == 2:
            levelgen.shrine = Shrines.library(levelgen.game.p1)
        if levelgen.game and levelgen.difficulty == 3:
            levelgen.shrine = Shrines.shrine(levelgen.game.p1)
    
    def on_levelgen(self, levelgen):
        if levelgen.difficulty == 2:
            all_port_tiles = [t for t in levelgen.level.iter_tiles() if type(t.prop) == Level.Portal]
            for tile, shrine in zip(all_port_tiles, Shrines.new_shrines):
                tile.prop.level_gen_params.shrine = Shrines.make_shrine(shrine[0](), levelgen.game.p1)
        if levelgen.difficulty == 1:
            all_port_tiles = [t for t in levelgen.level.iter_tiles() if type(t.prop) == Level.Portal]
            for tile, tag in zip(all_port_tiles, self.all_valid):
                tile.prop.level_gen_params.shrine = Level.PlaceOfPower(tag)

class Experimenter3(Mutators.Mutator):

    def __init__(self):
        Mutators.Mutator.__init__(self)
        self.description = ("You start with 10 SP and an extra Dragon Horn\n"
                            "Realms 1 and 2 contain no enemies, gates, items, or SP\n"
                            "Realm 1 contains one rift for each circle\n"
                            "Realm 2 contains one rift for each shrine")
        self.all_valid = primary_shrine_option + secondary_shrine_option + tertiary_shrine_option
    
    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty <= 2:
            levelgen.num_generators = 0
            levelgen.num_monsters = 0
            levelgen.num_recharges = 0
            levelgen.num_heals = 0
            levelgen.num_xp = 0
            levelgen.bosses = []
            levelgen.items = []
            levelgen.num_exits = len(self.all_valid) if levelgen.difficulty != 2 else len(Shrines.new_shrines)
        if levelgen.game and levelgen.difficulty == 2:
            levelgen.shrine = Shrines.library(levelgen.game.p1)
        if levelgen.game and levelgen.difficulty == 3:
            levelgen.shrine = Shrines.shrine(levelgen.game.p1)
    
    def on_levelgen(self, levelgen):
        if levelgen.difficulty == 2:
            all_port_tiles = [t for t in levelgen.level.iter_tiles() if type(t.prop) == Level.Portal]
            for tile, shrine in zip(all_port_tiles, Shrines.new_shrines):
                tile.prop.level_gen_params.shrine = Shrines.make_shrine(shrine[0](), levelgen.game.p1)
        if levelgen.difficulty == 1:
            all_port_tiles = [t for t in levelgen.level.iter_tiles() if type(t.prop) == Level.Portal]
            for tile, tag in zip(all_port_tiles, self.all_valid):
                tile.prop.level_gen_params.shrine = Level.PlaceOfPower(tag)
            
    def on_game_begin(self, game):
        game.p1.xp = 10
        game.p1.add_item(Consumables.dragon_horn())

Mutators.all_trials.append(Mutators.Trial("Experimenter", Experimenter1()))
Mutators.all_trials.append(Mutators.Trial("Experimenter Ultimate", Experimenter2()))
Mutators.all_trials.append(Mutators.Trial("Experimenter Unhinged", Experimenter3()))