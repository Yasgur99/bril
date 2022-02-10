import json
import sys
from form_blocks import form_blocks
from util import flatten

ID_COUNTER = 0
def fresh_id():
    global ID_COUNTER
    ID_COUNTER += 1
    return ID_COUNTER

def get_value(instr):
    value = []
    value.append(instr['op'])
    if 'args' in instr:
        value.extend(instr['args'])
    elif 'value' in instr:
        value.append(instr['value'])
    return tuple(value)

def will_be_overwritten(inst):
    return False

def replace_arg(arg, id_to_canonical, env):
    iD = env[arg]
    return id_to_canonical[iD]

def replace_args(args, id_to_canonical, env):
    new_args = []
    for arg in args:
        new_arg = replace_arg(arg, id_to_canonical, env)
        new_args.append(new_arg)
    return new_args

def get_overwrittens(block):
    dests_overwrittens = {}
    for instr in block:
        if 'dest' in instr:
            dest = instr['dest']
            if dest in dests_overwrittens:
                dests_overwrittens[dest] = True
            else:
                dests_overwrittens[dest] = False
    return dests_overwrittens

def fresh_dest(old_dest, dests_overwritten):
    while old_dest in dests_overwritten.keys():
        old_dest += "'"
    dests_overwritten[old_dest] = False
    return old_dest

def lvn_block(block):
    id_to_val = {}
    id_to_canonical = {}
    val_to_id = {}
    env = {}
    # Keys = all dests; Value = whether that dest gets overwritten later
    dests_overwritten = get_overwrittens(block)

    for instr in block:
        value = get_value(instr)
        if value in val_to_id.keys():
            iD = val_to_id[value]
            var = id_to_canonical[iD]
            if 'dest' in instr:
                env[instr['dest']] = iD
                instr['dest'] = id_to_canonical[iD]
        else:
            iD = fresh_id()
            if 'dest' in instr and dests_overwritten[instr['dest']]:
                dest = fresh_dest(instr['dest'], dests_overwritten)
                instr['dest'] = dest
            elif 'dest' in instr:
                dest = instr['dest']

            id_to_val[iD] = value
            id_to_canonical[iD] = dest
            val_to_id[value] = iD

            if 'args' in instr:
                new_args = replace_args(instr['args'],   \
                                        id_to_canonical, \
                                        env)
                instr['args'] = new_args

        if 'dest' in instr:
            env[instr['dest']] = iD
    return block

def lvn(prog):
    for func in prog['functions']:
        blocks = list(form_blocks(func['instrs']))
        opt_blocks = map(lvn_block, blocks)
        func['instrs'] = flatten(opt_blocks)
    json.dump(prog, sys.stdout, indent=2, sort_keys=True)


if __name__ == '__main__':
    lvn(json.load(sys.stdin))
