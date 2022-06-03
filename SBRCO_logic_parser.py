import re
from Resources.res.charms import charms


def resolve_logic_dict(logic, config):
    new_logic = {}
    maxcounter = 0
    for k, v in logic.items():  # remove parentheses
        new_logic[k], dic, maxcounter = parse_parentheses(v, new_logic, maxcounter)
        new_logic.update({k: v for k, v in dic.items() if k not in new_logic})
    logic = new_logic.copy()
    # print(logic, "\n")
    for k, v in logic.items():  # remove negate
        new_logic[k], dic, maxcounter = parse_negate(v, new_logic, maxcounter)
        new_logic.update({k: v for k, v in dic.items() if k not in new_logic})
    logic = new_logic.copy()
    # print(logic, "\n")
    for k, v in logic.items():  # remove plus
        new_logic[k], dic, maxcounter = parse_plus(v, new_logic, maxcounter)
        new_logic.update({k: v for k, v in dic.items() if k not in new_logic})
    logic = new_logic.copy()
    # print(logic, "\n")
    logic.update(config)  # add config values
    return logic


def parse_parentheses(value: str, logic_dict: dict, maxcounter: int):
    dic = logic_dict.copy()
    new_value = sanitize(value)
    inner_values = re.findall("\\([^()]*\\)", new_value)  # all values within innermost parentheses
    if not inner_values:
        return new_value, dic, maxcounter
    for inner in inner_values:
        inner = sanitize(inner)
        # find the (only) item in the dict that maps to this value inside parentheses (we only need one macro per expression)
        counter = [k for k, v in dic.items() if v == inner[1:-1] and re.match("^<.*>$", k)]
        assert len(counter) <= 1
        if counter:
            counter = counter[0]
        else:  # didn't find an existing macro, so we create a new one
            maxcounter += 1
            counter = f"<{maxcounter}>"
            dic[counter] = inner[1:-1]
        new_value = sanitize(new_value.replace(inner, f" {counter} "))
    return parse_parentheses(new_value, dic, maxcounter)


def parse_negate(value: str, logic_dict: dict, maxcounter: int):
    dic = logic_dict.copy()
    value = sanitize(value)
    while value.find("!") + 1:
        i = value.index("!")
        end = value.find(" ", i)
        if end + 1:
            new_value = value[i:end]
        else:
            new_value = value[i:]
        new_value = sanitize(new_value)
        counter = [k for k, v in dic.items() if v == new_value and re.match("^<.*>$", k)]
        assert len(counter) <= 1
        if counter:
            counter = counter[0]
        else:
            maxcounter += 1
            counter = f"<{maxcounter}>"
            dic[counter] = new_value
        value = sanitize(value.replace(new_value, counter))
    return value, dic, maxcounter


def parse_plus(value: str, logic_dict: dict, maxcounter: int):
    dic = logic_dict.copy()
    value = sanitize(value)
    plus_seqs = re.findall("\\|[^|]*\\+[^|]*|[^|]*\\+[^|]*\\|", value)
    for seq in plus_seqs:
        seq = sanitize(seq.replace("|", " "))
        counter = [k for k, v in dic.items() if v == seq and re.match("^<.*>$", k)]
        assert len(counter) <= 1
        if counter:
            counter = counter[0]
        else:
            maxcounter += 1
            counter = f"<{maxcounter}>"
            dic[counter] = seq
        value = sanitize(value.replace(seq, counter))
    return value, dic, maxcounter


def parse_entry(value, logic: dict, added: list, level: int=0, print=print):
    """parse the lowest level of a logic expression (i.e. single words, single negations,
    plus-separated words or ||-separated words). words include charm names, settings names
    and number restrictions"""
    index = len(added)
    print(" " * level, f"{'-'if not level else''} {value}", f" ({len(added)})"if not level else"", sep="")
    if isinstance(value, bool):
        return value
    value = value.strip()
    if level > 0:
        if value in charms:
            if value in added:
                print(" " * level, "• in added (True)")
                # update_sender.send("parser", "req charm in list", value)
                return True
            else:
                print(" " * level, "• not in added (False)")
                return False
    if "|" in value:
        or_list = value.split("||")
        vs = tuple(parse_entry(v.strip(), logic, added, level + 1, print=print) for v in or_list)
        any_non_booleans = tuple(v for v in vs if not isinstance(v, bool))
        if any_non_booleans:
            assert len(any_non_booleans) == 1
            remainder = list(set(vs) - set(any_non_booleans))
            if any(remainder):
                print(" " * level, ">>", " || ".join(str(s) for s in vs), "= True (ignored non-bools)")
                return True
            print(" " * level, ">>", " || ".join(str(s) for s in vs), "=", any_non_booleans[0])
            return any_non_booleans[0]
        print(" " * level, ">>", " || ".join(str(s) for s in vs), "=", any(vs))
        return any(vs)
    if "+" in value:
        and_list = value.split("+")
        vs = tuple(parse_entry(v.strip(), logic, added, level + 1, print=print) for v in and_list)
        any_non_booleans = tuple(v for v in vs if not isinstance(v, bool))
        if any_non_booleans:
            assert len(any_non_booleans) == 1
            remainder = list(set(vs) - set(any_non_booleans))
            if all(remainder):
                print(" " * level, ">>", " + ".join(str(s) for s in vs), "=", any_non_booleans[0])
                return any_non_booleans[0]
            print(" " * level, ">>", " + ".join(str(s) for s in vs), "= False (ignored non-bools)")
            return False
        print(" " * level, ">>", " + ".join(str(s) for s in vs), "=", all(vs))
        return all(vs)
    if "!" in value:
        v = parse_entry(value[1:], logic, added, level + 1, print=print)
        if isinstance(v, bool):
            print(" " * level, ">> !", v, "=", not v)
            return not v
        raise ValueError("v is not a bool but was negated")
    if "-" in value:
        if value.startswith("-"):
            value = "0" + value
        elif value.endswith("-"):
            value = value + "39"
        start, end = [int(v) for v in value.split("-")]
        print(" " * level, "•", start, "<=", index, "<=", end, "?")
        if start <= index <= end:
            print(" " * level, ">> yes (True)")
            return True
        if end < index:
            print(" " * level, ">> overdue")
            return start, end
        print(" " * level, ">> no, too early (False)")
        return False
    if value in logic:
        print(" " * level, "• in logic, gives:", end=" ")
        return parse_entry(logic[value], logic, added, level + 1, print=print)
    print(" " * level, "• doesn't match any logic")
    if value in charms:  # and level == 0, i.e. we are just asking if an undefined charm at top level may be added
        print(" " * level, "•", value, "in charms (True)")
        return True
    print(" " * level, "•", value, "not in charms (False)")
    return False


def create_logic(logic: str, config: dict):
    logic_parts = []
    for line in logic.split("\n"):
        if line.strip() and not line.strip().startswith("#"):
            logic_parts.append(line.strip())
    logic = {}
    for part in logic_parts:
        k, v = part.split(":")
        logic[k.strip()] = v.strip()
    #print(logic)
    new_logic = resolve_logic_dict(logic, config)
    return new_logic


def sanitize(s: str):
    """remove double spaces"""
    while "  " in s:
        s = s.replace("  ", " ")
    return s.strip()


if __name__ == "__main__":
    from Resources.config.logic_config import config
    with open("Resources/config/logic.txt") as f:
        logic = f.read()
    new_logic = create_logic(logic, config)
    print(new_logic)
