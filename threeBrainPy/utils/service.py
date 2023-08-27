import http.server
import socket
import threading
import atexit
from .temps import ensure_temporary_directory
# import threebrainpy.utils.temps as tmps
# ensure_temporary_directory = tmps.ensure_temporary_directory


class ViewerService:
    def __init__(self, host = "localhost", directory = None):
        self.server = None
        self.thread = None
        self.host = host
        self.port = None
        self._directory = directory

    def start(self, port : int = None):
        force_port = False
        if port is not None:
            force_port = True
            port = int(port)
            if port > 65535 or port < 1024:
                raise ValueError("Port must be between 1024 and 65535")
            if port == self.port and self.thread is not None and self.thread.is_alive():
                return # Already running
            self.stop()
            self.port = port
        if self.thread is not None and self.thread.is_alive():
            return
        if not isinstance(self.port, int):
            self.port = 0 # Bind to any available port (0)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            try:
                server.bind((self.host, self.port))  # test port
            except:
                if force_port:
                    raise OSError(f"Port {port} is already in use...")
                server.bind((self.host, 0))
            self.port = server.getsockname()[1]
        
        if self._directory is None:
            self._directory = ensure_temporary_directory("threebrainpy-viewers")
        directory = self._directory

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory = directory, **kwargs)
            def log_message(self, format, *args):
                pass
        self.server = http.server.HTTPServer((self.host, self.port), Handler)
        def serve_directory():
            print(f"Serving at http://127.0.0.1:{self.port}")
            self.server.serve_forever()
        self.thread = threading.Thread(target=serve_directory)
        self.thread.daemon = True
        self.thread.start()
        atexit.register(self.stop)

    def stop(self):
        if self.thread is None or not self.thread.is_alive():
            return
        print(f"Stopping server at port {self.port} ...")
        if self.server is not None:
            self.server.shutdown()
            # service.server.server_close()
        if self.thread is not None:
            self.thread.join()

    def browse(self):
        import webbrowser
        webbrowser.open(f"http://{self.host}:{self.port}")

hosted_services = []

def start_service(host : str = None, port : int = None):
    if len(hosted_services) > 0:
        service = hosted_services[0]
        if service.host != host:
            service.stop()
            service.host = host
    else:
        service = ViewerService(host=host)
        hosted_services.append(service)
    # make sure the service is running
    service.start(port=port)
    return service

def stop_all_services():
    for service in hosted_services:
        try:
            service.stop()
        except:
            pass
    hosted_services.clear()
