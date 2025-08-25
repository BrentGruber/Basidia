import asyncio
from typing import Optional

class Service:
    """
    Service is the base class for all Basidia Services
    """
    name: Optional[str] = None

    def __init__(self):
        self._print_startup_banner()
        if not self.name:
            self.name = self.__class__.__name__

    def _print_startup_banner(self):
        banner = """
    ╔══════════════════════════════════════╗
    ║                                      ║
    ║        🍄 BASIDIA SERVICE 🍄         ║
    ║                                      ║
    ║    Async Microservices Framework     ║
    ║                                      ║
    ╚══════════════════════════════════════╝
        """
        print(banner)
        print(f"🚀 Starting service: {self.__class__.__name__}")
        print(f"📍 Service ready for connections\n")
