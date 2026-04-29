from __future__ import annotations

import io
import re

from PIL import Image

from .importers import build_manual_trade, infer_market, normalize_symbol

_LINE_PATTERN = re.compile(
    r"(?P<date>20\d{2}[/-]\d{1,2}[/-]\d{1,2}).*?"
    r"(?P<symbol>[A-Z]{1,5}|\d{4,6}).*?"
    r"(?P<action>BUY|SELL|B|S|買進|賣出|現買|現賣).*?"
    r"(?P<shares>\d[\d,]*\.?\d*).*?"
    r"(?P<price>\d[\d,]*\.?\d*)",
    re.IGNORECASE,
)


def _normalize_action(text: str) -> str | None:
    upper = text.strip().upper()
    if upper in {"BUY", "B"} or "買" in text:
        return "BUY"
    if upper in {"SELL", "S"} or "賣" in text:
        return "SELL"
    return None


def ocr_image_to_text(image_bytes: bytes) -> str:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise RuntimeError("尚未安裝 rapidocr-onnxruntime，無法使用照片 OCR。") from exc

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    engine = RapidOCR()
    result, _ = engine(image)
    if not result:
        return ""
    return "\n".join(item[1] for item in result)


def parse_trades_from_ocr_text(text: str) -> list[dict]:
    trades: list[dict] = []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        match = _LINE_PATTERN.search(line)
        if not match:
            continue
        symbol = normalize_symbol(match.group("symbol"))
        action = _normalize_action(match.group("action"))
        if not symbol or not action:
            continue
        market = infer_market(symbol)
        trades.append(
            build_manual_trade(
                trade_date=ImageDate(match.group("date")).to_date(),
                symbol=symbol,
                market=market,
                action=action,
                shares=float(match.group("shares").replace(",", "")),
                price=float(match.group("price").replace(",", "")),
                source="photo_ocr",
                note="OCR 匯入，請再次確認股數與價格。",
            )
        )
    return trades


class ImageDate:
    def __init__(self, raw: str):
        self.raw = raw

    def to_date(self):
        parts = re.split(r"[/-]", self.raw)
        year, month, day = [int(value) for value in parts]
        from datetime import date

        return date(year, month, day)
