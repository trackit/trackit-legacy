_NOVAL = object()

class Peekable(object):
    def __init__(self, iterator):
        self.iterator = iter(iterator)
        self._cached = None

    def has_next(self):
        try:
            self.peek()
            return True
        except StopIteration:
            return False

    def peek(self, default=_NOVAL):
        if not self._cached:
            try:
                self._cached = (next(self.iterator),)
            except StopIteration:
                if default is _NOVAL:
                    raise
                else:
                    return default
        return self._cached[0]

    def next(self, default=_NOVAL):
        if self._cached:
            o = self._cached[0]
            self._cached = None
            return o
        if default is _NOVAL:
            return next(self.iterator)
        else:
            return next(self.iterator, default)

    def __iter__(self):
        return self
