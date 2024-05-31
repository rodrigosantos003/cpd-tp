"""
 Simple JSON-RPC Client
"""

import json
import socket
import inspect
import functions


class JSONRPCServer:
    """The JSON-RPC server."""

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.funcs = {}

    def register(self, name, function):
        """Registers a function."""
        self.funcs[name] = function

    def start(self):
        """Starts the server."""
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        print(f'Listening on port {self.port} ...')

        try:
            while True:
                # Accepts and handles client
                conn, _ = self.sock.accept()
                self.handle_client(conn)

        except ConnectionAbortedError:
            pass
        except OSError:
            pass

    def stop(self):
        """Stops the server."""
        self.sock.close()

    def process_request(self, msg):
        """Process a single JSON-RPC request."""
        res = {'jsonrpc': '2.0'}

        try:
            # Check if the request is valid
            if 'method' not in msg:
                raise ValueError('Invalid Request')
            method = msg['method']

            # Check if the request is a JSON-RPC notification
            if 'id' in msg:
                res['id'] = msg['id']

            # Check if the method exists
            if method not in self.funcs:
                raise KeyError('Method not found')

            # Check function arguments
            func = self.funcs[method]
            func_params = inspect.signature(func).parameters
            if len(func_params) > 0:
                if 'params' in msg:
                    params = msg['params']

                    if isinstance(params, dict):
                        # Named parameters
                        res['result'] = func(**params)
                    elif len(params) == len(func_params):
                        # Positional parameters
                        res['result'] = func(*params)
                    else:
                        raise TypeError('Invalid params')
                else:
                    raise TypeError('Invalid params')
            else:
                res['result'] = func()
        except ValueError:
            res['id'] = None
            res['error'] = {'code': -32600, 'message': 'Invalid Request'}
        except KeyError:
            res['error'] = {'code': -32601, 'message': 'Method not found'}
        except TypeError:
            res['error'] = {'code': -32602, 'message': 'Invalid params'}
        except (ArithmeticError, Exception):
            res['error'] = {'code': -32603, 'message': 'Internal error'}

        return res

    def process_msg(self, msg):
        """Process the request message and build a response"""
        try:
            msgs = json.loads(msg)

            # Check if there are multiple requests on the message
            if isinstance(msgs, list):
                responses = []
                for m in msgs:
                    response = self.process_request(m)
                    responses.append(response)
                return responses

            response = self.process_request(msgs)
            return response
        except json.JSONDecodeError:
            return {'jsonrpc': '2.0',
                    'error': {
                        'code': -32700,
                        'message': 'Parse error'},
                    'id': None}

    def handle_client(self, conn):
        """Handles the client connection."""

        keep_alive = False

        while True:
            # Receive message
            msg = conn.recv(1024).decode()
            print('Received:', msg)

            # Process message
            res = self.process_msg(msg)

            # Send response
            if isinstance(res, list):
                batch_response = []
                for r in res:
                    if 'id' in r:
                        batch_response.append(r)
                conn.send(json.dumps(batch_response).encode())
            elif 'id' in res:
                conn.send(json.dumps(res).encode())

            # Check if the client wants to keep the connection alive
            if isinstance(res, list):
                for r in res:
                    if 'id' not in r and 'result' in r:
                        if r['result'] == 'keepAlive':
                            keep_alive = True
                        elif r['result'] == 'exit':
                            break

            if 'id' not in res and 'result' in res:
                if res['result'] == 'keepAlive':
                    keep_alive = True
                elif res['result'] == 'exit':
                    break

            if not keep_alive:
                break

        conn.close()


if __name__ == "__main__":
    # Test the JSONRPCServer class
    server = JSONRPCServer('0.0.0.0', 8000)

    # Register functions
    server.register('hello', functions.hello)
    server.register('greet', functions.greet)
    server.register('add', functions.add)
    server.register('sub', functions.sub)
    server.register('mul', functions.mul)
    server.register('div', functions.div)
    server.register('keepAlive', functions.keepAlive)
    server.register('exit', functions.closeConnection)

    # Start the server
    server.start()
