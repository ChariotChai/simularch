def transpose_2d(data):
    t = list(map(list, zip(*data)))
    return t
