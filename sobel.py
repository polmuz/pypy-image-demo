#!/usr/bin/env python

import errno
from noborder import NoBorderImagePadded
from math import sqrt

def sobeldx(img):
    res = img.clone(typecode='d')
    for p in img.pixeliter():
        res[p] = (-1.0 * img[p + (-1,-1)] + 1.0 * img[p + (1,-1)] + \
                  -2.0 * img[p + (-1, 0)] + 2.0 * img[p + (1, 0)] + \
                  -1.0 * img[p + (-1, 1)] + 1.0 * img[p + (1, 1)]) / 4.0
    return res

def sobeldy(img):
    res = img.clone(typecode='d')
    for p in img.pixeliter():
        res[p] = (-1.0*img[p + (-1,-1)] -2.0*img[p + (0,-1)] -1.0*img[p + (1,-1)] + \
                   1.0*img[p + (-1, 1)] +2.0*img[p + (0, 1)] +2.0*img[p + (1, 1)]) / 4.0
    return res

def sobel_magnitude(img):
    res = img.clone(typecode='d')
    for p in img.pixeliter():
        dx = -1.0 * img[p + (-1,-1)] + 1.0 * img[p + (1,-1)] + \
             -2.0 * img[p + (-1, 0)] + 2.0 * img[p + (1, 0)] + \
             -1.0 * img[p + (-1, 1)] + 1.0 * img[p + (1, 1)]
        dy = -1.0*img[p + (-1,-1)] -2.0*img[p + (0,-1)] -1.0*img[p + (1,-1)] + \
              1.0*img[p + (-1, 1)] +2.0*img[p + (0, 1)] +1.0*img[p + (1, 1)]
        res[p] = sqrt(dx*dx + dy*dy) / 4.0
    return res

def uint8(img):
    res = img.clone(typecode='B')
    for p in img.pixeliter():
        res[p] = min(max(int(img[p]), 0), 255)
    return res

def sobel_magnitude_uint8(img):
    res = img.clone(typecode='B')
    for p in img.pixeliter():
        dx = -1.0 * img[p + (-1,-1)] + 1.0 * img[p + (1,-1)] + \
             -2.0 * img[p + (-1, 0)] + 2.0 * img[p + (1, 0)] + \
             -1.0 * img[p + (-1, 1)] + 1.0 * img[p + (1, 1)]
        dy = -1.0*img[p + (-1,-1)] -2.0*img[p + (0,-1)] -1.0*img[p + (1,-1)] + \
              1.0*img[p + (-1, 1)] +2.0*img[p + (0, 1)] +1.0*img[p + (1, 1)]
        res[p] = min(int(sqrt(dx*dx + dy*dy) / 4.0), 255)
    return res

def main(args):
    Image = eval(args[0])
    n = 1000
    if len(args) == 1:
        for i in range(10):
            sobel_magnitude(Image(n, n))
        return 'sobel(%s(%dx%d))' % (Image.__name__, n, n)
    else:
        for i in range(10):
            sobel_magnitude_uint8(Image(n, n, typecode='B'))
        return 'sobel_uint8(%s(%dx%d))' % (Image.__name__, n, n)

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
    for fcnt, img in enumerate(mplayer(NoBorderImagePadded, fn)):
        #view(img)
        #sobeldx(img)
        #view(uint8(sobel_magnitude(img)))
        #sobel_magnitude_uint8(img)
        try:
            view(sobel_magnitude_uint8(img))
        except IOError, e:
            if e.errno != errno.EPIPE:
                raise
            print 'Exiting'
            break

        print 1.0 / (time() - start), 'fps, ', (fcnt-2) / (time() - start0), 'average fps'
        start = time()
        if fcnt==2:
            start0 = time()
