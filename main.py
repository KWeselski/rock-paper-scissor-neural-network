from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QStatusBar, QMainWindow, QPushButton, QAction, QFileDialog
from PyQt5.QtCore import pyqtSlot, QTimer
from PyQt5.QtGui import QIcon , QPixmap , QImage
from PyQt5.uic import loadUi
from PyQt5 import QtGui , QtCore
import keras
from keras.models import load_model,model_from_json
import cv2
import numpy as np
import sys
import threading
import time
import pickle
import os
import random


class App(QMainWindow):

    def __init__(self):
        """
        The __init__ method sets the needed pyQt variables, loads the UI and the model.
        """
        super().__init__()
        self.title = 'Rock Paper Scissor'
        self.left = 100
        self.top = 150
        self.width = 885
        self.height = 750
        loadUi('mainPage.ui', self)
        self.category = ['paper','rock','scissor']
        #yaml_file = open('model.yaml', 'r')
        #loaded_model_yaml = yaml_file.read()
        with open('model.json', 'r') as json_file:
            self.json_savedModel= json_file.read()
        self.model = model_from_json(self.json_savedModel)
        self.model.load_weights('weights.h5')
        self.image = None
        self.image2 = None
        self.playerOneScore = 0
        self.playerTwoScore = 0
        self.text = ""
        self.capture=None
        self.initUI()
        self.buttonExit.clicked.connect(self.push_Exit)
        self.event = threading.Event()
        self.countdown_thread = threading.Thread(target=self.timer_Down)
        self.startCam = threading.Thread(target=self.start_Webcam)
        self.countdown_thread.start()
        self.startCam.start()

    def push_Exit(self):
        """
        The push_Exit method turns off the program and turns off the camera.
        """
        self.capture.release()
        cv2.destroyAllWindows()
        sys.exit(self.exec_())

    def update_Frame(self,image,window):
        """
        The update_frame method gets the current image from the camera and delivers it to the displayImge method.
        """       
        self.image = image
        self.display_Image(self.image,window)

    def display_Image(self,img,window=1):
        """
        The display_Image method sets the pyQt label object to an image taken from the camera. 
        """
        qFormat=QImage.Format_Indexed8
        if len(img.shape)==3:
            if img.shape[2]==4:
                qFormat=QImage.Format_RGBA8888
            else:
                qFormat=QImage.Format_RGB888
        self.outImage=QImage(img,img.shape[1],img.shape[0],img.strides[0],qFormat)
        self.outImage=self.outImage.rgbSwapped()

        if window==1:
            self.framePlayer.setPixmap(QPixmap.fromImage(self.outImage))
            self.framePlayer.setScaledContents(True)
        if window==2:
            self.framePlayer2.setPixmap(QPixmap.fromImage(self.outImage))
            self.framePlayer2.setScaledContents(True)

    def preprocess(self,img):
        """
        The preprocess method pre-processing image according to the input layer of the model.
        """
        img = cv2.resize(img,(64,64))
        img = np.array(img,dtype=np.float32)
        img = np.reshape(img, (1, 64, 64, 3)) / 255
        return img

    def predict_result(self,image):
        """
        The predict_result method get preprocessed image and use predict method for get result.
        """
        processed = self.preprocess(image)
        pred_probab = self.model.predict(processed)[0]
        pred_class = list(pred_probab).index(max(pred_probab))
        return pred_class

    def initUI(self):
        """
        The initUI method sets some ui labels.
        """
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width , self.height)
        self.PlayerScore.setText(str(self.playerOneScore))
        self.Player2Score.setText(str(self.playerTwoScore))   
        self.PlayerName.setText("Player")
        self.Player2Name.setText("Bot") 
        img=cv2.imread('bot/nothingbot.jpg')
        self.update_Frame(img,2) 
        self.show()

    def bot(self):
        """
        The bot method draw choice and sets image of result.
        """
        x = random.randint(1,3)
        if x == 1:
            botresult = 'paper'
            img = cv2.imread('bot/paperbot.jpg')
            self.update_Frame(img,2)
        if x == 2:
            botresult = 'rock'
            img = cv2.imread('bot/rockbot.jpg')
            self.update_Frame(img,2)
        elif x == 3:
            botresult = 'scissor'
            img = cv2.imread('bot/scissorbot.jpg') 
            self.update_Frame(img,2)

        return botresult

    def set_Result(self,image):
        """
        The set_Result method obtains the results of the expected image and bot selection. 
        Then it uses the who_Won method to check the result of the duel.
        """
        result = self.category[self.predict_result(image)]
        resultBot = self.bot()
        self.who_Won(result,resultBot)
        self.PlayerResult.setText(result)           
        self.Player2Result.setText(resultBot)
        time.sleep(1.0)
        img=cv2.imread('bot/nothingbot.jpg')
        self.update_Frame(img,2)

    def who_Won(self,p1, p2):
        """
        The Who Won method compares the choices and gives the winning point.
        """
        if p1=='rock' and p2=='scissor':
            self.playerOneScore +=1
            self.PlayerScore.setText(str(self.playerOneScore))
            self.GameResult.setText('Player 1 Win')
        if p1=='rock' and p2=='paper':
            self.playerTwoScore +=1
            self.Player2Score.setText(str(self.playerTwoScore))
            self.GameResult.setText('Player 2 Win')
        if p1=='scissor' and p2=='paper':
            self.playerOneScore +=1
            self.PlayerScore.setText(str(self.playerOneScore))
            self.GameResult.setText('Player 1 Win')
        if p1=='scissor' and p2=='rock':
            self.playerTwoScore +=1
            self.Player2Score.setText(str(self.playerTwoScore))
            self.GameResult.setText('Player 2 Win')
        if p1=='paper' and p2=='rock':
            self.playerOneScore +=1
            self.PlayerScore.setText(str(self.playerOneScore))
            self.GameResult.setText('Player 1 Win')
        if p1=='paper' and p2=='scissor':
            self.playerTwoScore +=1
            self.Player2Score.setText(str(self.playerTwoScore))
            self.GameResult.setText('Player 2 Win')
        elif p1 == p2:
            self.GameResult.setText('Draw')

    def timer_Down(self):
        """
        The timer_Down method counts down time to the next duel.
        """
        global my_timer     
        while True:
            x=0
            my_timer = 3
            for x in range(my_timer):
                my_timer -= 1
                self.TimeLabel.setText(str(my_timer))
                time.sleep(1)
            self.set_Result(rect_img)

    def start_Webcam(self):
        """
        The start_Webcam method creates a camera object using openCv libraries and sends
        the image to update_frame methods.
        """
        global rect_img
        x, y , w, h = 300 ,100, 300, 300
        upper = (350,100)
        bottom = (550,300)       
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH,640)   
        while True:          
            _, frame = self.capture.read()
            frame = cv2.flip(frame,1)
            rect_img = frame[upper[1]:upper[0],bottom[1]:bottom[0]]                        
            predict_img = cv2.cvtColor(rect_img,cv2.COLOR_BGR2BGRA)  
            self.update_Frame(predict_img,1)     
            keypress = cv2.waitKey(1)

if __name__=='__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())