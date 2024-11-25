# class Api:
#     def __init__(self):
#
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors
from matplotlib.collections import PolyCollection

axes = plt.axes(projection="3d")


def colors(arg):
    return mcolors.to_rgba(arg, alpha=0.6)


x1 = np.arange(0, 10, 0.4)
verts = []
z1 = [0.0, 1.0, 2.0, 3.0]
for z in z1:
    y1 = np.random.rand(len(x1))
    y1[0], y1[-1] = 0, 0
    verts.append(list(zip(x1, y1)))

poly = PolyCollection(verts, facecolors=[colors('r'), colors('g'), colors('b'),
                                         colors('y')])
poly.set_alpha(0.7)
axes.add_collection3d(poly, zs=z1, zdir='y')

axes.set_xlabel('X')
axes.set_xlim3d(0, 10)
axes.set_ylabel('Y')
axes.set_ylim3d(-1, 4)
axes.set_zlabel('Z')
axes.set_zlim3d(0, 1)
axes.set_title("3D Waterfall plot")

plt.show()
