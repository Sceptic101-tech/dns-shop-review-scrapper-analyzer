from queue import Queue, Empty, Full
from scripts.parser import DNS_Shop_Parser

class ParserPool:
    def __init__(self, size:int, block:bool=True, timeout:float=None, browser_headless:bool=True):
        self._pool = Queue(maxsize=size)
        self._block = block
        self._timeout = timeout
        for _ in range(size):
            parser = DNS_Shop_Parser(browser_headless)
            self._pool.put(parser, self._block, self._timeout)

    def get(self):
        try:
           return self._pool.get(self._block, self._timeout)
        except Empty:
            return None


    def put(self, parser):
        try:
            self._pool.put(parser, self._block, self._timeout)
            return True
        except Full:
            return None
            
