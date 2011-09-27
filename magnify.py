#!/usr/bin/env python

import errno
from plain import Image
from math import atan2, sqrt, sin, cos, ceil, floor

class NNImage(Image):
    def __getitem__(self, (x, y)):
        return Image.__getitem__(self, (int(x + 0.5), int(y + 0.5)))

class BilinImage(Image):
    def __getitem__(self, (x, y)):
        if isinstance(x, float) and isinstance(y, float):
            x0, x1 = int(floor(x)), int(ceil(x))
            y0, y1 = int(floor(y)), int(ceil(y))
            xoff, yoff = x-x0, y-y0
            return (1.0-xoff)*(1.0-yoff) * self[x0, y0] + \
                   (1.0-xoff)*(    yoff) * self[x0, y1] + \
                   (    xoff)*(1.0-yoff) * self[x1, y0] + \
                   (    xoff)*(    yoff) * self[x1, y1]
        else:
            return Image.__getitem__(self, (x, y))
    

def magnify(img):
    out = Image(img.width, img.height, typecode='B')
    out.data[:] = img.data
    maxr = img.height/3
    for y in xrange(img.height/2 - maxr, img.height/2 + maxr):
        for x in xrange(img.width/2 - maxr, img.width/2 + maxr):
            dx, dy = x - img.width/2, y - img.height/2
            a = atan2(dy, dx)
            r = sqrt(dx ** 2 + dy ** 2)
            if r < maxr:
                nr = r*r / maxr
                nx, ny = nr*cos(a), nr*sin(a)
                out[x,y] = min(int(img[nx + img.width/2, ny + img.height/2]), 255)
            else:
                out[x,y] = img[x,y]
    return out

if __name__ == '__main__':
    from io import mplayer, view
    import sys
    from time import time
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-b', dest='bilin', action="store_true",
                      help="enable bilinear interpolation")
    options, args = parser.parse_args()

    if len(args) > 0:
        fn = args[0]
    else:
        fn = 'test.avi -vf scale=640:480 -benchmark'
    if options.bilin:
        MyImage=BilinImage
    else:
        MyImage=NNImage

    sys.setcheckinterval(2**30)
    try:
        import pypyjit
        pypyjit.set_param(trace_limit=200000)
    except ImportError:
        pass

    start = start0 = time()
    for fcnt, img in enumerate(mplayer(MyImage, fn)):
        try:
            view(magnify(img))
        except IOError, e:
            if e.errno != errno.EPIPE:
                raise
            print 'Exiting'
            break
        print 1.0 / (time() - start), 'fps, ', (fcnt-2) / (time() - start0), 'average fps'
        start = time()
        if fcnt==2:
            start0 = time()
