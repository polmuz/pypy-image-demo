import errno, os, re

from plain import Image
from array import array
from merge_videos import ColorMplayerViewer, ColorImage, color_mplayer

class ColorImageFPS(ColorImage):
    def __init__(self, w, h, f, typecode='d', fromfile=None):
        self.width = w
        self.height = h
        self.fps = f
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

class ColorMplayerViewerSaver(ColorMplayerViewer):
    def dump(self, img, **kargs):
        assert img.typecode == 'B'
        if not self.width:
            self.dumpfile = open(kargs["output"], 'w')
            self.width = img.width
            self.height = img.height
            self.dumpfile.write('YUV4MPEG2 W%d H%d F%s Ip A1:1\n' %
                       (img.width, img.height, img.fps))
        assert self.width == img.width
        assert self.height == img.height
        self.dumpfile.write('FRAME\n')
        img.tofile(self.dumpfile)

    def kill(self):
        try:
            self.dumpfile.close()
        except:
            pass


def non_looping_color_mplayer(Image, fn='tv://', options=''):
    f = os.popen('mplayer -loop 0 -really-quiet -noframedrop ' + options + ' '
                 '-vo yuv4mpeg:file=/dev/stdout 2>/dev/null </dev/null ' + fn)
    hdr = f.readline()
    m = re.search('W(\d+) H(\d+)', hdr)
    w, h = int(m.group(1)), int(m.group(2))
    try:
       n = re.search('F(\d+:\d+)', hdr)
       fps = n.group(1)
    except:
       fps = 25
    while True:
        hdr = f.readline()
        if hdr != 'FRAME\n':
            break
        yield ColorImageFPS(w, h, fps, typecode='B', fromfile=f)


default_viewer = ColorMplayerViewerSaver()
counter = 0
dump = False
outfile = "out.mpg"

if __name__ == '__main__':

    import sys
    from time import time
    videos = []
    for i in range(1, len(sys.argv)):
        videos.append(sys.argv[i] + " -vf scale=640:480 -benchmark")
    print videos
    sys.setcheckinterval(2 ** 30)
    try:
        import pypyjit
        pypyjit.set_param(trace_limit=200000)
    except ImportError:
        pass
    dump = True
    start = start0 = time()
    for video in videos:
        for fcnt, imgs in enumerate(non_looping_color_mplayer(ColorImage, video)):
            counter += 1
            try:
                if dump:
                    default_viewer.dump(imgs, output=outfile)
                else:
                    default_viewer.view(imgs)
            except IOError, e:
                if e.errno != errno.EPIPE:
                    raise
                print 'Exiting'
                default_viewer.kill()
                break
            if counter % 100 == 0:
                print 1.0 / (time() - start), 'fps, ', (fcnt-2) / (time() - start0), 'average fps'
            start = time()
            if fcnt == 2:
                start0 = time()

