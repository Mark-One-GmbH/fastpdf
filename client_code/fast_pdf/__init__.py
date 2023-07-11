"""
Main Document Class that acts as a wrapper for client and server side PDF Creation
Browser Library: JSPDF  ->  https://raw.githack.com/MrRio/jsPDF/master/docs/index.html
Server Library: FPDF2 (Reference implementation) ->  https://pyfpdf.github.io/fpdf2/index.html

Fpdf2  is strictly used as a reference implementation
The goal is to create pdfs client and server side without round trips and a unified sdk.

Subtle differences between server and client side implementation/results are possible!
"""

import anvil.server
import anvil.js
import anvil.media

from . import utils


class Document:
    def __init__(
        self,
        page_height=297,
        page_width=210,
        margin_top=10,
        margin_bottom=10,
        margin_left=10,
        margin_right=10,
        header_height=0,
        footer_height=0,
        header_function=None,
        footer_function=None,
        orientation="P",
    ):
        # Initial Variables that define the basic page layout
        self.page_height = page_height
        self.page_width = page_width
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.header_height = header_height
        self.footer_height = footer_height

        self.header_function = header_function
        self.footer_function = footer_function

        self.orientation = orientation
        self.server_side = anvil.is_server_side()

        # Set Base Renderer
        self.renderer_type = self._set_renderer(anvil.is_server_side())

    def _set_renderer(self, is_server_side):
        """
        Sets the base implementaion of the library as a document object
        This class primary purpose is to provide a common interface & code completion
        between fpdf2 and the python implementation of jspdf
        """

        # Set proxy classes depending if code is executed on server or client runtime
        if not self.server_side:
            return self._set_jspdf_renderer()
        else:
            return self._set_fpdf_renderer()

    def _set_jspdf_renderer(self):
        from .jspdf import jsPdf

        self.doc = jsPdf(self)
        self._proxy_doc = self.doc.doc
        return "jspdf"

    def _set_fpdf_renderer(self):
        from .fpdf import CustomFPDF

        self.doc = CustomFPDF(unit="mm", format=[self.page_width, self.page_height])
        self.doc.header_callback = self.header_function
        self.doc.footer_callback = self.footer_function
        self.doc.footer_height = self.footer_height
        self.doc.skip_header = False
        self.doc.skip_footer = False
        self.doc.set_margin(self.margin_bottom + self.footer_height)
        self.doc.set_left_margin(self.margin_left)
        self.doc.set_right_margin(self.margin_right)
        self.doc.set_top_margin(self.margin_top)
        self._proxy_doc = self.doc
        return "fpdf"

    ###########################
    # Public Methods
    ###########################

    def add_page(self, orientation="P", skip_header=False, skip_footer=False):
        if self.renderer_type == "jspdf":
            self.doc.add_page(orientation, skip_header, skip_footer)
        else:
            self.set_skip_header(skip_header)
            self.doc.add_page(orientation)
            self.set_skip_footer(skip_footer)

    def set_skip_header(self, value):
        if self.renderer_type == "fpdf":
            self.doc.skip_header = value

    def set_skip_footer(self, value):
        if self.renderer_type == "fpdf":
            self.doc.skip_footer = value

    def will_page_break(self, height):
        return self.doc.will_page_break(height)

    def add_font(self, file_name, font_name, base_64_font=None, font_style=""):
        """
        Adds a custom font to your pdf

        Preconditions:
          Server: upload the my_font.ttf file to anvil storage -> name must be identical to "file_name"
          Client: provide a base64 representation for your font and pass it over to "base_64_font"
                  Use something like: https://www.giftofspeed.com/base64-encoder/

        Args:
          file_name: name of the .ttf file store on anvil storage e.g poppins-medium.ttf
          font_name: name that will be used to reference from doc.set_font()
          font_style: defines the font style
        """

        if self.renderer_type == "jspdf":
            self.doc.add_font(file_name, font_name, base_64_font, font_style)
        else:
            from anvil.files import data_files

            self.doc.add_font(font_name, "", data_files[file_name])

    def set_font(self, font_name, size=19, style=""):
        self.doc.set_font(font_name, style, size)

    def cell(
        self,
        width,
        height,
        text,
        border=0,
        ln=0,
        align="L",
        fill=False,
        check_new_page=True,
    ):
        if self.renderer_type == "jspdf":
            self.doc.cell(
                width,
                height,
                text,
                border=border,
                ln=ln,
                align=align,
                fill=fill,
                check_new_page=check_new_page,
            )
        else:
            # Attention margin must be set since it is reset to 0 otherwise
            # https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break
            self.doc.set_auto_page_break(
                check_new_page, margin=self.margin_bottom + self.footer_height
            )  # margin 20 is the default value
            self.doc.cell(
                width, height, text, border=border, ln=ln, align=align, fill=fill
            )

    def vertical_text(self, width, height, text, border=0, ln=0, align="L", fill=False):
        self.doc.vertical_text(
            width, height, text, border=border, ln=ln, align=align, fill=fill
        )

    def multi_cell(self, width, height, text, border=0, ln=0, align="L"):
        self.doc.multi_cell(width, height, text, border=border, ln=ln, align=align)

    def spacer(self, height):
        self.cell(1, height, "", ln=1)

    def new_line(self, height):
        self.doc.ln(height)

    def line(self, x_start, y_start, x_end, y_end):
        self.doc.line(x_start, y_start, x_end, y_end)

    def set_y(self, value):
        self.doc.set_y(value)

    def set_x(self, value):
        self.doc.set_x(value)

    def set_xy(self, value_x, value_y):
        self.doc.set_xy(value_x, value_y)

    def page_no(self):
        return self.doc.page_no()

    def set_text_color(self, color_1, color_2=None, color_3=None):
        if color_2 != None and color_3 != None:
            self.doc.set_text_color(color_1, color_2, color_3)
        else:
            self.doc.set_text_color(color_1)

    def set_draw_color(self, color_1, color_2=None, color_3=None):
        if color_2 != None and color_3 != None:
            self.doc.set_draw_color(color_1, color_2, color_3)
        else:
            self.doc.set_draw_color(color_1)

    def set_fill_color(self, color_1, color_2=None, color_3=None):
        if color_2 != None and color_3 != None:
            self.doc.set_fill_color(color_1, color_2, color_3)
        else:
            self.doc.set_fill_color(color_1)

    def set_line_width(self, line_width):
        self.doc.set_line_width(line_width)

    def get_x(self):
        return self.doc.get_x()

    def get_y(self):
        return self.doc.get_y()

    def rotate(self, angle):
        self.doc.rotate(angle)

    def add_image(self, image_data, x=0, y=0, w=100, h=50, keep_aspect_ratio=True):
        """Takes an image in form of a blob and prints it on the pdf"""
        self.doc.add_image(
            image_data, x=x, y=y, w=w, h=h, keep_aspect_ratio=keep_aspect_ratio
        )

    ###########################
    # Output functions
    ###########################

    def to_blob(self, file_name="file"):
        """returns an anvil blob media with the type application/pdf"""
        if self.server_side:
            byte_string = bytes(self.doc.output())
            return anvil.BlobMedia(
                "application/pdf", byte_string, name=f"{file_name}.pdf"
            )
        else:
            return anvil.js.to_media(
                self._proxy_doc.output("blob"),
                content_type="application/pdf",
                name=f"{file_name}.pdf",
            )

    ###########################
    # Display modes for the pdf
    ############################

    def print(self, new_tab=False):
        """prints the pdf to the browser window"""
        utils.print_pdf(self.to_blob(), new_tab=new_tab)

    def download(self, file_name="file"):
        """downloads the pdf file"""
        utils.download_pdf(self.to_blob(file_name))

    def preview(self, role=None, buttons=None, dismissible=True, large=True):
        """Opens an alert to preview"""
        pdf_form = utils.pdf_to_component(self.to_blob())
        anvil.alert(
            pdf_form, large=large, role=role, buttons=buttons, dismissible=dismissible
        )

    def get_form(self):
        """Returns a nestable component wich allows the pdf to be embedded into forms"""
        return utils.pdf_to_component(self.to_blob())
