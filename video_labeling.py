import sys
import os
import cv2 as cv
import csv
import pandas as pd

from PySide2.QtCore import Qt, QSize, QPoint, QRect, Signal, QDir
from PySide2.QtGui import QIcon, QImage, QPixmap, QPainter, QPen
from PySide2.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget,
    QAction, 
    QHBoxLayout, 
    QVBoxLayout, 
    QPushButton, 
    QLabel,
    QFileDialog,
    QComboBox,
    QLineEdit,
    QInputDialog,
    QSlider,
    QListWidget,
    QMessageBox
)

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        # Tags Dataset
        self.tags_dataset = TagDataset()

        # Default Tags
        self.tags = [Tag()]
        self.labels_path = "labels.txt"
        file = open(self.labels_path)
        labels_lines = file.readlines()
        for _, line in enumerate(labels_lines):
            if len(line.split(',')) == 2:
                label_id, label_name = line.rstrip().split(',')
                tag = Tag(int(label_id), label_name)
                self.tags.append(tag)
        file.close()

        self.selected_tag = None

        self.cap = None
        self.curr_frame = 0
        self.total_frames = 0

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Video Labeling App")

        load_video_button_action = QAction(QIcon("blue-document-import.png"), "&Load Video", self)
        load_video_button_action.setStatusTip("Load Video Button")
        load_video_button_action.triggered.connect(self.onLoadVideoButtonClick)

        save_data_button_action = QAction(QIcon("blue-document-excel-csv.png"), "&Save Data", self)
        save_data_button_action.setStatusTip("Save Data Button")
        save_data_button_action.triggered.connect(self.onSaveButtonClick)

        load_data_button_action = QAction(QIcon("blue-document-excel-csv.png"), "&Load Data", self)
        load_data_button_action.setStatusTip("Load Data Button")
        load_data_button_action.triggered.connect(self.onLoadDataButtonClick)

        add_label_button_action = QAction(QIcon("node-insert.png"), "&Add Label", self)
        add_label_button_action.setStatusTip("Add Label Button")
        add_label_button_action.triggered.connect(self.onAddItemButtonClick)

        save_labels_button_action = QAction(QIcon("blue-document-excel-csv.png"), "&Save Labels", self)
        save_labels_button_action.setStatusTip("Save Ñabels Button")
        save_labels_button_action.triggered.connect(self.onSaveLabelsButtonClick)

        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.setCursor(Qt.PointingHandCursor)
        file_menu.addAction(load_video_button_action)
        file_menu.addAction(load_data_button_action)
        file_menu.addAction(save_data_button_action)

        options_menu = menu.addMenu("&Options")
        options_menu.setCursor(Qt.PointingHandCursor)
        options_menu.addAction(add_label_button_action)
        options_menu.addAction(save_labels_button_action)

        main_hor_layout = QVBoxLayout()

        img_ctl_ver_layout = QHBoxLayout()
        
        prev_btn = QPushButton("&Prev")
        prev_btn.setStatusTip("Previous Image Button")
        prev_btn.setCursor(Qt.PointingHandCursor)
        prev_btn.clicked.connect(self.onPrevButtonClick)
        
        next_btn = QPushButton("&Next")
        next_btn.setStatusTip("Next Image Button")
        next_btn.setCursor(Qt.PointingHandCursor)
        next_btn.clicked.connect(self.onNextButtonClick)
        
        self.image_label = Label()
        self.image_label.setFixedSize(QSize(640, 480))
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.rect_created.connect(self.onRect)

        img_ctl_ver_layout.addWidget(prev_btn)
        img_ctl_ver_layout.addWidget(self.image_label)
        img_ctl_ver_layout.addWidget(next_btn)

        main_hor_layout.addLayout(img_ctl_ver_layout)

        self.frames_slider = QSlider()
        self.frames_slider.setOrientation(Qt.Horizontal)
        self.frames_slider.setSingleStep(1)
        self.frames_slider.setPageStep(10)
        self.frames_slider.setTickPosition(QSlider.TicksBelow)
        self.frames_slider.setCursor(Qt.PointingHandCursor)
        self.frames_slider.sliderReleased.connect(self.sliderReleased)

        main_hor_layout.addWidget(self.frames_slider)

        # Create tags combo box
        self.tags_combo_box = QComboBox()
        self.tags_combo_box.setCursor(Qt.PointingHandCursor)
        for tag in self.tags:
            self.tags_combo_box.addItem(tag.name)

        # Add List Widget
        self.list_widget = QListWidget()
        self.list_widget.setCursor(Qt.PointingHandCursor)
        self.list_widget.itemClicked.connect(self.onListWidgetItemClicked)
        self.list_widget.itemDoubleClicked.connect(self.onListWidgetItemDoubleClicked)

        # Add Delete Button
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.onDeleteBtnClicked)

        main_hor_layout.addWidget(self.tags_combo_box)
        main_hor_layout.addWidget(self.list_widget)
        main_hor_layout.addWidget(self.delete_btn)

        container = QWidget()
        container.setLayout(main_hor_layout)
        self.setCentralWidget(container)

    def onLoadVideoButtonClick(self, s):
        print("Load Button Clicked ")

        self.video_file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video", 
            os.path.expanduser('~'), 
            "Video Files (*.mp4 *.avi *.mpeg *.mov *.wmv *.flv *.mpg *.mkv)"
            )

        # Initilize capture device
        self.cap = cv.VideoCapture(self.video_file_path)

        # Get total frames
        self.total_frames = self.cap.get(cv.CAP_PROP_FRAME_COUNT)

        # Initilize current frames
        self.curr_frame = 0

        if self.cap != None and self.cap.isOpened():
            print(self.video_file_path)
            print("Opened with {} frames".format(self.total_frames))

            self.frames_slider.setMinimum(0)
            self.frames_slider.setMaximum(self.total_frames)
            self.frames_slider.setValue(0)

            self.moveToCurrFrame()
        else:
            print("Cannot open {}".format(self.video_file_path))

    def onLoadDataButtonClick(self, s):
        print("Load Data Button Click")
        
        self.data_file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV Data File", 
            os.path.expanduser('~'), 
            "Data Files (*.csv)"
            )
        
        if self.data_file_path != "":
            self.tags_dataset.loadDataset(self.data_file_path)
    
    def onSaveButtonClick(self, s):
        print("Save Button Clicked ")

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV Data File", 
            os.getcwd() + "/bbox_dataset.csv", 
            "Data Files (*.csv)"
            )

        if save_path != '':
            self.tags_dataset.saveDataset(save_path)

    def onNextButtonClick(self, s):
        if self.curr_frame < self.total_frames:
            self.curr_frame += 1
        else:
            self.curr_frame = 0

        self.moveToCurrFrame()

    def onPrevButtonClick(self, s):
        if self.curr_frame > 0:
            self.curr_frame -= 1
        else:
            self.curr_frame = self.total_frames

        self.moveToCurrFrame()
        
    def moveToCurrFrame(self):
    
        if self.cap is None:
            return

        print("Move to Frame: ", self.curr_frame)

        # Set frame position
        self.cap.set(cv.CAP_PROP_POS_FRAMES, self.curr_frame)

        # Get image
        retval, image = self.cap.read()

        if retval:
    
            # Set image label
            self.curr_image = QImage(image.data, image.shape[1], image.shape[0], QImage.Format_RGB888).rgbSwapped()
            pixmap_img = QPixmap.fromImage(self.curr_image)

            # Find bboxes in this image label to draw it
            bbox_tags = self.tags_dataset.getFrameBBoxs(self.video_file_path, self.curr_frame)

            painter = QPainter(pixmap_img)

            self.list_widget.clear()
            for bbox_tag in bbox_tags:
                drawBBoxLabel(painter, bbox_tag.rect, bbox_tag.tag.name)
                self.list_widget.addItem(getBBoxLabelName(bbox_tag.rect, bbox_tag.tag.name))

            painter.end()

            self.image_label.setPixmap(pixmap_img)

            self.frames_slider.setValue(self.curr_frame)

            self.selected_tag = None
            
        else:
            showMessage("Cannot retrieve frame at {}".format(self.curr_frame))

    def onRect(self, r):
        
        bbox_tag = BBoxTag()
        tag = self.tags[self.tags_combo_box.currentIndex()]
        bbox_tag.setValues(r, tag, self.curr_frame, self.video_file_path)

        if self.selected_tag is None:            
            self.tags_dataset.addTag(bbox_tag)
        else:
            self.tags_dataset.updateBBoxTag(self.selected_tag, bbox_tag)

        pixmap_img = QPixmap.fromImage(self.curr_image)

        # Find bboxes in this image label to draw it
        bbox_tags = self.tags_dataset.getFrameBBoxs(self.video_file_path, self.curr_frame)

        painter = QPainter(pixmap_img)

        self.list_widget.clear()
        for bbox_tag in bbox_tags:
            drawBBoxLabel(painter, bbox_tag.rect, bbox_tag.tag.name)
            self.list_widget.addItem(getBBoxLabelName(bbox_tag.rect, bbox_tag.tag.name))

        painter.end()

        self.image_label.setPixmap(pixmap_img)
        self.image_label.update()

        self.selected_tag = None

    def onAddItemButtonClick(self):
        text, ok = QInputDialog().getText(self, "Add new item label",
                                     "Label:", QLineEdit.Normal,
                                     QDir().home().dirName())
        if ok and text:
            new_tag = Tag(len(self.tags), text)
            self.tags.append(new_tag)
            self.tags_combo_box.addItem(new_tag.name)

    def sliderReleased(self):
        print("Slider Released at {}".format(self.frames_slider.value()))

        self.curr_frame = self.frames_slider.value()

        self.moveToCurrFrame()

    def onListWidgetItemClicked(self, item):
        
        # Parse item string
        label_dict = parseBBoxLabelName(item.text())
        
        # Get item rect
        target_rect = QRect(int(label_dict['x']), int(label_dict['y']), int(label_dict['w']), int(label_dict['h']))
        
        # Get item tag name
        target_name = label_dict["name"]

        # Find bboxes in this image label to draw it
        bbox_tags = self.tags_dataset.getFrameBBoxs(self.video_file_path, self.curr_frame)

        image_label_pixmap= self.image_label.pixmap()
        painter = QPainter(image_label_pixmap)

        for bbox_tag in bbox_tags:
            if bbox_tag.tag.name.replace(" ", "") == target_name and bbox_tag.rect == target_rect: 
                drawBBoxLabel(painter, bbox_tag.rect, bbox_tag.tag.name, color=Qt.green)
                self.selected_tag = bbox_tag
                self.delete_btn.setEnabled(True) 
            else:
                drawBBoxLabel(painter, bbox_tag.rect, bbox_tag.tag.name)

        painter.end()

        self.image_label.setPixmap(image_label_pixmap)
        self.image_label.update()

    def onListWidgetItemDoubleClicked(self, item):
        self.list_widget.clearSelection()
        self.selected_tag = None
        self.delete_btn.setEnabled(False)

        pixmap_img = QPixmap.fromImage(self.curr_image)
        
        bbox_tags = self.tags_dataset.getFrameBBoxs(self.video_file_path, self.curr_frame)

        painter = QPainter(pixmap_img)
        for bbox_tag in bbox_tags:
            drawBBoxLabel(painter, bbox_tag.rect, bbox_tag.tag.name)
        painter.end()
        
        self.image_label.setPixmap(pixmap_img)
        self.image_label.update()

    def onDeleteBtnClicked(self):
        print("Delete Button Clicked")

        # Find selected tag in database
        # Delete from database
        self.tags_dataset.deleteBBoxTag(self.selected_tag)

        # Repaint labels
        # Find bboxes in this image label to draw it
        bbox_tags = self.tags_dataset.getFrameBBoxs(self.video_file_path, self.curr_frame)

        pixmap_img = QPixmap.fromImage(self.curr_image)
        
        painter = QPainter(pixmap_img)
        self.list_widget.clear()
        for bbox_tag in bbox_tags:
            drawBBoxLabel(painter, bbox_tag.rect, bbox_tag.tag.name)
            self.list_widget.addItem(getBBoxLabelName(bbox_tag.rect, bbox_tag.tag.name))
        painter.end()
        
        self.image_label.setPixmap(pixmap_img)
        self.image_label.update()    

    def onSaveLabelsButtonClick(self):
        self.saveLabels()

    def saveLabels(self):

        try:        
            file = open(self.labels_path, "w")

            try:
            
                for tag in self.tags:
                    if tag.id > 0:
                        file.write(str(tag) + "\n")

                showMessage("Labels saved to {}".format(self.labels_path))
            except:
                showMessage("Something went wrong when writing to file {}".format(self.labels_path))
            finally:
                file.close()
        except:
            showMessage("Something went worng when opening the file {}".format(self.labels_path))

