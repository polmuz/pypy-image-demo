convert -size 320x240 xc:black blackimage.png
ffmpeg -y -loop_input -i blackimage.png -r 25 -t $1 -sameq -an blackbg.mpg
pypy text_animation.py blackbg.mpg "$2" $3 $4 $5
#totem out.mpg
