import os
import sys
import bpy
import cv2
import threading
from time import time
from math import sqrt
from mathutils import Euler, Vector, Matrix
import tensorflow as tf

# Falta incluir os paths do baseline e do tf_pose_estimation
tf.app.flags.DEFINE_string("P", "", "Blender...")

SCRIPT_DIR = None
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
from baseline.src.predict3d import predict_3d, get_3d_estimator
from tf_pose_estimation.predict2d import predict_2d, get_2d_estimator

estimator_3d = None
estimator_2d = None

# Nomes dos ossos
items = ('Shoulder','Elbow','Wrist','Hip','Knee','Ankle')
items = [
    ('fhapHeadBase','Head'),
    ('fhapSpineBase','Spine Base'),
    ('fhapSpineUpper','Spine Upper'),
] + [('fhap'+side+x, side+' '+x) for side in ('Left','Right') for x in items]
# mapeamento entre nome dos ossos e as predições que recebo
mapItems = {
  'fhapRightHip': (0,1),
  'fhapRightKnee': (1,2),
  'fhapRightAnkle': (2,3),

  'fhapLeftHip': (11,6),
  'fhapLeftKnee': (6,7),
  'fhapLeftAnkle': (7,8),

  'fhapRightShoulder': (13,25),
  'fhapRightElbow': (25,26),
  'fhapRightWrist': (26,27),

  'fhapLeftShoulder': (13,17),
  'fhapLeftElbow': (17,18),
  'fhapLeftWrist': (18,19),

  'fhapSpineBase': (0,29),
  'fhapSpineUpper': (29, 24),

  'fhapHeadBase': (24,14),
  'fhapHeadUpper': (14,15),
}
# utilidades
def norm(vec):
  s = sqrt(sum(x*x for x in vec))
  return [x/s for x in vec]

# --------------------------
# Propriedadws a serem usadas no painel
# --------------------------
class Properties(bpy.types.PropertyGroup):
  fps: bpy.props.IntProperty(
    name = "FPS",
    description = "Frames to capture per second",
    default = 1,
    min = 1,
    max = bpy.context.scene.render.fps
  )
  filename: bpy.props.StringProperty(
    name="Video path",
    description="Video to capture motion from",
    subtype='FILE_PATH'
  )
  sframe: bpy.props.IntProperty(
    name = "Starting Frame",
    description = "Starting frame",
    default = 1,
    min = 0
  )
  nseconds: bpy.props.IntProperty(
    name = "Duration",
    description = "Number of seconds to record",
    default = 60,
    min = 1
  )
  model: bpy.props.EnumProperty(
    name = "Model",
    default = '100',
    items = [
      ('50', '50', 'Model 50'),
      ('75', '75', 'Model 75'),
      ('100', '100', 'Model 100'),
      ('101', '101', 'Model 101')
    ]
  )
  cam_width: bpy.props.IntProperty(
    name = "Camera Width",
    default = 1280
  )
  cam_height: bpy.props.IntProperty(
    name = "Camera Height",
    default = 720
  )
  scale_factor: bpy.props.FloatProperty(
    name = "Scale Factor",
    default = 0.3,
    min = 0,
    max = 1
  )

# --------------------------
#  Processamento dos dados
# --------------------------
def thread_modal(self, context):
  ##################################################
  #     aqui devemos ler um frame de self.cap,     #
  #   obter informação sobre os pontos das juntas  #
  # e guardar esses pontos em algum lugar de self. #
  #  Não se deve alterar nada aqui pois o Blender  #
  #   não suporta alteracões feitas por threads.   #
  ##################################################
  if self.cap.isOpened():
    ret, image = self.cap.read()
    if ret:
      two_d = predict_2d(image, estimator_2d)
      thr_d = predict_3d(two_d, estimator_3d)
      self.positions = thr_d
      self.frame_count += 1
      self.isProcessing = False
      return
  self.isFinished = True
  self.isProcessing = False
  # --------
  # self.isFinished = True
  # if self.frame_count > 600:
  #   self.isFinished = True

