import errno
from array import array
import os, re

from plain import Image


class ColorImage(Image):
    def __init__(self, w, h, typecode='d', fromfile=None):
        self.width = w
        self.height = h
        if fromfile is not None:
            self.data = array(typecode)
            self.data.fromfile(fromfile, w*h)
            self.color_data = array(typecode)
            self.color_data.fromfile(fromfile, (w * h) / 2)
        else:
            self.data = array(typecode, [0]) * (w * h)
            self.color_data = (array('B', [127]) *
                               (w * h / 2))

        self.typecode = typecode

    def tofile(self, f):
        self.data.tofile(f)
        self.color_data.tofile(f)


def color_mplayer(Image, fn='tv://', options=''):
    f = os.popen('mplayer -loop 0 -really-quiet -noframedrop ' + options + ' '
                 '-vo yuv4mpeg:file=/dev/stdout 2>/dev/null </dev/null ' + fn)
    hdr = f.readline()
    while True:
        m = re.search('W(\d+) H(\d+)', hdr)
        w, h = int(m.group(1)), int(m.group(2))
        while True:
            hdr = f.readline()
            if hdr != 'FRAME\n':
                break
            yield ColorImage(w, h, typecode='B', fromfile=f)


class ColorMplayerViewer(object):
    def __init__(self):
        self.width = self.height = None

    def view(self, img):
        assert img.typecode == 'B'
        if not self.width:
            self.mplayer = os.popen('mplayer -really-quiet -noframedrop - ' +
                                    '2> /dev/null ', 'w')
            self.mplayer.write('YUV4MPEG2 W%d H%d F100:1 Ip A1:1\n' %
                               (img.width, img.height))
            self.width = img.width
            self.height = img.height

        assert self.width == img.width
        assert self.height == img.height
        self.mplayer.write('FRAME\n')
        img.tofile(self.mplayer)

default_viewer = ColorMplayerViewer()


from PIL import ImageFont


def create_array_mask():
    font = ImageFont.truetype("game_over.ttf", 100)
    mask = font.getmask("PyPy Rocks!")
    msk_x, msk_y = mask.size
    arraymask = Image(msk_x, msk_y, typecode='B')
    for x in range(msk_x):
        for y in range(msk_y):
            arraymask[x, y] = mask.getpixel((x, y))
    return arraymask

arraymask = create_array_mask()
counter = 0


def apply_text(img):
    w = img.width
    h = img.height
    for x in range(arraymask.width):
        for y in range(arraymask.height):
            if 0 < (x - arraymask.width + (counter % 500) * 2) < w \
               and y < h \
               and arraymask[x, y] != 0:
                img[x - arraymask.width + (counter % 500) * 2,
                    y] = arraymask[x, y]
    global counter
    counter += 1
    return img


if __name__ == '__main__':

    import sys
    from time import time

    if len(sys.argv) > 1:
        fn = sys.argv[1]
    else:
        fn = 'test.avi -vf scale=640:480 -benchmark'

    sys.setcheckinterval(2 ** 30)
    try:
        import pypyjit
        pypyjit.set_param(trace_limit=200000)
    except ImportError:
        pass

    start = start0 = time()
    for fcnt, img in enumerate(color_mplayer(ColorImage, fn)):
        try:
            # default_viewer.view(img)
            default_viewer.view(apply_text(img))
        except IOError, e:
            if e.errno != errno.EPIPE:
                raise
            print 'Exiting'
            break
        print 1.0 / (time() - start), 'fps, ', (fcnt-2) / (time() - start0), 'average fps'
        start = time()
        if fcnt == 2:
            start0 = time()
