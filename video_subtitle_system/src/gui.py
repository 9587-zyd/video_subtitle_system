"""
主界面：PyQt5实现，包含视频播放、字幕编辑、波形显示、批量处理
"""
import sys
import os
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from pathlib import Path
import traceback

# 导入内部模块
from src.audio_processor import AudioProcessor
from src.asr_engine import ASREngine
from src.alignment import CTCForcedAligner
from src.ocr_engine import OCREngine
from src.subtitle_editor import SubtitleEditor
import yaml


# ==================== 工作线程类（批量处理） ====================
class WorkerThread(QThread):
    """批量处理的工作线程，避免界面卡死"""
    progress_updated = pyqtSignal(int, int)   # 当前处理索引, 总数
    status_updated = pyqtSignal(str)          # 状态消息
    video_done = pyqtSignal(int, str)         # 索引, 自动导出的字幕路径（若无则为空）
    error_occurred = pyqtSignal(int, str)     # 索引, 错误信息
    all_done = pyqtSignal()                   # 全部完成

    def __init__(self, video_paths, asr_engine, audio_processor, ocr_engine=None,
                 auto_export=False, export_dir=""):
        super().__init__()
        self.video_paths = video_paths
        self.asr_engine = asr_engine
        self.audio_processor = audio_processor
        self.ocr_engine = ocr_engine
        self.auto_export = auto_export
        self.export_dir = export_dir
        self.subtitles_list = []   # 存储每个视频的字幕

    def run(self):
        total = len(self.video_paths)
        for idx, video_path in enumerate(self.video_paths):
            try:
                self.status_updated.emit(f"正在处理 ({idx+1}/{total}): {os.path.basename(video_path)}")
                # 1. 提取音频
                audio_path = self.audio_processor.extract_audio(video_path)
                # 2. ASR识别
                result = self.asr_engine.transcribe(audio_path, word_timestamps=True)
                sentences = self.asr_engine.get_sentences(result)
                # 3. OCR融合（如果启用）
                if self.ocr_engine:
                    ocr_subs = self.ocr_engine.extract_subtitles(video_path, frame_interval=30)
                    for ocr in ocr_subs:
                        exists = any(s['text'] == ocr[2] for s in sentences)
                        if not exists:
                            sentences.append({"start": ocr[0], "end": ocr[1], "text": ocr[2]})
                    sentences.sort(key=lambda x: x['start'])
                # 存储字幕
                self.subtitles_list.append(sentences)
                # 自动导出
                out_path = ""
                if self.auto_export and self.export_dir:
                    base_name = os.path.splitext(os.path.basename(video_path))[0]
                    out_path = os.path.join(self.export_dir, f"{base_name}.srt")
                    SubtitleEditor.to_srt(sentences, out_path)
                self.video_done.emit(idx, out_path)
                self.progress_updated.emit(idx+1, total)
            except Exception as e:
                error_msg = f"处理失败: {str(e)}\n{traceback.format_exc()}"
                self.error_occurred.emit(idx, error_msg)
        self.all_done.emit()


