class groupby:
    def __init__(self, predicate, iterable):
        self.predicate = predicate
        self.it = iter(iterable)
        self.curr_val = next(self.it, None)

    def __iter__(self):
        return self

    def __next__(self):
        if self.curr_val:
            return self._grouper()
        else:
            raise StopIteration

    def _grouper(self):
        while self.curr_val:
            yield self.curr_val

            try:
                next_val = next(self.it, None)

                if not next_val or not self.predicate(self.curr_val, next_val):
                    self.curr_val = next_val
                    break

                self.curr_val = next_val
            except StopIteration:
                return


def slice_len(offset, length):
    return slice(offset, offset + length)
