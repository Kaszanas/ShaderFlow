from moderngl_window.context.base import BaseWindow as ModernglWindow

from .. import *

# isort: off
from .SombreroMessage import *
from .SombreroShader import *
from .SombreroModule import *
from .Modules import *
from .SombreroEngine import *
from .SombreroScene import *

# Make modules findable as property on the scene
SombreroModule.make_findable(SombreroContext)
