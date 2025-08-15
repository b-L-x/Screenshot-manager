#!/usr/bin/env python3
"""
Screenshot Manager Application
A powerful tool for taking website screenshots and managing them with a beautiful GUI.
"""

import os
import sys
import threading
import re
import json
import zipfile
import logging
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar, QGroupBox,
    QStatusBar, QListWidget, QListWidgetItem, QLineEdit, QSplitter,
    QMessageBox, QInputDialog, QScrollArea, QToolBar, QTextEdit,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QTextBrowser, QFrame
)
from PyQt6.QtGui import QPixmap, QFont, QIcon, QAction, QKeySequence, QShortcut, QPainter, QDesktopServices, QColor
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, QUrl, QSettings, QPropertyAnimation, QEasingCurve
from playwright.sync_api import sync_playwright

logging.basicConfig(filename='app.log', level=logging.DEBUG)

class AnimatedButton(QPushButton):
    """Custom button with hover animations"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton { 
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #666666, stop: 1 #4d4d4d);
                color: white; 
                border: 1px solid #555;
                padding: 4px 6px; 
                border-radius: 6px; 
                font-size: 11px;
                font-weight: 500;
                min-height: 24px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover { 
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #7a7a7a, stop: 1 #666666);
                border: 1px solid #777;
            }
            QPushButton:pressed { 
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4d4d4d, stop: 1 #333333);
                border: 1px solid #444;
                padding: 5px 6px 3px 6px;
            }
            QPushButton:disabled { 
                background-color: #444; 
                color: #777; 
                border: 1px solid #333;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def enterEvent(self, event):
        self.animate_hover(True)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.animate_hover(False)
        super().leaveEvent(event)
        
    def animate_hover(self, entering):
        # Subtle hover animation
        if hasattr(self, '_animation'):
            self._animation.stop()
            
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        if entering:
            current = self.geometry()
            new = current.adjusted(-1, -1, 1, 1)
            self._animation.setStartValue(current)
            self._animation.setEndValue(new)
        else:
            current = self.geometry()
            original = current.adjusted(1, 1, -1, -1)
            self._animation.setStartValue(current)
            self._animation.setEndValue(original)
            
        self._animation.start()


class ImageViewer(QGraphicsView):
    """Custom image viewer with smooth zoom and pan"""
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QColor(17, 17, 17))  # #111
        self.pixmap_item = None
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
    def set_image(self, pixmap):
        """Set and display an image"""
        self.scene.clear()
        if pixmap and not pixmap.isNull():
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.pixmap_item)
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.pixmap_item = None

    def wheelEvent(self, event):
        """Handle zoom with mouse wheel"""
        if event.angleDelta().y() > 0:
            self.scale(1.1, 1.1)
        else:
            self.scale(0.9, 0.9)

    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        if self.pixmap_item:
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)


class ThumbnailItem(QListWidgetItem):
    """Custom thumbnail item for the list"""
    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.setText(self.filename)
        
        # Create thumbnail
        pixmap = QPixmap(filepath)
        if not pixmap.isNull():
            thumbnail = pixmap.scaled(65, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.setIcon(QIcon(thumbnail))
        
        # Selection style
        self.setBackground(QColor(60, 60, 60, 100))
        
    def setSelected(self, selected):
        super().setSelected(selected)
        if selected:
            self.setBackground(QColor(74, 144, 226, 200))  # #4a90e2 with transparency
        else:
            self.setBackground(QColor(60, 60, 60, 100))


class AnimatedProgressBar(QProgressBar):
    """Custom progress bar with animations"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setStyleSheet("""
            QProgressBar {
                height: 14px;
                border-radius: 7px;
                background-color: #333;
                border: 1px solid #444;
                text-align: center;
                font-size: 9px;
                color: #fff;
                font-weight: 500;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, 
                    stop: 0 #4a90e2, 
                    stop: 0.5 #5cb85c,
                    stop: 1 #5cb85c);
                border-radius: 7px;
            }
        """)
        
    def setValue(self, value):
        super().setValue(value)
        # Subtle bar animation
        if value > 0:
            self.setStyleSheet(f"""
                QProgressBar {{
                    height: 14px;
                    border-radius: 7px;
                    background-color: #333;
                    border: 1px solid #444;
                    text-align: center;
                    font-size: 9px;
                    color: #fff;
                    font-weight: 500;
                }}
                QProgressBar::chunk {{
                    background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, 
                        stop: 0 #4a90e2, 
                        stop: {min(value/100 + 0.1, 1.0)} #5cb85c,
                        stop: 1 #5cb85c);
                    border-radius: 7px;
                }}
            """)


class ScreenshotViewer(QMainWindow):
    """Main application window"""
    scan_completed = pyqtSignal()
    scan_progress = pyqtSignal(int, str)
    scan_new_image = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📸 Screenshot Manager")
        self.resize(1600, 1000)
        self.setObjectName("ScreenshotManager")
        
        # Settings
        self.settings = QSettings("ScreenshotManager", "GUI")
        self.load_settings()
        
        # Scan variables
        self.scan_active = False
        self.scan_future = None
        self.executor = None
        
        # Enhanced style with shadows and gradients
        self.setStyleSheet("""
            QMainWindow { 
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #151515, stop: 1 #252525);
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton { 
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #666666, stop: 1 #4d4d4d);
                color: white; 
                border: 1px solid #555;
                padding: 4px 6px; 
                border-radius: 6px; 
                font-size: 11px;
                font-weight: 500;
                min-height: 24px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover { 
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #7a7a7a, stop: 1 #666666);
                border: 1px solid #777;
            }
            QPushButton:pressed { 
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4d4d4d, stop: 1 #333333);
                border: 1px solid #444;
            }
            QPushButton:disabled { 
                background-color: #444; 
                color: #777; 
                border: 1px solid #333;
            }
            QLabel { 
                color: #e0e0e0; 
                font-size: 12px; 
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #555, stop: 1 #333);
                border-radius: 10px; 
                margin-top: 15px; 
                padding: 15px; 
                color: #aaaaaa;
                background-color: rgba(40, 40, 40, 180);
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox::title { 
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px; 
                background-color: rgba(60, 60, 60, 220);
                border-radius: 5px;
                font-weight: 600;
            }
            QProgressBar {
                height: 14px;
                border-radius: 7px;
                background-color: #333;
                border: 1px solid #444;
                text-align: center;
                font-size: 9px;
                color: #fff;
                font-weight: 500;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, 
                    stop: 0 #4a90e2, 
                    stop: 0.5 #5cb85c,
                    stop: 1 #5cb85c);
                border-radius: 7px;
            }
            QStatusBar {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #1e1e1e, stop: 1 #151515);
                color: #cccccc; 
                font-size: 11px;
                border-top: 1px solid #444;
                padding: 3px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QListWidget {
                background-color: rgba(45, 45, 45, 200);
                border: 2px solid qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #555, stop: 1 #333);
                border-radius: 8px;
                color: #e0e0e0;
                alternate-background-color: rgba(55, 55, 55, 150);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4a90e2, stop: 1 #357abd);
                color: white;
                border: 1px solid #2a75b3;
            }
            QListWidget::item:hover {
                background-color: rgba(80, 80, 80, 180);
                border: 1px solid #666;
            }
            QLineEdit {
                background-color: rgba(60, 60, 60, 220);
                border: 2px solid qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #555, stop: 1 #333);
                border-radius: 6px;
                padding: 8px;
                color: #e0e0e0;
                selection-background-color: #4a90e2;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #4a90e2;
            }
            QToolBar {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #252525, stop: 1 #1a1a1a);
                border: none;
                spacing: 6px;
                padding: 6px;
                border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #444, stop: 1 #222);
            }
            QToolBar QToolButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #555, stop: 1 #444);
                border: 1px solid #666;
                border-radius: 6px;
                padding: 7px 12px;
                margin: 3px;
                font-size: 11px;
                color: #eee;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QToolBar QToolButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #666, stop: 1 #555);
                border: 1px solid #777;
            }
            QTextBrowser {
                background-color: rgba(45, 45, 45, 200);
                border: 2px solid qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #555, stop: 1 #333);
                border-radius: 6px;
                color: #66ccff;
                font-size: 12px;
                padding: 10px;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTextBrowser a {
                color: #66ccff;
                text-decoration: underline;
            }
            QTextBrowser a:hover {
                color: #99ddff;
                text-decoration: none;
            }
            QSplitter::handle {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #444, stop: 1 #222);
                width: 3px;
                border-radius: 1px;
            }
            QSplitter::handle:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #666, stop: 1 #444);
            }
        """)

        self.output_dir = self.settings.value("output_dir", "screenshots")
        self.history_file = "scan_history.json"
        self.url_mapping_file = "url_mapping.json"
        self.images = []
        self.url_mapping = {}
        self.current_index = 0
        self.load_url_mapping()
        self.setup_ui()
        self.create_shortcuts()
        self.connect_signals()
        self.scan_completed.connect(self.on_scan_completed)
        self.scan_progress.connect(self.update_progress)
        self.scan_new_image.connect(self.add_new_image_to_list)

    def setup_ui(self):
        """Setup the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Toolbar
        self.create_toolbar()

        # Main content area (splitter)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)
        main_layout.addWidget(splitter)

        # Left panel (thumbnails and controls)
        left_panel = QWidget()
        left_panel.setObjectName("LeftPanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search by domain...")
        self.search_input.textChanged.connect(self.filter_thumbnails)
        search_layout.addWidget(self.search_input)
        
        self.clear_search_btn = AnimatedButton("❌")
        self.clear_search_btn.setFixedWidth(30)
        self.clear_search_btn.clicked.connect(lambda: self.search_input.clear())
        search_layout.addWidget(self.clear_search_btn)
        left_layout.addLayout(search_layout)

        # Thumbnails list
        self.thumbnails_list = QListWidget()
        self.thumbnails_list.setIconSize(QSize(70, 55))
        self.thumbnails_list.setSpacing(5)
        self.thumbnails_list.itemClicked.connect(self.thumbnail_clicked)
        self.thumbnails_list.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.thumbnails_list.setAlternatingRowColors(True)
        left_layout.addWidget(self.thumbnails_list)

        # Controls
        controls_group = QGroupBox("🎮 Controls")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(6)
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(5)
        self.zoom_in_btn = AnimatedButton("➕ Zoom In")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = AnimatedButton("➖ Zoom Out")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(self.zoom_out_btn)
        
        self.reset_zoom_btn = AnimatedButton("⭕ Reset View")
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        zoom_layout.addWidget(self.reset_zoom_btn)
        controls_layout.addLayout(zoom_layout)
        
        # Navigation controls
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(5)
        self.prev_btn = AnimatedButton("⬅️ Previous")
        self.prev_btn.clicked.connect(self.prev_image)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = AnimatedButton("Next ➡️")
        self.next_btn.clicked.connect(self.next_image)
        nav_layout.addWidget(self.next_btn)
        controls_layout.addLayout(nav_layout)
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(5)
        self.delete_btn = AnimatedButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_current_image)
        actions_layout.addWidget(self.delete_btn)
        
        self.export_btn = AnimatedButton("📤 Export")
        self.export_btn.clicked.connect(self.export_all)
        actions_layout.addWidget(self.export_btn)
        controls_layout.addLayout(actions_layout)
        
        controls_group.setLayout(controls_layout)
        left_layout.addWidget(controls_group)

        # Progress info
        self.progress_label = QLabel("🚀 Ready to scan websites")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("""
            color: #bbb; 
            font-style: italic; 
            font-size: 12px;
            padding: 6px;
            background-color: rgba(40, 40, 40, 180);
            border-radius: 6px;
            border: 1px solid #444;
            font-weight: 500;
        """)
        left_layout.addWidget(self.progress_label)

        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setValue(0)
        left_layout.addWidget(self.progress_bar)

        splitter.addWidget(left_panel)

        # Right panel (image viewer)
        right_panel = QWidget()
        right_panel.setObjectName("RightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # URL link
        self.url_link = QTextBrowser()
        self.url_link.setMaximumHeight(45)
        self.url_link.setOpenExternalLinks(True)
        right_layout.addWidget(self.url_link)

        # Image viewer
        self.image_viewer = ImageViewer()
        self.image_viewer.setMinimumHeight(500)
        self.image_viewer.setStyleSheet("""
            QGraphicsView {
                background-color: #111;
                border: 2px solid qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #555, stop: 1 #333);
                border-radius: 10px;
            }
        """)
        right_layout.addWidget(self.image_viewer)

        # Image info
        self.image_info = QLabel("📭 No image selected")
        self.image_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_info.setStyleSheet("""
            color: #aaa; 
            font-size: 12px; 
            padding: 8px;
            background-color: rgba(40, 40, 40, 180);
            border-radius: 6px;
            border: 1px solid #444;
            font-weight: 500;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        right_layout.addWidget(self.image_info)

        splitter.addWidget(right_panel)

        # Set splitter sizes for 20%/80% ratio
        splitter.setSizes([350, 1250])

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("✨ Application ready")
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #1e1e1e, stop: 1 #151515);
                color: #cccccc;
                font-size: 11px;
                border-top: 2px solid qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #444, stop: 1 #222);
                padding: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)

        # Load existing captures
        self.load_captures()

    def create_toolbar(self):
        """Create the toolbar"""
        toolbar = QToolBar("MainToolbar")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # Toolbar actions
        self.select_file_action = QAction("📁 Select URLs File", self)
        self.select_file_action.setObjectName("SelectFileAction")
        self.select_file_action.triggered.connect(self.select_input_file)
        toolbar.addAction(self.select_file_action)

        self.select_output_action = QAction("📂 Output Folder", self)
        self.select_output_action.setObjectName("SelectOutputAction")
        self.select_output_action.triggered.connect(self.select_output_dir)
        toolbar.addAction(self.select_output_action)

        toolbar.addSeparator()

        self.start_scan_action = QAction("▶️ Start Scan", self)
        self.start_scan_action.setObjectName("StartScanAction")
        self.start_scan_action.triggered.connect(self.start_scan)
        toolbar.addAction(self.start_scan_action)

        self.stop_scan_action = QAction("⏹️ Stop Scan", self)
        self.stop_scan_action.setObjectName("StopScanAction")
        self.stop_scan_action.triggered.connect(self.stop_scan)
        self.stop_scan_action.setEnabled(False)
        toolbar.addAction(self.stop_scan_action)

        self.refresh_action = QAction("🔄 Refresh", self)
        self.refresh_action.setObjectName("RefreshAction")
        self.refresh_action.triggered.connect(self.load_captures)
        toolbar.addAction(self.refresh_action)

        toolbar.addSeparator()

        self.fullscreen_action = QAction("⛶ Fullscreen", self)
        self.fullscreen_action.setObjectName("FullscreenAction")
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        toolbar.addAction(self.fullscreen_action)

        self.history_action = QAction("📚 History", self)
        self.history_action.setObjectName("HistoryAction")
        self.history_action.triggered.connect(self.show_history)
        toolbar.addAction(self.history_action)

        toolbar.addSeparator()

        self.save_config_action = QAction("💾 Save Config", self)
        self.save_config_action.setObjectName("SaveConfigAction")
        self.save_config_action.triggered.connect(self.save_settings)
        toolbar.addAction(self.save_config_action)

    def connect_signals(self):
        """Connect signals and slots"""
        pass

    def create_shortcuts(self):
        """Create keyboard shortcuts"""
        QShortcut(QKeySequence("Ctrl+F"), self, self.search_input.setFocus)
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Ctrl++"), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.reset_zoom)
        QShortcut(QKeySequence("Right"), self, self.next_image)
        QShortcut(QKeySequence("Left"), self, self.prev_image)
        QShortcut(QKeySequence("Delete"), self, self.delete_current_image)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_settings)

    def select_input_file(self):
        """Select input file with any extension"""
        file, _ = QFileDialog.getOpenFileName(
            self, "Select input file", "", "All Files (*.*)"
        )
        if file:
            self.input_file = file
            self.status_bar.showMessage(f"📄 File selected: {os.path.basename(file)}")
            self.animate_status_feedback()

    def select_output_dir(self):
        """Select output directory"""
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_dir = folder
            self.settings.setValue("output_dir", folder)
            self.status_bar.showMessage(f"📂 Output folder: {folder}")
            self.animate_status_feedback()

    def animate_status_feedback(self):
        """Animate status bar feedback"""
        original_style = self.status_bar.styleSheet()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4a90e2, stop: 1 #357abd);
                color: white;
                font-size: 11px;
                border-top: 2px solid #2a75b3;
                padding: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        QTimer.singleShot(1000, lambda: self.status_bar.setStyleSheet(original_style))

    def save_settings(self):
        """Save application settings"""
        self.settings.setValue("output_dir", self.output_dir)
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("window_state", self.saveState())
        self.status_bar.showMessage("💾 Configuration saved successfully")
        self.animate_status_feedback()

    def load_settings(self):
        """Load application settings"""
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.contains("window_state"):
            self.restoreState(self.settings.value("window_state"))

    def closeEvent(self, event):
        """Handle application close event"""
        self.save_settings()
        self.save_url_mapping()
        event.accept()

    def start_scan(self):
        """Start the scanning process"""
        if not hasattr(self, 'input_file'):
            self.show_error("Please select a file.")
            return

        reply = QMessageBox.question(
            self, "Confirm Scan", 
            f"Start processing {self.input_file} → {self.output_dir} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.scan_active = True
        self.start_scan_action.setEnabled(False)
        self.stop_scan_action.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("🚀 Initializing process...")
        self.status_bar.showMessage("🔍 Processing file... Please wait")
        
        # Start animation
        self.animate_scan_start()

        # Start scan in thread
        self.scan_thread = threading.Thread(target=self.run_scan)
        self.scan_thread.daemon = True
        self.scan_thread.start()

    def animate_scan_start(self):
        """Animate scan start"""
        animation = QPropertyAnimation(self.progress_bar, b"value")
        animation.setDuration(800)
        animation.setStartValue(0)
        animation.setEndValue(5)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()

    def stop_scan(self):
        """Stop the scanning process"""
        self.scan_active = False
        self.status_bar.showMessage("🛑 Process stopped by user")
        self.progress_label.setText("⏹️ Process halted")
        self.start_scan_action.setEnabled(True)
        self.stop_scan_action.setEnabled(False)
        
        # Stop animation
        self.animate_scan_stop()

    def animate_scan_stop(self):
        """Animate scan stop"""
        animation = QPropertyAnimation(self.progress_bar, b"value")
        animation.setDuration(500)
        animation.setStartValue(self.progress_bar.value())
        animation.setEndValue(0)
        animation.start()

    def run_scan(self):
        """Run the scanning process"""
        def read_content():
            """Read content from file"""
            try:
                with open(self.input_file, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                urls = set()
                # Extract URLs
                for match in re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text, re.IGNORECASE):
                    try:
                        parsed = urlparse(match)
                        if parsed.netloc:
                            urls.add(f"{parsed.scheme}://{parsed.netloc}")
                    except:
                        pass
                return list(urls)
            except Exception as e:
                print(f"Read error: {e}")
                return []

        def capture(url):
            """Capture screenshot of URL"""
            if not self.scan_active:
                return False, url, "Process stopped"
            
            try:
                with sync_playwright() as p:
                    # Optimized browser launch
                    browser = p.chromium.launch(
                        headless=True,
                        args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
                    )
                    
                    # Optimized context
                    context = browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        java_script_enabled=True,
                        bypass_csp=True,
                        accept_downloads=False
                    )
                    
                    # Block heavy resources
                    def block_media(route):
                        if any(ext in route.request.url for ext in 
                              ['.mp4', '.avi', '.webm', '.mp3', '.wav', '.ogg']):
                            route.abort()
                        else:
                            route.continue_()
                    
                    context.route("**/*", block_media)
                    
                    page = context.new_page()
                    
                    # Reduced timeouts for better performance
                    page.goto(url, timeout=15000)
                    page.wait_for_timeout(1000)

                    safe_name = re.sub(r'[^\w\-_\.]', '_', urlparse(url).netloc)
                    filepath = os.path.join(self.output_dir, f"{safe_name}.png")
                    
                    # Optimized screenshot
                    page.screenshot(
                        path=filepath,
                        type='jpeg',
                        quality=85,
                        full_page=False
                    )
                    
                    browser.close()
                    return True, url, filepath
            except Exception as e:
                return False, url, str(e)

        os.makedirs(self.output_dir, exist_ok=True)
        self.urls = read_content()
        total = len(self.urls)
        if total == 0:
            self.scan_progress.emit(0, "⚠️ No valid URLs found in file")
            self.status_bar.showMessage("❌ No URLs found to process")
            self.start_scan_action.setEnabled(True)
            self.stop_scan_action.setEnabled(False)
            return

        # Optimized thread count
        num_threads = min(4, os.cpu_count() or 1)
        successful_captures = 0
        self.executor = ThreadPoolExecutor(max_workers=num_threads)
        
        try:
            # Submit all tasks
            futures = [self.executor.submit(capture, url) for url in self.urls]
            
            # Process results as they complete
            for i, future in enumerate(as_completed(futures)):
                if not self.scan_active:
                    # Cancel remaining tasks
                    for f in futures[i:]:
                        f.cancel()
                    break
                    
                try:
                    success, url, result = future.result(timeout=60)
                    if success:
                        self.images.append(result)
                        self.url_mapping[os.path.basename(result)] = url
                        successful_captures += 1
                        # Emit signal to add image to interface
                        self.scan_new_image.emit(result)
                    
                    progress = int((i + 1) / total * 100)
                    status_text = f"📊 Progress: {i + 1}/{total} ({successful_captures} ✅ captured)"
                    self.scan_progress.emit(progress, status_text)
                    
                except Exception as e:
                    print(f"Error processing result: {e}")
                    progress = int((i + 1) / total * 100)
                    status_text = f"📊 Progress: {i + 1}/{total} ({successful_captures} ✅ captured)"
                    self.scan_progress.emit(progress, status_text)
                    
        except Exception as e:
            print(f"Scan error: {e}")
        finally:
            self.executor.shutdown(wait=False)
            
        # Save mappings
        self.save_url_mapping()
        self.save_to_history(len(self.urls), successful_captures)
        
        # Complete scan
        self.scan_active = False
        self.scan_completed.emit()

    def update_progress(self, value, text):
        """Update progress bar and text"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(text)
        
        # Pulse effect during scan
        if 0 < value < 100:
            self.progress_label.setStyleSheet("""
                color: #66ccff; 
                font-style: italic; 
                font-size: 12px;
                padding: 6px;
                background-color: rgba(40, 40, 40, 180);
                border-radius: 6px;
                border: 1px solid #4a90e2;
                font-weight: 500;
            """)

    def add_new_image_to_list(self, filepath):
        """Add new image to list in real-time"""
        filename = os.path.basename(filepath)
        
        # Create list item
        item = ThumbnailItem(filepath)
        
        # Add to list with animation
        self.thumbnails_list.addItem(item)
        
        # Animate appearance
        self.animate_thumbnail_appear(item)
        
        # Update navigation if first image
        if len(self.images) == 1:
            self.current_index = 0
            self.show_current_image()
            self.update_navigation()

    def animate_thumbnail_appear(self, item):
        """Animate thumbnail appearance"""
        # Simple visual feedback
        row = self.thumbnails_list.row(item)
        if row >= 0:
            # Temporary style change
            original_bg = item.background()
            item.setBackground(QColor(74, 144, 226, 150))  # Blue with transparency
            QTimer.singleShot(300, lambda: item.setBackground(original_bg))

    def on_scan_completed(self):
        """Handle scan completion"""
        self.progress_label.setText("🎉 Process completed successfully!")
        self.status_bar.showMessage("✅ All websites captured! Ready for review")
        self.start_scan_action.setEnabled(True)
        self.stop_scan_action.setEnabled(False)
        self.update_navigation()
        
        # Completion animation
        self.animate_scan_complete()

    def animate_scan_complete(self):
        """Animate scan completion"""
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 14px;
                border-radius: 7px;
                background-color: #333;
                border: 1px solid #444;
                text-align: center;
                font-size: 9px;
                color: #fff;
                font-weight: 500;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, 
                    stop: 0 #5cb85c, 
                    stop: 0.5 #4cae4c,
                    stop: 1 #5cb85c);
                border-radius: 7px;
            }
        """)
        QTimer.singleShot(2000, lambda: self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 14px;
                border-radius: 7px;
                background-color: #333;
                border: 1px solid #444;
                text-align: center;
                font-size: 9px;
                color: #fff;
                font-weight: 500;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, 
                    stop: 0 #4a90e2, 
                    stop: 0.5 #5cb85c,
                    stop: 1 #5cb85c);
                border-radius: 7px;
            }
        """))

    def load_captures(self):
        """Load existing captures"""
        self.images.clear()
        self.thumbnails_list.clear()
        
        if os.path.exists(self.output_dir):
            # Load all image files
            files = [f for f in os.listdir(self.output_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            self.images = sorted([os.path.join(self.output_dir, f) for f in files])

        # Add thumbnails
        for img_path in self.images:
            item = ThumbnailItem(img_path)
            self.thumbnails_list.addItem(item)

        self.update_navigation()
        if self.images:
            self.current_index = 0
            self.show_current_image()

    def filter_thumbnails(self, text):
        """Filter thumbnails by text"""
        for i in range(self.thumbnails_list.count()):
            item = self.thumbnails_list.item(i)
            item.setHidden(text.lower() not in item.text().lower() if text else False)

    def thumbnail_clicked(self, item):
        """Handle thumbnail click"""
        index = self.thumbnails_list.row(item)
        self.current_index = index
        self.show_current_image()
        self.update_navigation()
        
        # Selection animation
        self.animate_thumbnail_select(index)

    def animate_thumbnail_select(self, index):
        """Animate thumbnail selection"""
        # Simple visual feedback
        item = self.thumbnails_list.item(index)
        if item:
            original_bg = item.background()
            item.setBackground(QColor(255, 215, 0, 150))  # Gold with transparency
            QTimer.singleShot(200, lambda: item.setBackground(original_bg))

    def show_current_image(self):
        """Show current image"""
        if 0 <= self.current_index < len(self.images):
            path = self.images[self.current_index]
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.image_viewer.set_image(pixmap)
                filename = os.path.basename(path)
                
                # Extract URL from filename
                if filename in self.url_mapping:
                    url = self.url_mapping[filename]
                else:
                    # Generate URL from filename
                    domain = filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '').replace('.gif', '').replace('.bmp', '')
                    url = f"https://{domain}"
                
                self.image_info.setText(f"📄 {filename}")
                
                # Show clickable link
                self.url_link.setHtml(f'''
                    <div style="text-align: center;">
                        <a href="{url}" style="color: #66ccff; text-decoration: none; font-weight: 600; font-size: 14px;">
                            🔗 {url}
                        </a>
                    </div>
                ''')
            else:
                self.image_viewer.set_image(None)
                self.image_info.setText("❌ Unable to load image")
                self.url_link.setHtml("")
        else:
            self.image_viewer.set_image(None)
            self.image_info.setText("📭 No image selected")
            self.url_link.setHtml("")

    def update_navigation(self):
        """Update navigation buttons"""
        has_images = len(self.images) > 0
        self.prev_btn.setEnabled(has_images and self.current_index > 0)
        self.next_btn.setEnabled(has_images and self.current_index < len(self.images) - 1)
        self.delete_btn.setEnabled(has_images)

    def prev_image(self):
        """Show previous image"""
        if self.current_index > 0:
            self.current_index -= 1
            self.thumbnails_list.setCurrentRow(self.current_index)
            self.show_current_image()
            self.update_navigation()

    def next_image(self):
        """Show next image"""
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.thumbnails_list.setCurrentRow(self.current_index)
            self.show_current_image()
            self.update_navigation()

    def zoom_in(self):
        """Zoom in on image"""
        self.image_viewer.scale(1.2, 1.2)

    def zoom_out(self):
        """Zoom out on image"""
        self.image_viewer.scale(0.8, 0.8)

    def reset_zoom(self):
        """Reset image zoom"""
        if self.image_viewer.pixmap_item:
            self.image_viewer.fitInView(self.image_viewer.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def delete_current_image(self):
        """Delete current image"""
        if not self.images or not (0 <= self.current_index < len(self.images)):
            return

        path = self.images[self.current_index]
        filename = os.path.basename(path)
        
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Permanently delete {filename} ?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(path)
                # Remove from mapping
                if filename in self.url_mapping:
                    del self.url_mapping[filename]
                    self.save_url_mapping()
                
                # Update lists
                del self.images[self.current_index]
                
                # Update display
                self.thumbnails_list.takeItem(self.current_index)
                
                # Adjust index
                if self.current_index >= len(self.images):
                    self.current_index = max(0, len(self.images) - 1)
                
                self.show_current_image()
                self.update_navigation()
                self.status_bar.showMessage(f"✅ {filename} deleted successfully")
                self.animate_status_feedback()
            except Exception as e:
                self.show_error(f"Error during deletion: {str(e)}")

    def export_all(self):
        """Export all images"""
        if not self.images:
            self.show_error("No images to export")
            return

        # Ask for export format
        items = ["ZIP (all images)", "PDF (catalog)"]
        item, ok = QInputDialog.getItem(self, "Export Options", "Export format:", items, 0, False)
        
        if ok and item:
            if item == "ZIP (all images)":
                self.export_to_zip()
            elif item == "PDF (catalog)":
                self.export_to_pdf()

    def export_to_zip(self):
        """Export images to ZIP"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save ZIP Archive", "screenshots.zip", "ZIP Files (*.zip)"
        )
        
        if filename:
            try:
                with zipfile.ZipFile(filename, 'w') as zipf:
                    for img_path in self.images:
                        zipf.write(img_path, os.path.basename(img_path))
                self.status_bar.showMessage(f"✅ ZIP export successful: {filename}")
                self.animate_status_feedback()
            except Exception as e:
                self.show_error(f"Error during ZIP export: {str(e)}")

    def export_to_pdf(self):
        """Export images to PDF"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.utils import ImageReader
        except ImportError:
            self.show_error("Please install reportlab: pip install reportlab")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save PDF Document", "screenshots.pdf", "PDF Files (*.pdf)"
        )
        
        if filename:
            try:
                c = canvas.Canvas(filename, pagesize=letter)
                width, height = letter
                
                for i, img_path in enumerate(self.images):
                    # New page for each image
                    if i > 0:
                        c.showPage()
                    
                    # Add image
                    try:
                        img = ImageReader(img_path)
                        img_width, img_height = img.getSize()
                        # Adjust size for page
                        scale = min(width/img_width, height/img_height) * 0.8
                        new_width = img_width * scale
                        new_height = img_height * scale
                        x = (width - new_width) / 2
                        y = (height - new_height) / 2
                        c.drawImage(img, x, y, new_width, new_height)
                        
                        # Add filename
                        c.drawString(50, 50, os.path.basename(img_path))
                    except:
                        c.drawString(50, height-50, f"Unable to load: {os.path.basename(img_path)}")
                
                c.save()
                self.status_bar.showMessage(f"✅ PDF export successful: {filename}")
                self.animate_status_feedback()
            except Exception as e:
                self.show_error(f"Error during PDF export: {str(e)}")

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def show_history(self):
        """Show scan history"""
        history = self.load_history()
        if not history:
            QMessageBox.information(self, "Scan History", "No previous scans found in history")
            return

        # Create history window
        history_window = QMainWindow(self)
        history_window.setWindowTitle("📚 Scan History")
        history_window.resize(700, 500)
        history_window.setStyleSheet("""
            QMainWindow {
                background-color: #252525;
                color: #e0e0e0;
            }
            QTextEdit {
                background-color: #333;
                border: 2px solid #555;
                border-radius: 8px;
                color: #e0e0e0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        content = "=== 📚 Screenshot Scan History ===\n\n"
        for entry in history:
            content += f"📅 Date & Time: {entry['date']}\n"
            content += f"📁 Input File: {entry['input_file']}\n"
            content += f"📂 Output Folder: {entry['output_dir']}\n"
            content += f"📊 Total URLs: {entry['total_urls']}\n"
            content += f"✅ Successful Captures: {entry['successful']}\n"
            content += "─" * 60 + "\n\n"
        
        text_edit.setPlainText(content)
        history_window.setCentralWidget(text_edit)
        history_window.show()

    def save_to_history(self, total_urls, successful):
        """Save to history"""
        history = self.load_history()
        
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input_file": getattr(self, 'input_file', 'Unknown'),
            "output_dir": self.output_dir,
            "total_urls": total_urls,
            "successful": successful
        }
        
        history.insert(0, entry)  # Add to beginning
        # Keep only last 20
        history = history[:20]
        
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"History save error: {e}")

    def load_history(self):
        """Load history"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"History load error: {e}")
        return []

    def save_url_mapping(self):
        """Save URL mapping"""
        try:
            with open(self.url_mapping_file, 'w') as f:
                json.dump(self.url_mapping, f, indent=2)
        except Exception as e:
            print(f"Mapping save error: {e}")

    def load_url_mapping(self):
        """Load URL mapping"""
        try:
            if os.path.exists(self.url_mapping_file):
                with open(self.url_mapping_file, 'r') as f:
                    self.url_mapping = json.load(f)
        except Exception as e:
            print(f"Mapping load error: {e}")
            self.url_mapping = {}

    def show_error(self, msg):
        """Show error message"""
        QMessageBox.critical(self, "❌ Error", msg)


if __name__ == "__main__":
    # Enable hardware acceleration before creating QApplication
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern style
    
    # Gray gradient palette
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor(45, 45, 45))
    palette.setColor(palette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Base, QColor(35, 35, 35))
    palette.setColor(palette.ColorRole.AlternateBase, QColor(50, 50, 50))
    palette.setColor(palette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Button, QColor(60, 60, 60))
    palette.setColor(palette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(palette.ColorRole.Link, QColor(102, 204, 255))
    app.setPalette(palette)
    
    window = ScreenshotViewer()
    window.show()
    sys.exit(app.exec())