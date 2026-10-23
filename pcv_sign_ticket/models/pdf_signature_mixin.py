import base64
import re
from io import BytesIO

import pdfplumber
from PIL import Image
from odoo import models
from odoo.tools.pdf import PdfReaderBase, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from typing import Literal


class PdfSignatureMixin(models.AbstractModel):
    _name = "pdf.signature.mixin"
    _description = "PDF Signature Mixin"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_placeholders_in_pdf(self, pdf_bytes, placeholders):
        """Search a PDF for a set of placeholder strings using pdfplumber.

        :param pdf_bytes: Raw PDF bytes.
        :param placeholders: Iterable of strings to locate, e.g. ['[signer1]', '[signer2]'].
        :return: Set of placeholders that were *not* found in the document.
        """
        if not placeholders:
            return set()

        placeholders_to_find = set(placeholders)
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                found = page.search(
                    '|'.join(re.escape(p) for p in placeholders_to_find), regex=True
                )
                for match in found:
                    placeholders_to_find.discard(match['text'])
                if not placeholders_to_find:
                    return set()
        return placeholders_to_find

    def sign_pdf(self,
        keyword, signature_img_b64, encoded_pdf, stamp_img_b64=None,
        direction: Literal['horizontal', 'vertical'] = 'horizontal',
        offset: float = 0,
        sig_width: float = 75,
        sig_height: float = 55,
    ):
        """Locate a keyword in a PDF and overlay a stamped signature at that position.

        :param keyword: Word to search for in the PDF to determine placement.
        :param signature_img_b64: Base64-encoded signature image.
        :param encoded_pdf: Base64-encoded PDF file.
        :param stamp_img_b64: Base64-encoded stamp image (optional).
        :param direction: Place signature to the right ('horizontal') or below ('vertical') the keyword.
        :param offset: Gap in points between the keyword and the signature.
        :param sig_width: Width of the rendered signature in points.
        :param sig_height: Height of the rendered signature in points.
        :return: Base64-encoded signed PDF, or None if keyword not found.
        """
        if not (keyword and signature_img_b64 and encoded_pdf):
            return None

        pdf_bytes = base64.decodebytes(encoded_pdf)
        coordinate = self._find_keyword_coordinate(keyword, pdf_bytes)
        if not coordinate:
            return None

        signature_bytes = self._build_stamped_signature(signature_img_b64, stamp_img_b64)
        overlay_pdf = self._build_signature_overlay(
            signature_bytes, coordinate,
            direction=direction, offset=offset,
            sig_width=sig_width, sig_height=sig_height,
        )
        return self._merge_overlay_into_pdf(overlay_pdf, pdf_bytes, coordinate["page"])

    # ------------------------------------------------------------------
    # PDF helpers
    # ------------------------------------------------------------------

    def _find_keyword_coordinate(self, keyword, pdf_bytes):
        """Search all pages for the first occurrence of keyword and return its position.

        :param keyword: Text to locate.
        :param pdf_bytes: Raw PDF bytes.
        :return: dict(page, x, y_top, y_bottom, page_width, page_height) in PDF coordinate space, or None.
                 y_top/y_bottom are the top and bottom edges of the keyword word in PDF coords (origin bottom-left).
        """
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                for word in page.extract_words():
                    if keyword in word["text"]:
                        return {
                            "page": page_num + 1,
                            "x": word["x0"],
                            "y": page.height - word["top"],
                            "page_width": page.width,
                            "page_height": page.height,
                        }
        return None

    def _build_signature_overlay(self, signature_bytes, coordinate,
        direction: Literal['horizontal', 'vertical'] = 'horizontal',
        offset: float = 0,
        sig_width: float = 75,
        sig_height: float = 55,
    ):
        """Create a single-page PDF containing the signature image at the given coordinate.

        :param signature_bytes: Raw image bytes to embed.
        :param coordinate: dict from _find_keyword_coordinate.
        :param direction: 'horizontal' places signature to the right of keyword;
                         'vertical' places it below.
        :param offset: Gap in points between keyword edge and signature.
        :param sig_width: Rendered width of the signature in points.
        :param sig_height: Rendered height of the signature in points.
        :return: BytesIO of the overlay PDF.
        """
        page_width = coordinate.get("page_width")
        page_height = coordinate.get("page_height")

        y_offset = sig_height * 0.8
        x = coordinate["x"]
        y = coordinate["y"] - y_offset

        if direction == 'horizontal':
            x = x + offset * sig_width
            y = y
        else:
            x = x
            y = y - offset * sig_height

        if page_width and page_height:
            x = min(max(0, x), max(0, page_width - sig_width))
            y = min(max(0, y), max(0, page_height - sig_height))

        overlay = BytesIO()
        if page_width and page_height:
            c = canvas.Canvas(overlay, pagesize=(page_width, page_height))
        else:
            c = canvas.Canvas(overlay)
        c.drawImage(
            image=ImageReader(BytesIO(signature_bytes)),
            x=x,
            y=y,
            width=sig_width,
            height=sig_height,
        )
        c.save()
        overlay.seek(0)
        return overlay

    def _merge_overlay_into_pdf(self, overlay_pdf, pdf_bytes, target_page):
        """Merge the overlay PDF onto a specific page of the source PDF.

        :param overlay_pdf: BytesIO single-page overlay PDF.
        :param pdf_bytes: Raw bytes of the original PDF.
        :param target_page: 1-based page number to apply the overlay to.
        :return: Base64-encoded bytes of the merged PDF.
        """
        reader = PdfReaderBase(BytesIO(pdf_bytes))
        overlay_reader = PdfReaderBase(overlay_pdf)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            if i + 1 == target_page:
                page.merge_page(overlay_reader.pages[0])
            writer.add_page(page)

        output = BytesIO()
        writer.write(output)
        output.seek(0)
        return base64.b64encode(output.read())

    # ------------------------------------------------------------------
    # Image helpers
    # ------------------------------------------------------------------

    def _build_stamped_signature(self, signature_img_b64, stamp_img_b64=None):
        """Composite the signature onto the stamp (or a blank canvas) and return raw bytes.

        :param signature_img_b64: Base64-encoded signature image.
        :param stamp_img_b64: Base64-encoded stamp image (optional).
        :return: PNG bytes of the combined image.
        """
        signature = Image.open(BytesIO(base64.decodebytes(signature_img_b64))).convert("RGBA")
        signature = self._make_background_transparent(signature)
        sig_w, sig_h = signature.size

        if stamp_img_b64:
            stamp = Image.open(BytesIO(base64.decodebytes(stamp_img_b64))).convert("RGBA")
            stamp = self._resize_to_width(stamp, sig_w)
        else:
            stamp = Image.new("RGBA", (sig_w, sig_h), (255, 255, 255, 255))

        offset = (
            (stamp.size[0] - sig_w) // 2,
            (stamp.size[1] - sig_h) // 2,
        )
        result = stamp.copy()
        result.paste(signature, offset, signature)
        return self._image_to_bytes(result)

    def _make_background_transparent(self, image):
        """Replace near-white pixels with fully transparent ones.

        :param image: RGBA PIL Image.
        :return: Modified PIL Image.
        """
        data = image.getdata()
        image.putdata([
            (0, 0, 0, 0) if (px[0] > 200 and px[1] > 200 and px[2] > 200) else px
            for px in data
        ])
        return image

    def _resize_to_width(self, image, target_width):
        """Resize an image to target_width while preserving aspect ratio.

        :param image: PIL Image.
        :param target_width: Desired width in pixels.
        :return: Resized PIL Image.
        """
        orig_w, orig_h = image.size
        new_h = int(target_width * orig_h / orig_w)
        return image.resize((target_width, new_h))

    def _image_to_bytes(self, image):
        """Serialize a PIL Image to PNG bytes.

        :param image: PIL Image.
        :return: bytes.
        """
        buf = BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()
