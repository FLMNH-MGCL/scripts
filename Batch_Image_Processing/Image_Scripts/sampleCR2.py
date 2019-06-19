import rawpy
import imageio

path = 'MGCL_1085284_L.CR2'
with rawpy.imread(path) as raw:
    newImage = raw.postprocess(use_camera_wb = True, user_flip = 5, auto_bright_thr = 0.000015)

imageio.imsave('default.jpg', newImage, quality = 100, dpi = tuple((300,300)), exif = True)
imageio.help(name = 'jpg')
