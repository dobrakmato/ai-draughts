import tkinter
import random
import json
import math

import time


class Vec3:
    """
    Three dimensional vector class represented by components x, y and z.
    """

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f'Vec3({self.x}, {self.y}, {self.z})'

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __mul__(self, other):
        if isinstance(other, Vec3):
            return self.cross(other)
        elif isinstance(other, (int, float)):
            return Vec3(self.x * other, self.y * other, self.z * other)
        else:
            raise ValueError('Vec3 can only be multiplied by Vec3, int or float.')

    def len_squared(self):
        return self.x * self.x + self.y * self.y + self.z * self.z

    def len(self):
        return math.sqrt(self.len_squared())

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        u = self
        v = other
        return Vec3(
            u.y * v.z - u.z * v.y,
            u.z * v.x - u.x * v.z,
            u.x * v.y - u.y * v.x
        )


class Mat4:
    def __init__(self):
        self.m = [[1.0, 0.0, 0.0, 0.0],
                  [0.0, 1.0, 0.0, 0.0],
                  [0.0, 0.0, 1.0, 0.0],
                  [0.0, 0.0, 0.0, 1.0]]

    def __str__(self):
        a = ', '.join(map(str, self.m[0]))
        b = ', '.join(map(str, self.m[1]))
        c = ', '.join(map(str, self.m[2]))
        d = ', '.join(map(str, self.m[3]))

        return f'[{a}]\n[{b}]\n[{c}]\n[{d}]'

    def __getitem__(self, item):
        if not isinstance(item, int):
            raise ValueError('item must be integer')
        if item < 0 or item > 3:
            raise ValueError('index must be in range 0 - 4 (four not inclusive)')

        return self.m[item]

    def __setitem__(self, key, value):
        if not isinstance(key, int):
            raise ValueError('item must be integer')
        if key < 0 or key > 3:
            raise ValueError('index must be in range 0 - 4 (four not inclusive)')

        self.m[key] = value

    def __mul__(self, other):
        result = Mat4()
        for i in range(4):
            for j in range(4):
                result[i][j] = self.m[i][0] * other[0][j] + \
                               self.m[i][1] * other[1][j] + \
                               self.m[i][2] * other[2][j] + \
                               self.m[i][3] * other[3][j]
        return result

    def mul_point(self, vec3, normalize_w=True):
        result = Vec3()
        result.x = vec3.x * self.m[0][0] + vec3.y * self.m[1][0] + vec3.z * self.m[2][0] + self.m[3][0]
        result.y = vec3.x * self.m[0][1] + vec3.y * self.m[1][1] + vec3.z * self.m[2][1] + self.m[3][1]
        result.z = vec3.x * self.m[0][2] + vec3.y * self.m[1][2] + vec3.z * self.m[2][2] + self.m[3][2]

        w = vec3.x * self.m[0][3] + vec3.y * self.m[1][3] + vec3.z * self.m[2][3] + self.m[3][3]

        if normalize_w:
            w_inv = 1 / w

            result.x *= w_inv
            result.y *= w_inv
            result.z *= w_inv

        return result

    def mul_dir(self, vec3):
        result = Vec3()

        result.x = vec3.x * self.m[0][0] + vec3.y * self.m[1][0] + vec3.z * self.m[2][0]
        result.y = vec3.x * self.m[0][1] + vec3.y * self.m[1][1] + vec3.z * self.m[2][1]
        result.z = vec3.x * self.m[0][2] + vec3.y * self.m[1][2] + vec3.z * self.m[2][2]

        return result

    @staticmethod
    def create_scale(vec):
        result = Mat4()
        result[0][0] = vec.x
        result[1][1] = vec.y
        result[2][2] = vec.z
        return result

    @staticmethod
    def create_translation(vec):
        result = Mat4()
        result[3][0] = vec.x
        result[3][1] = vec.y
        result[3][2] = vec.z
        return result

    @staticmethod
    def create_rotation(vec):
        sina = math.sin(vec.x)
        sinb = math.sin(vec.y)
        sinc = math.sin(vec.z)

        cosa = math.cos(vec.x)
        cosb = math.cos(vec.y)
        cosc = math.cos(vec.z)

        result = Mat4()

        result[0][0] = cosa * cosb
        result[0][1] = cosa * sinb * sinc - sina * cosc
        result[0][2] = cosa * sinb * cosc + sina * cosc

        result[1][0] = sina * cosb
        result[1][1] = sina * sinb * sinc + cosa * cosc
        result[1][2] = sina * sinb * cosc - cosa * sinc

        result[2][0] = -sinb
        result[2][1] = cosb * sinc
        result[2][2] = cosb * cosc

        return result


class Camera:
    def __init__(self):
        self.view_matrix = Mat4()
        self.projection_matrix = Mat4()
        self.dirty_view_matrix = True


class SceneObject:
    def __init__(self):
        self.position = Vec3()
        self.rotation = Vec3(0, 0, 0)
        self.scale = Vec3(1, 1, 1)

        self.transform_matrix = Mat4()
        self.dirty_transform_matrix = True

    def update(self, camera, delta_time, total_time):
        if self.dirty_transform_matrix:
            self.recalculate_transform_matrix()

    def draw(self, g):
        pass

    def recalculate_transform_matrix(self):
        self.transform_matrix = Mat4.create_translation(self.position) * \
                                Mat4.create_rotation(self.rotation) * \
                                Mat4.create_scale(self.scale)


