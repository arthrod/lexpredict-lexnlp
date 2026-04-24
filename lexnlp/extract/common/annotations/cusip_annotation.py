__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from typing import Any

from lexnlp.extract.common.annotations.text_annotation import TextAnnotation
from lexnlp.utils.map import Map


class CusipAnnotation(TextAnnotation):
    """
    create an object of CusipAnnotation like
    cp = CusipAnnotation(coords=(0, 100))
    """

    record_type = "cusip"

    def __init__(
        self,
        coords: tuple[int, int],
        locale: str = "en",
        name: str = "",
        text: str | None = None,
        code: str | None = None,
        internal: bool | None = None,
        # ``lexnlp.extract.en.cusip`` passes a ``bool`` into ``ppn`` (flag
        # indicating the CUSIP matches the private-placement pattern) and an
        # ``int`` into ``checksum`` (the validated check digit). Keep ``str``
        # support so external callers constructing the annotation manually
        # still work.
        ppn: str | bool | None = None,
        tba: dict | None = None,
        checksum: str | int | None = None,
        issue_id: str | None = None,
        issuer_id: str | None = None,
    ):
        """
        Initialize a CusipAnnotation with positional bounds, locale, display name, text, and CUSIP-specific metadata.

        Parameters:
            coords (tuple[int, int]): Start and end character positions of the annotation in the source text.
            locale (str): Language/locale identifier (default 'en').
            name (str): Human-readable annotation name or label.
            text (str | None): Extracted substring for the annotation, if available.
            code (str | None): Extracted CUSIP code value.
            internal (bool | None): True if the code is an internal identifier; False or None otherwise.
            ppn (str | bool | None): Either a string PPN identifier or the
                private-placement-number boolean flag set by the EN extractor.
            tba (dict | None): Data for "To Be Announced" instruments, when applicable.
            checksum (str | int | None): Checksum character(s) for the CUSIP. The
                EN extractor supplies an ``int`` digit; external callers may
                supply a string.
            issue_id (str | None): Identifier for the specific issue.
            issuer_id (str | None): Identifier for the issuer.
        """
        super().__init__(name=name, locale=locale, coords=coords, text=text)

        self.code = code
        self.internal = internal
        self.ppn = ppn
        self.tba = tba
        self.checksum = checksum
        self.issue_id = issue_id
        self.issuer_id = issuer_id

    def get_cite_value_parts(self) -> list[str]:
        # ``self.ppn`` is a boolean flag in practice; coerce to "" for the cite
        # rendering so non-string values never leak into the citation path.
        ppn_str = self.ppn if isinstance(self.ppn, str) else ""
        parts = [
            self.code or "",
            ppn_str,
            # self.tba or '',
            self.issue_id or "",
            self.issuer_id or "",
        ]
        return parts

    def get_dictionary_values(self) -> dict:
        df = Map({"tags": {"Extracted Entity Code": self.code, "Extracted Entity Internal": self.internal}})
        if self.tba:
            df.tags["Extracted Entity TBA"] = self.tba
        if self.ppn:
            df.tags["Extracted Entity PPN"] = self.ppn
        if self.checksum:
            df.tags["Extracted Entity Checksum"] = self.checksum
        if self.issuer_id:
            df.tags["Extracted Entity Issuer ID"] = self.issuer_id
        if self.issue_id:
            df.tags["Extracted Entity Issue ID"] = self.issue_id

        return df

    def to_dictionary_legacy(self) -> dict[str, Any]:
        return {
            "location_start": self.coords[0],
            "location_end": self.coords[1],
            "text": self.code,
            "issuer_id": self.issuer_id,
            "issue_id": self.issue_id,
            "checksum": self.checksum,
            "internal": self.internal,
            "tba": self.tba,
            "ppn": self.ppn,
        }
