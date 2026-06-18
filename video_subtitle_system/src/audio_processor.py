"""
音频处理模块：提取视频中的音频，进行格式转换与预处理
"""
import os
import subprocess
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path


class AudioProcessor:
    """音频处理器，支持从视频提取音频、重采样、归一化等"""

    def __init__(self, target_sr=16000):
        self.target_sr = target_sr

    def extract_audio(self, video_path, output_wav=None):
        """
        使用FFmpeg从视频中提取音频并转换为WAV格式
        :param video_path: 输入视频路径
        :param output_wav: 输出WAV路径，默认放在temp目录
        :return: 音频文件路径
        """
        if output_wav is None:
            video_name = Path(video_path).stem
            output_wav = f"./temp/{video_name}_audio.wav"
        os.makedirs("./temp", exist_ok=True)

        # FFmpeg命令：提取音频，单声道，16kHz，16bit
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-ac", "1", "-ar", str(self.target_sr),
            "-acodec", "pcm_s16le", output_wav
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_wav

    def normalize_audio(self, wav_path, output_path=None):
        """
        音频幅度归一化（峰值至-1dBFS）
        """
        y, sr = librosa.load(wav_path, sr=None)
        max_val = np.max(np.abs(y))
        if max_val > 0:
            y = y / max_val * 0.9   # -1dBFS
        if output_path is None:
            output_path = wav_path.replace(".wav", "_norm.wav")
        sf.write(output_path, y, sr)
        return output_path

    def load_audio(self, wav_path):
        """加载音频为numpy数组，采样率target_sr"""
        y, sr = librosa.load(wav_path, sr=self.target_sr)
        return y, sr