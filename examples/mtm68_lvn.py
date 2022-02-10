import json
import sys
from form_blocks import form_blocks
from util import flatten

ID_COUNTER = 0
def fresh_id():
    """
    Returns an integer with the condition that this function never returns
    the same integer more than once (unless we call more than INT_MAX times)
    """
    global ID_COUNTER
    ID_COUNTER += 1
    return ID_COUNTER

def get_value(instr):
    """
    Creates a value based on the op of the instruction and
    the args or value if any.
    """
    value = []
    value.append(instr['op'])
    if 'args' in instr:
        value.extend(instr['args'])
    elif 'value' in instr:
        value.append(instr['value'])
    return tuple(value)

def replace_arg(arg, id_to_canonical, env):
    """
    Replaces arg with the canonical argument that holds the
    value that arg should contain
    """
    iD = env[arg]
    return id_to_canonical[iD]

def replace_args(args, id_to_canonical, env):
    """
    Replaces args with the canonical argument that holds the
    value each arg should contain
    """
    new_args = []
    for arg in args:
        new_arg = replace_arg(arg, id_to_canonical, env)
        new_args.append(new_arg)
    return new_args

def get_overwrittens(block):
    """
    Creates a map where keys are all destination registers in the program
    with value signifying whether or not that destination is written at least
    once more again in the program.
    """
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
    """
    Creates a new destination that is not used anywhere else in
    the program. Also adds the new dest to the dest_overwritten keys
    with a value of False, since this new dest is not used elsewhere.
    """
    while old_dest in dests_overwritten.keys():
        old_dest += "'"
    dests_overwritten[old_dest] = False
    return old_dest

def lvn_block(block):
    """
    Performs LVN on a given block
    """
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
    """
    Performs LVN on prog and prints LVNified program to stdout.
    """
    for func in prog['functions']:
        blocks = list(form_blocks(func['instrs']))
        opt_blocks = map(lvn_block, blocks)
        func['instrs'] = flatten(opt_blocks)
    json.dump(prog, sys.stdout, indent=2, sort_keys=True)


if __name__ == '__main__':
    lvn(json.load(sys.stdin))
