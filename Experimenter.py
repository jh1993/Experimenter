from RiftWizard import *
from Level import *
from Shrines import *
from Game import *
from Consumables import *

import sys
curr_module = sys.modules[__name__]

circles = [None, Tags.Arcane, Tags.Chaos, Tags.Conjuration, Tags.Dark, Tags.Dragon, Tags.Enchantment, Tags.Eye, Tags.Fire, Tags.Holy, Tags.Ice, Tags.Lightning, Tags.Metallic, Tags.Nature, Tags.Orb, Tags.Sorcery, Tags.Translocation, Tags.Word]

shrines = [s[0]() for s in new_shrines]
shrines.sort(key=lambda s: s.name)
shrines.insert(0, None)

OPTION_STARTING_CIRCLE = 8
OPTION_STARTING_SHRINE = 9
OPTION_LUCKY_START = 10
OPTION_EASY_START = 11

class StartingShrineBuff(Buff):

    def __init__(self, shrine):
        self.shrine = shrine
        Buff.__init__(self)
    
    def on_init(self):
        self.name = "%s Shrine" % self.shrine.name
        self.description = "The first eligible spell you gain will have %s shrine applied to it." % self.shrine.name
        self.buff_type = BUFF_TYPE_NONE
    
    def on_add_spell(self, spell):
        if not self.shrine.can_enhance(spell):
            return
        self.owner.apply_buff(self.shrine.get_buff(spell))
        self.owner.remove_buff(self)

