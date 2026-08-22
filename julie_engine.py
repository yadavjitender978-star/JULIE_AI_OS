import os, logging
from core.service_manager import JulieServiceManager
from core.kernel import JulieKernel
from core.database import DatabaseManager
from core.actions import JulieActionEngine
from core.screen_controller import JulieScreenController
from core.vision import JulieVisionEngine
from core.voice import JulieVoiceEngine

class JulieEngine:
    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.services = JulieServiceManager()
        self.kernel = JulieKernel(self.project_dir)
        self.services.register("kernel", self.kernel)
        self.db = DatabaseManager(os.path.join(self.project_dir, "data", "julie.db"))
        self.services.register("database", self.db)
        self.actions = JulieActionEngine()
        self.services.register("actions", self.actions)
        self.screen_controller = JulieScreenController()
        self.services.register("screen_controller", self.screen_controller)
        self.vision = JulieVisionEngine()
        self.services.register("vision", self.vision)
        self.voice = JulieVoiceEngine()
        self.services.register("voice", self.voice)

    def start(self):
        self.kernel.start()
        self.db.start()
        return self.status()

    def stop(self):
        if hasattr(self, "voice"): self.voice.shutdown()
        if hasattr(self, "db"): self.db.stop()
        if hasattr(self, "kernel"): self.kernel.stop()

    def status(self):
        return {
            "name": "JULIE AI OS",
            "version": "1.2.6",
            "running": True,
            "components": ["voice", "actions", "database", "screen_controller", "vision"]
        }
