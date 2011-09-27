from noborder import NoBorderImagePadded, NoBorderImage
from sobel import sobel_magnitude, sobel_magnitude_uint8
from time import time
import sys

sys.setcheckinterval(2**30)
try:
    import pypyjit
    pypyjit.set_param(trace_limit=200000)
except ImportError:
    pass

Image = eval(sys.argv[1])
n = 1000

sobel_magnitude(Image(n, n))
sobel_magnitude_uint8(Image(n, n, typecode='B'))
    
a = time()
for i in range(10):
    sobel_magnitude(Image(n, n))
b = time()
print 'sobel(%s):' % Image.__name__, b - a

a = time()
for i in range(10):
    sobel_magnitude_uint8(Image(n, n, typecode='B'))
b = time()
print 'sobel_uint8(%s):' % Image.__name__, b - a
