import asyncio
from basidia.service import Service
from basidia.decorators import rpc
from basidia.brokers.memory import MemoryBroker

class GreetingService(Service):
    name = "greeting"

    @rpc
    async def hello(self, name: str) -> str:
        return f"Hello, {name}!"

class UserService(Service):
    name = "user"

    @rpc
    async def get_greeting(self, user_name: str) -> str:
      # Call the greeting service
      greeting = await self.call_rpc("greeting", "hello", user_name)
      return f"User service says: {greeting}"

async def test_rpc():
  broker = MemoryBroker()

  greeting_service = GreetingService(broker)
  user_service = UserService(broker)

  # Start both services
  await greeting_service.start()
  await user_service.start()

  # Give services time to set up
  await asyncio.sleep(0.1)

  # Make RPC call
  result = await user_service.get_greeting("Alice")
  print(f"Result: {result}")

  await broker.disconnect()

if __name__ == "__main__":
  asyncio.run(test_rpc())
