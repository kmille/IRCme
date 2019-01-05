import arrow

def go():
    return "{}: Test message at {}".format(__name__, arrow.now().format("HH:mm:ss"))