class StartButton(bpy.types.Operator):
  bl_idname = "fhap.start"
  bl_label = "Start"

  @classmethod
  def poll(cls, context):
    return True

  def invoke(self, context, event):
    # carrega os estimatores
    global estimator_3d
    global estimator_2d
    if estimator_3d is None: estimator_3d = get_3d_estimator()
    if estimator_2d is None: estimator_2d = get_2d_estimator()

    # cria outras propriedades
    self.frame_count = 0
    self.isFinished = False
    self.isProcessing = False
    self.thread = None

    #fhap = context.scene.fhap
    # 0 = camwra
    # para capturar um vídeo, troca o 0 pelo caminho do arquivo
    print("Opening", context.scene.fhap.filename)
    self.cap = cv2.VideoCapture(context.scene.fhap.filename)
    #self.cap.set(3, fhap.cam_width)
    #self.cap.set(4, fhap.cam_height)
    context.window_manager.modal_handler_add(self)
    bpy.ops.object.mode_set(mode='POSE')
    return {'RUNNING_MODAL'}

  def modal(self, context, event):
    if self.isFinished:
      self.report({'INFO'}, 'Finished')
      return {'FINISHED'}
    if not self.isProcessing:
      if self.thread is not None:
        self.thread.join()
        self.report({'INFO'}, str(self.frame_count)+' frames')
        #####################################
        #  Terminou de processar um frame.  #
        #  Agora precisamos obter os dados  #
        #  que foram guardados em self parw #
        # movimentar os ossos adequadamente #
        #####################################
        positions = self.positions
        if len(positions) > 0:
          positions = positions[0]
          bones = context.active_object.pose.bones
          base  = Vector((0, -1, 0))
          for name,_ in items:
            bone = getattr(context.scene, name)
            if bone:
              bone   = bones[bone]
              vector = [b - a for a,b in zip(positions[mapItems[name][0]], positions[mapItems[name][1]])]
              vector = Vector(norm(vector))
              euler  = vector.rotation_difference(base).to_euler()
              euler   = euler.to_matrix().to_4x4()
              scale  = bone.matrix.to_scale()
              scale  = Matrix([ [scale[0], 0, 0, 0], [0, scale[1], 0, 0], [0, 0, scale[2], 0], [0, 0, 0, 1] ])
              locat  = Matrix.Translation(bone.matrix.translation)
              bone.matrix = locat @ euler @ scale
              context.view_layer.update()
              bone.keyframe_insert(data_path='rotation_euler', frame=self.frame_count)
        # -----------------------------------
      self.isProcessing = True
      self.thread = threading.Thread(target=thread_modal, args=(self, context))
      self.thread.start()
    return {'PASS_THROUGH'}


# --------------------------
#  Dezenho do Painel
# --------------------------
class FhapPanel(bpy.types.Panel):
  bl_idname = "OBJECT_PT_fhap"
  bl_label = "FHAP Options"

  bl_context = "data"
  bl_region_type = "WINDOW"
  bl_space_type = "PROPERTIES"
  bl_options = {"DEFAULT_CLOSED"}

  def draw(self, context):
    #self.layout.prop(context.scene.fhap, "fps")
    self.layout.prop(context.scene.fhap, "filename")
    self.layout.prop(context.scene.fhap, "sframe")

    #row = self.layout.row()
    #row.prop(context.scene.fhap, "cam_width")
    #row.prop(context.scene.fhap, "cam_height")
    #row.prop(context.scene.fhap, "scale_factor")

    armature = context.active_object.data
    for name, display in items:
      self.layout.prop_search(context.scene, name, armature, "bones", text=display)
    self.layout.operator("fhap.start", text="Process")

# --------------------------
# Registro das classes criadas
# --------------------------
classes = (Properties, StartButton, FhapPanel)
def register():
  for c in classes: bpy.utils.register_class(c)
  bpy.types.Scene.fhap = bpy.props.PointerProperty(type=Properties)
  for name,_ in items:
    setattr(bpy.types.Scene, name, bpy.props.StringProperty())

def unregister():
  for c in clsses: bpy.utils.unregister_class(c)
  del bpy.types.Scene.fhap
  for name,_ in items:
    del bpy.types.Scene[name]

# Auto executa, pro caso de ter sudo
# copiado e colado na área de scripting.
if __name__ == "__main__":
  register()
