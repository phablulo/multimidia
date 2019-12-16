# FHAP - Fast Human Animation Prototyping

## Dependencies

- OpenCV 3
- Tensorflow
- Numpy

## Instructions (Ubuntu)

This isn't even an alpha release. You should expect bugs.

- clone this repo
- execute `install.sh`
- open blender 2.8+
- go to Scripting tab
- open the `index.py` file
- change the `SCRIPT_DIR` variable (line 14) to the path you clonned the repo
- press `ALT + P` to load the file (you Blender will freeze for some seconds)
- go back to layout mode
- create the armature (if you don't have one already)
- assign the desired bones in `FHAP Options` inside `Object Data Properties`
- assign a video source in `FHAP Options`
- click Process. (your Blender will freeze for a long time before starting to create the animation)


## Known issues

#### Blender freezes when loading the script

It's loading the needed libraries

#### Blender freezes for along time the first time the button `Process` is clicked

Tensorflow is loading all the needed models

#### Animation is "trembling"

Yap. Some smoothing will be implemented in future.

#### Animation sometimes is really incorrect

The model isn't perfect and it makes many mistakes. It can be mitigated by set each frame a score and striping out the bad ones. It might be implemented in future.

#### Armature does not translate automatically

Yes.


## TODO

- animation smoothing
- assign a score to each frame and strip out the bad ones
- armature translation
- turn this into a Blender plugin


## How does it works?

Each video frame is feed to [tf-pose-estimation](https://github.com/ildoonet/tf-pose-estimation) model. It's 2D estimations are feed to [3d-pose-baseline](https://github.com/una-dinosauria/3d-pose-baseline) model. It's 3D estimations are converted to Blender space.


Thanks to [ArashHosseini](https://github.com/ArashHosseini/3d-pose-baseline) for guidelines on his/her repo.

