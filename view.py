from noborder import NoBorderImage
from io import mplayer, view

for img in mplayer(NoBorderImage, 'test.avi'):
    view(img)
    
