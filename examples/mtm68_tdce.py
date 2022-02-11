import sys
import json
from form_blocks import form_blocks
from util import flatten

def fix_map(last_def, idx):
    """
    Decreases all values by 1 that are greater or equal to idx in last_def.
    """
    for k in last_def.keys():
        if last_def[k] >= idx:
            last_def[k] = last_def[k] - 1

def use_defs(block):
    # var -> instrId; variables defined by inst but not yet used
    last_def = {} 
    deleted_inst = False

    j = 0
    for i in range(len(block)):
        instr = block[i-j]
        # check for use
        if 'args' in instr:
            for arg in instr['args']:
                if arg in last_def.keys():
                    del last_def[arg]

        # check for defs
        if 'dest' in instr:
            if instr['dest'] in last_def.keys():
                idx = last_def[instr['dest']]
                block.pop(idx)
                fix_map(last_def, idx)
                last_def[instr['dest']] = i
                deleted_inst = True
                j+=1
            else:
                last_def[instr['dest']] = i

    return deleted_inst 

def remove_unused(instrs):
    """
    Removes from instrs where variables are defined but never used 
    by instrunctions later in the list.
    """
    defined_but_not_used = set()
    for instr in instrs:
        if 'args' in instr:
            for arg in instr['args']:
                defined_but_not_used.remove(arg)
        if 'dest' in instr:
            defined_but_not_used.add(instr['dest'])

    new_instrs = []
    for instr in instrs:
        if 'dest' not in instr or instr['dest'] not in defined_but_not_used:
            new_instrs.append(instr)
        else:
            deleted = True

    instrs[:] = new_instrs 



def tdce_block(block):
    """
    Repeatedly runs TDCE pass on block until no instrunctions are removed
    by the pass.
    """
    while True:
        deleted_inst = use_defs(block)
        if not deleted_inst:
            break

def tdce_prog(prog):
    """
    Performs TDCE until convergence on each function in the entire program,
    and then deletes trivially globally dead variables and removes them.
    Then prints out the optimized program in JSON form.
    """
    for func in prog['functions']:
        blocks = list(form_blocks(func['instrs']))
        for block in blocks:
            tdce_block(block)
        instrs  = flatten(blocks)
        remove_unused(instrs) # Globally removes variables never used
        func['instrs'] = instrs
    json.dump(prog, sys.stdout, indent=2, sort_keys=True)

if __name__ == "__main__":
    tdce_prog(json.load(sys.stdin))
