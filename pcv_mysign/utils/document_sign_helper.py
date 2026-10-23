import base64
import datetime
import io
import os
import pytz
import tempfile
from typing import Optional

import aiohttp
from PIL import Image, ImageDraw, ImageFont

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields
from pyhanko.sign.general import SigningError
from pyhanko import stamp
from pyhanko.pdf_utils import images
from pyhanko.sign.signers.pdf_signer import PdfSigner, PdfSignatureMetadata
from pyhanko.sign.signers.csc_signer import (
    CSCAuthorizationInfo,
    CSCAuthorizationManager,
    CSCCredentialInfo,
    CSCServiceSessionInfo,
    CSCSigner,
)
from pyhanko.sign.timestamps import HTTPTimeStamper

from .common import get_hash_algo_oid


_STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "static"
)
_FONT_PATH = os.path.join(_STATIC_DIR, "src", "fonts", "arial.ttf")
_CHECKMARK_PATH = os.path.join(_STATIC_DIR, "description", "checkmark.png")

_STAMP_IMAGE_WIDTH = 100
_STAMP_FONT_SIZE = 7
_STAMP_LINE_GAP = 8
_STAMP_PADDING_X = 14
_STAMP_PADDING_Y = 14
_STAMP_GAP = 10


_SIG_BOX_WIDTH = 200
_SIG_BOX_HEIGHT = 200
_SIG_BOX_FALLBACK = (50, 600, 50 + _SIG_BOX_WIDTH, 600 + _SIG_BOX_HEIGHT)


class MysignAuthorizationManager(CSCAuthorizationManager):
    def __init__(
        self,
        csc_session_info: CSCServiceSessionInfo,
        credential_info: CSCCredentialInfo,
        session: aiohttp.ClientSession,
        documents: Optional[list] = None,
        description: Optional[str] = None,
    ):
        super().__init__(csc_session_info, credential_info)
        self._session = session
        self.documents = documents
        self.description = description

    async def authorize_signature(self, hash_b64s: list) -> CSCAuthorizationInfo:
        req_data = self.format_csc_auth_request(
            num_signatures=len(hash_b64s),
            hash_b64s=hash_b64s,
            description=self.description,
        )
        if self.documents:
            req_data["documents"] = self.documents

        url = self.csc_session_info.endpoint_url("credentials/authorize")
        try:
            async with self._session.post(
                url,
                headers=self.auth_headers,
                json=req_data,
                raise_for_status=True,
            ) as response:
                response_data = await response.json()
        except aiohttp.ClientError as e:
            raise SigningError(f"credentials/authorize failed: {e}") from e

        return self.parse_csc_auth_response(response_data)


class _MysignCSCSigner(CSCSigner):
    """CSCSigner adapted to MySign's signHash payload.

    Overrides get_signature_mechanism_for_digest to skip CSCSigner's
    supported_mechanisms check — MySign reports the generic rsaEncryption OID
    (1.2.840.113549.1.1.1) instead of sha256WithRSAEncryption.
    """

    def get_signature_mechanism_for_digest(self, digest_algorithm: str):
        # Bypass CSCSigner's OID allowlist check; delegate to base Signer.
        return super(CSCSigner, self).get_signature_mechanism_for_digest(
            digest_algorithm
        )

    async def format_csc_signing_req(
        self, tbs_hashes: list, digest_algorithm: str
    ) -> dict:
        mechanism = self.get_signature_mechanism_for_digest(digest_algorithm)
        auth_info: CSCAuthorizationInfo = await self.auth_manager.authorize_signature(
            tbs_hashes
        )

        payload = {
            "credentialID": self.auth_manager.csc_session_info.credential_id,
            "SAD": auth_info.sad,
            "hash": tbs_hashes,
            "hashAlgo": get_hash_algo_oid(digest_algorithm),
            "signAlgo": mechanism["algorithm"].dotted,
            "async": 0,
        }
        if self.auth_manager.documents:
            payload["documents"] = self.auth_manager.documents
        return payload


def _build_info_panel(
    signer_name: str, dn: str, font_size: int = _STAMP_FONT_SIZE
) -> Image.Image:
    font = ImageFont.truetype(_FONT_PATH, size=font_size)
    now = datetime.datetime.now(tz=pytz.timezone("Asia/Ho_Chi_Minh"))
    date_str = now.strftime("%Y.%m.%d %H:%M:%S +07'00'")
    # dn_text = dn.split(",CN")[0] if ",CN" in dn else dn[:20]
    lines = [
        f"Signed by {signer_name}",
        f"Date: {date_str}",
    ]
    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    line_metrics = [dummy.textbbox((0, 0), ln, font=font) for ln in lines]
    line_w = int(max(box[2] - box[0] for box in line_metrics))
    line_h = max(box[3] - box[1] for box in line_metrics) + _STAMP_LINE_GAP
    panel_w = line_w
    panel_h = line_h * len(lines)
    panel = Image.new("RGB", (panel_w, panel_h), "white")
    draw = ImageDraw.Draw(panel)
    draw.fontmode = "L"
    for i, ln in enumerate(lines):
        text_w = draw.textlength(ln, font=font)
        draw.text(
            ((panel_w - text_w) / 2, i * line_h),
            text=ln,
            font=font,
            fill="#000000",
        )
    return panel


