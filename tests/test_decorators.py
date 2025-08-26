import pytest
from basidia.decorators import rpc

class TestRPCDecorator:

    def test_rpc_decorator_marks_function(self):
        """Test that the rpc decorator marks function as RPC"""
        @rpc
        def test_function():
            pass

        assert hasattr(test_function, "_is_rpc")
        assert test_function._is_rpc is True
        assert hasattr(test_function, "_rpc_name")
        assert test_function._rpc_name == "test_function"

    def test_rpc_decorator_preserves_function_name(self):
        """Test that decorator preserves original function name"""
        @rpc
        def test_function():
            pass

        assert test_function.__name__ == "test_function"
        assert test_function._rpc_name == "test_function"

    def test_rpc_decorator_on_method(self):
        """Test that @rpc works on class methods"""
        class TestService:
            @rpc
            def get_data(self):
                return "data"

        service = TestService()
        assert hasattr(service.get_data, "_is_rpc")
        assert service.get_data._is_rpc is True
        assert service.get_data._rpc_name == "get_data"

    def test_rpc_decorator_on_async_function(self):
        """Test that @rpc works on async functions"""
        @rpc
        async def async_function():
            return "async result"

        assert hasattr(async_function, "_is_rpc")
        assert async_function._is_rpc is True
        assert async_function._rpc_name == "async_function"

    def test_multiple_rpc_functions(self):
        """Test multiple functions can be decorated"""
        @rpc
        def function_one():
            return 1

        @rpc
        def function_two():
            return 2

        assert function_one._is_rpc is True
        assert function_two._is_rpc is True
        assert function_one._rpc_name == "function_one"
        assert function_two._rpc_name == "function_two"

    def test_rpc_decorator_doesnt_affect_execution(self):
        """test that decorated functions still execute normally"""
        @rpc
        def add_numbers(a, b):
            return a + b

        result = add_numbers(3, 4)
        assert result == 7

    @pytest.mark.asyncio
    async def test_rpc_decorator_doesnt_affect_async_execution(self):
        """Test that decorated async functions still execute normally"""
        @rpc
        async def async_add(a, b):
            return a + b

        result = await async_add(5, 6)
        assert result == 11
