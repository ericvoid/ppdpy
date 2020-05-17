class Node:
    def __eq__(self, other):
        return self._to_tuple() == other._to_tuple()

    def __ne__(self, other):
        return not self == other

    def _to_tuple(self):
        raise NotImplemented

    def eval(self, symbols:set) -> bool:
        raise NotImplemented


class Id(Node):
    id: str

    def __init__(self, id:str):
        self.id = id

    def _to_tuple(self):
        return ('id', self.id)

    def eval(self, symbols:set) -> bool:
        return self.id in symbols


class Not(Node):
    n: Node

    def __init__(self, node):
        self.n = node

    def _to_tuple(self):
        return ('not', self.n._to_tuple())

    def eval(self, symbols:set) -> bool:
        return not self.n.eval(symbols)


class And(Node):
    left: Node
    right: Node

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def _to_tuple(self):
        return ('and', self.left._to_tuple(), self.right._to_tuple())

    def eval(self, symbols:set) -> bool:
        return self.left.eval(symbols) and self.right.eval(symbols)


class Or(Node):
    left: Node
    right: Node

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def _to_tuple(self):
        return ('or', self.left._to_tuple(), self.right._to_tuple())

    def eval(self, symbols:set) -> bool:
        return self.left.eval(symbols) or self.right.eval(symbols)
