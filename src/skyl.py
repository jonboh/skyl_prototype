import math
from dataclasses import dataclass

import solid2 as s

CYL = 100


@dataclass
class Properties:
    plate_x: int = 19
    plate_y: int = 21
    plate_z: int = 3

    point_size: float = 0.5


def place_finger(shape, col):
    """
    0 -> Thumb
    2 -> Index (Col2)
    ..
    4 -> Pinky
    """
    if col == 0:
        shape = s.translate([-47, -32, 9])(s.rotate([0, -75, 10])(shape))

    elif col == 1:
        shape = s.translate([-38.5, 0, 12])(s.rotate([-10, 15, 0])(shape))
    elif col == 2:
        shape = s.translate([-19, 5, 6])(s.rotate([-10, 15, 0])(shape))
    elif col == 3:
        shape = s.translate([2, -5, 4])(s.rotate([-10, 15, 0])(shape))
    elif col == 4:
        shape = s.translate([23, -30, 4])(s.rotate([-10, 15, 0])(shape))
    else:
        raise RuntimeError(f"Invalid place position {col}")
    return shape


def place_allfingers(shape):
    return s.union()(*[place_finger(shape, i) for i in range(5)])


def place_corner(shape, x0, y0, p):
    x = p.plate_x / 2
    if not x0:
        x *= -1
    y = p.plate_y / 2
    if not y0:
        y *= -1
    z = p.plate_z / 2
    return s.translate([x, y, z])(shape)


def skrhade():
    skrhade = s.import_stl("../src/parts/skrhade_single_pcb.stl")
    stem = s.import_stl("../src/parts/Stem.stl")
    thumbstick = s.import_stl("../src/parts/Cap - Meta Quest Thumbstick.stl")
    # NOTE: maybe we need to write this manually to add tolerances
    return s.union()(
        # fix small tubes under skrhade
        skrhade,
        s.up(0.8)(s.cube([7, 7, 1.6], center=True)),
        # Stem and thumbstick
        s.translate([0, 1, 5])(stem),
        s.translate([0, 1, 10])(thumbstick),
    )


def skrhade_pcb(p: Properties):
    rtol = 0.125
    xtol = 0.20
    x = 16.5
    y = 18.5
    z = 2

    x_ = x + xtol
    y_ = y + xtol

    return s.down(z / 2 - 0.01)(
        s.difference()(
            s.cube([x_, y_, z], center=True),
            s.translate([x_ / 2, y_ / 2])(
                s.cylinder(h=10, r=3 - rtol, center=True, _fn=CYL)
            ),
            s.translate([-x_ / 2, y_ / 2])(
                s.cylinder(h=10, r=3 - rtol, center=True, _fn=CYL)
            ),
            s.translate([x_ / 2, -y_ / 2])(
                s.cylinder(h=10, r=4 - rtol, center=True, _fn=CYL)
            ),
            s.translate([-x_ / 2, -y_ / 2])(
                s.cylinder(h=10, r=4 - rtol, center=True, _fn=CYL)
            ),
            s.translate([0, -16 + y_ / 2])(
                s.cylinder(h=10, r=1.5 - rtol, center=True, _fn=CYL)
            ),
        )
    )


def _plate(p: Properties):
    offset = 1.5
    return s.translate([0, offset / 2, -p.plate_z / 2])(
        s.cube([p.plate_x, p.plate_y - offset, p.plate_z], center=True)
    )


def plate(p: Properties):
    return s.difference()(_plate(p), skrhade_pcb(p))


def make_skyl(p: Properties):
    point = s.cube(p.point_size, center=True)

    shape = place_allfingers(plate(p))

    columns = list()
    # first column done manually
    recep_offset = s.translate([0, 0, -p.plate_z])(_plate(p))
    recep = place_finger(recep_offset, col=0)
    projec = s.projection()(place_finger(recep_offset, col=0))
    columns.append(
        s.hull()(
            recep,
            s.linear_extrude(height=0.01)(projec),
            s.translate([15, 0, 0])(s.linear_extrude(height=0.01)(projec)),
            s.translate([5, 7, 0])(s.linear_extrude(height=0.01)(projec)),
            s.translate([5, -7, 0])(s.linear_extrude(height=0.01)(projec)),
        )
    )
    for i in range(1, 5):
        recep_offset = s.translate([0, 0, -p.plate_z])(_plate(p))
        recep = place_finger(recep_offset, col=i)
        projec = s.projection()(place_finger(recep_offset, col=i))
        columns.append(
            s.hull()(
                recep,
                s.linear_extrude(height=0.01)(projec),
                s.translate([2, -2])(s.linear_extrude(height=0.01)(projec)),
                s.translate([-2, 2])(s.linear_extrude(height=0.01)(projec)),
                s.translate([2, 2])(s.linear_extrude(height=0.01)(projec)),
            ),
        )
    floor = s.translate([-11, -65, -1])(s.cube([91, 170, 2], center=True))
    floor = s.difference()(
        floor,
        s.translate([0, 42, 0])(s.rotateZ(-25)(s.cube(200, 50, 100, center=True))),
        s.translate([53, -70, 0])(s.rotateZ(75)(s.cube(250, 50, 100, center=True))),
    )
    shape = s.union()(
        shape,
        floor,
        *columns,
    )
    shape = s.difference()(
        shape,
        s.down(52)(s.cube([200, 200, 100], center=True)),
    )
    shape = s.difference()(shape, place_allfingers(skrhade_pcb(p)))

    return shape


def make_joystick(p: Properties):
    xtol = 0.05
    insertxy = 2
    insert_z = 1.5
    joystick_height = 3
    shape = s.union()(
        s.up(joystick_height)(s.cylinder(h=2, r=6.5, _fn=CYL, center=True)),
        s.difference()(
            s.cylinder(h=joystick_height, r=3, _fn=CYL),
            s.up(insert_z / 2 - 0.01)(
                s.cube([insertxy + xtol, insertxy + xtol, insert_z], center=True)
            ),
        ),
    )
    return shape


if __name__ == "__main__":
    p = Properties()
    skyl_right = make_skyl(p)
    skyl_left = s.mirrorX()(skyl_right)
    joystick = make_joystick(p)
    s.scad_render_to_file(skyl_right, "./things/skyl_right.scad")
    s.scad_render_to_file(skyl_left, "./things/skyl_left.scad")
    s.scad_render_to_file(joystick, "./things/joystick.scad")
