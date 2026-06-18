"""
OCR引擎：使用PaddleOCR识别视频帧中的硬字幕
"""
import cv2
import numpy as np
from paddleocr import PaddleOCR
from typing import List, Tuple, Dict


class OCREngine:
    def __init__(self, lang='ch', use_angle_cls=True):
        """
        初始化PaddleOCR
        :param lang: ch 表示中英文混合
        """
        self.ocr = PaddleOCR(use_angle_cls=use_angle_cls, lang=lang, show_log=False)

    def extract_frames(self, video_path, frame_interval=30):
        """
        提取视频关键帧
        :param video_path: 视频路径
        :param frame_interval: 每隔多少帧提取一帧
        :return: list of (frame_number, frame_image)
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = []
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % frame_interval == 0:
                frames.append((frame_count, frame))
            frame_count += 1
        cap.release()
        return frames, fps

    def recognize_frame(self, frame):
        """
        对单帧图像进行OCR识别
        :return: list of [ [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, confidence) ]
        """
        result = self.ocr.ocr(frame, cls=True)
        if result and result[0]:
            return result[0]
        return []

    def extract_subtitles(self, video_path, frame_interval=30, min_confidence=0.7):
        """
        从视频中提取硬字幕，合并为时间区间
        :return: list of [start_time, end_time, text]
        """
        frames, fps = self.extract_frames(video_path, frame_interval)
        subtitle_regions = []   # (frame_num, text, bbox)
        for frame_num, frame in frames:
            ocr_results = self.recognize_frame(frame)
            for line in ocr_results:
                bbox, (text, conf) = line
                if conf >= min_confidence and text.strip():
                    subtitle_regions.append((frame_num, text.strip(), bbox))

        # 合并相邻帧相同的文本
        merged = []
        if not subtitle_regions:
            return merged
        current_text = subtitle_regions[0][1]
        start_frame = subtitle_regions[0][0]
        end_frame = start_frame
        for i in range(1, len(subtitle_regions)):
            frame_num, text, _ = subtitle_regions[i]
            if text == current_text and frame_num - end_frame <= 10:
                end_frame = frame_num
            else:
                start_time = start_frame / fps
                end_time = (end_frame + 30) / fps
                merged.append([start_time, end_time, current_text])
                current_text = text
                start_frame = frame_num
                end_frame = frame_num
        # 最后一段
        start_time = start_frame / fps
        end_time = (end_frame + 30) / fps
        merged.append([start_time, end_time, current_text])
        return merged