"""This file contains all relevant classes for fight"""

import time
import random
import logging
import scrap_engine as se
import pokete_data as p_data
from pokete_classes import animations, ob_maps as obmp, \
    deck, game_map as gm
from release import SPEED_OF_TIME
from ..hotkeys import Action, get_action
from ..audio import audio
from ..npcs import Trainer
from ..providers import NatureProvider, ProtoFigure
from ..ui_elements import StdFrame2
from ..classes import OutP
from ..input import ask_bool
from ..achievements import achievements
from ..inv_items import invitems
from ..settings import settings
from ..loops import std_loop
from ..tss import tss
from .. import movemap as mvp
from .attack import AttackBox
from .inv import InvBox


class FightMap(gm.GameMap):
    """Wrapper for gm.GameMap
    ARGS:
        height: The height of the map
        width: The width of the map"""

    def __init__(self, height, width):
        super().__init__(height, width, name="fightmap")
        self.providers = []
        self.box = AttackBox(self)
        self.invbox = InvBox(height - 3, 35, "Inventory", overview=self)
        # icos
        self.deadico1 = se.Text(r"""
    \ /
     o
    / \ """)
        self.deadico2 = se.Text("""

     o""")
        self.pball = se.Text(r"""   _____
  /_____\
  |__O__|
  \_____/""")
        # visual objects
        self.frame_big = StdFrame2(self.height - 5, self.width,
                                   state="float")
        self.frame_small = se.Frame(height=4, width=self.width,
                                    state="float")
        self.e_underline = se.Text("----------------+", state="float")
        self.e_sideline = se.Square("|", 1, 3, state="float")
        self.p_upperline = se.Text("+----------------", state="float")
        self.p_sideline = se.Square("|", 1, 4, state="float")
        self.outp = OutP("", state="float")
        self.label = se.Text(
            f"{Action.CHOOSE_ATTACK.mapping}: Attack  "
            f"{Action.RUN.mapping}: Run!  "
            f"{Action.CHOOSE_ITEM.mapping}: Inv.  "
            f"{Action.CHOOSE_POKE.mapping}: Deck"
        )
        # adding
        self.e_underline.add(self, 1, 4)
        self.e_sideline.add(self, len(self.e_underline.text), 1)
        self.add_base_boxes()

    def add_base_boxes(self):
        """Adds the basic map layout"""
        self.outp.add(self, 1, self.height - 4)
        self.p_upperline.add(self, self.width - 1 - len(self.p_upperline.text),
                             self.height - 10)
        self.frame_big.add(self, 0, 0)
        self.p_sideline.add(self, self.width - 1 - len(self.p_upperline.text),
                            self.height - 9)
        self.frame_small.add(self, 0, self.height - 5)
        self.label.add(self, 0, self.height - 1)

    def resize_view(self):
        """Manages recursive view resizing"""
        player_added = self.providers[0].curr.ico.added
        enem_added = self.providers[1].curr.ico.added
        for obj in [
            self.outp, self.p_upperline, self.providers[1].curr.ico,
            self.frame_big, self.p_sideline, self.frame_small, self.label
        ]:
            obj.remove()
        self.clean_up(self.providers[0], resize=True)

        self.resize(tss.height - 1, tss.width, background=" ")
        self.frame_big.resize(self.height - 5, self.width)
        self.frame_small.resize(4, self.width)
        mvp.movemap.resize_view()

        self.add_base_boxes()
        if player_added:
            self.add_player(self.providers[0], resize=True)
        if enem_added:
            self.providers[1].curr.ico.add(self, self.width - 14, 2)

    def clean_up(self, *providers, resize=False):
        """Removes all labels from self
        ARGS:
            providers: The Providers to clean up that the labels belong to
            resize: Whether or not the box is beeing resized"""
        for prov in providers:
            for obj in (
                prov.curr.text_name, prov.curr.text_lvl, prov.curr.text_hp,
                prov.curr.ico, prov.curr.hp_bar, prov.curr.tril, prov.curr.trir,
                prov.curr.pball_small
            ):
                obj.remove()
            if not resize:
                if isinstance(prov, ProtoFigure):
                    self.box.box.remove_c_obs()
            for j in prov.curr.effects:
                j.cleanup()

    def add_player(self, player, resize=False):
        """Adds player labels
        ARGS:
            player: The player provider object
            resize: Whether or not the box is beeing resized"""
        player.curr.text_name.add(self, self.width - 17, self.height - 9)
        player.curr.text_lvl.add(self, self.width - 17, self.height - 8)
        player.curr.tril.add(self, self.width - 11, self.height - 7)
        player.curr.trir.add(self, self.width - 2, self.height - 7)
        player.curr.hp_bar.add(self, self.width - 10, self.height - 7)
        player.curr.text_hp.add(self, self.width - 17, self.height - 7)
        player.curr.ico.add(self, 3, self.height - 10)
        if not resize:
            self.box.box.add_c_obs(
                [atc.label for atc in player.curr.attack_obs])
            self.box.box.set_index(0)

    def add_1(self, player, enem):
        """Adds enemy and general labels to self
        ARGS:
            player: The player Poke object
            enem: The enemy Poke object that the labels belong to"""
        for obj, _x, _y in zip(
            (
                enem.curr.tril,
                enem.curr.trir,
                enem.curr.text_name,
                enem.curr.text_lvl,
                enem.curr.text_hp,
                enem.curr.ico,
                enem.curr.hp_bar
            ),
            (7, 16, 1, 1, 1, self.width - 14, 8),
            (3, 3, 1, 2, 3, 2, 3)
        ):
            obj.add(self, _x, _y)
        if enem.curr.identifier in player.caught_pokes:
            enem.curr.pball_small.add(self, len(self.e_underline.text) - 1, 1)

    def add_2(self, player):
        """Adds player labels with sleeps
        ARGS:
            player: The player Poke object that the labels belong to"""
        player.curr.text_name.add(self, self.width - 17, self.height - 9)
        time.sleep(SPEED_OF_TIME * 0.05)
        self.show()
        player.curr.text_lvl.add(self, self.width - 17, self.height - 8)
        time.sleep(SPEED_OF_TIME * 0.05)
        self.show()
        player.curr.tril.add(self, self.width - 11, self.height - 7)
        player.curr.trir.add(self, self.width - 2, self.height - 7)
        player.curr.hp_bar.add(self, self.width - 10, self.height - 7)
        player.curr.text_hp.add(self, self.width - 17, self.height - 7)
        time.sleep(SPEED_OF_TIME * 0.05)
        self.show()
        player.curr.ico.add(self, 3, self.height - 10)
        self.box.box.add_c_obs([atc.label for atc in player.curr.attack_obs])
        self.box.box.set_index(0)

    def fast_change(self, arr, setob):
        """Changes fast between a list of texts
        ARGS:
            arr: List of se.Texts that will be changed through
            setob: A reference se.Text with the coordinates the objs in arr
                   will be set to."""
        for _i in range(1, len(arr)):
            arr[_i - 1].remove()
            arr[_i].add(self, setob.x, setob.y)
            self.show()
            time.sleep(SPEED_OF_TIME * 0.1)

    def get_figure_attack(self, figure, enem):
        """Chooses the players attack
        ARGS:
            figure: The players provider
            enem: The enemys provider"""
        quick_attacks = [
                            Action.QUICK_ATC_1, Action.QUICK_ATC_2,
                            Action.QUICK_ATC_3, Action.QUICK_ATC_4
                        ][:len(figure.curr.attack_obs)]
        self.outp.append(se.Text(("\n" if "\n" not in self.outp.text
                                  else "") +
                                 "What do you want to do?",
                                 state="float"))
        while True:  # Inputloop for general options
            action = get_action()
            if action.triggers(*quick_attacks):
                attack = figure.curr.attack_obs[
                    quick_attacks.index(
                        next(i for i in action if i in quick_attacks)
                    )
                ]
                if attack.ap > 0:
                    return attack
            elif action.triggers(Action.CHOOSE_ATTACK, Action.ACCEPT):
                attack = self.box(self, figure.curr.attack_obs)
                if attack != "":
                    return attack
            elif action.triggers(Action.RUN):
                if (
                    not enem.escapable
                    or not ask_bool(
                        self,
                        "Do you really want to run away?",
                        overview=self
                    )
                ):
                    continue
                if (
                    random.randint(0, 100) < max(
                        5,
                        min(
                            50 - (
                                figure.curr.initiative - enem.curr.initiative
                            ),
                            95
                        )
                    )
                ):
                    self.outp.outp("You failed to run away!")
                    time.sleep(SPEED_OF_TIME * 1)
                    return ""
                audio.switch("xDeviruchi - Decisive Battle (End).mp3")
                self.outp.outp("You ran away!")
                time.sleep(SPEED_OF_TIME * 2)
                self.clean_up(figure, enem)
                logging.info("[Fight] Ended, ran away")
                figure.curr.poke_stats.set_run_away_battle()
                audio.switch(figure.map.song)
                return "won"
            elif action.triggers(Action.CHOOSE_ITEM):
                items = [getattr(invitems, i)
                         for i in figure.inv
                         if getattr(invitems, i).func is not None
                         and figure.inv[i] > 0]
                if not items:
                    self.outp.outp(
                        "You don't have any items left!\n"
                        "What do you want to do?"
                    )
                    continue
                item = self.invbox(self, items, figure.inv)
                if item == "":
                    continue
                # I hate you python for not having switch statements
                if (i := getattr(fightitems, item.func)(figure, enem)) == 1:
                    continue
                if i == 2:
                    figure.curr.poke_stats.add_battle(True)
                    logging.info("[Fight] Ended, fightitem")
                    time.sleep(SPEED_OF_TIME * 2)
                    audio.switch(figure.map.song)
                    return "won"
                return ""
            elif action.triggers(Action.CHOOSE_POKE):
                if not self.choose_poke(figure):
                    self.show(init=True)
                    continue
                return ""
            std_loop(False, box=self)
            self.show()

    def fight(self, providers):
        """Fight between two Pokes
        ARGS:
            providers
        RETURNS:
            Provider that won the fight"""
        audio.switch("xDeviruchi - Decisive Battle (Loop).mp3")
        self.providers = providers
        logging.info(
            "[Fight] Started between %s",
            "and ".join(
                f"{prov.curr.name} ({type(prov)}) lvl. {prov.curr.lvl()}"
                for prov in self.providers
            )
        )
        self.resize_view()
        for prov in self.providers:
            prov.index_conf()
        if settings("animations").val:  # Intro animation
            animations.fight_intro(self.height, self.width)
        self.add_1(*self.providers)
        for prov in self.providers:
            prov.greet(self)
        time.sleep(SPEED_OF_TIME * 1)
        self.add_2(self.providers[0])
        self.fast_change(
            [self.providers[0].curr.ico, self.deadico2, self.deadico1,
             self.providers[0].curr.ico], self.providers[0].curr.ico)
        self.outp.outp(f"You used {self.providers[0].curr.name}")
        self.show()
        time.sleep(SPEED_OF_TIME * 0.5)
        index = self.providers.index(
            max(self.providers, key=lambda i: i.curr.initiative)
        )
        for prov in self.providers:
            i = prov.curr
            for j in i.effects:
                j.readd()
        while True:
            player = self.providers[index % 2]
            enem = self.providers[(index + 1) % 2]

            attack = player.get_attack(self, enem)
            time.sleep(SPEED_OF_TIME * 0.3)
            if attack == "won":
                return player
            if attack != "":
                player.curr.attack(attack, enem.curr, self, self.providers)
            self.show()
            time.sleep(SPEED_OF_TIME * 0.5)
            winner = None
            loser = None
            for i, prov in enumerate(self.providers):
                if prov.curr.hp <= 0:
                    loser = prov
                    winner = self.providers[(i + 1) % 2]
            if winner is not None:
                self.outp.outp(f"{loser.curr.ext_name} is dead!")
            elif all(i.ap == 0 for i in player.curr.attack_obs):
                winner = self.providers[(index + 1) % 2]
                loser = player
                time.sleep(SPEED_OF_TIME * 2)
                self.outp.outp(
                    f"{player.curr.ext_name} has used all its' attacks!")
                time.sleep(SPEED_OF_TIME * 3)
            if winner is not None:
                if any(p.hp > 0 for p in loser.pokes[:6]):
                    if not loser.handle_defeat(self, winner):
                        break
                else:
                    break
            index += 1
        audio.switch("xDeviruchi - Decisive Battle (End).mp3")
        time.sleep(SPEED_OF_TIME * 1)
        _xp = sum(
            poke.lose_xp + max(0, poke.lvl() - winner.curr.lvl())
            for poke in loser.pokes
        ) * loser.xp_multiplier
        self.outp.outp(
            f"{winner.curr.ext_name} won!" +
            (f'\nXP + {_xp}' if winner.curr.player else '')
        )
        if winner.curr.player and isinstance(loser, Trainer):
            achievements.achieve("first_duel")
        if winner.curr.player and winner.curr.add_xp(_xp * 2):
            time.sleep(SPEED_OF_TIME * 1)
            self.outp.outp(
                f"{winner.curr.name} reached lvl {winner.curr.lvl()}!"
            )
            winner.curr.moves.shine()
            time.sleep(SPEED_OF_TIME * 0.5)
            winner.curr.set_vars()
            winner.curr.learn_attack(self, self)
            winner.curr.evolve(winner, self)
        if winner.curr.player:
            winner.curr.poke_stats.add_battle(True)
        else:
            loser.curr.poke_stats.add_battle(False)
        self.show()
        time.sleep(SPEED_OF_TIME * 1)
        ico = loser.curr.ico
        self.fast_change([ico, self.deadico1, self.deadico2], ico)
        self.deadico2.remove()
        self.show()
        self.clean_up(*self.providers)
        mvp.movemap.balls_label_rechar(winner.pokes)
        logging.info(
            "[Fight] Ended, %s(%s) won",
            winner.curr.name, "player" if winner.curr.player else "enemy"
        )
        audio.switch(self.providers[0].map.song)
        return winner

    def choose_poke(self, player, allow_exit=True):
        """Lets the player choose another Pokete from their deck
        ARGS:
            player: The players' used Poke
            allow_exit: Whether or not it's allowed to exit without choosing
        RETURNS:
            bool whether or not a Pokete was choosen"""
        self.clean_up(player)
        index = None
        while index is None:
            index = deck.deck(self, 6, "Your deck", True)
            if allow_exit:
                break
        if index is not None:
            player.play_index = index
        self.add_player(player)
        self.outp.outp(f"You have choosen {player.curr.name}")
        for j in player.curr.effects:
            time.sleep(SPEED_OF_TIME * 1)
            j.readd()
        if index is None:
            return False
        return True


