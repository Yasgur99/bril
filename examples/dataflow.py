from enum import Enum, auto
class Cfg:

    def Cfg(self, blocks):
        self.blocks = blocks
        self.succ = {}
        self.pred = {}

        lbl_to_block = {}
        for block in blocks:
            lbl = block[0]['label']
            lbl_to_block[lbl] = block

        for i in range(len(blocks)):
            block = blocks[i]
            last = block[-1]
            if 'op' in last and last['op'] == 'jmp':
                lbl = last['labels'][0]
                next_block = lbl_to_block[lbl]
                create_succ(block, next_block)
                create_pred(block, next_block)
            elif 'op' in last and last['op'] == 'br':
                true_lbl = last['labels'][0]
                true_block = lbl_to_block[true_lbl]
                create_succ(block, true_block)
                create_pred(block, true_block)

                false_lbl = last['labels'][1]
                false_block = lbl_to_block[false_lbl]
                create_succ(block, false_block)
                create_pred(block, false_block)
            else:
                more_blocks = i < len(blocks) - 1
                next_block = blocks[i+1] if more_blocks else None
                create_succ(block, next_block)
                create_pred(block, next_block)

    def create_succ(self, block, next_block):
        if block in self.succ.keys() and next_block is not None:
            lst = self.succ[block]
            lst.append(next_block)
        else if next_block is not None:
            self.succ[block] = [next_block]
        else:
            self.succ[block] = []

    def create_pred(self, block, next_block):
        if next_block in self.pred.keys() and next_block is not None:
            lst = self.pred[next_block]
            lst.append(block)
        elif next_block is not None:
            self.pred[next_block] = [block]
        else:
            self.pred[block] = []

    def succ(block):
        return self.succ[block]

    def pred(block):
        return self.pred[block]

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
    def __init__(self, items):
        self.items = items
        self.isTop = False

    def __init__(self, isTop):
        self.isTop = isTop
        if not isTop:
            self.items = set()

class InitVal(Enum):
    EMPTY = auto()
    TOP = auto()

class Direction(Enum):
    FORWARD = auto()
    BACKWARD = auto()

def union(a, b):
    return a.union(b)

def intersection(a, b):
    if a.isTop:
        return b
    elif b.isTop:
        return a
    else
        return DfSet(a.items.intersection(b.items))

def difference(a, b):
    return DfSet(a.items.difference(b.items))

def init_in(a, blocks):
    b_len = len(blocks)
    isTop = a.init_val == InitVal.EMPTY
    return [DfSet(isTop) for i in range(b_len)]

def init_out(a, blocks):
    b_len = len(blocks)

def worklist(a, cfg):
    in_ = init_in(a, cfg.blocks)
    out = init_out(a, cfg.blocks)

    worklist = cfg.blocks[:]
    while worklist:
        block = worklist.pop()

        if a.direction = Direction.FORWARD:
            for pred in cfg.pred(block):
                in_[block] = out[pred].merge(block)

            len_before = len(out)
            out_b[block] = a.transfer(block, in_[block])
            len_after = len(out)
        else:
            for succ in cfg.succ(block):
                out[block] = in_[succ].merge(block)

            len_before = len(in_)
            out_b[block] = a.transfer(block, out[block])
            len_after = len(in_)

        if len_before != len_after:
            worklist.append(block.successors)

def df(cfg):
    a = Analysis(
        InitVal.EMPTY,
        reaching_defns_transfer,
        union,
        Direction.FORWARD
    )
    return worklist(a, cfg)

########################################################
# Reaching Definitions Analysis
########################################################

def defn(b):
    pass

def kills(b):
    pass

def reaching_defns_transfer(b, in_):
     return union(defn(b), difference(in_, kills(b)))

if __name__ == '__main__':
    blocks = form_blocks(json.load(sys.stdin))
    cfg = Cfg(blocks)
    analysis = df(cfg)
    print(analysis)