class Label(QLabel):

    rect_created = Signal(QRect) 

    def __init__(self):
        super(Label, self).__init__()
        
        self.setScaledContents(True)

        self.begin, self.destination = QPoint(), QPoint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(QPoint(), self.pixmap())

        if not self.begin.isNull() and not self.destination.isNull():
            rect = QRect(self.begin, self.destination)
            drawBBoxLabel(painter, rect)

    def mousePressEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.begin = event.pos()
            self.destination = self.begin
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:	
            self.destination = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        
        if (event.button() & Qt.LeftButton) and self.pixmap() != None:

            x_left = min(self.begin.x(), self.destination.x())
            y_top = min(self.begin.y(), self.destination.y())
            x_right = max(self.begin.x(), self.destination.x())
            y_bottom = max(self.begin.y(), self.destination.y())

            rect = QRect(x_left, y_top, abs(x_left-x_right), abs(y_top - y_bottom))

            # Reset draw rect
            self.begin, self.destination = QPoint(), QPoint()
            
            self.rect_created.emit(rect)
        
class Tag():

    def __init__(self, id=0, name="Undefined"):
        self.id = id
        self.name = name

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Tag):
            equal_value = self.id == other.id and self.name == other.name
            return equal_value
        return NotImplemented

    def __str__(self):
        return f"{self.id},{self.name}"

