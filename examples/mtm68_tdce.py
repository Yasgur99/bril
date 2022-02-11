import sys
import json
from form_blocks import form_blocks
from util import flatten

def fix_map(last_def, idx):
    """
    Decreases all values by 1 that are greater to idx in last_def.
    """
    for k in last_def.keys():
        if last_def[k] > idx:
            last_def[k] = last_def[k] - 1

def removed_overwritten_before_use(block):
    last_def = {} # var -> instrIdx; 
    deleted_inst = False
    j = 0 # used to keep index in bounds because deleting during iterating
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
                last_def[instr['dest']] = i - 1
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
                if arg in defined_but_not_used:
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

def tdce_until_converge(instrs):
    """
    Peforms global trivial dead code elimination followed by local
    trivial dead code elimination until the size of instrunctions
    converges.
    """
    len1 = len(instrs)
    remove_unused(instrs) 

    blocks = list(form_blocks(instrs))
    for block in blocks:
        removed_overwritten_before_use(block) 
    instrs = flatten(blocks)
    len2 = len(instrs)

    if len1 != len2:
        return tdce_until_converge(instrs)
    else:
       return instrs 


def tdce_prog(prog):
    """
    Performs TDCE until convergence on each function in the entire program,
    and then deletes trivially globally dead variables and removes them.
    Then prints out the optimized program in JSON form.
    """
    for func in prog['functions']:
        func['instrs'] = tdce_until_converge(func['instrs'])

    json.dump(prog, sys.stdout, indent=2, sort_keys=True)

if __name__ == "__main__":
    tdce_prog(json.load(sys.stdin))