def prepare_sig_field_spec(
    field_name: str,
    coordinate: Optional[dict],
    box_spec: Optional[tuple] = None,
    img_width: int = _SIG_BOX_WIDTH,
    composite_height: int = _SIG_BOX_HEIGHT,
) -> fields.SigFieldSpec:
    """Build a SigFieldSpec from a keyword coordinate, falling back to a default box.

    :param field_name: Name of the PDF signature field.
    :param coordinate: dict(page, x, y) from _find_keyword_coordinate, or None.
    :param width: Width of the signature box. Falls back to module-level default.
    :param height: Height of the signature box. Falls back to module-level default.
    :return: SigFieldSpec positioned at the coordinate, or at the fallback position.
    """

    if coordinate:
        x, y = coordinate["x"], coordinate["y"]

        half_x = box_spec.get("width", _SIG_BOX_WIDTH) / 2
        half_h = composite_height / 2
        min_x = x - half_x if x > half_x else 0
        min_y = y - half_h if y > half_h else 0
        box = (min_x, min_y, min_x + img_width, min_y + composite_height)

        return fields.SigFieldSpec(field_name, on_page=coordinate["page"] - 1, box=box)
    return fields.SigFieldSpec(field_name, box=_SIG_BOX_FALLBACK)


def prepare_stamp_style(
    signer_name: str = "",
    dn: str = "",
    stamp_img: Optional[str] = None,
) -> stamp.TextStampStyle:
    """Return a PyHanko TextStampStyle with the image above and text centered below."""
    info_panel = _build_info_panel(signer_name, dn)

    if stamp_img:
        underlay = Image.open(io.BytesIO(base64.b64decode(stamp_img))).convert("RGB")
    else:
        underlay = Image.open(_CHECKMARK_PATH).convert("RGB")
    underlay = _resize_to_width(underlay, _STAMP_IMAGE_WIDTH)
    gap = _STAMP_GAP
    composite = Image.new(
        "RGB",
        (
            max(underlay.size[0], info_panel.size[0]),
            underlay.size[1] + gap + info_panel.size[1],
        ),
        "white",
    )
    underlay_x = max(0, (composite.size[0] - underlay.size[0]) // 2)
    panel_x = max(0, (composite.size[0] - info_panel.size[0]) // 2)
    composite.paste(underlay, (underlay_x, 0))
    composite.paste(info_panel, (panel_x, underlay.size[1] + gap))

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
        composite.save(tmp_path, format="PNG")
    try:
        return stamp.TextStampStyle(
            stamp_text="",
            background=images.PdfImage(tmp_path),
            background_opacity=1.0,
            border_width=0,
        ), underlay.size[0], composite.size[1]
    finally:
        os.remove(tmp_path)


def prepare_sig_meta(
    field_name: str,
    hash_algo: str,
    signer_name: str,
    reason: str = "I am the author of this document",
) -> PdfSignatureMetadata:
    """Build PdfSignatureMetadata for a MySign signing operation."""
    return PdfSignatureMetadata(
        field_name=field_name,
        md_algorithm=hash_algo,
        name=signer_name,
        reason=reason,
    )


async def sign_pdf_async(
    file_bytes: bytes,
    session_info: CSCServiceSessionInfo,
    credential_info: CSCCredentialInfo,
    stamp_style: stamp.TextStampStyle,
    sig_meta: PdfSignatureMetadata,
    sig_field_spec: fields.SigFieldSpec,
    tsa_url: Optional[str] = None,
    documents: Optional[list] = None,
    description: Optional[str] = None,
) -> bytes:
    async with aiohttp.ClientSession() as http_session:
        auth_manager = MysignAuthorizationManager(
            csc_session_info=session_info,
            credential_info=credential_info,
            session=http_session,
            documents=documents,
            description=description,
        )
        signer = _MysignCSCSigner(
            session=http_session,
            auth_manager=auth_manager,
            batch_size=1,
            batch_autocommit=True,
        )
        if tsa_url:
            signer.timestamper = HTTPTimeStamper(tsa_url)

        writer = IncrementalPdfFileWriter(io.BytesIO(file_bytes), strict=False)
        fields.append_signature_field(writer, sig_field_spec=sig_field_spec)
        output = io.BytesIO()
        await PdfSigner(
            sig_meta, signer=signer, stamp_style=stamp_style
        ).async_sign_pdf(writer, output=output)
        return output.getvalue()


def _resize_to_width(image, target_width):
    """Resize an image to target_width while preserving aspect ratio.

    :param image: PIL Image.
    :param target_width: Desired width in pixels.
    :return: Resized PIL Image.
    """
    orig_w, orig_h = image.size
    new_h = int(target_width * orig_h / orig_w)
    resample = getattr(Image, "Resampling", Image).LANCZOS
    return image.resize((target_width, new_h), resample=resample)
