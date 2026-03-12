"""
AR开关识别 MVP Demo — 云端服务
摄像头拍照 → OCR识别铭牌文字 → 匹配设备型号 → 返回设备信息+操作规程
"""
import base64
import json
import os
import re
from io import BytesIO
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image

app = FastAPI(title="AR开关识别Demo")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── 数据目录 ──
BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

# ── 加载设备知识库 ──
with open(DATA / "equipment.json", "r", encoding="utf-8") as f:
    EQUIPMENT_DB = json.load(f)

# 所有已知型号关键词（用于OCR文本匹配）
MODEL_KEYWORDS = {}
for key, info in EQUIPMENT_DB.items():
    # 主键本身
    MODEL_KEYWORDS[key.upper()] = key
    # aliases
    for alias in info.get("aliases", []):
        MODEL_KEYWORDS[alias.upper()] = key


# ── OCR引擎（延迟加载）──
_ocr_engine = None

def get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang="ch")
    return _ocr_engine


def recognize_text(img_array: np.ndarray) -> list[str]:
    """OCR识别图片中的所有文字"""
    ocr = get_ocr()
    result = ocr.ocr(img_array, cls=True)
    texts = []
    if result and result[0]:
        for line in result[0]:
            texts.append(line[1][0])
    return texts


def match_equipment(texts: list[str]) -> tuple[str | None, list[str]]:
    """从OCR文字中匹配设备型号"""
    combined = " ".join(texts).upper()

    # 方法1：直接匹配已知型号关键词
    for keyword, equip_key in sorted(MODEL_KEYWORDS.items(), key=lambda x: -len(x[0])):
        if keyword in combined:
            return equip_key, texts

    # 方法2：正则匹配常见型号模式
    patterns = [
        r'(ZN\d{2})',
        r'(VS\d)',
        r'(LW\d{2}[\-]?\d*)',
        r'(GW\d)',
        r'(KYN\d{2})',
        r'(XGN\d{2})',
        r'(FZN\d{2})',
        r'(HXGN[\-]?\d{2})',
        r'(ZW\d{2})',
    ]
    for pat in patterns:
        m = re.search(pat, combined)
        if m:
            found = m.group(1).upper()
            for keyword, equip_key in MODEL_KEYWORDS.items():
                if found in keyword or keyword in found:
                    return equip_key, texts

    return None, texts


# ── API ──

class RecognizeRequest(BaseModel):
    image: str  # base64编码的图片


class RecognizeResponse(BaseModel):
    success: bool
    model_key: str | None = None
    ocr_texts: list[str] = []
    equipment: dict | None = None


@app.post("/api/recognize", response_model=RecognizeResponse)
def recognize(req: RecognizeRequest):
    """核心接口：接收图片，OCR识别 → 匹配设备 → 返回信息"""
    try:
        # 解码图片
        img_data = req.image.split(",")[-1]  # 去掉 data:image/xxx;base64, 前缀
        img_bytes = base64.b64decode(img_data)
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        img_array = np.array(img)

        # OCR
        texts = recognize_text(img_array)

        # 匹配
        model_key, _ = match_equipment(texts)

        if model_key:
            return RecognizeResponse(
                success=True,
                model_key=model_key,
                ocr_texts=texts,
                equipment=EQUIPMENT_DB[model_key],
            )
        else:
            return RecognizeResponse(success=False, ocr_texts=texts)

    except Exception as e:
        return RecognizeResponse(success=False, ocr_texts=[f"Error: {str(e)}"])


@app.get("/api/equipment")
def list_equipment():
    """返回所有设备型号列表"""
    return [{"key": k, "name": v["full_name"], "category": v["category"]}
            for k, v in EQUIPMENT_DB.items()]


@app.get("/api/equipment/{model_key}")
def get_equipment(model_key: str):
    """查询单个设备详情"""
    if model_key in EQUIPMENT_DB:
        return EQUIPMENT_DB[model_key]
    return {"error": "未找到该型号"}


# ── 静态文件 ──
web_dir = BASE / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

    @app.get("/")
    def index():
        return FileResponse(str(web_dir / "index.html"))


if __name__ == "__main__":
    import uvicorn
    cert_dir = Path(__file__).parent
    cert = cert_dir / "cert.pem"
    key = cert_dir / "key.pem"
    ssl_args = {"ssl_certfile": str(cert), "ssl_keyfile": str(key)} if cert.exists() else {}
    uvicorn.run(app, host="0.0.0.0", port=8081, **ssl_args)
