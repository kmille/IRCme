import arrow

def go():
    return "PING at {}".format(arrow.now().format("HH:mm:ss"))
