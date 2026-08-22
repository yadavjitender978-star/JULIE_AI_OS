class JulieKernel:
    def __init__(self, p): self.p = p; self.running = False
    def start(self): self.running = True
    def stop(self): self.running = False
