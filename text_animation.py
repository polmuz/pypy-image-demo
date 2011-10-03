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
        Cr = self.color_data[self._idxy(x, y)+(total)/4]
        return (Y, Cb, Cr)

    def __setitem__(self, (x, y), (Y, Cb, Cr)):
        total = self.width * self.height
        self.data[self._idx(x, y)] = Y
        self.color_data[self._idxy(x, y)] = Cb
        self.color_data[self._idxy(x, y)+(total)/4] = Cr

    def tofile(self, f):
        self.data.tofile(f)
        self.color_data.tofile(f)


def color_mplayer(Image, fn='tv://', options=''):
    f = os.popen('mplayer -loop 0 -really-quiet -noframedrop ' + options + ' '
                 '-vo yuv4mpeg:file=/dev/stdout 2>/dev/null </dev/null ' + fn)
    hdr = f.readline()
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
            self.mplayer.write('YUV4MPEG2 W%d H%d F25:1 Ip A1:1\n' %
                               (img.width, img.height))
            self.width = img.width
            self.height = img.height

        assert self.width == img.width
        assert self.height == img.height
        self.mplayer.write('FRAME\n')
        img.tofile(self.mplayer)
    
    def dump(self, img):
        assert img.typecode == 'B'
        if not self.width:
            self.mplayer = open('out1.mpg', 'w')
            self.mplayer.write('YUV4MPEG2 W%d H%d F25:1 Ip A1:1\n' %
                               (img.width, img.height))
            self.width = img.width
            self.height = img.height

        assert self.width == img.width
        assert self.height == img.height
        self.mplayer.write('FRAME\n')
        img.tofile(self.mplayer)

    def kill(self):
        self.mplayer.close()


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
        colorMask = RGB2YCbCr("#FFFFFF")
    font = ImageFont.truetype(fontfile, size)
    mask = font.getmask(text, mode="L")
    msk_x, msk_y = mask.size

    arraymask = ColorImage(msk_x+(4-msk_x%4), msk_y+(4-msk_y%4), typecode='B')
    for x in range(msk_x+(4-msk_x%4)):
        for y in range(msk_y+(4-msk_y%4)):
            try:
            	arraymask[x, y] = paint(mask.getpixel((x, y)), colorMask) 
            except:
                arraymask[x, y] = (255, 255, 255)
    return arraymask


arraymask = create_array_mask(sys.argv[2], size=int(sys.argv[3]), color=sys.argv[4], fontfile=sys.argv[5])

counter = 0

def apply_text(img):
    blank = (255, 255, 255)
    pad = 10
    W = img.width
    H = img.height
    for x in range(arraymask.width):
        for y in range(arraymask.height):
            num = min(counter * 2, W - pad)
            if 0 < (x-arraymask.width+counter*2) < W and \
               0 < (H+y-arraymask.height-pad) < H and \
               0 < (x-arraymask.width+num) < W and \
               arraymask[x, y] != blank:
                print x-arraymask.width+num, \
                    H+y-arraymask.height-pad
                img[x-arraymask.width+num, \
                    H+y-arraymask.height-pad] = arraymask[x, y]
    global counter
    counter += 3
    return img


if __name__ == '__main__':

    import sys
    from time import time

    if len(sys.argv) > 2:
        fn = sys.argv[1] + " -benchmark"
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
            default_viewer.dump(apply_text(img))
        except IOError, e:
            if e.errno != errno.EPIPE:
                raise
            print 'Exiting'
            default_viewer.kill()
            break
        if counter % 50:
            print 1.0 / (time() - start), 'fps, ', (fcnt-2) / (time() - start0), 'average fps'
        start = time()
        if fcnt == 2:
            start0 = time()
