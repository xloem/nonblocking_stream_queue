# Nonblocking Stream Queue

This is a simple python package for nonblocking reading from streams.

It could be expanded for general nonblocking usage if desired.

A simple nonblocking queue reader is provided, with implementation from https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python/4896288#4896288 .

When constructed, the reader spawns a thread and begins reading everything from the stream.

## Installation
    $ python3 -m pip install nonblocking-stream-queue

## Usage

    import sys
    import nonblocking_stream_queue as nonblocking
    
    reader = nonblocking.Reader(
        sys.stdin, # object to read from
        max_size=4096, # max size of each read
        lines=False, # whether or not to break reads into lines
        max_count=None, # max queued reads
        drop_timeout=None, # time to wait for queue to drain before dropping
        drop_older=False, # which end of the queue to drop from
        pre_cb=None, # if set, data = (pre_cb(), read())
        post_cb=None, # if set, data = post_cb(data)
        drop_cb=None, # if set, call with dropped data
        verbose=False, # if set, display progress filling max_count
    )

    print(reader.read_one()) # outputs up to 4096 characters, or None if nothing queued
    print(reader.read_many()) # outputs all 4096 character chunks queued
    print(''.join(reader.read_many())) # outputs all queued text
    reader.block() # waits for data to be present or end, returns number of reads queued
    reader.is_pumping() # False if data has ended

### Timestamping

    import sys, time
    import nonblocking_stream_queue as nonblocking
    
    reader = nonblocking.Reader(
        sys.stdin.buffer,
        pre_cb=lambda: time.time(),
        post_cb=lambda time_data_tuple: (time_data_tuple[0], time_data_tuple[1], time.time())
    )

    while reader.block():
        start_time, data, end_time = reader.read_one()
        print(start_time, data, end_time)

## Lines

    import sys
    import nonblocking_stream_queue as nonblocking
    
    reader = nonblocking.Reader(
        sys.stdin,
        lines=True
    )

    while reader.block():
        print(reader.read_one().rstrip()) # outputs each line of text that is input

## Other solutions

There are likely many other existing solutions to this common task.

Here's one:
- https://github.com/kata198/python-nonblock
