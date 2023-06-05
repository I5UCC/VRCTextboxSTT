import os
import openvr
from helper import get_absolute_path
from PIL import Image, ImageDraw, ImageFont
import ctypes
import textwrap
from config import overlay_config
from psutil import process_iter
import traceback
import logging

log = logging.getLogger(__name__)

ACTIONSETHANDLE = "/actions/textboxstt"
STTLISTENHANDLE = "/actions/textboxstt/in/sttlisten"

class NotInitializedException(Exception):
    """Raised when OpenVR is not initialized."""
    pass


class OVRHandler(object):
    def __init__(self, config_overlay: overlay_config, script_path, debug = False) -> None:
        self.debug = debug
        self.overlay_conf: overlay_config = config_overlay
        self._script_path = script_path
        self.initialized = False
        
    def init(self):
        if self.initialized:
            self.shutdown()

        self.initialized = False

        try:
            self.application = openvr.init(openvr.VRApplication_Overlay)
            self.action_path = get_absolute_path("bindings/textboxstt_actions.json", self._script_path)
            self.appmanifest_path = get_absolute_path("app.vrmanifest", self._script_path)
            if not self.debug:
                openvr.VRApplications().addApplicationManifest(self.appmanifest_path)
            openvr.VRInput().setActionManifestPath(self.action_path)
            self.action_set_handle = openvr.VRInput().getActionSetHandle(ACTIONSETHANDLE)
            self.button_action_handle = openvr.VRInput().getActionHandle(STTLISTENHANDLE)
            self.initialized = True
            if self.overlay_conf.enabled:
                self.overlay_handle = openvr.VROverlay().createOverlay("i5ucc.textboxstt", "TextboxSTT")
                openvr.VROverlay().setOverlayWidthInMeters(self.overlay_handle, 1)
                openvr.VROverlay().setOverlayColor(self.overlay_handle, 1.0, 1.0, 1.0)
                openvr.VROverlay().setOverlayAlpha(self.overlay_handle, self.overlay_conf.opacity)
                self.overlay_font = ImageFont.truetype(get_absolute_path("resources/CascadiaCode.ttf", self._script_path), 46)
                self.set_overlay_position_to_device()
        except openvr.openvr.error_code.InitError_Init_HmdNotFound:
            self.initialized = False
            log.info("SteamVR is not running.")
        except openvr.openvr.error_code.InitError_Init_NoServerForBackgroundApp:
            self.initialized = False
            log.info("SteamVR is not running.")
        except Exception:
            self.initialized = False
            log.error("Error initializing OVR: ")
            log.error(traceback.format_exc())

    def _check_init(self) -> bool:
        """Checks if OpenVR is initialized."""
        if not self.initialized:
            raise NotInitializedException("OpenVR not initialized")

    def set_overlay_position_to_device(self, device: str="HMD") -> bool:
        """Sets the overlay position to the position relative to the given device."""

        try:
            self._check_init()

            tracked_device = openvr.k_unTrackedDeviceIndex_Hmd

            match device.upper():
                case "HAND_LEFT":
                    tracked_device = openvr.TrackedControllerRole_LeftHand
                case "HAND_RIGHT":
                    tracked_device = openvr.TrackedControllerRole_RightHand
                case _:
                    tracked_device = openvr.k_unTrackedDeviceIndex_Hmd

            overlay_matrix = openvr.HmdMatrix34_t()
            overlay_matrix[0][0] = self.overlay_conf.size
            overlay_matrix[1][1] = self.overlay_conf.size
            overlay_matrix[2][2] = self.overlay_conf.size
            overlay_matrix[0][3] = self.overlay_conf.pos_x
            overlay_matrix[1][3] = self.overlay_conf.pos_y
            overlay_matrix[2][3] = self.overlay_conf.distance

            openvr.VROverlay().setOverlayTransformTrackedDeviceRelative(self.overlay_handle, tracked_device, overlay_matrix)
            return True
        except NotInitializedException:
            return False
        except Exception as e:
            log.error("Error setting overlay position: ")
            log.error(traceback.format_exc())
            return False

    def set_overlay_text(self, text: str, retry = False) -> bool:
        """Sets the text of the overlay by wrapping it to 70 characters and drawing it to an image.
        Then converts the image to bytes and sets the overlay texture to it."""
        
        if not self.overlay_conf.enabled:
            return False
        
        try:
            self._check_init()

            if text == "":
                openvr.VROverlay().hideOverlay(self.overlay_handle)
                return False

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
        except NotInitializedException:
            return False
        except openvr.openvr.error_code.OverlayError_RequestFailed:
            if not retry:
                log.error("Request setting overlay text failed. Retrying...")
                self.init()
                return self.set_overlay_text(text, True)
            else:
                log.error("Request setting overlay text failed. x2")
                return False
        except Exception:
            log.error("Error setting overlay text: ")
            log.error(traceback.format_exc())
            return False

    def get_ovraction_bstate(self) -> bool:
        """Returns the state of the ovr action"""

        try:
            self._check_init()

            _event = openvr.VREvent_t()
            _has_events = True
            while _has_events:
                _has_events = self.application.pollNextEvent(_event)
            _actionsets = (openvr.VRActiveActionSet_t * 1)()
            _actionset = _actionsets[0]
            _actionset.ulActionSet = self.action_set_handle
            openvr.VRInput().updateActionState(_actionsets)
            return bool(openvr.VRInput().getDigitalActionData(self.button_action_handle, openvr.k_ulInvalidInputValueHandle).bState)
        except NotInitializedException:
            return False
        except Exception:
            log.error("Error getting OVR action state: ")
            log.error(traceback.format_exc())
            return False

    def destroy_overlay(self) -> bool:
        """Destroys the overlay."""

        try:
            self._check_init()

            openvr.VROverlay().destroyOverlay(self.overlay_handle)
            return True
        except NotInitializedException:
            return False
        except Exception:
            log.error("Error destroying overlay: ")
            log.error(traceback.format_exc())
            return False

    def shutdown(self) -> bool:
        """Shuts down the OVR handler."""

        self.destroy_overlay()
        try:
            self._check_init()
            openvr.shutdown()
            return True
        except NotInitializedException:
            return False
        except Exception as e:
            log.error("Error shutting down OVR: " + str(e))
            return False

    @staticmethod
    def is_running() -> bool:
        """Checks if SteamVR is running."""
        _proc_name = "vrmonitor.exe" if os.name == 'nt' else "vrmonitor"
        return _proc_name in (p.name() for p in process_iter())
