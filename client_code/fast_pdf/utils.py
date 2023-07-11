"""
Utility functions for pdf interactions
"""


def media_obj_to_base64(media_obj):
    """returns a base 64 representation of the pdf media obj"""
    import base64

    return base64.b64encode(media_obj.get_bytes()).decode("utf-8")


def print_pdf(blob_media, new_tab=False):
    """prints an anvil blob media of type pdf"""
    if new_tab:
        import anvil.media

        anvil.media.print_media(blob_media)
    else:
        import anvil.js
        from anvil.js.window import printJS

        printJS(
            {
                "printable": media_obj_to_base64(blob_media),
                "type": "pdf",
                "base64": True,
                "onPrintDialogClose": onClose,
            }
        )


def onClose():
    try:
        from anvil.js.window import document

        document.getElementById("printJS").remove()
    except Exception as e:
        print(e)


def download_pdf(blob_media):
    import anvil.media

    anvil.media.download(blob_media)


def pdf_to_component(blob_media):
    from ..components.preview import preview

    comp = preview()
    comp.pdf_media = blob_media
    return comp


def media_obj_to_pil(blob_media):
    try:
        from PIL import Image
        from io import BytesIO

        return Image.open(BytesIO(blob_media.get_bytes()))
    except Exception as e:
        print("WARNING: image could not be converted", e)


def get_image_dimenstions(blob_media) -> tuple:
    """returns a tuple -> (width,height)"""
    import anvil

    if anvil.is_server_side():
        from PIL import Image
        import io

        bytes_io = io.BytesIO(blob_media.get_bytes())
        pil_image = Image.open(bytes_io)
        return pil_image.size
    else:
        return anvil.image.get_dimensions(blob_media)
