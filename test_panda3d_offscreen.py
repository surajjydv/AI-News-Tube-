from panda3d.core import loadPrcFileData
# Configure Panda3D for offscreen rendering
loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "win-size 1280 720")
loadPrcFileData("", "framebuffer-alpha #t")

from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec4, NodePath

import numpy as np
from PIL import Image

class TestApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Disable default mouse camera control
        self.disableMouse()
        
        # Position camera
        self.camera.setPos(0, -20, 5)
        self.camera.lookAt(0, 0, 0)
        
        # Add basic lighting
        alight = AmbientLight('alight')
        alight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        dlight = DirectionalLight('dlight')
        dlight.setColor(Vec4(0.8, 0.8, 0.5, 1))
        dnp = self.render.attachNewNode(dlight)
        dnp.setHpr(0, -60, 0)
        self.render.setLight(dnp)
        
        # Create a simple box (we can use Panda3D's built-in loader for simple primitive if available,
        # or load the smile.egg that comes with Panda3D)
        try:
            self.model = self.loader.loadModel("models/box")
            self.model.reparentTo(self.render)
            self.model.setScale(2)
            self.model.setColor(0.8, 0.2, 0.2, 1)
        except Exception as e:
            print(f"Failed to load model: {e}")
            self.model = None
            
        print("TestApp initialized.")
        
    def render_and_save(self, filename="panda3d_test.png"):
        if self.model:
            self.model.setHpr(45, 45, 0)
        
        # Render a frame
        self.graphicsEngine.renderFrame()
        self.graphicsEngine.renderFrame()
        
        # Get screenshot
        dr = self.win.getDisplayRegion(0)
        tex = dr.getScreenshot()
        
        if not tex:
            print("Failed to get screenshot!")
            return False
            
        data = tex.getRamImageAs("RGB")
        image = np.frombuffer(data, np.uint8)
        image = image.reshape((tex.getYSize(), tex.getXSize(), 3))
        
        # Flip vertically because OpenGL renders bottom-up
        image = np.flipud(image)
        
        # Save with PIL
        img = Image.fromarray(image)
        img.save(filename)
        print(f"Saved {filename}")
        return True

if __name__ == "__main__":
    app = TestApp()
    app.render_and_save()
