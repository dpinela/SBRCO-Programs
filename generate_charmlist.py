import random
from Resources.res.charms import charms as vanilla_charms
from SBRCO_logic_parser import parse_entry, resolve_logic_dict, create_logic
from functools import wraps


def update_params(sentryclass, *params):
    """class decorator; wrap all class attributes specified as strings in *params with
    a "send" function of the sentryclass. this send function is passed the following
    *args: <wrapped_function.__name__>, <wrapped_function *args>, <wrapped_function return value>"""
    def decorator(cls):
        def closure(function, *args, **kw):
            """necessary because otherwise, the sentryclass.send function will be evaluated and bound
            at define-time, rather than runtime, which we want in order to be able to override it from outside the module"""
            @wraps(function)
            def wrapper(*args, **kw):
                x = function(*args, **kw)
                sentryclass.send(function.__name__, *args, x)
                return x
            return wrapper
        for param in params:
            function = getattr(cls, param)
            wrapper = closure(function)
            setattr(cls, param, wrapper)
        return cls
    return decorator


class update_sender:
    def __init__(self, send=None, list_send=None, tmplist_send=None):
        if hasattr(send, "__call__"):
            self.send = send
        if hasattr(list_send, "__call__"):
            self.list_send = list_send
        else:
            self.list_send = self.create_class_list_send()
        if hasattr(tmplist_send, "__call__"):
            self.tmplist_send = tmplist_send
        else:
            self.tmplist_send = self.create_class_tmplist_send()

    @staticmethod
    def send(*args):
        pass

    list_send = list
    tmplist_send = list

    def create_class_list_send(self):
        """we need to create and modify the class for each new instance of update_sender, otherwise the lists created
        in generate_charm_order() won't be coupled with this instance's send function and no updates will be received"""
        @update_params(self, "append", "insert", "remove", "__contains__")
        class list_send(list):
            pass
        return list_send

    def create_class_tmplist_send(self):
        @update_params(self, "pop")
        class tmplist_send(list):
            pass
        return tmplist_send


def generate_charm_order(logic: dict, update_sender=update_sender, seed: int=False, print=print):
    if seed:
        print("seed:", seed)
    charmlist = update_sender.list_send()
    charms = vanilla_charms.copy()
    r = random.Random()  # this will make it so any local random calls will share the same state (e.g. seed)
    if seed is not False and seed is not None:
        r.seed(seed)
    while charms:
        charm = r.choice(charms)
        update_sender.send("generate", "attempt add new charm", charm, len(charmlist))
        result = parse_entry(charm, logic, charmlist, print=print)
        if result is True:
            charmlist.append(charm)
            charms.remove(charm)
            print("added", charm, f"({charmlist.index(charm)})")
            continue
        if result is False:
            continue
        assert isinstance(result, tuple)  # we are overdue on this charm's rule
        temp_list = update_sender.tmplist_send(charmlist)#.copy()
        temp_result = result
        req_charm = None
        while isinstance(temp_result, tuple):
            try:
                req_charm = temp_list.pop()
            except IndexError:
                # we didn't have any charm requirements, can simply insert charm within range
                req_charm = None
                print("got tuple", result, "even for list length 0, yet no charm requirements found. "
                      "this shouldn't really be possible, but aaanyway, inserting charm at a random "
                      "point within list")
                break
            temp_result = parse_entry(charm, logic, temp_list, print=print)
            update_sender.send("generate", "move charm forward overdue", charm, temp_result, temp_list)
        if not req_charm:  # we shouldn't even get here
            index = r.randint(result[0], result[1])
            charmlist.insert(index, charm)
            charms.remove(charm)
            print("added", charm, index)
            raise ValueError("how did you get here?")
            continue
        if temp_result is True:
            # we found a position for charm that is definitely valid
            index = len(temp_list)
            while parse_entry(charm, logic, temp_list, print=print) is True:  # shuffle new position within valid range
                try:
                    temp_list.pop()
                except IndexError:
                    break
                update_sender.send("generate", "move charm forward inbounds", charm, temp_list)
            earliest = len(temp_list) + (1 if temp_list else 0)  # if we were stopped by a req charm, +1, if by IndexError, +0
            charmlist.insert(r.randint(earliest, index), charm)
            charms.remove(charm)
            print("added", charm, f"({charmlist.index(charm)})")
        elif temp_result is False:  # req charm is most likely the required one
            # insert req charm at a random point within result-range and check validity
            index_choices = list(range(result[1]))
            index = -1
            while index_choices:
                index = index_choices.pop(r.randrange(len(index_choices)))
                if parse_entry(req_charm, logic, temp_list[:index], print=print) is True:
                    # we found a valid place for req_charm
                    break
                index = -1
            if index + 1:  # we got a valid index
                charmlist.remove(req_charm)
                charmlist.insert(index, req_charm)
            else:  # there was no valid index, which means that req_charm has complex restrictions
                print(f"while trying to find a valid position for {charm}, had to move requirement",
                      f"{req_charm} within range for {charm} (before pos {result[1]}) but couldn't",
                      f"find valid position. {req_charm} may have complex requirements. inserting",
                      f"{charm} at earliest possible position behind {req_charm} ({len(temp_list) + 1}).")
                charmlist.insert(len(temp_list) + 1, charm)
                charms.remove(charm)
                print("added", charm, len(temp_list) + 1)
                continue
    return charmlist


if __name__ == "__main__":
    # example config
    from config.logic_config import config
    from list_permutations import index
    from base64 import b64encode
    from charm_select import generate_charm_orderlist
    with open("config/logic.txt") as f:
        logic = f.read()
    logic = create_logic(logic, config)
    charmlist = generate_charm_order(logic)
    print("\n", charmlist)
    charmlist_id = index(generate_charm_orderlist(charmlist))
    print("charmlist in base10:", charmlist_id)
    print("charmlist in base64:", b64encode(charmlist_id.to_bytes(20, "big")).decode())
