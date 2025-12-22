from PySide6.QtWidgets import QProgressBar, QStylePainter, QStyleOptionProgressBar
from PySide6.QtCore import Qt, QPropertyAnimation, Property, QRect
from PySide6.QtGui import QPainter, QLinearGradient, QColor

import random


class PulseProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pulse_offset = random.uniform(-1.0, 3.0)
        self._pulse_direction = "ltr"  # "ltr" or "rtl"
        self._pulse_color = QColor(255, 255, 255, 60) # Default white shimmer

        self.animation = QPropertyAnimation(self, b"pulse_offset")
        self.animation.setDuration(
            random.randint(6000, 10000)
        )  # Randomize speed (6-10s)
        self.animation.setStartValue(-1.5)  # Off-screen left
        self.animation.setEndValue(3.5)  # Off-screen right
        self.animation.setLoopCount(-1)

        # Random start position
        self.animation.setCurrentTime(random.randint(0, 6000))
        self.animation.start()

    @Property(float)
    def pulse_offset(self):
        return self._pulse_offset

    @pulse_offset.setter
    def pulse_offset(self, value):
        self._pulse_offset = value
        self.update()

    @Property(QColor)
    def pulse_color(self):
        return self._pulse_color

    @pulse_color.setter
    def pulse_color(self, value):
        self._pulse_color = value
        self.update()

    def setPulseDirection(self, direction):
        self._pulse_direction = direction
        if direction == "rtl":
            self.animation.setStartValue(1.5)
            self.animation.setEndValue(-0.5)
        else:
            self.animation.setStartValue(-0.5)
            self.animation.setEndValue(1.5)

    def paintEvent(self, event):
        # Let the standard style draw the background and chunk first
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        width = rect.width()
        height = rect.height()

        # Calculate the chunk area
        val_range = self.maximum() - self.minimum()
        if val_range <= 0:
            return

        progress = (self.value() - self.minimum()) / val_range
        chunk_width = width * progress

        # Determine the actual chunk rectangle (handling inverted appearance)
        if self.invertedAppearance():
            chunk_rect = QRect(width - chunk_width, 0, chunk_width, height)
        else:
            chunk_rect = QRect(0, 0, chunk_width, height)

        # Clip to the chunk area
        painter.setClipRect(chunk_rect)

        # Adjust shimmer position relative to the WHOLE width for smooth panning
        shimmer_width = width * 0.6 # Slightly wider shimmer
        pos = width * self._pulse_offset

        gradient = QLinearGradient()
        if self._pulse_direction == "ltr":
            gradient.setStart(pos - shimmer_width / 2, 0)
            gradient.setFinalStop(pos + shimmer_width / 2, 0)
        else:
            gradient.setStart(pos + shimmer_width / 2, 0)
            gradient.setFinalStop(pos - shimmer_width / 2, 0)

        # Light elegant pulse with customizable color
        c = self._pulse_color
        highlight = QColor(c.red(), c.green(), c.blue(), 0)
        mid_shine = c
        
        gradient.setColorAt(0, highlight)
        gradient.setColorAt(0.4, mid_shine)
        gradient.setColorAt(0.6, mid_shine) # Wider peak for better visibility
        gradient.setColorAt(1, highlight)

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)

        # Draw shimmer over the WHOLE area (the clip will restrict it to the chunk)
        shimmer_rect = QRect(0, 0, rect.width(), rect.height())
        painter.drawRect(shimmer_rect)

        # Optional: Add a top highlights line for more "premium" feel
        top_line_gradient = QLinearGradient(pos - shimmer_width / 2, 0, pos + shimmer_width / 2, 0)
        top_line_color = QColor(255, 255, 255, 100)
        top_line_gradient.setColorAt(0, QColor(255, 255, 255, 0))
        top_line_gradient.setColorAt(0.5, top_line_color)
        top_line_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(top_line_gradient)
        painter.drawRect(QRect(0, 0, rect.width(), 2))

        painter.end()