def modify_class(cls):

    if cls is PyGameView:

        def __init__(self):
            self.game = None

            try:
                with open('options2.dat', 'rb') as options_file:
                    self.options = pickle.load(options_file)
            except:
                self.options = {}

            if 'sound_volume' not in self.options:
                self.options['sound_volume'] = 100
            if 'music_volume' not in self.options:
                self.options['music_volume'] = 100
            if 'smart_targeting' not in self.options:
                self.options['smart_targeting'] = False
            if 'spell_speed' not in self.options:
                self.options['spell_speed'] = 0
            if "starting_circle" not in self.options:
                self.options["starting_circle"] = 0
            if "starting_shrine" not in self.options:
                self.options["starting_shrine"] = 0
            if "lucky_start" not in self.options:
                self.options["lucky_start"] = False
            if "easy_start" not in self.options:
                self.options["easy_start"] = False

            self.rebinding = False
            self.key_binds = dict(default_key_binds)
            self.key_binds.update(self.options.get('key_binds', {}))

            pygame.mixer.pre_init(buffer=512)
            pygame.init()
            pygame.display.init()

            pygame.display.set_caption("Rift Wizard")

            level_width = LEVEL_SIZE * SPRITE_SIZE

            self.h_margin = (1600 - (2 * level_width)) // 2 

            # Weird trick to do a fast 2x blit, probably unnecceary
            self.whole_level_display = pygame.Surface((800, 450))
            self.level_display = self.whole_level_display.subsurface(pygame.Rect(self.h_margin // 2, 0, SPRITE_SIZE * LEVEL_SIZE, SPRITE_SIZE * LEVEL_SIZE))
            self.targeting_display = pygame.Surface((self.level_display.get_width(), self.level_display.get_height()))

            self.character_display = pygame.Surface((self.h_margin, 900))
            self.examine_display = pygame.Surface((self.h_margin, 900))

            self.middle_menu_display = pygame.Surface((1600 - 2 * self.h_margin, 900))\

            self.real_display = None

            self.outer_x_margin = 0
            self.outer_y_margin = 0
            self.tiny_mode = False

            modes = pygame.display.list_modes()

            self.screen = pygame.Surface((1600, 900))

            self.windowed = 'windowed' in sys.argv
            self.native_res = 'native_res' in sys.argv

            # Windowed
            info = pygame.display.Info()
            self.display_res = (info.current_w, info.current_h)
            if self.display_res not in modes:
                self.display_res = modes[0]

            if self.windowed:
                # For windowed- try 1600 x 900(1x), but for smaller displays do 1/2 scale
                # For now 4K users will have to maximize or resize, and thats ok.
                if info.current_w > 1600:
                    self.display_res = (1600, 900)
                else:
                    self.display_res = (800, 450)
                pygame.display.set_mode(self.display_res, pygame.RESIZABLE)
            elif self.native_res:
                # If no res opts are given just use the current desktop res
                assert((1600, 900) in modes)
                self.display_res = (1600, 900)
                pygame.display.set_mode(self.display_res, pygame.FULLSCREEN)
            else:
                # If no res opts are given just use the current desktop res
                pygame.display.set_mode(self.display_res, pygame.FULLSCREEN | pygame.SCALED)


            self.clock = pygame.time.Clock()

            #pygame.mixer.init()
            self.can_play_sound = False
            if not 'nosound' in sys.argv:
                try:
                    self.hit_sound_channel = pygame.mixer.Channel(0)
                    self.hit_player_sound_channel = pygame.mixer.Channel(1)
                    self.death_sound_channel = pygame.mixer.Channel(2)
                    self.cast_sound_channel = pygame.mixer.Channel(3)
                    self.step_sound_channel = pygame.mixer.Channel(4)
                    self.misc_sound_channel = pygame.mixer.Channel(5)
                    self.ui_sound_channel = pygame.mixer.Channel(6)

                    pygame.mixer.set_reserved(6)

                    self.base_volumes = {
                        self.hit_sound_channel : .5,
                        self.hit_player_sound_channel: .6,
                        self.death_sound_channel: .75,
                        self.cast_sound_channel: .65,
                        self.step_sound_channel: .15,
                        self.misc_sound_channel: .75,
                        self.ui_sound_channel: .25
                    }

                    sound = True #'sound' in sys.argv

                    if not sound:
                        pygame.mixer.music.stop()
                        channels = [self.hit_sound_channel, self.hit_player_sound_channel, self.death_sound_channel, self.cast_sound_channel, self.step_sound_channel]
                        for channel in channels:
                            channel.set_volume(0)

                    self.can_play_sound = True

                    self.adjust_volume(0, "sound")

                except:
                    pass

            pygame.font.init()
            #self.font = pygame.font.SysFont("sylfaen", 20)
            font_path = os.path.join("rl_data", "PrintChar21.ttf")
            self.font = pygame.font.Font(font_path, 16)
            self.ascii_idle_font = pygame.font.Font(font_path, 16)
            self.ascii_attack_font = pygame.font.Font(font_path, 16)
            self.ascii_flinch_font = pygame.font.Font(font_path, 16)

            self.frameno = 0

            floor_path = os.path.join("rl_data", "floor_tile.png")

            self.load_chasm_sprites()
            self.load_wall_sprites()
            self.load_floor_sprites()
        
            self.effects = []
            
            self.load_effect_images()

            self.sprite_sheets = {}
            self.cur_spell = None
            self.cur_spell_target = None
            self.targetable_tiles = None
            self.examine_target = None

            prop_path = os.path.join("rl_data", "tiles", "shrine", "shrine_white.png")
            self.prop_sprite = pygame.image.load(prop_path)

            self.deploy_target = None
            self.border_margin = 12
            self.linesize = self.font.get_linesize() + 2

            self.state = None
            self.return_to_title()

            self.char_sheet_select_index = 0
            self.char_sheet_select_type = 0
            self.shop_type = SHOP_TYPE_SPELLS
            self.shop_upgrade_spell = None
            self.shop_selection_index = 0
            self.shop_page = 0
            self.max_shop_objects = 44

            self.tag_keys = {
                'f': Tags.Fire,
                'i': Tags.Ice,
                'l': Tags.Lightning,
                'n': Tags.Nature,
                'a': Tags.Arcane,
                'd': Tags.Dark,
                'h': Tags.Holy,
                'm': Tags.Metallic,

                's': Tags.Sorcery,
                'e': Tags.Enchantment,
                'c': Tags.Conjuration,

                'y': Tags.Eye,
                'r': Tags.Dragon,
                'b': Tags.Orb,
                'o': Tags.Chaos,
                'w': Tags.Word,
                't': Tags.Translocation
            }

            self.reverse_tag_keys = {v: k.upper() for k, v in self.tag_keys.items()}

            self.tag_filter = set()

            self.path = []

            self.effect_queue = []
            self.sound_effects = {}

            self.ui_tiles = {}
            self.red_ui_tiles = {}
            self.load_ui_tiles()

            self.examine_icon_surface = pygame.Surface((16, 16))
            self.char_panel_examine_lines = {}

            self.second_step = False

            self.path_delay = 0

            self.option_selection = OPTION_SOUND_VOLUME

            self.message = None

            self.gameover_frames = 0
            self.gameover_tiles = None

            self.deploy_anim_frames = 0

            self.title_image = get_image(['title'])
            self.title_frame = 0

            self.los_image = get_image(['UI', 'los'])
            self.hostile_los_image = get_image(['UI', 'hostile_los'])

            self.shop_scroll_frame = 0

            self.ui_rects = []

            self.threat_zone = None
            self.last_threat_highlight = None

            icon = get_image(['UI', 'icon'])
            pygame.display.set_icon(icon)

            self.repeat_keys = {}

            fill_color = (255, 255, 255, 150)
            self.tile_targetable_image = get_image(['UI', 'square_valid_animated'])
            self.tile_targetable_image.fill(fill_color, special_flags=pygame.BLEND_RGBA_MIN)
            self.tile_impacted_image = get_image(['UI', 'square_impacted_animated'])
            self.tile_impacted_image.fill(fill_color, special_flags=pygame.BLEND_RGBA_MIN)
            self.tile_targeted_image = get_image(['UI', 'square_targeted_animated'])
            self.tile_targeted_image.fill(fill_color, special_flags=pygame.BLEND_RGBA_MIN)
            self.tile_invalid_target_image = get_image(['UI', 'square_invalid_target_animated'])
            self.tile_invalid_target_image.fill(fill_color, special_flags=pygame.BLEND_RGBA_MIN)
            self.tile_invalid_target_in_range_image = get_image(['UI', 'square_invalid_target_animated']).copy()
            self.tile_invalid_target_in_range_image.fill((255, 255, 255, 45), special_flags=pygame.BLEND_RGBA_MIN)

            self.reminisce_folder = None
            self.reminisce_index = 0

            self.abort_to_spell_shop = False


            self.examine_icon_subframe = 0
            self.examine_icon_frame = 0

            self.cast_fail_frames = 0
            #pygame.mouse.set_visible(False)

            self.combat_log_offset = 0
            self.combat_log_turn = 0
            self.combat_log_level = 0

            self.confirm_text = None
            self.confirm_yes = None
            self.confirm_no = None

            self.next_message = None
            self.fast_forward = False

        def draw_options_menu(self):

            cur_x = self.screen.get_width() // 2 - self.font.size("Sound Volume")[0]
            cur_y = self.screen.get_height() // 2 - self.linesize * OPTION_MAX

            rect_w = self.font.size("Music Volume:  100")[0]

            self.draw_string("How to Play", self.screen, cur_x, cur_y, mouse_content=OPTION_HELP, content_width=rect_w)
            cur_y += self.linesize

            self.draw_string("Sound Volume:  %3d" % self.options['sound_volume'], self.screen, cur_x, cur_y, mouse_content=OPTION_SOUND_VOLUME, content_width=rect_w)
            cur_y += self.linesize

            self.draw_string("Music Volume:  %3d" % self.options['music_volume'], self.screen, cur_x, cur_y, mouse_content=OPTION_MUSIC_VOLUME, content_width=rect_w)
            cur_y += self.linesize

            if self.options['spell_speed'] == 0:
                speed_fmt = "normal"
            elif self.options['spell_speed'] == 1:
                speed_fmt = "fast"
            if self.options['spell_speed'] == 2:
                speed_fmt = "turbo"
            if self.options['spell_speed'] == 3:
                speed_fmt = "Xturbo"

            self.draw_string("Anim Speed: %6s" % speed_fmt, self.screen, cur_x, cur_y, mouse_content=OPTION_SPELL_SPEED, content_width=rect_w)
            cur_y += self.linesize

            if self.options["starting_circle"] == 0:
                circle_fmt = "None"
            else:
                circle_fmt = circles[self.options["starting_circle"]].name
            self.draw_string("Starting Circle: %s" % circle_fmt, self.screen, cur_x, cur_y, mouse_content=OPTION_STARTING_CIRCLE)
            cur_y += self.linesize

            if self.options["starting_shrine"] == 0:
                shrine_fmt = "None"
            else:
                shrine_fmt = shrines[self.options["starting_shrine"]].name
            self.draw_string("Starting Shrine: %s" % shrine_fmt, self.screen, cur_x, cur_y, mouse_content=OPTION_STARTING_SHRINE)
            cur_y += self.linesize

            self.draw_string("Lucky Start: %s" % ("Yes" if self.options["lucky_start"] else "No"), self.screen, cur_x, cur_y, mouse_content=OPTION_LUCKY_START)
            cur_y += self.linesize

            self.draw_string("Easy Start: %s" % ("Yes" if self.options["easy_start"] else "No"), self.screen, cur_x, cur_y, mouse_content=OPTION_EASY_START)
            cur_y += self.linesize

            self.draw_string("Rebind Controls", self.screen, cur_x, cur_y, mouse_content=OPTION_CONTROLS, content_width=rect_w)
            cur_y += self.linesize

            if self.game:
                self.draw_string("Return to Game", self.screen, cur_x, cur_y, mouse_content=OPTION_RETURN, content_width=rect_w)
                cur_y += self.linesize
            
                self.draw_string("Save and Exit", self.screen, cur_x, cur_y, mouse_content=OPTION_EXIT, content_width=rect_w)
                cur_y += self.linesize

            else:
                self.draw_string("Back to Title", self.screen, cur_x, cur_y, mouse_content=OPTION_EXIT, content_width=rect_w)
                cur_y += self.linesize

        def process_options_input(self):
            for evt in [e for e in self.events if e.type == pygame.KEYDOWN]:

                if evt.key in self.key_binds[KEY_BIND_UP]:
                    if self.examine_target is None:
                        self.examine_target = 0
                    else:
                        self.examine_target -= 1
                        if not self.game and self.examine_target == OPTION_RETURN:
                            self.examine_target -= 1
                        self.examine_target = max(0, self.examine_target)
                        self.play_sound("menu_confirm")
                if evt.key in self.key_binds[KEY_BIND_DOWN]:
                    if self.examine_target is None:
                        self.examine_target = 0
                    else:
                        self.examine_target += 1
                        if not self.game and self.examine_target == OPTION_RETURN:
                            self.examine_target += 1
                        self.examine_target = min(self.examine_target, OPTION_MAX)
                        self.play_sound("menu_confirm")

                if evt.key in self.key_binds[KEY_BIND_LEFT]:
                    self.play_sound("menu_confirm")
                    if self.examine_target == OPTION_MUSIC_VOLUME:
                        self.adjust_volume(-10, 'music')
                    if self.examine_target == OPTION_SOUND_VOLUME:
                        self.adjust_volume(-10, 'sound')
                    if self.examine_target == OPTION_SMART_TARGET:
                        self.toggle_smart_targeting()               
                    if self.examine_target == OPTION_SPELL_SPEED:
                        self.options['spell_speed'] = (self.options['spell_speed'] - 1) % 4
                    if self.examine_target == OPTION_STARTING_CIRCLE:
                        self.options["starting_circle"] = (self.options["starting_circle"] - 1) % len(circles)
                    if self.examine_target == OPTION_STARTING_SHRINE:
                        self.options["starting_shrine"] = (self.options["starting_shrine"] - 1) % len(shrines)
                    if self.examine_target == OPTION_LUCKY_START:
                        self.options["lucky_start"] = not self.options["lucky_start"]
                    if self.examine_target == OPTION_EASY_START:
                        self.options["easy_start"] = not self.options["easy_start"]

                if evt.key in self.key_binds[KEY_BIND_RIGHT]:
                    self.play_sound("menu_confirm")
                    if self.examine_target == OPTION_MUSIC_VOLUME:
                        self.adjust_volume(10, 'music')
                    if self.examine_target == OPTION_SOUND_VOLUME:
                        self.adjust_volume(10, 'sound')
                    if self.examine_target == OPTION_SMART_TARGET:
                        self.toggle_smart_targeting()               
                    if self.examine_target == OPTION_SPELL_SPEED:
                        self.options['spell_speed'] = (self.options['spell_speed'] + 1) % 4
                    if self.examine_target == OPTION_STARTING_CIRCLE:
                        self.options["starting_circle"] = (self.options["starting_circle"] + 1) % len(circles)
                    if self.examine_target == OPTION_STARTING_SHRINE:
                        self.options["starting_shrine"] = (self.options["starting_shrine"] + 1) % len(shrines)
                    if self.examine_target == OPTION_LUCKY_START:
                        self.options["lucky_start"] = not self.options["lucky_start"]
                    if self.examine_target == OPTION_EASY_START:
                        self.options["easy_start"] = not self.options["easy_start"]

                if evt.key in self.key_binds[KEY_BIND_CONFIRM]:
                    if self.examine_target == OPTION_EXIT:
                        if self.game:
                            self.game.save_game()
                        self.return_to_title()

                    elif self.examine_target == OPTION_RETURN:
                        self.play_sound("menu_confirm")
                        self.state = STATE_LEVEL
                    elif self.examine_target == OPTION_HELP:
                        self.play_sound("menu_confirm")
                        self.show_help()
                    elif self.examine_target == OPTION_SMART_TARGET:
                        self.toggle_smart_targeting()
                    elif self.examine_target == OPTION_CONTROLS:
                        self.open_key_rebind()
                    elif self.examine_target == OPTION_SPELL_SPEED:
                        self.options['spell_speed'] = (self.options['spell_speed'] + 1) % 4
                    elif self.examine_target == OPTION_STARTING_CIRCLE:
                        self.options["starting_circle"] = (self.options["starting_circle"] + 1) % len(circles)
                    elif self.examine_target == OPTION_STARTING_SHRINE:
                        self.options["starting_shrine"] = (self.options["starting_shrine"] + 1) % len(shrines)
                    elif self.examine_target == OPTION_LUCKY_START:
                        self.options["lucky_start"] = not self.options["lucky_start"]
                    elif self.examine_target == OPTION_EASY_START:
                        self.options["easy_start"] = not self.options["easy_start"]

                if evt.key in self.key_binds[KEY_BIND_ABORT]:
                    self.state = STATE_LEVEL if self.game else STATE_TITLE
                    if self.state == STATE_TITLE:
                        self.examine_target = TITLE_SELECTION_LOAD if can_continue_game() else TITLE_SELECTION_NEW
                    self.play_sound("menu_confirm")


            m_loc = self.get_mouse_pos()
            for evt in [e for e in self.events if e.type == pygame.MOUSEBUTTONDOWN]:

                for r, o in self.ui_rects:
                    if r.collidepoint(m_loc):
                        if evt.button == pygame.BUTTON_LEFT:
                            self.play_sound("menu_confirm")
                            if o == OPTION_EXIT:
                                self.save_options()
                                if self.game:
                                    self.game.save_game()
                                self.return_to_title()
                                break
                            if o == OPTION_RETURN:
                                self.play_sound("menu_confirm")
                                self.state = STATE_LEVEL
                                break
                            if o == OPTION_HELP:
                                self.play_sound("menu_confirm")
                                self.show_help()
                                break
                            if o == OPTION_SOUND_VOLUME:
                                self.adjust_volume(10, 'sound')
                                break
                            if o == OPTION_MUSIC_VOLUME:
                                self.adjust_volume(10, 'music')
                                break
                            if o == OPTION_SMART_TARGET:
                                self.toggle_smart_targeting()
                                break
                            if self.examine_target == OPTION_CONTROLS:
                                self.open_key_rebind()
                                break
                            elif self.examine_target == OPTION_SPELL_SPEED:
                                self.options['spell_speed'] = (self.options['spell_speed'] + 1) % 4
                                break
                            elif self.examine_target == OPTION_STARTING_CIRCLE:
                                self.options['starting_circle'] = (self.options['starting_circle'] + 1) % len(circles)
                                break
                            elif self.examine_target == OPTION_STARTING_SHRINE:
                                self.options['starting_shrine'] = (self.options['starting_shrine'] + 1) % len(shrines)
                                break
                            elif self.examine_target == OPTION_LUCKY_START:
                                self.options["lucky_start"] = not self.options["lucky_start"]
                                break
                            elif self.examine_target == OPTION_EASY_START:
                                self.options["easy_start"] = not self.options["easy_start"]
                                break

                        if evt.button == pygame.BUTTON_RIGHT:
                            self.play_sound("menu_confirm")
                            if o == OPTION_SOUND_VOLUME:
                                self.adjust_volume(-10, 'sound')
                                break
                            if o == OPTION_MUSIC_VOLUME:
                                self.adjust_volume(-10, 'music')
                                break
                            elif self.examine_target == OPTION_SPELL_SPEED:
                                self.options['spell_speed'] = (self.options['spell_speed'] - 1) % 4
                                break
                            elif self.examine_target == OPTION_STARTING_CIRCLE:
                                self.options['starting_circle'] = (self.options['starting_circle'] - 1) % len(circles)
                                break
                            elif self.examine_target == OPTION_STARTING_SHRINE:
                                self.options['starting_shrine'] = (self.options['starting_shrine'] - 1) % len(shrines)
                                break
                            elif self.examine_target == OPTION_LUCKY_START:
                                self.options["lucky_start"] = not self.options["lucky_start"]
                                break
                            elif self.examine_target == OPTION_EASY_START:
                                self.options["easy_start"] = not self.options["easy_start"]
                                break

                else:
                    self.play_sound("menu_confirm")
                    if self.game:
                        self.state = STATE_LEVEL
                    else:
                        self.return_to_title()

        def new_game(self, mutators=None, trial_name=None, seed=None):

            # If you are overwriting an old game, break streak
            if can_continue_game():
                SteamAdapter.set_stat('s', 0)
                SteamAdapter.set_stat('l', SteamAdapter.get_stat('l') + 1)

            self.game = Game(view=self, save_enabled=True, mutators=mutators, trial_name=trial_name, seed=seed)
            self.message = text.intro_text

            if mutators:
                self.message += "\n\n\n\nChallenge Modifiers:"
                for mutator in mutators:
                    self.message += "\n" + mutator.description

            self.center_message = True
            self.state = STATE_MESSAGE
            self.play_music('battle_2')
            self.make_level_screenshot()
            SteamAdapter.set_presence_level(1)

    if cls is Game:

        def __init__(self, view, generate_level=True, save_enabled=False, mutators=None, trial_name=None, seed=None):

            self.build_compat_num = BUILD_NUM
            self.seed = seed
            if self.seed:
                random.seed(self.seed)
            else:
                random.seed()

            self.starting_circle = view.options["starting_circle"]
            self.starting_shrine = view.options["starting_shrine"]
            self.lucky_start = view.options["lucky_start"]
            self.easy_start = view.options["easy_start"]

            self.level_seeds = {}
            for i in range(26):
                seeds_per_difficulty = 12
                self.level_seeds[i] = [random.random() for i in range(seeds_per_difficulty)]

            self.mutators = mutators
            if not self.mutators:
                self.mutators = []

            for mutator in self.mutators:
                mutator.set_seed(random.random())

            self.trial_name = trial_name

            self.p1 = self.make_player_character()

            self.run_number = self.get_run_number()

            self.generate_level = generate_level
            if generate_level:
                self.cur_level = LevelGenerator(1, self, self.seed).make_level()
            else:
                self.cur_level = Level(32, 32)
                self.cur_level.start_pos = Point(0, 0)

            self.cur_level.spawn_player(self.p1)

            if view.options["lucky_start"]:
                self.p1.add_item(dragon_horn())
                for t in self.cur_level.iter_tiles():
                    prop = t.prop
                    if isinstance(prop, ManaDot):
                        self.p1.xp += 1

            if view.options["easy_start"]:
                for t in self.cur_level.iter_tiles():
                    prop = t.prop
                    if isinstance(prop, ManaDot):
                        prop.on_player_enter(self.p1)
                for u in list(self.cur_level.units):
                    if u.team == TEAM_ENEMY:
                        u.kill(trigger_death_event=False)

            circle = circles[view.options["starting_circle"]]
            if circle:
                if not self.cur_level.tiles[self.p1.x][self.p1.y].prop:
                    circle = PlaceOfPower(circle)
                    self.cur_level.add_prop(circle, self.p1.x, self.p1.y)
                    circle.on_player_enter(self.p1)

            shrine = shrines[view.options["starting_shrine"]]
            if shrine:
                self.p1.apply_buff(StartingShrineBuff(type(shrine)()))

            self.gameover = False
            self.level_num = 1

            self.deploying = False
            self.next_level = None
            self.prev_next_level = None

            self.victory = False

            self.has_granted_xp = False

            self.victory_evt = False

            self.recent_upgrades = []

            self.total_turns = 0

            self.all_player_spells = make_player_spells()
            self.all_player_skills = make_player_skills()

            for mutator in self.mutators:
                mutator.on_generate_spells(self.all_player_spells)
                mutator.on_generate_skills(self.all_player_skills)
                mutator.on_game_begin(self)

            # Gather all spell tags for UI and other consumers
            self.spell_tags = []
            self.spell_tags.extend(t for t in Tags if any(t in s.tags for s in self.all_player_spells))
            self.spell_tags.extend(t for t in Tags if any(t in s.tags for s in self.all_player_skills) if t not in self.spell_tags)

            self.subscribe_mutators()

            if save_enabled:
                self.save_game()
                self.logdir = os.path.join('saves', str(self.run_number), 'log')
                os.mkdir(self.logdir)
            else:
                self.logdir = None

            self.cur_level.setup_logging(logdir=self.logdir, level_num=self.level_num)

    for func_name, func in [(key, value) for key, value in locals().items() if callable(value)]:
        if hasattr(cls, func_name):
            setattr(cls, func_name, func)

for cls in [PyGameView, Game]:
    curr_module.modify_class(cls)