class CubeObject(SceneObject):
    def __init__(self):
        SceneObject.__init__(self)

        self.A = Vec3(-1, -1, 1)
        self.B = Vec3(1, -1, 1)
        self.C = Vec3(1, -1, -1)
        self.D = Vec3(-1, -1, -1)
        self.E = Vec3(-1, 1, 1)
        self.F = Vec3(1, 1, 1)
        self.G = Vec3(1, 1, -1)
        self.H = Vec3(-1, 1, -1)

        self.color = 'red'
        self.combined_matrix = Mat4()

    def draw(self, g):
        # transform points
        A = self.combined_matrix.mul_point(self.A)
        B = self.combined_matrix.mul_point(self.B)
        C = self.combined_matrix.mul_point(self.C)
        D = self.combined_matrix.mul_point(self.D)
        E = self.combined_matrix.mul_point(self.E)
        F = self.combined_matrix.mul_point(self.F)
        G = self.combined_matrix.mul_point(self.G)
        H = self.combined_matrix.mul_point(self.H)

        g.dbg_point(A, 'A')
        g.dbg_point(B, 'B')
        g.dbg_point(C, 'C')
        g.dbg_point(D, 'D')
        g.dbg_point(E, 'E')
        g.dbg_point(F, 'F')
        g.dbg_point(G, 'G')
        g.dbg_point(H, 'H')

        # draw all 12 lines
        g.line(A, B, self.color)
        g.line(A, E, self.color)
        g.line(B, C, self.color)
        g.line(B, F, self.color)
        g.line(C, G, self.color)
        g.line(C, D, self.color)
        g.line(D, H, self.color)
        g.line(D, A, self.color)
        g.line(E, F, self.color)
        g.line(F, G, self.color)
        g.line(G, H, self.color)
        g.line(H, E, self.color)

    def update(self, camera, delta_time, total_time):
        super().update(camera, delta_time, total_time)

        self.combined_matrix = camera.projection_matrix * camera.view_matrix * self.transform_matrix


# class LinePool:
#     def __init__(self):
#         self.available = []
#         self.used = []
#
#     def acquire(self):
#         pass
#
#     def release(self, line):


class Graphics:
    def __init__(self, canvas):
        self.c = canvas
        self.width_half = 720 / 2
        self.height_half = 720 / 2
        print(f'Initialized graphics instance on canvas with half size {self.width_half}x{self.height_half} px')

    def clear(self):
        self.c.delete('all')

    def dbg_point(self, point, name, color='blue'):
        p = ((point.x * self.width_half) + self.width_half, (point.y * self.height_half) + self.height_half)

        self.c.create_oval(p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8, fill=color)
        self.c.create_text(p[0], p[1] - 16, text=name, font=('Arial', '12', 'bold'), fill='black')

    def line(self, point_a, point_b, color='black'):
        p1 = ((point_a.x * self.width_half) + self.width_half, (point_a.y * self.height_half) + self.height_half)
        p2 = ((point_b.x * self.width_half) + self.width_half, (point_b.y * self.height_half) + self.height_half)

        # print('line', 'from=', p1, 'to=', p2)

        self.c.create_line(p1, p2, fill=color)


class Scene:
    def __init__(self):
        self.camera = Camera()
        self.objects = []

    def add_object(self, obj):
        self.objects.append(obj)

    def remove_object(self, obj):
        self.objects.remove(obj)

    def update_all(self, delta_time, total_time):
        for obj in self.objects:
            obj.update(self.camera, delta_time, total_time)

    def draw_all(self, g):
        for obj in self.objects:
            obj.draw(g)


class Program:
    def __init__(self):
        self.canvas = None
        self.g = None
        self.total_time = 0
        self.scene = Scene()

        self.load()
        self.loop()
        self.clean_up()

    def load(self):
        print('Creating canvas...')
        self.canvas = tkinter.Canvas(width=720, height=720)
        self.canvas.pack()

        print('Creating graphics...')
        self.g = Graphics(self.canvas)

        print('Creating scene...')
        self.load_scene()

    def loop(self):
        delta = 1 / 60
        while True:
            start = time.clock()

            # clear screen
            self.g.clear()

            # update world
            self.scene.update_all(delta, self.total_time)
            self.update(delta, self.total_time)
            # print('tick=', delta, 'ms', '   fps=', 1000 / delta, '   objects=', len(self.scene.objects))
            time.sleep(0.016)

            # draw world
            self.scene.draw_all(self.g)

            # compute next delta time
            delta = (time.clock() - start) * 1000  # convert to ms
            self.total_time += delta

            # poll events
            self.canvas.update_idletasks()
            self.canvas.update()

    def clean_up(self):
        pass

    def update(self, delta_time, total_time):
        self.cube.position = Vec3(0, 0, math.sin(total_time * 0.005))
        self.cube.rotation = Vec3(0, math.radians(total_time * 0.05), math.radians(10))
        self.cube.scale = Vec3(0.4, math.fabs(math.sin(total_time * 0.004) * 0.4) + 0.2, 0.4)
        self.cube.dirty_transform_matrix = True

    def load_scene(self):
        self.cube = CubeObject()
        self.cube.scale = Vec3(0.4, 0.4, 0.4)
        self.cube.rotation = Vec3(math.radians(1), 0, 0)
        self.cube.dirty_transform_matrix = True

        self.scene.add_object(self.cube)


# Program()
# a = Vec3(1, 2, 3)
# b = Vec3(1, 5, 7)
# c = b.dot(a)

A = Mat4()
B = Vec3(200, 7, 11)

A.m[0] = [1, 2, 3, 4]
A.m[1] = [5, 6, 7, 8]
A.m[2] = [9, 8, 7, 6]
A.m[3] = [5, 4, 3, 2]

print(A.mul_point(B))

Program()
