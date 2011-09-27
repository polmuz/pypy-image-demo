from array import array

class NoBorderImage(object):
    "An image class for people who dont care about border effects"
    
    def __init__(self, w, h, typecode='d', fromfile=None):
        self.width = w
        self.height = h
        if fromfile is not None:
            self.data = array(typecode)
            self.data.fromfile(fromfile, w*h)
        else:
            self.data = array(typecode, [0]) * (w*h)
        self.typecode = typecode

    def _idx(self, p):
        if isinstance(p, Pixel):
            assert p.image.__class__ is self.__class__
            assert p.image.width == self.width
            idx = p.idx
        else:
            idx = p[1] * self.width + p[0]
        return min(max(idx, 0), len(self.data)-1)

    def __getitem__(self, p):
        return self.data[self._idx(p)]

    def __setitem__(self, p, val):
        self.data[self._idx(p)] = val

    def pixels(self):
        for i in self.pixelrange():
            yield Pixel(i, self)

    def pixeliter(self):
        return PixelIter(self)

    def pixelrange(self):
        return xrange(self.width * self.height)

    def setup(self, data):
        for y in xrange(self.height):
            for x in xrange(self.width):
                self[x, y] = data[y][x]
        return self

    def clone(self, **kwargs):
        return self.__class__(self.width, self.height, **kwargs)

    def tofile(self, f):
        self.data.tofile(f)

class NoBorderImagePadded(NoBorderImage):
    def __init__(self, w, h, typecode='d', fromfile=None):
        self.width = w
        self.height = h
        self.typecode = typecode
        if fromfile is None:
            self.data = array(typecode, [0]) * (w*(h+2)+2)
        else:
            self.data = array(typecode, [0]) * (w + 1)
            self.data.fromfile(fromfile, w*h)
            self.data += array(typecode, [0]) * (w + 1)

    def _idx(self, p):
        if isinstance(p, Pixel):
            assert p.image.__class__ is self.__class__
            assert p.image.width == self.width
            idx = p.idx
        else:
            idx = (p[1]+1) * self.width + p[0] + 1
        return min(max(idx, 0), len(self.data)-1)

    def pixelrange(self):
        return xrange(self.width + 1, (self.width+1) * self.height + 1)

    def tofile(self, f):
        self.data[(self.width+1):(-self.width-1)].tofile(f)


class NoBorderImagePadded640x480(NoBorderImagePadded):
    def _idx(self, p):
        assert self.width == 640
        assert self.height == 480
        assert len(self.data) == 640*(480+2)+2
        return NoBorderImagePadded._idx(self, p)
    

class Pixel(object):
    def __init__(self, idx, image):
        self.idx = idx
        self.image = image

    def __add__(self, other):
        return Pixel(self.idx + other[1]*self.image.width + other[0], self.image)

class PixelIter(object):
    def __init__(self, image):
        self.image = image
        self.pixelrange = iter(image.pixelrange())
        
    def __iter__(self):
        return self

    def next(self):
        return Pixel(self.pixelrange.next(), self.image)

def conv3x3(img, k):
    assert k.width == k.height == 3
    res = img.clone()
    for p in img.pixels():
        res[p] = k[2,2]*img[p + (-1,-1)] + k[1,2]*img[p + (0,-1)] + k[0,2]*img[p + (1,-1)] + \
                 k[2,1]*img[p + (-1, 0)] + k[1,1]*img[p + (0, 0)] + k[0,1]*img[p + (1, 0)] + \
                 k[2,0]*img[p + (-1, 1)] + k[1,0]*img[p + (0, 1)] + k[0,0]*img[p + (1, 1)]
    return res

def conv3x3iter(img, k):
    assert k.width == k.height == 3
    res = img.clone()
    for p in img.pixeliter():
        res[p] = k[2,2]*img[p + (-1,-1)] + k[1,2]*img[p + (0,-1)] + k[0,2]*img[p + (1,-1)] + \
                 k[2,1]*img[p + (-1, 0)] + k[1,1]*img[p + (0, 0)] + k[0,1]*img[p + (1, 0)] + \
                 k[2,0]*img[p + (-1, 1)] + k[1,0]*img[p + (0, 1)] + k[0,0]*img[p + (1, 1)]
    return res

def conv3x3range(img, k):
    assert k.width == k.height == 3
    res = img.clone()
    for i in img.pixelrange():
        p = Pixel(i, img)
        res[p] = k[2,2]*img[p + (-1,-1)] + k[1,2]*img[p + (0,-1)] + k[0,2]*img[p + (1,-1)] + \
                 k[2,1]*img[p + (-1, 0)] + k[1,1]*img[p + (0, 0)] + k[0,1]*img[p + (1, 0)] + \
                 k[2,0]*img[p + (-1, 1)] + k[1,0]*img[p + (0, 1)] + k[0,0]*img[p + (1, 1)]
    return res

def main(args):
    Image = eval(args[0])
    if len(args) == 1:
        func = conv3x3
    else:
        func = eval('conv3x3' + args[1])
    n = 1000
    for i in range(10):
        func(Image(n, n), Image(3, 3))
    if len(args) > 1:
        return 'conv3x3%s(%s(%dx%d))' % (args[1], Image.__name__, n, n)
    else:
        return Image.__name__

if __name__ == '__main__':
    import time, sys
    sys.setcheckinterval(2**30)
    try:
        import pypyjit
        pypyjit.set_param(trace_limit=200000)
    except ImportError:
        pass
    Image = eval(sys.argv[1])
    n = 1000

    # Warmup
    conv3x3(Image(n, n), Image(3,3))
    conv3x3iter(Image(n, n), Image(3,3))
    conv3x3range(Image(n, n), Image(3,3))

    a = time.time()
    for i in range(10):
        conv3x3(Image(n, n), Image(3,3))
    b = time.time()
    print 'conv3x3(%s(%dx%d)):' % (Image.__name__, n, n), b - a

    a = time.time()
    for i in range(10):
        conv3x3iter(Image(n, n), Image(3,3))
    b = time.time()
    print 'conv3x3iter(%s(%dx%d)):' % (Image.__name__, n, n), b - a

    a = time.time()
    for i in range(10):
        conv3x3range(Image(n, n), Image(3,3))
    b = time.time()
    print 'conv3x3range(%s(%dx%d)):' % (Image.__name__, n, n), b - a

