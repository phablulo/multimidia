import sys
import bpy
import cv2
import threading
from time import time

# Falta incluir os paths do baseline e do tf_pose_estimation
from baseline.src.predict3d import predict_3d
from tf_pose_estimation.predict2d import predict_2d

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
  ret, image = cap.read()
  positions = predict_3d(predict_2d(image))
  # exemplo: [{0: [-201.0, 0.0, 51.943537047730615], 1: [-474.1705721109482, -208.9401718290081, 41.40220148657022], 2: [-310.4092332429054, 515.359416142776, 116.26839402713733], 3: [374.0801572763701, -1202.4916760930146, -478.7140994529624], 4: [-254.4517822012352, -761.0045776252917, 209.24702818902642], 5: [-260.4314763508859, -754.9812414179652, 253.05739556990284], 6: [561.8215577517103, 31.85806864941271, 1.5929822520888592], 7: [-111.41899993235573, -696.0916758466257, 539.4809032617857], 8: [-450.2937588911521, -2084.811599789097, 260.20405665801604], 9: [-113.63099885741627, -763.2151493235973, 225.79199976086852], 10: [-107.21460308078916, -749.7813889209444, 269.38457661396797], 11: [-200.99776414206212, 0.08829094862748263, 51.93958567553727], 12: [-329.9766614671375, 717.9654263739253, -334.99480290584194], 13: [-66.05758537631186, 706.9487877038273, 264.21336009428614], 14: [-851.3423462897127, -585.472410147423, 220.44094057700238], 15: [36.41865626712308, 450.66962739672044, -781.0300433232476], 16: [-210.1657483307293, 446.7268439086299, 70.65606596383668], 17: [87.39825995149113, 752.7396655121845, -51.31546231658194], 18: [772.3476980093778, 718.2256092213223, 836.5579763365683], 19: [630.7578525252668, 610.0256617863613, 882.9735803709782], 20: [-76.6741738415401, 128.39619334869604, 153.31145710694466], 21: [-99.9138814495444, 160.29844102879164, 158.72176157764738], 22: [-71.56121011653607, 116.27853842081963, 182.20651550829587], 23: [-71.56121011653607, 116.27853842081963, 182.20651550829587], 24: [-210.1657483307293, 446.7268439086299, 70.65606596383668], 25: [-185.10346828848552, 142.3705601694388, -409.40275260022], 26: [-658.0805817463331, -572.7733683406746, -288.7826951082323], 27: [-1024.231552037622, 1370.0311574406014, -449.4788105659387], 28: [-330.9456254440301, 171.31846748715904, 163.17554580024557], 29: [-316.18461677758563, 204.76324720699077, 161.47876637270804], 30: [-336.36867847431273, 168.84721632622492, 198.28469953145577], 31: [-336.36867847431273, 168.84721632622492, 198.28469953145577]}]
  # falta mapear pra os ossos!
  # --------
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
