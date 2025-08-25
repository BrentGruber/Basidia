import asyncio
import json
import uuid
from typing import Dict, Any, Callable, Optional
from basidia.brokers.base import MessageBroker

class Service:
    """
    Service is the base class for all Basidia Services
    """
    name: Optional[str] = None

    def __init__(self, broker: Optional[MessageBroker] = None):
        self.name = self.name or self.__class__.__name__ # if no name defined, default to class name
        self.broker = broker
        self._rpc_methods = self._discover_rpc_methods()
        self._pending_requests = {}

        # Print a startup banner for flare
        self._print_startup_banner()

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

    def _discover_rpc_methods(self) -> Dict[str, Callable]:
        """Find all methods decorated with @rpc"""
        methods = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, "_is_rpc"):
                methods[attr_name] = attr
        return methods

    def _handle_rpc_response(self, message: bytes):
        """Handle RPC response messages"""
        try:
            response = json.loads(message.decode())
            request_id = response["request_id"]

            if request_id in self._pending_requests:
                future = self._pending_requests[request_id]
                if not future.done():
                    future.set_result(response)
        except Exception as e:
            print(f"Error handling RPC response: {e}")

    async def _handle_rpc_request(self, message: bytes):
        """Handle incoming RPC requests"""
        try:
            print(f"{self.name} handling an incoming request")
            print(self._rpc_methods)
            request = json.loads(message.decode())
            method_name = request["method"]
            args = request.get("args", [])
            kwargs = request.get("kwargs", {})
            request_id = request["request_id"]
            reply_to = request["reply_to"]

            if method_name in self._rpc_methods:
                # Call the method
                method = self._rpc_methods[method_name]
                result = await method(*args, **kwargs)

                # Send response
                response = {
                        "request_id": request_id,
                        "result": result,
                        "error": None
                }
            else:
                response = {
                        "request_id": request_id,
                        "result": None,
                        "error": f"Method {method_name} not found"
                }

            await self.broker.publish(reply_to, json.dumps(response).encode())

        except Exception as e:
            # Send error response
            response = {
                    "request_id": request.get("request_id", "unknown"),
                    "result": None,
                    "error": str(e)
            }
            reply_to = request.get("reply_to", f"rpc.{self.name}.reply")
            await self.broker.publish(reply_to, json.dumps(response).encode())

    async def start(self):
        """Start the service and begin listening for RPC Calls"""
        if not self.broker:
            raise ValueError("Service needs a broker to start")

        await self.broker.connect()

        # Listen for RPC Calls to this service
        rpc_queue = f"rpc.{self.name}"
        await self.broker.declare_queue(rpc_queue)
        await self.broker.consume(rpc_queue, self._handle_rpc_request)

        print(f"🎯 {self.name} listening for RPC calls on {rpc_queue}")

    async def call_rpc(self, service_name: str, method_name: str, *args, **kwargs):
        """Make an RPC Call to another service"""
        if not self.broker:
            raise ValueError("Service needs a broker for rpc calls")

        request_id = str(uuid.uuid4())
        reply_queue = f"rpc.{self.name}.reply.{request_id}"

        # Set up response handler
        response_future = asyncio.Future()
        self._pending_requests[request_id] = response_future

        # Listen for response (temporary)
        await self.broker.consume(reply_queue, self._handle_rpc_response)

        # Send request
        request = {
                "method": method_name,
                "args": args,
                "kwargs": kwargs,
                "request_id": request_id, 
                "reply_to": reply_queue
        }

        target_queue = f"rpc.{service_name}"
        await self.broker.publish(target_queue, json.dumps(request).encode())

        # Wiat for the response
        try:
            response = await asyncio.wait_for(response_future, timeout=30.0)
            if response.get("error"):
                raise Exception(f"RPC Error: {response['error']}")
            return response['result']
        finally:
            # Cleanup
            if request_id in self._pending_requests:
                del self._pending_requests[request_id]


