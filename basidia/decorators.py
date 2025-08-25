from functools import wraps

def rpc(func):
    """Mark a method as available for RPC calls"""
    func._is_rpc = True
    func._rpc_name = func.__name__
    print(f"Applied @rpc to {func.__name__}")
    return func
