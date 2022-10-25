# Nonblocking

This is a simple python package for nonblocking use of streams.

At the moment, a simple nonblocking queue reader is provided, with implementation from https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python/4896288#4896288 .

When constructed, the reader spawns a thread and reads everything from the stream, until it is either garbage collected or EOF is reached.

## Usage

    import sys
    import nonblocking
    
    reader = nonblocking.Reader(sys.stdin, 4096, limit_num_buffered=None, drop_timeout=None, transform_cb=None)

    print(reader.read_one()) # outputs up to 4096 characters, or None if nothing queued
    print(reader.read_many()) # outputs all 4096 character chunks queued
    print(''.join(reader.read_many())) # outputs all queued text

### Timestamping

    import sys, time
    import nonblocking
    
    reader = nonblocking.Reader(
        sys.stdin,
        0,
        limit_num_buffered=None,
        drop_timeout=None,
        transform_cb=lambda data: (time.time(), data)
    )

    while True:
        print(*reader.read_one(block=True)) # shows the timestamp each item was buffered

## Other solutions

There are likely many other existing solutions to this common task.

Here's one:
- https://github.com/kata198/python-nonblock
