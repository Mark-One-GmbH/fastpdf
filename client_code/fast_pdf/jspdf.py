

class jsPdf:
    def __init__(self, parent):
        # parent document
        self.parent = parent
        # Inherited Page layout
        self.page_height = parent.page_height
        self.page_width = parent.page_width
        self.margin_top = parent.margin_top
        self.margin_bottom = parent.margin_bottom
        self.margin_left = parent.margin_left
        self.margin_right = parent.margin_right
        self.header_height = parent.header_height
        self.footer_height = parent.footer_height

        self.footer_callback = parent.footer_function
        self.header_callback = parent.header_function

        self.orientation = parent.orientation

        if self.get_orientation() == "landscape":
            self.page_width = parent.page_height
            self.page_height = parent.page_width

        # JS PDF Proxy Object
        from anvil.js.window import jspdf

        self.doc = jspdf.jsPDF(
            self.get_orientation(), "mm", [self.page_width, self.page_height]
        )

        # Cursor position
        self.current_x = 0
        self.current_y = 0
        self._reset_x()
        self._reset_y()

        # Helper Flags
        self.auto_page_break = True
        self.first_page = True
        self.current_font = None
        self.current_text_color = None
        self.page_number = 0

    def get_orientation(self):
        return "portrait" if self.orientation == "P" else "landscape"

    def header(self):
        # get current font attributes
        font_tuple = self.current_font
        text_color = self.current_text_color

        self._reset_x()
        self.current_y = self.margin_top
        self.header_callback(self)

        # reset current font attributes
        if font_tuple:
            font_name, style, size = font_tuple
            self.set_font(font_name, style, size)
        if text_color:
            self.set_text_color(*text_color)

    def footer(self):
        # get current font attributes
        font_tuple = self.current_font
        text_color = self.current_text_color

        self._reset_x()
        self.current_y = self.page_height - self.margin_bottom - self.footer_height
        self.auto_page_break = False
        self.footer_callback(self)
        self.auto_page_break = True

        # reset current font attributes
        if font_tuple:
            font_name, style, size = font_tuple
            self.set_font(font_name, style, size)
        if text_color:
            self.set_text_color(*text_color)

    def add_page(self, orientation="P", skip_header=False, skip_footer=False):
        self.page_number += 1

        self.orientation = orientation
        # ignore first page since fpdf start with 0 pages but js pdf with 1
        if self.first_page:
            self.first_page = False
        else:
            self.doc.addPage(
                [self.page_width, self.page_height], self.get_orientation()
            )

        if not skip_footer:
            self.footer()
        self._reset_y()
        if not skip_header:
            self.header()
        self._reset_x()

    def will_page_break(self, height):
        return (
            self.current_y + height + self.margin_bottom + self.footer_height
            >= self.page_height
        )

    def add_font(self, file_name, font_name, base_64_font, font_style=""):
        self.doc.addFileToVFS(file_name, base_64_font)
        self.doc.addFont(file_name, font_name, font_style)

    def set_font(self, font_name, style="", size=10):
        self.current_font = (font_name, style, size)
        self.doc.setFont(font_name, style)
        self.doc.setFontSize(size)

    def _check_new_page(self, offset):
        if (
            self.auto_page_break
            and self.current_y + offset + self.margin_bottom + self.footer_height
            >= self.page_height
        ):
            self.add_page(orientation=self.orientation)

    def _reset_x(self):
        self.current_x = self.margin_left

    def _reset_y(self):
        self.current_y = self.margin_top

    def _get_font(self):
        return self.current_font

    def vertical_text(self, width, height, text, border=0, ln=1, align="L", fill=False):
        # check if new page must be added
        self._check_new_page(height)

        if fill:
            rect_height = self.doc.getTextDimensions(text).get("w") + 2
            add_height = self.doc.getTextDimensions(text).get("w") + 1
            self.doc.rect(
                self.current_x, self.current_y - add_height, height, rect_height, "F"
            )

        font_name, style, font_size = self._get_font()
        add_width = height / 2 + font_size * 0.106

        self.doc.text(text, self.current_x + add_width, self.current_y, {"angle": 90})

        self.current_x += width
        if ln == 1:
            self.current_y += height
            self._reset_x()

    def cell(
        self,
        width,
        height,
        text,
        border=0,
        ln=1,
        align="L",
        fill=False,
        check_new_page=True,
    ):
        # check if new page must be added
        if check_new_page:
            self._check_new_page(height)

        if fill:
            self.doc.rect(self.current_x, self.current_y, width, height, "F")

        font_name, style, font_size = self._get_font()
        add_height = (
            (height / 2 + font_size * 0.106)
            if isinstance(height, (int, float)) and isinstance(font_size, (int, float))
            else 4
        )

        if align == "C":
            self.doc.text(
                text,
                self.current_x + width / 2,
                self.current_y + add_height,
                {"align": "center"},
            )
        elif align == "R":
            self.doc.text(
                text + " ",
                self.current_x + width,
                self.current_y + add_height,
                {"align": "right"},
            )
        else:
            self.doc.text(
                text, self.current_x, self.current_y + add_height, {"align": "left"}
            )

        self.current_x += width
        if ln == 1:
            self.current_y += height
            self._reset_x()

    def multi_cell(self, width, height, text, border=0, ln=1, align="L"):
        if not text:
            return
        # splits the text into parts
        current_x = self.current_x
        lines_list = text.splitlines()

        for line in lines_list:
            words_list = line.split(" ")
            current_row_text = ""
            for word in words_list:
                # in new lines when text is longer that actual cell -> shorten text until it fits and redo it until whole word is done
                if (
                    not current_row_text
                    and self.doc.getTextDimensions(word).get("w") > width
                ):
                    current_row_text = word
                    while (
                        self.doc.getTextDimensions(current_row_text).get("w") > width
                    ):  # loop over and cut last character of word
                        current_row_text = current_row_text[:-1]
                        if (
                            self.doc.getTextDimensions(current_row_text).get("w")
                            <= width
                        ):  # if word fits -> make cell and set remaining word - if it is shorter than cell -> continue, if it is larger -> redo cycle
                            self.cell(
                                width, height, current_row_text, border=border, ln=1
                            )
                            self.current_x = current_x
                            word = word[len(current_row_text) :]
                            current_row_text = word
                    current_row_text += " "
                    continue

                # if text plus word is larger than cell -> append cell and start new row
                if (
                    self.doc.getTextDimensions(current_row_text + word).get("w")
                    >= width
                ):
                    self.cell(width, height, current_row_text, border=border, ln=1)
                    self.current_x = current_x
                    current_row_text = ""

                current_row_text += word + " "

            # in the end if there is still a text to append
            if current_row_text:
                self.cell(width, height, current_row_text, border=border, ln=1)
                self.current_x = current_x

        self._reset_x()

    def line(self, x_start, y_start, x_end, y_end):
        self.doc.line(x_start, y_start, x_end, y_end)

    def set_text_color(self, color_1, color_2=None, color_3=None):
        if color_2 is not None and color_3 is not None:
            self.doc.setTextColor(color_1, color_2, color_3)
        else:
            self.doc.setTextColor(color_1)

        self.current_text_color = (color_1, color_2, color_3)

    def set_draw_color(self, color_1, color_2=None, color_3=None):
        if color_2 is not None and color_3 is not None:
            self.doc.setDrawColor(color_1, color_2, color_3)
        else:
            self.doc.setDrawColor(color_1)

    def set_fill_color(self, color_1, color_2=None, color_3=None):
        if color_2 is not None and color_3 is not None:
            self.doc.setFillColor(color_1, color_2, color_3)
        else:
            self.doc.setFillColor(color_1)

    def set_line_width(self, line_width):
        self.doc.setLineWidth(line_width)

    def get_x(self):
        return self.current_x

    def get_y(self):
        return self.current_y

    def rotate(self, angle):
        self.doc.rotate(angle)

    def doc(self, width, height, text):
        self.doc.text(text, height, width)

    def add_image(
        self,
        image_data,
        x=0,
        y=0,
        w=0,
        h=0,
        alias="",
        compression="FAST",
        rotation=0,
        keep_aspect_ratio=True,
    ):
        """Takes an image in form of a blob and prints it on the pdf"""
        from . import utils

        if keep_aspect_ratio:
            d_width, d_height = utils.get_image_dimenstions(image_data)
            image_ar = d_width / d_height
            pdf_ar = w / h
            if image_ar < pdf_ar:
                # adjust height
                w = h * image_ar
            elif image_ar > pdf_ar:
                h = w / image_ar

        base_64_image = utils.media_obj_to_base64(image_data)
        self.doc.addImage(
            base_64_image, "JPEG", x, y, w, h, alias, compression, rotation
        )

    def page_no(self):
        return self.page_number

    def set_y(self, value):
        if value <= 0:
            return
            self.current_y = self.page_height - value
        else:
            self.current_y = value

    def set_x(self, value):
        self.current_x = value

    def set_xy(self, value_x, value_y):
        self.set_x(value_x)
        self.set_y(value_y)
