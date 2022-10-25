import sys, threading, time
try:
    import queue
except:
    import Queue as queue # python2

class Reader:
    def __init__(self, stream, max_size=-1, lines=False, max_count=None, drop_timeout=None, transform_cb=None):
        '''
        Wraps a stream to read from it in a nonblocking manner, by using a reader thread, as per
        https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python/4896288#4896288

        max_size: size of each read in the pump thread
        lines: break reads at linebreaks using stream.readline
        max_count: maximum number of reads to buffer at once
        drop_timeout: drop reads after this many seconds if buffer is full
        transform_cb: transform data via passing to this callback before queueing
        '''
        self.stream = stream
        if lines:
            self._read = stream.readline
        else:
            if hasattr(stream, 'read1'):
                self._read = stream.read1
            else:
                self._read = stream.read
        self.max_size = max_size
        self.drop_timeout = drop_timeout
        self.queue = queue.Queue(max_count or 0)
        self.transform_cb = transform_cb
        self.parent_thread = threading.current_thread()
        self.thread = threading.Thread(target=self._pump)
        self.condition = threading.Condition()
        self._is_pumping = True
        self.thread.start()

    def __del__(self):
        self._is_pumping = False
        self.thread.join()

    def __iter__(self):
        while True:
            try:
                yield self.queue.get_nowait()
            except queue.Empty:
                return

    def read_one(self):
        try:
            return self.queue.get_nowait()
        except queue.Empty:
            return None

    def read_many(self):
        return list(self)

    def is_pumping(self):
        return self._is_pumping and self.thread.is_alive()

    def block(self, timeout=None, for_ct_read=1):
        with self.condition:
            if self.queue.qsize() < for_ct_read and self.is_pumping():
                self.condition.wait(timeout)
            return self.queue.qsize()

    def _pump(self):
        while self._is_pumping and not self.stream.closed and self.parent_thread.is_alive():
            data = self._read(self.max_size or -1)
            
            if data is None:
                time.sleep(0.01)
            elif len(data) == 0:
                break
            else:
                if self.transform_cb is not None:
                    data = self.transform_cb(data)
                self.queue.put(data, timeout=self.drop_timeout)
                with self.condition:
                    self.condition.notify()
        with self.condition:
            self._is_pumping = False
            self.condition.notify_all()
