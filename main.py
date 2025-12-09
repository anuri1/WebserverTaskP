import asyncio
import os
import mimetypes
import aiohttp
import datetime
from FileDescriptorCache import FileDescriptorCache
from HttpRequestParser import HttpRequestParser
import yaml


class HTTPServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.buffer = b""
        self.proxy_routes = {
            "/yt": "https://www.youtube.com/results?search_query=",
        }

    async def get_response(self, route, page_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.proxy_routes[route]}{page_url}') as response:
                self.send_response(response.status, await response.text())

    def connection_made(self, transport):
        self.transport = transport
        self.client_address = transport.get_extra_info('peername')

    def data_received(self, data):
        self.buffer += data
        end_of_headers = self.buffer.find(b"\r\n\r\n")
        if end_of_headers == -1:
            return

        content = self.buffer[end_of_headers:].decode()[4:]
        request = self.buffer.decode()
        match = parser.parse_http(request)

        if not match:
            self.log_request("GET", "/", 400)
            self.send_response(400, "bad request")
            return

        method = match.group(1)
        req_address = match.group(2)

        content_length = parser.get_content_length(request)
        if content_length == (len(content)):
            return

        if method == "GET":
            self.get_handler(req_address)
        elif method == "POST":
            self.post_handler(request, req_address)

    def get_handler(self, request_address):
        for route in self.proxy_routes:
            if request_address.startswith(route):
                asyncio.create_task(self.get_response(route, request_address[len(route) + 1:]))
                return

        file_path = os.path.join("C:", request_address.lstrip("/"))

        if os.path.isdir(file_path):
            self.get_dir_handler(file_path, request_address)

        elif os.path.isfile(file_path):
            self.get_file_handler(file_path, request_address)

        else:
            self.log_request("GET", request_address, 404)
            self.send_response(404, "Directory or File Not Found")

    def get_file_handler(self, file_path, request_address):
        content = file_descriptor_cache.get_file_content(file_path)
        if content is None:
            self.log_request("GET", request_address, 404)
            self.send_response(404, "File Not Found")
        else:
            content_type, encoding = mimetypes.guess_type(file_path)
            self.log_request("GET", request_address, 200)
            self.send_response(200, content, content_type=content_type, is_binary=True)

    def get_dir_handler(self, file_path, request_address):
        content = self.generate_directory_index(file_path)
        self.log_request("GET", request_address, 200)
        self.send_response(200, content)

    def post_handler(self, request, route):
        form_data = parser.parse_post_data(request)
        if form_data:
            filename = form_data.group(1)
            content = form_data.group(2)
            with open(f"{route[1:]}/{filename}", "w") as f:
                f.write(content)
        self.send_response(200, "Текстовый файл успешно создан")
        print(request)

    def generate_directory_index(self, directory_path):
        if directory_path[-1] != "\\":
            directory_path += "\\"
        files = os.listdir(directory_path)

        links = [f'<li><a href="/{os.path.join(directory_path, file)}">{file}</a></li>' for file in files]
        return f"""
            <html>
            <head><title>Папка {directory_path.replace("/", "\\")}</title></head>
            <body>
                <h1>Папка {directory_path.replace("/", "\\")}</h1>
                <ul>
                    {''.join(links)}
                </ul>
                
                <h1>Создать текстовый файл</h1>
                <form method="post">
                    <label>
                        Введите имя файла
                        <input name="filename" />
                    </label>
                    <p><p>
                    <label>
                        Введите текст файла
                        <input name="content" />
                    </label>
                    <p><p>
                    <button>Создать</button>
                </form>
                
            </body>
            </html>
        """

    def send_response(self, status_code, content, content_type="text/html", is_binary=False):
        status_messages = {
            200: "OK",
            400: "Bad Request",
            404: "Not Found"
        }
        status_message = status_messages.get(status_code, "Unknown")

        if not is_binary:
            content = content.encode()

        response = (
            f"HTTP/1.1 {status_code} {status_message}\r\n"
            f"Date: {datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
            f"Content-Length: {len(content)}\r\n"
            f"Content-Type: {content_type}; charset=utf-8\r\n"
            "Connection: keep-alive\r\n"
            "Keep-Alive: timeout=5, max=100\r\n"
            "\r\n"
        )

        self.transport.write(response.encode() + content)
        self.transport.close()

    def log_request(self, method, path, status_code):
        log_message = (
            f"{datetime.datetime.now()} - "
            f"{self.client_address[0]}:{self.client_address[1]} - "
            f"{method} {path} - {status_code}\n"
        )
        print(log_message)


with open("config.yml", "r") as f:
    data = yaml.safe_load(f)


async def main():
    loop = asyncio.get_running_loop()

    server = await loop.create_server(
        HTTPServerProtocol,
        data["webserver"]["host"],
        data["webserver"]["port"]
    )

    async with server:
        await server.serve_forever()


file_descriptor_cache = FileDescriptorCache(
    data["filedescriptorcache"]["size"],
    data["filedescriptorcache"]["ttl"]
)
parser = HttpRequestParser()

print(data)

asyncio.run(main())


# Виртуальные серверы
# Конфигурация через файл конфигураций
# Proxy pass
