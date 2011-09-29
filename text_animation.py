import errno
from array import array
import os, re, sys

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
                               ((w * h) / 2))
        self.typecode = typecode

    def _idx(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return y*self.width + x
        raise IndexError

    def _idxy(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return y/2*self.width/2 + x/2
        raise IndexError

    def __getitem__(self, (x, y)):
        total = self.width * self.height
        Y = self.data[self._idx(x, y)]
        Cb = self.color_data[self._idxy(x, y)]
        Cr = self.color_data[self._idxy(x, y)+total/4]
        return (Y, Cb, Cr)

    def __setitem__(self, (x, y), (Y, Cb, Cr)):
        total = self.width * self.height
        self.data[self._idx(x, y)] = Y
        self.color_data[self._idxy(x, y)] = Cb
        self.color_data[self._idxy(x, y)+total/4] = Cr

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


from PIL import ImageFont, ImageColor

def RGB2YCbCr(color):
    (R, G, B) = ImageColor.getrgb(color)
    Y  = R *  0.29900 + G *  0.58700 + B *  0.11400
    Cb = R * -0.16874 + G * -0.33126 + B *  0.50000 + 128
    Cr = R *  0.50000 + G * -0.41869 + B * -0.08131 + 128
    return (int(Y), int(Cb), int(Cr))

def paint(pixel_mask, color):
    if pixel_mask:
        return color
    return (255, 255, 255) #This is our transparency constant

def create_array_mask(text="PyPy Rocks!", **kargs):
    try:
        fontfile = kargs["fontfile"]
    except:
        fontfile = "game_over.ttf"
    try:
        size = kargs["size"]
    except:
        size = 100
    try:
        colorMask = RGB2YCbCr("#"+kargs["color"])
    except:
        colorMask = RGB2YCbCr("#FFFF00")
    font = ImageFont.truetype(fontfile, size)
    mask = font.getmask(text)
    msk_x, msk_y = mask.size
    arraymask = ColorImage(msk_x, msk_y, typecode='B')
    for x in range(msk_x):
        for y in range(msk_y):
            arraymask[x, y] = paint(mask.getpixel((x, y)), colorMask)
    return arraymask


arraymask = create_array_mask("Soy Manu", size=int(sys.argv[1]), color=sys.argv[3])#fontfile="/usr/share/fonts/truetype/freefont/FreeMono.ttf")

counter = 0


def apply_text(img):
    w = img.width
    h = img.height
    for x in range(arraymask.width):
        for y in range(arraymask.height):
            if 0 < (x - arraymask.width + (counter % 500) * 2) < w \
               and y < h \
               and arraymask[x, y] != (255, 255, 255):
                img[x - arraymask.width + (counter % 500) * 2, #TODO: remove 500 magic number
                    y] = arraymask[x, y]
    out = ColorImage(w, h, typecode='B')
    for x in range(img.width):
        for y in range(img.height):
            out[x, y] = img[x, y]
    global counter
    counter += 1
    return img


if __name__ == '__main__':

    import sys
    from time import time

    if len(sys.argv) > 2:
        fn = sys.argv[2]
    else:
        fn = 'test.mpg -vf scale=640:480 -benchmark'

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