# ==================== 主窗口类 ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频字幕自动生成与对齐系统")
        self.resize(1200, 800)

        # 加载配置
        with open("config.yaml", 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # 初始化模块
        self.audio_processor = AudioProcessor()
        self.asr_engine = ASREngine(
            model_name=self.config['asr']['model_name'],
            device=self.config['asr']['device'],
            language=self.config['asr']['language']
        )
        self.ocr_engine = OCREngine(lang=self.config['ocr']['lang']) if self.config['ocr']['enable'] else None
        self.current_subtitles = []   # 存储当前字幕列表

        # 批量处理相关变量
        self.batch_video_paths = []
        self.worker_thread = None

        self.init_ui()
        self.video_path = None

    def init_ui(self):
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 工具栏
        toolbar = QHBoxLayout()
        self.btn_open = QPushButton("打开视频")
        self.btn_open.clicked.connect(self.open_video)
        self.btn_process = QPushButton("自动生成字幕")
        self.btn_process.clicked.connect(self.process_video)
        self.btn_export = QPushButton("导出字幕")
        self.btn_export.clicked.connect(self.export_subtitle)

        # 批量处理按钮
        self.btn_batch_add = QPushButton("批量添加视频")
        self.btn_batch_add.clicked.connect(self.batch_add_videos)
        self.btn_batch_start = QPushButton("开始批量处理")
        self.btn_batch_start.clicked.connect(self.start_batch_process)
        self.btn_batch_export = QPushButton("批量导出字幕")
        self.btn_batch_export.clicked.connect(self.batch_export_subtitles)

        toolbar.addWidget(self.btn_open)
        toolbar.addWidget(self.btn_process)
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_batch_add)
        toolbar.addWidget(self.btn_batch_start)
        toolbar.addWidget(self.btn_batch_export)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 视频播放与字幕区域（水平分割）
        splitter = QSplitter(Qt.Horizontal)
        # 左侧：视频播放器
        self.video_widget = QLabel("视频预览区域")
        self.video_widget.setAlignment(Qt.AlignCenter)
        self.video_widget.setStyleSheet("background: black; color: white;")
        self.video_widget.setMinimumSize(500, 400)
        splitter.addWidget(self.video_widget)

        # 右侧：字幕表格
        self.subtitle_table = QTableWidget()
        self.subtitle_table.setColumnCount(3)
        self.subtitle_table.setHorizontalHeaderLabels(["开始时间", "结束时间", "字幕文本"])
        self.subtitle_table.horizontalHeader().setStretchLastSection(True)
        # 允许编辑
        self.subtitle_table.setEditTriggers(QTableWidget.AllEditTriggers)
        splitter.addWidget(self.subtitle_table)
        splitter.setSizes([600, 400])
        layout.addWidget(splitter)

        # 音频波形与时间轴
        self.wave_plot = pg.PlotWidget()
        self.wave_plot.setLabel('left', '振幅')
        self.wave_plot.setLabel('bottom', '时间 (秒)')
        layout.addWidget(self.wave_plot)

        # 进度条和状态标签（初始隐藏）
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.batch_status_label = QLabel("")
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.batch_status_label)

        # 状态栏
        self.statusBar().showMessage("就绪")

        # 连接表格编辑信号，同步更新字幕列表
        self.subtitle_table.itemChanged.connect(self.on_subtitle_item_changed)

    # ==================== 单个视频处理 ====================
    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "",
                                                   "Video Files (*.mp4 *.avi *.mov *.mkv)")
        if file_path:
            self.video_path = file_path
            # 显示视频第一帧
            import cv2
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg).scaled(self.video_widget.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.video_widget.setPixmap(pixmap)
            cap.release()
            self.statusBar().showMessage(f"已加载: {os.path.basename(file_path)}")

    def process_video(self):
        if not self.video_path:
            QMessageBox.warning(self, "警告", "请先打开视频文件")
            return
        self.statusBar().showMessage("处理中...")
        QApplication.processEvents()

        try:
            # 1. 提取音频
            audio_path = self.audio_processor.extract_audio(self.video_path)
            # 2. ASR识别
            asr_result = self.asr_engine.transcribe(audio_path, word_timestamps=True)
            sentences = self.asr_engine.get_sentences(asr_result)
            # 3. 如果启用OCR，融合硬字幕
            if self.config['ocr']['enable'] and self.ocr_engine:
                ocr_subs = self.ocr_engine.extract_subtitles(self.video_path, frame_interval=30)
                for ocr in ocr_subs:
                    exists = any(s['text'] == ocr[2] for s in sentences)
                    if not exists:
                        sentences.append({"start": ocr[0], "end": ocr[1], "text": ocr[2]})
                sentences.sort(key=lambda x: x['start'])
            self.current_subtitles = sentences
            # 更新表格
            self.update_subtitle_table()
            # 绘制波形
            y, sr = self.audio_processor.load_audio(audio_path)
            self.wave_plot.clear()
            time_axis = np.linspace(0, len(y)/sr, len(y))
            self.wave_plot.plot(time_axis, y, pen=pg.mkPen('b'))
            self.statusBar().showMessage("处理完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理失败: {str(e)}")
            self.statusBar().showMessage("处理失败")

    def update_subtitle_table(self):
        self.subtitle_table.setRowCount(len(self.current_subtitles))
        for i, sub in enumerate(self.current_subtitles):
            start_item = QTableWidgetItem(f"{sub['start']:.2f}")
            end_item = QTableWidgetItem(f"{sub['end']:.2f}")
            text_item = QTableWidgetItem(sub['text'])
            self.subtitle_table.setItem(i, 0, start_item)
            self.subtitle_table.setItem(i, 1, end_item)
            self.subtitle_table.setItem(i, 2, text_item)
        self.subtitle_table.resizeColumnsToContents()

    def on_subtitle_item_changed(self, item):
        """表格编辑时同步更新 self.current_subtitles"""
        row = item.row()
        col = item.column()
        if row < len(self.current_subtitles):
            try:
                if col == 0:  # 开始时间
                    self.current_subtitles[row]['start'] = float(item.text())
                elif col == 1:  # 结束时间
                    self.current_subtitles[row]['end'] = float(item.text())
                elif col == 2:  # 文本
                    self.current_subtitles[row]['text'] = item.text()
            except ValueError:
                # 时间格式错误时恢复原值
                if col == 0:
                    item.setText(f"{self.current_subtitles[row]['start']:.2f}")
                elif col == 1:
                    item.setText(f"{self.current_subtitles[row]['end']:.2f}")

    def export_subtitle(self):
        if not self.current_subtitles:
            QMessageBox.warning(self, "警告", "没有可导出的字幕")
            return
        file_path, selected_filter = QFileDialog.getSaveFileName(self, "保存字幕", "./output/",
                                                                  "SRT文件 (*.srt);;ASS文件 (*.ass);;WebVTT (*.vtt)")
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.srt':
                SubtitleEditor.to_srt(self.current_subtitles, file_path)
            elif ext == '.ass':
                SubtitleEditor.to_ass(self.current_subtitles, file_path)
            elif ext == '.vtt':
                SubtitleEditor.to_vtt(self.current_subtitles, file_path)
            else:
                SubtitleEditor.to_srt(self.current_subtitles, file_path + '.srt')
            QMessageBox.information(self, "成功", f"字幕已保存至 {file_path}")

    # ==================== 批量处理相关方法 ====================
    def batch_add_videos(self):
        """选择多个视频文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择多个视频文件", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.flv *.wmv)"
        )
        if file_paths:
            self.batch_video_paths = file_paths
            self.batch_status_label.setText(f"已添加 {len(file_paths)} 个视频")
            QMessageBox.information(self, "批量添加", f"成功添加 {len(file_paths)} 个视频")

    def start_batch_process(self):
        """开始批量处理"""
        if not self.batch_video_paths:
            QMessageBox.warning(self, "警告", "请先添加视频文件")
            return

        # 询问是否自动导出
        reply = QMessageBox.question(
            self, "批量处理",
            "是否在处理完成后自动导出字幕？（若选否，可稍后手动批量导出）",
            QMessageBox.Yes | QMessageBox.No
        )
        auto_export = (reply == QMessageBox.Yes)

        export_dir = ""
        if auto_export:
            export_dir = QFileDialog.getExistingDirectory(self, "选择字幕导出目录")
            if not export_dir:
                return

        # 禁用按钮，防止重复点击
        self.btn_batch_start.setEnabled(False)
        self.btn_batch_add.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 创建工作线程
        self.worker_thread = WorkerThread(
            self.batch_video_paths,
            self.asr_engine,
            self.audio_processor,
            self.ocr_engine if self.config['ocr']['enable'] else None,
            auto_export,
            export_dir
        )

        # 连接信号
        self.worker_thread.progress_updated.connect(self.update_batch_progress)
        self.worker_thread.status_updated.connect(self.update_batch_status)
        self.worker_thread.video_done.connect(self.on_video_done)
        self.worker_thread.error_occurred.connect(self.on_batch_error)
        self.worker_thread.all_done.connect(self.on_batch_finished)

        self.worker_thread.start()

    def update_batch_progress(self, current, total):
        """更新进度条"""
        percent = int(current / total * 100)
        self.progress_bar.setValue(percent)
        self.batch_status_label.setText(f"处理进度: {current}/{total} ({percent}%)")

    def update_batch_status(self, message):
        """更新状态标签"""
        self.batch_status_label.setText(message)
        print(message)

    def on_video_done(self, idx, subtitle_path):
        """单个视频处理完成"""
        if subtitle_path:
            print(f"视频 {idx+1} 字幕已保存: {subtitle_path}")

    def on_batch_error(self, idx, error_msg):
        """处理出错"""
        QMessageBox.critical(self, "批量处理错误", f"视频 {idx+1} 出错:\n{error_msg}")

    def on_batch_finished(self):
        """批量处理完成"""
        self.progress_bar.setVisible(False)
        self.btn_batch_start.setEnabled(True)
        self.btn_batch_add.setEnabled(True)
        self.batch_status_label.setText("批量处理完成！")
        QMessageBox.information(self, "批量处理", "所有视频处理完毕！\n可使用'批量导出字幕'导出已识别的字幕。")

    def batch_export_subtitles(self):
        """批量导出所有已处理视频的字幕"""
        if not self.worker_thread or not self.worker_thread.subtitles_list:
            QMessageBox.warning(self, "警告", "没有已处理的字幕数据，请先运行批量处理")
            return

        export_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not export_dir:
            return

        success_count = 0
        for idx, subtitles in enumerate(self.worker_thread.subtitles_list):
            if subtitles:
                video_path = self.batch_video_paths[idx]
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                out_path = os.path.join(export_dir, f"{base_name}.srt")
                SubtitleEditor.to_srt(subtitles, out_path)
                success_count += 1

        QMessageBox.information(self, "批量导出", f"成功导出 {success_count} 个字幕文件到\n{export_dir}")