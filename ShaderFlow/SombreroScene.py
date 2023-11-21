from . import *


@attrs.define
class SombreroScene(SombreroModule):
    modules: Dict[SombreroID, SombreroModule] = attrs.field(factory=dict)

    # Base classes and utils for a Scene
    ffmpeg: BrokenFFmpeg      = attrs.field(factory=BrokenFFmpeg, repr=False)
    vsync:  BrokenVsync       = attrs.field(factory=BrokenVsync)
    client: BrokenVsyncClient = None

    # Internal state
    __quit__: bool = False

    def __attrs_post_init__(self):

        # Special registry for the Scene
        self.modules[self.uuid] = self
        self.scene = self

        # Add default modules
        self.add(SombreroContext)
        self.add(SombreroEngine)

        # Setup the scene
        self.context.init()
        self.setup()
        self.engine.render_to_window()

    # # Loop wise

    def quit(self) -> None:
        """
        Stops the scene main loop created in the loop method
        """
        self.__quit__ = True

    def run(self) -> None:
        """
        Start the scene main loop, which will call the update method every vsync

        Returns:
            None: Code stays on loop until quit is called
        """

        # Create Vsync client
        self.client = self.vsync.new(self.__update__, dt=True)

        while not self.__quit__:
            self.client.frequency = self.context.fps
            self.vsync.next()

    def __update__(self, dt: float):

        # Temporal
        self.context.time += dt
        self.context.dt    = dt

        log.trace(f"Time: {self.context.time:.2f} | dt: {self.context.dt:.4f}")

        # Update modules
        for module in list(self.modules.values()) + [self]:
            module.update()

        # Swap buffers
        self.context.window.swap_buffers()
