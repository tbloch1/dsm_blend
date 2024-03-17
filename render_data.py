import os
import bpy
import argparse
import numpy as np

def update_texture_image():
    img_path = 'data/dsm.tif'
    shader = bpy.context.selected_objects[0].active_material
    node_tree = shader.node_tree
    node = node_tree.nodes['Image Texture']
    node.image = bpy.data.images.load(img_path)
    return node


def update_render_resolution(percentage):
    render_obj = bpy.data.scenes[0].render
    render_obj.resolution_percentage = percentage
    return render_obj


def deg2rad(deg):
    return 2*np.pi*(deg / 360)


def update_light_rotation(rx, ry, rz):
    light = bpy.data.objects['Light']
    light.rotation_mode = 'XYZ' # Force the right rotation mode
    rotation = light.rotation_euler
    rotation.x = deg2rad(rx)
    rotation.y = deg2rad(ry)
    rotation.z = deg2rad(rz)
    return light


def update_light_location(x, y, z):
    light = bpy.data.objects['Light']
    location = light.location
    location.x = x
    location.y = y
    location.z = z
    return light


def update_sun_strength(strength):
    light = bpy.data.objects['Light']
    light.data.use_nodes = True
    light.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = strength
    return light


def update_surface_emission(strength):
    world = bpy.data.worlds['World']
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = strength
    return world


def update_displacement_scaling(scale):
    plane = bpy.data.materials["Material.001"]
    plane.node_tree.nodes["Displacement"].inputs[2].default_value = scale
    return plane


def do_render(fpath):
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.filepath = fpath
    bpy.ops.render.render(use_viewport = True, write_still = True)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--quick', type=bool, nargs='?', default=False,
        help='Whether to do a quick render (10\\% \\resolution)'
    )
    parser.add_argument(
        '--rp', type=int, nargs='?', default=25,
        help='Percentage of full resolution (as integer 0-100)'
    )
    parser.add_argument(
        '--lx', type=float, nargs='?', default=5,
        help='Eastwards position of light-source'
    )
    parser.add_argument(
        '--ly', type=float, nargs='?', default=5,
        help='Northwards position of light-source'
    )
    parser.add_argument(
        '--lz', type=float, nargs='?', default=15,
        help='Vertical position of light-source'
    )
    parser.add_argument(
        '--lrx', type=float, nargs='?', default=0,
        help='Rotates clockwise around the East-West axis (0 is 6pm, 90 is 9pm etc.)'
    )
    parser.add_argument(
        '--lry', type=float, nargs='?', default=45,
        help='Rotates clockwise around the North-South axis (0 is 6pm, 90 is 9pm etc.)'
    )
    parser.add_argument(
        '--lrz', type=float, nargs='?', default=45,
        help='Rotates clockwise around the vertical axis (0 is 6pm, 90 is 9pm etc.)'
    )
    parser.add_argument(
        '--sun_brightness', type=float, nargs='?', default=1,
        help='Brightness value'
    )
    parser.add_argument(
        '--surface_brightness', type=float, nargs='?', default=1,
        help='Brightness value'
    )
    parser.add_argument(
        '--vscale', type=float, nargs='?', default=0.0001,
        help='Vertical displacement multiplier from DSM'
    )
    
    args = parser.parse_args()

    if args.quick:
        args.rp = 10
    

    # Load blender file
    bf = bpy.ops.wm.open_mainfile(filepath=os.path.abspath('dem_vis.blend'))
    image_node = update_texture_image()

    render_obj = update_render_resolution(args.rp)

    light = update_light_rotation(args.lrx, args.lry, args.lrz)
    
    light = update_light_location(args.lx, args.ly, args.lz)

    light = update_sun_strength(args.sun_brightness)

    world = update_surface_emission(args.surface_brightness)

    material = update_displacement_scaling(args.vscale)

    do_render('render.png')