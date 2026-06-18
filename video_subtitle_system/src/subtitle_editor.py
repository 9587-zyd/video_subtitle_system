"""
字幕编辑与导出模块：支持SRT/ASS/VTT格式
"""
import os
from typing import List, Dict


class SubtitleEditor:
    @staticmethod
    def format_time(seconds: float) -> str:
        """将秒数转换为SRT时间格式 HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def to_srt(subtitles: List[Dict], filepath: str):
        """
        导出SRT格式
        subtitles: [{"start": float, "end": float, "text": str}, ...]
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            for idx, sub in enumerate(subtitles, 1):
                start = SubtitleEditor.format_time(sub['start'])
                end = SubtitleEditor.format_time(sub['end'])
                f.write(f"{idx}\n{start} --> {end}\n{sub['text']}\n\n")

    @staticmethod
    def to_ass(subtitles: List[Dict], filepath: str):
        """ASS格式导出（基础版）"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("[Script Info]\nTitle: Generated Subtitle\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,SimHei,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            for sub in subtitles:
                start = sub['start']
                end = sub['end']
                start_str = f"{int(start//3600):01d}:{int((start%3600)//60):02d}:{start%60:.2f}"
                end_str = f"{int(end//3600):01d}:{int((end%3600)//60):02d}:{end%60:.2f}"
                f.write(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{sub['text']}\n")

    @staticmethod
    def to_vtt(subtitles: List[Dict], filepath: str):
        """WebVTT格式"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            for idx, sub in enumerate(subtitles, 1):
                start = sub['start'].replace(',', '.')
                end = sub['end'].replace(',', '.')
                f.write(f"{idx}\n{start} --> {end}\n{sub['text']}\n\n")