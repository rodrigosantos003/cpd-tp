"""
 Simple JSON-RPC Client
"""

import json
import socket


class JSONRPCClient:
    """The JSON-RPC client."""

    def __init__(self, host, port):
        self.sock = socket.socket()
        self.sock.connect((host, port))
        self.ID = 1

    def close(self):
        """Closes the connection."""
        self.sock.close()

    def send(self, msg):
        """Sends a message to the server."""
        self.sock.sendall(msg.encode())
        return self.sock.recv(1024).decode()

    def invoke(self, method, params):
        """Invokes a remote function."""

        req = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.ID
        }
        self.ID += 1
        msg = self.send(json.dumps(req))
        res = json.loads(msg)

        if 'error' in res:
            error_code = res['error'].get('code')
            error_message = res['error'].get('message')
            if error_code == -32602:
                raise TypeError(error_message)
            if error_code == -32601:
                raise AttributeError(error_message)

        if 'result' in res:
            return res['result']

        return res

    def batch(self, requests):
        """Sends a batch of requests."""
        batch_requests = []
        for req in requests:
            batch_requests.append({
                "jsonrpc": "2.0",
                "method": req['method'],
                "params": req.get('params', []),
                "id": self.ID
            })
            self.ID += 1
        msg = self.send(json.dumps(batch_requests))
        return json.loads(msg)

    def __getattr__(self, name):
        """Invokes a generic function."""

        def inner(*params):
            return self.invoke(name, params)

        return inner


if __name__ == "__main__":
    # Test the JSONRPCClient class
    client = JSONRPCClient('127.0.0.1', 8000)

    # Single request example
    res = client.div(2, 3)
    print(res)

    # Batch request example
    batch_requests = [
        {"method": "hello"},
        {"method": "greet", "params": ["World"]},
        {"method": "add", "params": [1, 2]}
    ]
    batch_responses = client.batch(batch_requests)
    print(batch_responses)

    client.close()
