import sys
import bpy
import cv2
import threading
from time import time
import tensorflow as tf

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
  self.frame_count += 1
  self.report({'INFO'}, str(self.frame_count)+' frames')
  if self.frame_count > 600:
    self.isFinished = True
  self.isProcessing = False

class StartButton(bpy.types.Operator):
  bl_idname = "fhap.start"
  bl_label = "Start"

  @classmethod
  def poll(cls, context):
    return True

  def invoke(self, context, event):
    self.sess = tf.compat.v1.Session()
    self.frame_count = 0
    self.isFinished = False
    self.isProcessing = False
    self.thread = None

    fhap = context.scene.fhap
    model_cfg, model_outputs = posenet.load_model(int(fhap.model), self.sess)
    self.output_stride = model_cfg['output_stride']
    # 0 = camwra
    # para capturar um vídeo, troca o 0 pelo caminho do arquivo
    self.cap = cv2.VideoCapture(0)
    self.cap.set(3, fhap.cam_width)
    self.cap.set(4, fhap.cam_height)
    self.model_outputs = model_outputs
    context.window_manager.modal_handler_add(self)
    return {'RUNNING_MODAL'}

  def modal(self, context, event):
    if self.isFinished:
      return {'FINISHED'}
    if not self.isProcessing:
      if self.thread is not None:
        self.thread.join()
        #####################################
        #  Terminou de processar um frame.  #
        #  Agora precisamos obter os dados  #
        #  que foram guardados em self parw #
        # movimentar os ossos adequadamente #
        #####################################
      self.isProcessing = True
      self.thread = threading.Thread(target=thread_modal, args=(self, context))
      self.thread.start()
    return {'PASS_THROUGH'}


# --------------------------
#  Dezenho do Painel
# --------------------------
# Nomes dos ossos
items = ('Shoulder','Elbow','Wrist','Hip','Knee','Ankle')
items = [('fhapHead','Head')] + [('fhap'+side+x, side+' '+x) for side in ('Left','Right') for x in items]
class FhapPanel(bpy.types.Panel):
  bl_idname = "OBJECT_PT_fhap"
  bl_label = "FHAP Options"

  bl_context = "data"
  bl_region_type = "WINDOW"
  bl_space_type = "PROPERTIES"
  bl_options = {"DEFAULT_CLOSED"}

  def draw(self, context):
    self.layout.prop(context.scene.fhap, "fps")

    row = self.layout.row()
    row.prop(context.scene.fhap, "sframe")
    row.prop(context.scene.fhap, "nseconds")

    self.layout.prop(context.scene.fhap, "model")

    row = self.layout.row()
    row.prop(context.scene.fhap, "cam_width")
    row.prop(context.scene.fhap, "cam_height")
    row.prop(context.scene.fhap, "scale_factor")

    armature = context.active_object.data
    for name, display in items:
      self.layout.prop_search(context.scene, name, armature, "bones", text=display)
    self.layout.operator("fhap.start", text="Start")

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
