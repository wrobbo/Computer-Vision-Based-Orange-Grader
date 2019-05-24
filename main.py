import cv2, math, sys, numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QPushButton, QVBoxLayout
from interface import Ui_GradingWindow

class MainWindow(QMainWindow):
    # Initialise global variables.
    orange_lower_1 = np.array([0, 150, 150])
    orange_upper_1 = np.array([20, 255, 255])
    number_of_defects = 0
    area_of_defects_1 = 0
    area_of_defects_2 = 0
    total_area_of_defects = 0
    area_of_specimen_1 = 0
    area_of_specimen_2 = 0
    total_area_of_specimen = 0
    percentage_of_defects = 0
    orange_grade = ''
    img_pixmap = ''

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        #self.ui.setStyleSheet(open("style.qss", "r").read())
        # Initialise interface.
        self.ui = Ui_GradingWindow()
        self.ui.setup_ui(self)
        self.init_UI()

    def init_UI(self):
        self.ui.btn_first_img.clicked.connect(lambda: self.choose_img(1))
        self.ui.btn_second_img.clicked.connect(lambda: self.choose_img(2))
        self.ui.btn_grade.clicked.connect(lambda: self.grade())

    def choose_img(self, img):
        # Open file picker.
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        # Set file_name equal to the path of the chosen file.
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "All Files (*);;Python Files (*.py)", options=options)
        # Check if file_name contains something.
        if file_name:
            # Set img_path equal to the last 20 characters to get local path to image.
            # Create pixmap from chosen image then scale and display it.
            if img == 1:
                self.img_path_1 = file_name[-20:]
                self.img_pixmap = QtGui.QPixmap(self.img_path_1)
                self.img_pixmap = self.img_pixmap.scaled(250, 250, QtCore.Qt.KeepAspectRatio)
                self.ui.pixmap_img_1.setPixmap(self.img_pixmap)
            elif img == 2:
                self.img_path_2 = file_name[-20:]
                self.img_pixmap = QtGui.QPixmap(self.img_path_2)
                self.img_pixmap = self.img_pixmap.scaled(250, 250, QtCore.Qt.KeepAspectRatio)
                self.ui.pixmap_img_2.setPixmap(self.img_pixmap)

    def grade(self):
        self.number_of_defects = 0
        self.area_of_defects_1 = 0
        self.area_of_defects_2 = 0
        self.total_area_of_defects = 0
        self.area_of_specimen_1 = 0
        self.area_of_specimen_2 = 0
        self.total_area_of_specimen = 0
        self.percentage_of_defects = 0
        self.grade_img(self.img_path_1, 1)
        self.grade_img(self.img_path_2, 2)
        self.calculate_grade()
        self.ui.defect_area_label.setText("Percentage Damaged: " + str(round(self.percentage_of_defects, 3)) + "%.")
        #self.ui.defects_label.setText("Number of Defects: " + str(self.number_of_defects) + '.')
        self.ui.grade_label.setText("Grade of Specimen " + str(self.orange_grade) + '.')

    def grade_img(self, img_path, number):
        # Choose image based on the image path.
        cimg = cv2.imread(img_path, 1)
        # Convert image from BGR to HSV.
        hsv = cv2.cvtColor(cimg, cv2.COLOR_BGR2HSV)
        # Define lower and upper boundaries of orange in HSV.
        # HSV uses max values as H: 180, S: 255, V: 255 for HSV.
        # This compares to the normal max values of H: 360, S: 100, V: 100.
        # Setting upper and lower bounds for first mask.
        mask = cv2.inRange(hsv, self.orange_lower_1, self.orange_upper_1)
        # Bitwise-AND mask and original image (combine the two).
        result = cv2.bitwise_and(cimg, cimg, mask=mask)
        #cv2.imshow('res', result)
        # Save the result to the library to display on screen.
        if number == 1:
            cv2.imwrite('images/specimen_mask_1.jpg', result)
            self.img_pixmap = QtGui.QPixmap('images/specimen_mask_1.jpg')
            self.img_pixmap = self.img_pixmap.scaled(250, 250, QtCore.Qt.KeepAspectRatio)
            self.ui.pixmap_mask_1.setPixmap(self.img_pixmap)
        elif number == 2:
            cv2.imwrite('images/specimen_mask_2.jpg', result)
            self.img_pixmap = QtGui.QPixmap('images/specimen_mask_2.jpg')
            self.img_pixmap = self.img_pixmap.scaled(250, 250, QtCore.Qt.KeepAspectRatio)
            self.ui.pixmap_mask_2.setPixmap(self.img_pixmap)
        # Convert result to gray for contouring.
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        # ret, thresh = cv2.threshold(gray, 127, 255, 3)
        result_2, contours, hierachy = cv2.findContours(gray,cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        #cv2.drawContours(result, contours, -1, (0, 255, 0), 1). 
        specimen_area_1 = 0
        specimen_area_2 = 0
        # Loop through the contours found in the image.
        for c in contours:
            # If contour area is big enough, then continue with loop.
            if cv2.contourArea(c) <= 1500:
                continue
            # Largest contour will be area of the specimen.
            if number == 1:
                if cv2.contourArea(c) > specimen_area_1:
                    specimen_area_1 = cv2.contourArea(c)
                    self.area_of_specimen_1 = specimen_area_1
            elif number == 2:
                if cv2.contourArea(c) > specimen_area_2:
                    specimen_area_2 = cv2.contourArea(c)
                    self.area_of_specimen_2 = specimen_area_2 
            # Add to number of defects.
            self.number_of_defects += 1
            # Get the location and radius of a cirlce that covers the contour area.
            (x, y), radius = cv2.minEnclosingCircle(c)
            # Set center and radius values.
            center = (int(x), int(y))
            radius = int(radius)
            # Draw circle on original image where contour was found.
            cv2.circle(cimg, center, radius, (0, 255, 0), 10)
            # Add area of contours to the area_of_defects to get total area of defects.
            if number == 1:
                self.area_of_defects_1 += cv2.contourArea(c)
            elif number == 2:
                self.area_of_defects_2 += cv2.contourArea(c)
        
        # Depending on which specimen is being analysed, save the image with suffix '1' or '2'.
        if number == 1:
            cv2.imwrite('images/specimen_result_1.jpg', cimg)
            self.img_pixmap = QtGui.QPixmap('images/specimen_result_1.jpg')
            self.img_pixmap = self.img_pixmap.scaled(250, 250, QtCore.Qt.KeepAspectRatio)
            self.ui.pixmap_result_1.setPixmap(self.img_pixmap)
        elif number == 2:
            cv2.imwrite('images/specimen_result_2.jpg', cimg)
            self.img_pixmap = QtGui.QPixmap('images/specimen_result_2.jpg')
            self.img_pixmap = self.img_pixmap.scaled(250, 250, QtCore.Qt.KeepAspectRatio)
            self.ui.pixmap_result_2.setPixmap(self.img_pixmap)

    def calculate_grade(self):
        # Total area of specimen.
        self.total_area_of_specimen = (self.area_of_specimen_1 + self.area_of_specimen_2)
        # Total defected area.
        self.total_area_of_defects = (self.area_of_defects_1 + self.area_of_defects_2)
        # Take total area from area of defects to get total area of defects.
        self.total_area_of_defects = self.total_area_of_defects - self.total_area_of_specimen
        # Work out percentage of defected area in relation to the area of the orange.
        self.percentage_of_defects = (self.total_area_of_defects / self.total_area_of_specimen) * 100
        # Look at number of defects and area of defects of selected orange and grade the orange appropriately.
        if self.percentage_of_defects < 1:
            self.orange_grade = 'A'
        elif self.percentage_of_defects > 1 and self.percentage_of_defects < 2 :
            self.orange_grade = 'B'
        else:
            self.orange_grade = 'C'

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    my_app = MainWindow()
    my_app.show()
    sys.exit(app.exec_())
