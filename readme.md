This repo contains everything needed to:
1. Create a docker container* (more below) for the project - with the necessary set-up and installs etc.
2. Download UK LIDAR data from Defra, and process it into a nice geotiff.
3. Render the geotiff as a topographic, shaded-relief map in blender.
4. Format the render into a nice printable format (inc. changing the colours to CYMK).

Steps:
1. `cd` into the repo folder.
2. `bash dsm_blend_docker_setup.sh`.
3. Enter the container (I attach vscode and do it that way).
4. Edit `run.sh` with desired coordinates and blender config* (more below).
5. `bash run.sh`.
5. Enjoy poster.

Notes:
- The docker image is probably over-the-top for this, but it's just the one I use for everything...
- If you don't have a GPU, you should comment out line 42 (`--gpus all \`) in `bash dsm_blend_docker_setup.sh` - so that you don't get errors trying to mount non-existent GPUs.
- The arguments for render_data.py are explained in a little more detail in the python script. These are mostly trial and error and depend on the specific area you are rendering. But largely the only ones you need to change are:
  - `gpu`. Set to False by default, this should work if you don't have a GPU. Set to True if
  you do have a GPU.
  - `rp`. Set this to 10-25 for initial renders, as it will be faster and you get some idea of how it will look. Usually the contrast increases a bit when you up `rp`.
  - `vscale`. This changes the vertical scaling of the data. Practically, this affects shadow lengths and depth. Too low and the details appear a bit washed out. But too high and streets can appear too shadowed and details appear lost.
  - `sun_brightness` and `surface_brightness`. Together, these affect (surprisingly) the brightness of the render. Broadly I find that `sun_brightness` is best use to increase the definition of the shadows, while `surface_brightness` is best used to soften the shadows,