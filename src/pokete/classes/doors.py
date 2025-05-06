"""Contains doors"""

import random
import scrap_engine as se
from . import game, ob_maps as obmp
from pokete.base.input_loops import ask_bool


class CenterDoor(se.Object):
    """Door class for the map to enter centers and shops"""

    def action(self, ob):
        """Trigger
        ARGS:
            ob: The object triggering this action"""
        ob.remove()
        i = ob.map.name
        ob.add(ob.oldmap,
               ob.oldmap.dor.x
               if ob.map == obmp.ob_maps["centermap"]
               else ob.oldmap.shopdor.x,
               ob.oldmap.dor.y + 1
               if ob.map == obmp.ob_maps["centermap"]
               else ob.oldmap.shopdor.y + 1)
        ob.oldmap = obmp.ob_maps[i]
        raise game.MapChangeExeption(ob.map)


class Door(se.Object):
    """Door class for the map to enter other maps"""

    def action(self, ob):
        """Trigger
        ARGS:
            ob: The object triggering this action"""
        # Check if the current map is an arena based on its pretty_name
        is_arena = "Arena" in getattr(ob.map, "pretty_name", "")

        # If it's an arena, check if all trainers have been defeated
        if is_arena and hasattr(ob.map, "trainers") and ob.map.trainers:
            all_trainers_used = all(trainer.used for trainer in ob.map.trainers)
            if not all_trainers_used:
                # Not all trainers have been defeated, prevent the player from leaving
                ob.map.outp.outp("You must win or lose against all trainers in this arena before leaving!")
                ob.map.full_show()
                return

        # If it's not an arena or all trainers have been defeated, allow the player to leave
        if not is_arena or all(trainer.used for trainer in ob.map.trainers):
            ob.remove()
            i = ob.map.name
            ob.add(obmp.ob_maps[self.arg_proto["map"]], self.arg_proto["x"],
                   self.arg_proto["y"])
            ob.oldmap = obmp.ob_maps[i]
            raise game.MapChangeExeption(obmp.ob_maps[self.arg_proto["map"]])


class DoorToCenter(Door):
    """Door that leads to the Pokete center"""

    def __init__(self):
        super().__init__("#", state="float",
                         arg_proto={"map": "centermap",
                                    "x": int(
                                        obmp.ob_maps["centermap"].width / 2),
                                    "y": 7})

    def action(self, ob):
        """Triggers the door
        ARGS:
            ob: The object triggering this action"""
        ob.last_center_map = ob.map
        super().action(ob)


class DoorToShop(Door):
    """Door that leads to the shop"""

    def __init__(self):
        super().__init__("#", state="float",
                         arg_proto={"map": "shopmap",
                                    "x": int(obmp.ob_maps["shopmap"].width / 2),
                                    "y": 7})


class ChanceDoor(Door):
    """Same as door but with a chance"""

    def action(self, ob):
        """Trigger
        ARGS:
            ob: The object triggering this action"""
        if random.randint(0, self.arg_proto["chance"]) == 0:
            super().action(ob)




if __name__ == "__main__":
    print("\033[31;1mDo not execute this!\033[0m")
