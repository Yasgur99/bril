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

COMMUTATIVE_OPS = ['add', 'mul', 'eq', 'and']
def get_value(instr):
    """
    Creates a value based on the op of the instruction and
    the args or value if any.
    """
    value = []
    value.append(instr['op'])
    if 'args' in instr:
        if instr['op'] in COMMUTATIVE_OPS:
            value.extend(sorted(instr['args']))
        else:
            value.extend(instr['args'])
    elif 'value' in instr:
        value.append(instr['value'])
    return tuple(value)

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
                dests_overwrittens[dest] = dests_overwrittens[dest] + 1
            else:
                dests_overwrittens[dest] = 0
    return dests_overwrittens

DEST_COUNTER = 0
def fresh_dest(old_dest, dests_overwritten):
    """
    Creates a new destination that is not used anywhere else in
    the program. Also adds the new dest to the dest_overwritten keys
    with a value of False, since this new dest is not used elsewhere.
    """
    # Generate fresh dest
    global DEST_COUNTER
    new_dest = "lvn.{}".format(DEST_COUNTER)
    DEST_COUNTER += 1

    while new_dest in dests_overwritten.keys():
        new_dest += "lvn.{}".format(DEST_COUNTER)
        DEST_COUNTER += 1

    # Update map accordingly 
    dests_overwritten[old_dest] = dests_overwritten[old_dest] - 1
    dests_overwritten[new_dest] = 0

    return new_dest 

def handle_args(block, id_to_canonical, env):
    read = set()
    written = set()

    for instr in block:
        read.update(set(instr.get('args', [])) - written)
        if 'dest' in instr:
            written.add(instr['dest'])

    for v in read:
        iD = fresh_id()
        id_to_canonical[iD] = v
        env[v] = iD

def lvn_block(block):
    """
    Performs LVN on a given block
    """
    id_to_val = {}
    id_to_canonical = {}
    val_to_id = {}
    env = {}
    dests_overwritten = get_overwrittens(block)

    # Some variables are passed to function. These won't have
    # vals but need to be added to table for canonical reasons
    handle_args(block, id_to_canonical, env)

    for instr in block:
        # We only care about real instructions
        if 'label' in instr:
            continue 

        value = get_value(instr)

        # Don't recompute the value, set dest to canonical instead
        if value in val_to_id.keys():
            iD = val_to_id[value]
            var = id_to_canonical[iD]
            if 'dest' in instr:
                instr.update({'op' : 'id', 'args' : [id_to_canonical[iD]]})

        # Put value into table
        else:
            iD = fresh_id()

            if 'dest' in instr and dests_overwritten[instr['dest']] > 0:
                dest = fresh_dest(instr['dest'], dests_overwritten)
                env[instr['dest']] = iD
                instr['dest'] = dest
            elif 'dest' in instr:
                dest = instr['dest']

            if 'dest' in instr:
                id_to_val[iD] = value
                id_to_canonical[iD] = dest
                val_to_id[value] = iD

            # Use values from table instead of original values
            if 'args' in instr:
                instr['args'] = [id_to_canonical[env[arg]] \
                        for arg in instr['args']]

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
