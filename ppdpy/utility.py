class listview():
    __slots__ = ['l', 'h', 'llen']

    def __init__(self, the_list, head_index=0, list_length=None):
        self.l = the_list
        self.h = head_index

        self.llen = list_length if list_length is not None else len(the_list)

    def walk(self):
        if self.h >= self.llen:
            raise StopIteration()

        return self.head, self.tail

    @property
    def head(self):
        if self.h >= self.llen:
            raise StopIteration()

        return self.l[self.h]

    @property
    def tail(self):
        if self.h >= self.llen:
            raise StopIteration()

        return listview(self.l, self.h+1, self.llen)

    def __len__(self):
        return self.llen - self.h