class FightItems:
    """Contains all fns callable by an item in fight
    The methods that can actually be called in fight follow
    the following pattern:
        ARGS:
            obj: The players Provider
            enem: The enemys Provider
        RETURNS:
            1: To continue the attack round
            2: To win the game
            None: To let the enemy attack"""

    @staticmethod
    def throw(obj, enem, chance, name):
        """Throws a ball
        ARGS:
            obj: The players Poke object
            enem: The enemys Poke object
            chance: The balls catch chance
            name: The balls name
        RETURNS:
            1: The continue the attack round
            2: The win the game
            None: To let the enemy attack"""

        if not isinstance(enem, NatureProvider):
            fightmap.outp.outp("You can't do that in a duel!")
            return 1
        fightmap.outp.rechar(f"You threw a {name.capitalize()}!")
        fightmap.fast_change(
            [enem.curr.ico, fightmap.deadico1, fightmap.deadico2,
             fightmap.pball], enem.curr.ico)
        time.sleep(SPEED_OF_TIME * random.choice([1, 2, 3, 4]))
        obj.remove_item(name)
        catch_chance = 20 if obj.map == obmp.ob_maps["playmap_1"] else 0
        for effect in enem.curr.effects:
            catch_chance += effect.catch_chance
        if random.choices([True, False],
                          weights=[(enem.curr.full_hp / enem.curr.hp)
                                   * chance + catch_chance,
                                   enem.curr.full_hp], k=1)[0]:
            audio.switch("xDeviruchi - Decisive Battle (End).mp3")
            obj.add_poke(enem.curr, caught_with=name)
            fightmap.outp.outp(f"You caught {enem.curr.name}!")
            time.sleep(SPEED_OF_TIME * 2)
            fightmap.pball.remove()
            fightmap.clean_up(obj, enem)
            mvp.movemap.balls_label_rechar(obj.pokes)
            logging.info("[Fighitem][%s] Caught %s", name, enem.curr.name)
            achievements.achieve("first_poke")
            if all(poke in obj.caught_pokes for poke in p_data.pokes):
                achievements.achieve("catch_em_all")
            return 2
        fightmap.outp.outp("You missed!")
        fightmap.show()
        fightmap.pball.remove()
        enem.curr.ico.add(fightmap, enem.curr.ico.x, enem.curr.ico.y)
        fightmap.show()
        logging.info("[Fighitem][%s] Missed", name)
        return None

    @staticmethod
    def potion(obj, hp, name):
        """Potion function
        ARGS:
            obj: The players Poke object
            hp: The hp that will be given to the Poke
            name: The potions name"""

        obj.remove_item(name)
        obj.curr.oldhp = obj.curr.hp
        obj.curr.hp = min(obj.curr.full_hp, obj.curr.hp + hp)
        obj.curr.hp_bar.update(obj.curr.oldhp)
        logging.info("[Fighitem][%s] Used", name)

    def heal_potion(self, obj, _):
        """Healing potion function"""
        return self.potion(obj, 5, "healing_potion")

    def super_potion(self, obj, _):
        """Super potion function"""
        return self.potion(obj, 15, "super_potion")

    def poketeball(self, obj, enem):
        """Poketeball function"""
        return self.throw(obj, enem, 1, "poketeball")

    def superball(self, obj, enem):
        """Superball function"""
        return self.throw(obj, enem, 6, "superball")

    def hyperball(self, obj, enem):
        """Hyperball function"""
        return self.throw(obj, enem, 1000, "hyperball")

    @staticmethod
    def ap_potion(obj, _):
        """AP potion function"""
        obj.remove_item("ap_potion")
        for atc in obj.curr.attack_obs:
            atc.set_ap(atc.max_ap)
        logging.info("[Fighitem][ap_potion] Used")


fightitems = FightItems()
fightmap: FightMap = None

if __name__ == "__main__":
    print("\033[31;1mDo not execute this!\033[0m")
