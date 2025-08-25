import pytest
from io import StringIO
import sys
from basidia.service import Service

class TestGreetingService(Service):
    name = "greeting_service"

class TestService:
    def test_service_initialization(self):
        # Capture stdout to test banner output
        captured_output = StringIO()
        sys.stdout = captured_output

        service = TestGreetingService()

        # Reset stdout
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        # Verify service was initialized
        assert service.name == "greeting_service"
        assert isinstance(service, Service)

        # Verify banner was printed
        assert "BASIDIA SERVICE" in output
        assert "TestGreetingService" in output
        assert "Service ready" in output

    def test_service_auto_naming(self):
        # Test service without explicit name uses class name
        captured_output = StringIO()
        sys.stdout = captured_output

        class AutoNamedService(Service):
            pass

        service = AutoNamedService()

        sys.stdout = sys.__stdout__

        assert service.name == "AutoNamedService"
