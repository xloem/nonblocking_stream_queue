import sys, threading, time
from six.moves import queue # python3 queue

class Reader:
    def __init__(self, stream, max_size, limit_num_buffered=None, drop_timeout=None, transform_cb=None):
        '''
        Wraps a stream to read from it in a nonblocking manner, by using a reader thread, as per
        https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python/4896288#4896288

        max_size: size of each read in the thread
        limit_num_buffered: maximum number of reads to buffer
        drop_timeout: drop reads after this many seconds if buffer is full
        transform_cb: transform data via passing to this callback before queueing
        '''
        self.stream = stream
        self.max_size = max_size
        self.drop_timeout = drop_timeout
        self.queue = queue.Queue(limit_num_buffered or 0)
        self.transform_cb = transform_cb
        self.thread = threading.Thread(target=self._pump)
        self.thread.daemon = True # terminate with process
        self.thread.start()
    def __del__(self):
        self.stream.close()
        self.thread.join()

    def __iter__(self):
        while True:
            try:
                yield self.queue.get_nowait()
            except queue.Empty:
                return
    def read_one(self):
        try:
            with self.lock:
                return self.queue.get_nowait()
        except queue.Empty:
            return None
    def read_many(self):
        return [*iter(self)]

    def _pump(self):
        while not self.stream.closed:
            data = self.stream.read(self.max_size)
            if data is None:
                time.sleep(0.01)
            elif len(data) == 0:
                break
            else:
                if self.transform_cb is not None:
                    data = self.transform_cb(data)
                self.queue.put(data, timeout=self.drop_timeout)
