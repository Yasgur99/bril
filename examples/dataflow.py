import sys
import json
from enum import Enum, auto
from form_blocks import form_blocks

########################################################
# CFG with ability to get pred and succ for each block
# in O(1) time
########################################################
class Cfg:
    def __init__(self, blocks):
        self.blocks = blocks
        self.succ = {}
        self.pred = {}

        lbl_to_block = {}
        for block in blocks:
            lbl = block[0]['label']
            lbl_to_block[lbl] = block

        # Setup first block pred
        self.create_pred(None, blocks[0])
        for i in range(len(blocks)):
            block = blocks[i]
            last = block[-1]
            if 'op' in last and last['op'] == 'jmp':
                lbl = last['labels'][0]
                next_block = lbl_to_block[lbl]
                self.create_succ(block, next_block)
                self.create_pred(block, next_block)
            elif 'op' in last and last['op'] == 'br':
                true_lbl = last['labels'][0]
                true_block = lbl_to_block[true_lbl]
                self.create_succ(block, true_block)
                self.create_pred(block, true_block)

                false_lbl = last['labels'][1]
                false_block = lbl_to_block[false_lbl]
                self.create_succ(block, false_block)
                self.create_pred(block, false_block)
            else:
                more_blocks = i < len(blocks) - 1
                next_block = blocks[i+1] if more_blocks else None
                self.create_succ(block, next_block)
                self.create_pred(block, next_block)

    def create_succ(self, block, next_block):
        block_name = block[0]['label']
        if block_name in self.succ.keys() and next_block != None:
            lst = self.succ[block_name]
            lst.append(next_block)
        elif next_block != None:
            self.succ[block_name] = [next_block]
        else:
            self.succ[block_name] = []

    def create_pred(self, block, next_block):
        if next_block is None:
            return

        next_block_name = next_block[0]['label']
        if block is None:
            self.pred[next_block_name] = []
            return
        if next_block_name in self.pred.keys():
            lst = self.pred[next_block_name]
            lst.append(block)
        else :
            self.pred[next_block_name] = [block]

    def get_succ(self, block):
        return self.succ[block[0]['label']]

    def get_pred(self, block):
        return self.pred[block[0]['label']]

########################################################
# Dataflow Framework
########################################################

class Analysis:
    def __init__(self, init_val, transfer, merge, direction):
        self.init_val = init_val
        self.transfer = transfer
        self.merge = merge
        self.direction = direction

class DfSet:
    def __init__(self, items, isTop=False):
        self.items = items
        self.isTop = isTop

class InitVal(Enum):
    EMPTY = auto()
    TOP = auto()

class Direction(Enum):
    FORWARD = auto()
    BACKWARD = auto()

def union(a, b):
    if a.isTop or b.isTop:
        return a
    else:
        return DfSet(a.items.union(b.items))

def intersection(a, b):
    if a.isTop:
        return b
    elif b.isTop:
        return a
    else:
        return DfSet(a.items.intersection(b.items))

def difference(a, b):
    return DfSet(a.items.difference(b.items))

def init_in(a, blocks):
    isTop = a.init_val == InitVal.TOP
    in_ = {}
    if a.direction == Direction.FORWARD and blocks:
        in_[blocks[0][0]['label']] = DfSet(set(), isTop)
    else:
        for block in blocks:
            in_[block[0]['label']] = DfSet(set(), isTop)
    return in_

def init_out(a, blocks):
    isTop = a.init_val == InitVal.TOP
    out = {}
    if a.direction == Direction.FORWARD:
        for block in blocks:
            out[block[0]['label']] = DfSet(set(), isTop)
    elif blocks:
        out[blocks[-1][0]['label']] = DfSet(set(), isTop)
    return out

def worklist(a, cfg):
    in_ = init_in(a, cfg.blocks)
    out = init_out(a, cfg.blocks)

    worklist = cfg.blocks[:]
    while worklist:
        if a.direction == Direction.FORWARD:
            block = worklist.pop(0)
            name = block_name(block)
            for pred in cfg.get_pred(block):
                if name in in_.keys():
                    x = in_[name]
                else:
                    x = DfSet(set(), a.init_val == InitVal.TOP)
                in_[name] = a.merge(out[block_name(pred)], x)

            len_before = len(out[name].items)
            out[name] = a.transfer(block, in_[name])
            len_after = len(out[name].items)
            add_to_worklist = cfg.get_succ(block)
        else:
            block = worklist.pop()
            name = block_name(block)
            for succ in cfg.get_succ(block):
                if name in out.keys():
                    x = out[name]
                else:
                    x = DfSet(set(), a.init_val == InitVal.TOP)
                out[name] = a.merge(in_[block_name(succ)], x)

            len_before = len(in_[name].items)
            in_[name] = a.transfer(block, out[name])
            len_after = len(in_[name].items)
            add_to_worklist = cfg.get_pred(block)

        if len_before != len_after:
            for b in add_to_worklist:
                worklist.append(b)

    return in_, out

def block_name(block):
    return block[0]['label']

def print_vars(varz):
    l = len(varz.items)
    if l == 0:
        print('\u2205')
    else:
        i = 0
        for var in varz.items:
            print(var, end = '')
            if i < l -1:
                print(", ", end ='')
            i += 1
        print('')

def print_analysis(blocks, info):
    in_, out = info
    for block in blocks:
        name = block_name(block)
        print(name + ':')

        in_b = in_[name]
        print('  in:  ', end='')
        print_vars(in_b)

        out_b = out[name]
        print('  out: ', end ='')
        print_vars(out_b)

def df(prog, a):
    for func in prog['functions']:
        blocks = list(form_blocks(func['instrs']))
        cfg = Cfg(blocks)
        info  = worklist(a, cfg)
        print_analysis(blocks, info)


########################################################
# Live Variable Analysis
########################################################
def live_var_transfer(b, out):
    return union(use(b), difference(out, defn(b)))

def use(block):
    use = set()
    defn = set()
    for instr in block:
        if 'args' in instr:
            for arg in instr['args']:
                if arg not in defn:
                    use.add(arg)
        if 'dest' in instr:
            defn.add(instr['dest'])
    return DfSet(use)

########################################################
# Defined Variable Analysis
########################################################
def defined_var_transfer(b, in_):
    return union(defn(b), in_)

########################################################
# Reaching Definitions Analysis
########################################################

def defn(block):
    defs = set()
    for instr in block:
        if 'dest' in instr:
            defs.add(instr['dest'])
    return DfSet(defs)

def kills(block):
    kills = set()
    for instr in block:
        if 'dest' in instr:
            kills.add(instr['dest'])
    return DfSet(kills)

def reaching_defns_transfer(b, in_):
     return union(defn(b), difference(in_, kills(b)))

########################################################
# All Analysis to choose from
########################################################
ANALYSES = {
    'reaching-defns' : Analysis(
        InitVal.EMPTY,
        reaching_defns_transfer,
        union,
        Direction.FORWARD
    ),
    'defined' : Analysis(
        InitVal.EMPTY,
        defined_var_transfer,
        union,
        Direction.FORWARD
    ),
    'live' : Analysis(
        InitVal.EMPTY,
        live_var_transfer,
        union,
        Direction.BACKWARD
    )
}

if __name__ == '__main__':
    df(json.load(sys.stdin), ANALYSES[sys.argv[1]])

