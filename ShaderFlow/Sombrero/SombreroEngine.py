from . import *


@attrs.define
class SombreroEngine(SombreroModule):
    shader: SombreroShader = attrs.field(factory=SombreroShader)
    textures: dict[SombreroTexture] = attrs.field(factory=dict)

    # ModernGL attributes
    program:          moderngl.Program     = None
    __texture__:      moderngl.Texture     = None
    __fbo__:          moderngl.Framebuffer = None
    vao:              moderngl.VertexArray = None
    vbo:              moderngl.Buffer      = None
    clear:            bool                 = True
    instances:        int                  = 1

    # Should this instance render finally to the window
    final:            bool                 = False

    # # Texture

    @property
    def texture(self) -> moderngl.Texture:
        if not self.__texture__:
            self.create_texture_fbo()
        return self.__texture__

    @texture.setter
    def texture(self, value: moderngl.Texture) -> None:
        self.__texture__ = value

    def create_texture_fbo(self):

        # Recreate the Headless window FBO, as it doesn't answer to self.window.size
        # Todo: Talk to ModernGL devs about this, headless to resize its own FBO?
        if self.final:
            self.context.window._fbo = self.context.opengl.framebuffer(
                color_attachments=self.context.opengl.texture(self.context.resolution, 4),
                depth_attachment=self.context.opengl.depth_texture(self.context.resolution),
            )
            return

        # Release the old objects
        if self.__texture__:
            self.__texture__.release()
        if self.__fbo__:
            self.__fbo__.release()

        # Create new ones
        self.texture = self.context.opengl.texture(size=self.context.render_resolution, components=4)
        self.fbo     = self.context.opengl.framebuffer(color_attachments=[self.texture])

    # # Frame buffer object

    @property
    def fbo(self) -> moderngl.Framebuffer:
        if self.final:
            return self.context.window.fbo
        if not self.__fbo__:
            self.create_texture_fbo()
        return self.__fbo__

    @fbo.setter
    def fbo(self, value: moderngl.Framebuffer) -> None:
        if self.final:
            return
        self.__fbo__ = value

    # # Uniforms

    def set_uniform(self, name: str, value: Any) -> Self:
        """Send an uniform to the shader by name and value"""
        if (value is not None) and (name in self.program):
            self.program[name].value = value
        return self

    def get_uniform(self, name: str) -> Any | None:
        """Get a uniform from the shader by name"""
        return self.program[name].get(value, None)

    # # Rendering

    def load_shaders(self, vertex: str=Unchanged, fragment: str=Unchanged) -> None:
        """Reload the shaders after some change of variables or content"""
        log.info(f"{self.who} Reloading shaders")

        # Add pipeline variable definitions
        for variable in self.full_pipeline():
            self.shader.common_variable(variable)
            log.trace(f"{self.who} • {variable.declaration}")

        # Render the vertices that are defined on the shader
        self.vbo = self.context.opengl.buffer(self.shader.vertices)

        # Set new optional shaders
        self.shader.vertex   = vertex   or self.shader.__vertex__
        self.shader.fragment = fragment or self.shader.__fragment__

        # Create the Moderngl Program
        self.program = self.context.opengl.program(
            fragment_shader=self.shader.fragment,
            vertex_shader=self.shader.vertex,
        )

        # Create the Vertex Array Object
        self.vao = self.context.opengl.vertex_array(
            self.program,
            [(self.vbo, *self.shader.vao_definition)],
            skip_errors=True
        )

    # # Textures

    @property
    def __texture_modules__(self) -> list[SombreroTexture]:
        """Get SombreroTexture modules bound to this instance"""
        return [module for module in self.bound if isinstance(module, SombreroTexture)]

    def new_texture(self, *args, **kwargs) -> SombreroTexture:
        return self.add(SombreroTexture(*args, **kwargs))

    # # SombreroModule

    def update(self) -> None:
        if not self.program:
            self.load_shaders()
        self.render()

    def render(self, read: bool=False) -> Option[None, bytes]:

        # Set indexes to textures
        for index, module in enumerate(self.__texture_modules__):
            module.texture.use(index)
            module.index = index

        # Pipe the pipeline
        for variable in self.full_pipeline():
            self.set_uniform(variable.name, variable.value)
            # log.trace(f"{self.who} • {variable.name} = {variable.value}")

        # Set render target
        self.fbo.use()

        if self.clear:
            self.fbo.clear()

        # Render the shader
        self.vao.render(moderngl.TRIANGLE_STRIP, instances=self.instances)

        # Optionally read the pixels
        return self.fbo.read() if read else None

    def handle(self, message: SombreroMessage) -> None:

        # Resize window action
        if isinstance(message, SombreroMessage.Window.Resize):
            self.create_texture_fbo()

            # The final Engine has to update the Window FBO
            if self.final:
                self.fbo.viewport = (0, 0, message.width, message.height)

        # Recreate textures action
        if isinstance(message, SombreroMessage.Engine.RecreateTextures):
            self.create_texture_fbo()

        # Reload shaders action
        if isinstance(message, SombreroMessage.Engine.ReloadShaders):
            self.load_shaders()