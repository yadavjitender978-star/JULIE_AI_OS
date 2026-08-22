class JulieServiceManager:
    def __init__(self): self._s = {}
    def register(self, n, s): self._s[n] = s
    def get(self, n): return self._s.get(n)
    def names(self): return list(self._s.keys())
