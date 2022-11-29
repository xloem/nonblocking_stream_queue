import sys, threading, time
try:
    import queue
except:
    import Queue as queue # python2

class Reader:
    def __init__(self, stream, max_size=-1, lines=False, max_count=None, drop_timeout=None, drop_older=False, pre_cb=None, post_cb=None, drop_cb=None):
        '''
        Wraps a stream to read from it in a nonblocking manner, by using a reader thread, as per
        https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python/4896288#4896288

        max_size: size of each read in the pump thread
        lines: break reads at linebreaks using stream.readline
        max_count: maximum number of reads to buffer at once
        drop_timeout: drop reads after this many seconds if buffer is full
        drop_older: whether to kick out older buffered data instead of dropping newer
        pre_cb: call this before every read, and tuple it with data
        post_cb: transform data via passing to this callback before buffering
        drop_cb: data will be passed to this when dropped
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
        self.drop_older = drop_older
        self.queue = queue.Queue(max_count or 0)
        self.pre_cb = pre_cb
        self.post_cb = post_cb
        self.drop_cb = drop_cb
        self.parent_thread = threading.current_thread()
        self.thread = threading.Thread(target=self._pump)
        self.condition = threading.Condition()
        self.dropped_ct = 0
        self.dropped_size = 0
        self._is_pumping = True
        self.thread.start()

    def __del__(self):
        self._is_pumping = False
        self.thread.join()

    def __iter__(self):
        while True:
            try:
                yield self.queue.get_nowait()[1]
            except queue.Empty:
                return

    def __len__(self):
        return self.queue.qsize()

    def __enter__(self, *params, **kwparams):
        return self.condition.__enter__(*params, **kwparams)

    def __exit__(self, *params, **kwparams):
        return self.condition.__exit__(*params, **kwparams)

    def read_one(self):
        try:
            return self.queue.get_nowait()[1]
        except queue.Empty:
            return None

    def read_many(self, max=None):
        if max is None:
            return list(self)
        else:
            return [item for item, x in zip(self, range(max))]

    def is_pumping(self):
        return self._is_pumping and self.thread.is_alive()

    def block(self, timeout=None, for_ct_read=1):
        with self.condition:
            self.condition.wait_for(
                lambda: len(self) >= for_ct_read or not self.is_pumping(),
                timeout
            )
            return len(self)

    def dropped(self, reset = False):
        with self.condition:
            result = (self.dropped_ct, self.dropped_size)
            if reset:
                self.dropped_ct = 0
                self.dropped_size = 0
            return result

    def _pump(self):
        while self._is_pumping and not self.stream.closed and self.parent_thread.is_alive():
            if self.pre_cb is not None:
                pre_data = self.pre_cb()
            data = self._read(self.max_size or -1)
            
            if data is None:
                time.sleep(0.01)
            else: 
                data_len = len(data)
                if data_len == 0:
                    break
                if self.pre_cb is not None:
                    data = (pre_data, data)
                if self.post_cb is not None:
                    data = self.post_cb(data)
                try:
                    self.queue.put((data_len, data), timeout=self.drop_timeout)
                except queue.Full:
                    with self.condition:
                        if self.queue.full():
                            if self.drop_older:
                                dropped_len, dropped = self.queue.get()
                                self.queue.put_nowait((data_len, data))
                            else:
                                dropped_len = data_len
                                dropped = data
                            self.dropped_ct += 1
                            self.dropped_size += dropped_len
                            if self.drop_cb is not None:
                                self.drop_cb(dropped)
                        else:
                            # queue drained while lock held
                            self.queue.put_nowait((data_len, data))
                with self.condition:
                    self.condition.notify()
        with self.condition:
            self._is_pumping = False
            self.condition.notify_all()
