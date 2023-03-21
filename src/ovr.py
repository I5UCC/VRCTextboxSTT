import openvr
from helper import get_absolute_path
from PIL import Image, ImageDraw, ImageFont
import ctypes
import textwrap
from config import overlay_config

ACTIONSETHANDLE = "/actions/textboxstt"
STTLISTENHANDLE = "/actions/textboxstt/in/sttlisten"


class OVRHandler(object):
    def __init__(self, overlay_conf: overlay_config, script_path) -> None:
        self.overlay_conf: overlay_config = overlay_conf
        
        self.initialized = True
        try:
            self.application = openvr.init(openvr.VRApplication_Background)
            self.action_path = get_absolute_path("bindings/textboxstt_actions.json", script_path)
            self.appmanifest_path = get_absolute_path("app.vrmanifest", script_path)
            openvr.VRApplications().addApplicationManifest(self.appmanifest_path)
            openvr.VRInput().setActionManifestPath(self.action_path)
            self.action_set_handle = openvr.VRInput().getActionSetHandle(ACTIONSETHANDLE)
            self.button_action_handle = openvr.VRInput().getActionHandle(STTLISTENHANDLE)
            if self.overlay_conf.enabled:
                self.overlay_handle = openvr.VROverlay().createOverlay("i5ucc.textboxstt", "TextboxSTT")
                openvr.VROverlay().setOverlayWidthInMeters(self.overlay_handle, 1)
                openvr.VROverlay().setOverlayColor(self.overlay_handle, 1.0, 1.0, 1.0)
                openvr.VROverlay().setOverlayAlpha(self.overlay_handle, self.overlay_conf.opacity)
                self.overlay_font = ImageFont.truetype(get_absolute_path("resources/CascadiaCode.ttf", script_path), 46)
                self.set_overlay_position_hmd()
        except Exception as e:
            self.initialized = False
            print("Error initializing OVR: " + str(e))

    def check_init(self) -> bool:
        """Checks if OpenVR is initialized."""
        if not self.initialized:
            raise Exception("OpenVR not initialized")

    def set_overlay_position_hmd(self) -> bool:
        """Sets the overlay position to the HMD position."""

        try:
            self.check_init()

            overlay_matrix = openvr.HmdMatrix34_t()
            overlay_matrix[0][0] = self.overlay_conf.size
            overlay_matrix[1][1] = self.overlay_conf.size
            overlay_matrix[2][2] = self.overlay_conf.size
            overlay_matrix[0][3] = self.overlay_conf.pos_x
            overlay_matrix[1][3] = self.overlay_conf.pos_y
            overlay_matrix[2][3] = self.overlay_conf.distance

            openvr.VROverlay().setOverlayTransformTrackedDeviceRelative(self.overlay_handle, openvr.k_unTrackedDeviceIndex_Hmd, overlay_matrix)
            return True
        except Exception as e:
            print("Error setting overlay position: " + str(e))
            return False

    def set_overlay_text(self, text: str) -> bool:
        """Sets the text of the overlay by wrapping it to 70 characters and drawing it to an image.
        Then converts the image to bytes and sets the overlay texture to it."""
        
        if not self.overlay_conf.enabled:
            return False

        if text == "":
            openvr.VROverlay().hideOverlay(self.overlay_handle)
            return False
        
        try:
            self.check_init()

            openvr.VROverlay().showOverlay(self.overlay_handle)
            text = textwrap.fill(text, 70)

            _width = 1920
            _height = 200

            _img = Image.new("RGBA", (_width, _height))
            _draw = ImageDraw.Draw(_img)
            _draw.text((_width/2, _height/2), text, font=self.overlay_font, fill=self.overlay_conf.font_color, anchor="mm", stroke_width=2, stroke_fill=self.overlay_conf.border_color, align="center")
            _img_data = _img.tobytes()

            _buffer = (ctypes.c_char * len(_img_data)).from_buffer_copy(_img_data)

            openvr.VROverlay().setOverlayRaw(self.overlay_handle, _buffer, _width, _height, 4)
            return True
        except Exception as e:
            print("Error setting overlay text: " + str(e))
            return False

    def get_ovraction_bstate(self) -> bool:
        """Returns the state of the ovr action"""

        try:
            self.check_init()

            _event = openvr.VREvent_t()
            _has_events = True
            while _has_events:
                _has_events = self.application.pollNextEvent(_event)
            _actionsets = (openvr.VRActiveActionSet_t * 1)()
            _actionset = _actionsets[0]
            _actionset.ulActionSet = self.action_set_handle
            openvr.VRInput().updateActionState(_actionsets)
            return bool(openvr.VRInput().getDigitalActionData(self.button_action_handle, openvr.k_ulInvalidInputValueHandle).bState)
        except Exception as e:
            print("Error getting OVR action state: " + str(e))
            return False

    def destroy_overlay(self) -> bool:
        """Destroys the overlay."""

        try:
            self.check_init()

            openvr.VROverlay().destroyOverlay(self.overlay_handle)
            return True
        except Exception as e:
            print("Error destroying overlay: " + str(e))
            return False

    def shutdown(self) -> bool:
        """Shuts down the OVR handler."""

        try:
            self.check_init()

            openvr.shutdown()
            return True
        except Exception as e:
            print("Error shutting down OVR: " + str(e))
            return False