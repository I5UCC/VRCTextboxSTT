import pyperclip
import logging

log = logging.getLogger(__name__)

class clipboardHandler(object):
    def __init__(self):
        self.content = ""
    
    def set_clipboard(self, text="") -> None:
        """
        Sets the clipboard to the content.
        
        Args:
            text: The text to set the clipboard to.
        
        Returns:
            None
        """
        text = text if text else self.content
        pyperclip.copy(text)
        log.info(f"Set clipboard to: {text}")
