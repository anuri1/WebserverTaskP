import os
import time


class FileDescriptorCache:
    def __init__(self, size=100, ttl=60):
        self.cache = {}
        self.size = size
        self.ttl = ttl

    def get_file_descriptor(self, filename):
        if filename in self.cache.keys():
            file = self.cache[filename]
            if time.time() - file["create_time"] < self.ttl:
                if self.is_file_actual(filename, file["modification_time"]):
                    print(file["descriptor"])
                    print(self.cache, "5252")
                    return file["descriptor"]
            os.close(file["descriptor"])
            del self.cache[filename]

        descriptor = os.open(filename, os.O_RDONLY | os.O_BINARY)
        stats = os.stat(descriptor)

        if len(self.cache) >= self.size:
            oldest_key = next(iter(self.cache))
            oldest_desc = self.cache[oldest_key]
            os.close(oldest_desc["descriptor"])
            del self.cache[oldest_key]

        self.cache[filename] = {
            "descriptor": descriptor,
            "modification_time": stats.st_mtime,
            "create_time": time.time(),
            "size": stats.st_size
        }
        print(self.cache, "1")
        return descriptor

    def get_file_content(self, file_path):
        descriptor = self.get_file_descriptor(file_path)
        f = os.fdopen(descriptor, "rb", closefd=False)
        f.seek(0)
        return f.read()

    def is_file_actual(self, filename, mtime):
        try:
            current_mtime = os.stat(filename).st_mtime
            return current_mtime == mtime
        except OSError:
            return False

