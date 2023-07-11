"""
JS codes to convert blobs taken from:
https://stackoverflow.com/questions/40674532/how-to-display-base64-encoded-pdf

"""

from ._anvil_designer import previewTemplate
from anvil import *
import anvil.js

class preview(previewTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

  
  def form_show(self, **event_args):
    self.update_ui()

  def update_ui(self):
    if self.pdf_media:
      from ...fast_pdf import utils
      self.call_js('display_blob', utils.media_obj_to_base64(self.pdf_media))
    elif self.url:
      self.call_js('display_url',self.url)

