from array import array
from math import sqrt

class Image(object):
    def __init__(self, w, h, typecode='d', fromfile=None):
        self.width = w
        self.height = h
        if fromfile is not None:
            self.data = array(typecode)
            self.data.fromfile(fromfile, w*h)
        else:
            self.data = array(typecode, [0]) * (w*h)
        self.typecode = typecode

    def tofile(self, f):
        self.data.tofile(f)

    def _idx(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return y*self.width + x
        raise IndexError

    def __getitem__(self, (x, y)):
        return self.data[self._idx(x, y)]

    def __setitem__(self, (x, y), val):
        self.data[self._idx(x, y)] = val

    def pixels(self, border=0):
        for y in xrange(border, self.height-border):
            for x in xrange(border, self.width-border):
                yield x, y


def sobel_magnitude(a):
    b = Image(a.width, a.height, typecode='B')
    for y in xrange(1, a.height-1):
        for x in xrange(1, a.width-1):
            dx = -1.0 * a[x-1, y-1] + 1.0 * a[x+1, y-1] + \
                 -2.0 * a[x-1, y]   + 2.0 * a[x+1, y] + \
                 -1.0 * a[x-1, y+1] + 1.0 * a[x+1, y+1]
            dy = -1.0 * a[x-1, y-1] -2.0 * a[x, y-1] -1.0 * a[x+1, y-1] + \
                  1.0 * a[x-1, y+1] +2.0 * a[x, y+1] +1.0 * a[x+1, y+1]
            b[x, y] = min(int(sqrt(dx*dx + dy*dy) / 4.0), 255)

    return b

def sobel_magnitude_generator(a):
    b = Image(a.width, a.height, typecode='B')
    for x, y in a.pixels(border=1):
        dx = -1.0 * a[x-1, y-1] + 1.0 * a[x+1, y-1] + \
             -2.0 * a[x-1, y]   + 2.0 * a[x+1, y] + \
             -1.0 * a[x-1, y+1] + 1.0 * a[x+1, y+1]
        dy = -1.0 * a[x-1, y-1] -2.0 * a[x, y-1] -1.0 * a[x+1, y-1] + \
              1.0 * a[x-1, y+1] +2.0 * a[x, y+1] +1.0 * a[x+1, y+1]
        b[x, y] = min(int(sqrt(dx*dx + dy*dy) / 4.0), 255)

    return b

if __name__ == '__main__':
    from io import mplayer, view
    import sys
    from time import time

    if len(sys.argv) > 1:
        fn = sys.argv[1]
    else:
        fn = 'test.avi -vf scale=640:480 -benchmark'

    sys.setcheckinterval(2**30)
    try:
        import pypyjit
        pypyjit.set_param(trace_limit=200000)
    except ImportError:
        pass

    start = start0 = time()
    for fcnt, img in enumerate(mplayer(Image, fn)):
        #view(img)
        view(sobel_magnitude(img))
        #view(sobel_magnitude_generator(img))
        #sobel_magnitude_generator(img)
        #sobel_magnitude(img)
        print 1.0 / (time() - start), 'fps, ', (fcnt-2) / (time() - start0), 'average fps'
        start = time()
        if fcnt==2:
            start0 = time()
