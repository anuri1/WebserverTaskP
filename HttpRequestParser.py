import re


class HttpRequestParser:
    def __init__(self):
        self.__http_reg = r"(GET|POST) (/[\S]*) HTTP/1\.1"
        self.__post_data_reg = r"filename=([^&]+)&content=([^&\s]+)"
        self.__content_len_reg = r"Content-Length:\s*(\d+)+"

    def parse_http(self, request):
        return re.search(self.__http_reg, request)

    def parse_post_data(self, request):
        return re.search(self.__post_data_reg, request)

    def get_content_length(self, request):
        return re.search(self.__content_len_reg, request)
