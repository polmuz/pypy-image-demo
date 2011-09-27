from noborder import *

def test_noborder():
    for Image in (NoBorderImagePadded, NoBorderImage):
        a = Image(5, 5).setup([[11, 12, 13, 14, 15],
                               [21, 22, 23, 24, 25],
                               [31, 32, 33, 34, 35],
                               [41, 42, 43, 44, 45],
                               [51, 52, 53, 54, 55]])
        k = Image(3, 3).setup([[1, 2, 3],
                               [1, 1, 2],
                               [2, 1, 1]])
        def tst(conv, a, k):
            b = conv(a, k)
            assert b[1,1]== 326 and b[2,1]==340 and b[3,1]==354
            assert b[1,2]== 466 and b[2,2]==480 and b[3,2]==494
            assert b[1,3]== 606 and b[2,3]==620 and b[3,3]==634

        for c in (conv3x3, conv3x3iter, conv3x3range):
            yield tst, c, a, k

    