class BBoxTag():
    def __init__(self):

        # Bounding Box Label props
        self.rect = QRect()
        self.tag = Tag()
        self.frame_id = -1
        self.file_name = ""

    def setValues(self, rect, tag, frame_id, file_name):
        self.rect = rect
        self.tag = tag
        self.frame_id = frame_id
        self.file_name = file_name

    def getValues(self):
        return [
                    self.rect.left(),
                    self.rect.top(),
                    self.rect.width(),
                    self.rect.height(),
                    self.tag.id,
                    self.tag.name,
                    self.frame_id,
                    self.file_name
                ]
    
    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, BBoxTag):
            equal_value = self.rect == other.rect and self.tag == other.tag and self.frame_id == other.frame_id and self.file_name == other.file_name
            return equal_value
        return NotImplemented

class TagDataset():

    def __init__(self):
        self.bbox_tags = []

        self.headers = ["x", "y", "w", "h", "tag_id", "tag_name", "frame_id", "file_name"]

    def addTag(self, bbox_tag):
        self.bbox_tags.append(bbox_tag)

    def saveDataset(self, save_path):
        with open(save_path, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

            for bbox_tag in self.bbox_tags:
                row_data = bbox_tag.getValues()
                writer.writerow(row_data)

    def loadDataset(self, file_path):
        print("Load Dataset")

        print("Before: ", len(self.bbox_tags))
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            rect = QRect(row["x"], row["y"], row["w"], row["h"])
            tag = Tag(row["tag_id"], row["tag_name"])
            frame_id = row["frame_id"]
            filename = row["file_name"]

            bbox_tag = BBoxTag()
            bbox_tag.setValues(rect, tag, frame_id, filename)

            self.bbox_tags.append(bbox_tag)
        
        print("After: ", len(self.bbox_tags))

    def getFrameBBoxs(self, file_name, frame_id):
        
        bbox_values = [bbox_tag.getValues() for bbox_tag in self.bbox_tags]

        df = pd.DataFrame(data=bbox_values, columns=self.headers)

        df_filtered = df.query("file_name == @file_name and frame_id == @frame_id")

        bbox_tags = []
        for _, row in df_filtered.iterrows():
            rect = QRect(row["x"], row["y"], row["w"], row["h"])
            tag = Tag(row["tag_id"], row["tag_name"])
            frame_id = row["frame_id"]
            file_name = row["file_name"]

            bbox_tag = BBoxTag()
            bbox_tag.setValues(rect, tag, frame_id, file_name)

            bbox_tags.append(bbox_tag)
        
        return bbox_tags

    def deleteBBoxTag(self, target_tag):
        if target_tag is None:
            showMessage("The tag cannot be deleted, it does not exist")
            return

        # Get index to delete
        index_to_delete = -1
        for i in range(len(self.bbox_tags)):
            bbox_tag = self.bbox_tags[i]
            if bbox_tag == target_tag:
                index_to_delete = i
                break
        
        if index_to_delete != -1: 
            del self.bbox_tags[index_to_delete]
        else:
            showMessage("The tag cannot be deleted, it does not exist")

    def updateBBoxTag(self, target_tag, new_tag):
        if target_tag is None:
            showMessage("The tag cannot be updated, it does not exist")
            return

        # Get index to delete
        index_to_change = -1
        for i in range(len(self.bbox_tags)):
            bbox_tag = self.bbox_tags[i]
            if bbox_tag == target_tag:
                index_to_change = i
                break
        
        if index_to_change != -1: 
            self.bbox_tags[index_to_change] = new_tag
        else:
            showMessage("The tag cannot be updated, it does not exist")
        
def drawBBoxLabel(painter, rect, label = None, color=Qt.red):
    pen = QPen(color, 3) # Set red pen
    painter.setPen(pen)
    painter.drawRect(rect.normalized())
    
    if label is not  None:
        pen = QPen(Qt.green, 3) # Set green pen
        painter.setPen(pen)
        painter.drawText(rect, label)

def getBBoxLabelName(rect, tag_name):
    return f"{rect.x()}, {rect.y()}, {rect.width()}, {rect.height()}, {tag_name}"

def parseBBoxLabelName(bbox_label):

    split_txt = bbox_label.replace(" ", "").split(',')

    return {'x': split_txt[0], 'y': split_txt[1], 'w': split_txt[2], 'h': split_txt[3], 'name': split_txt[4]}        

def showMessage(message):
    msgBox = QMessageBox()
    msgBox.setText(message)
    msgBox.exec_() 

def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec_()

    window.saveLabels()

if __name__ == "__main__":
    main()