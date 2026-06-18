"""
语音识别引擎：封装Whisper模型，支持生成带时间戳的转录
"""
import whisper
import torch
import numpy as np
from typing import List, Dict, Any


class ASREngine:
    """Whisper语音识别封装"""

    def __init__(self, model_name="small", device="cuda", language="zh", compute_type="float16"):
        """
        :param model_name: tiny, base, small, medium, large
        :param device: cuda / cpu
        :param language: 语言代码，如zh, en
        :param compute_type: float16 / float32 / int8
        """
        self.model_name = model_name
        self.device = device if torch.cuda.is_available() and device == "cuda" else "cpu"
        self.language = language
        self.compute_type = compute_type

        # 加载模型
        self.model = whisper.load_model(model_name, device=self.device)
        # 如果需要半精度推理
        if compute_type == "float16" and self.device == "cuda":
            self.model = self.model.half()

    def transcribe(self, audio_path: str, word_timestamps: bool = True) -> Dict[str, Any]:
        """
        转录音频，返回带时间戳的结果
        :param audio_path: 音频文件路径
        :param word_timestamps: 是否返回单词级时间戳
        :return: 字典包含 'text', 'segments', 'language'
        """
        options = {
            "language": self.language,
            "task": "transcribe",
            "word_timestamps": word_timestamps,
        }
        result = self.model.transcribe(audio_path, **options)
        return result

    def get_sentences(self, result: Dict) -> List[Dict]:
        """
        提取句子级别的时间戳和文本
        :param result: transcribe返回的结果
        :return: [{"start": float, "end": float, "text": str}, ...]
        """
        sentences = []
        for seg in result["segments"]:
            sentences.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip()
            })
        return sentences

    def get_word_timestamps(self, result: Dict) -> List[Dict]:
        """
        提取单词级时间戳（如果word_timestamps启用）
        """
        words = []
        for seg in result["segments"]:
            for word in seg.get("words", []):
                words.append({
                    "word": word["word"].strip(),
                    "start": word["start"],
                    "end": word["end"],
                    "probability": word.get("probability", 1.0)
                })
        return words