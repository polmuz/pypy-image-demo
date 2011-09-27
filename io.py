import os, re, array

def mplayer(Image, fn='tv://', options=''):
    f = os.popen('mplayer -really-quiet -noframedrop ' + options + ' ' 
                 '-vo yuv4mpeg:file=/dev/stdout 2>/dev/null </dev/null ' + fn)
    hdr = f.readline()
    m = re.search('W(\d+) H(\d+)', hdr)
    w, h = int(m.group(1)), int(m.group(2))
    while True:
        hdr = f.readline()
        if hdr != 'FRAME\n':
            break
        yield Image(w, h, typecode='B', fromfile=f)
        f.read(w*h/2) # Color data

class MplayerViewer(object):
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
            self.color_data = array.array('B', [127]) * (img.width * img.height / 2)
        assert self.width == img.width
        assert self.height == img.height
        self.mplayer.write('FRAME\n')
        img.tofile(self.mplayer)
        self.color_data.tofile(self.mplayer)

default_viewer = MplayerViewer()

def view(img):
    default_viewer.view(img)
    
