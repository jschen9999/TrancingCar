import numpy as np
import cv2
import RPi.GPIO as GPIO
import time
import readchar
from gtts import gTTS
import os
import requests
from mfrc522 import SimpleMFRC522
import tempfile
from pygame import mixer
import datetime
from datetime import datetime
from time import strftime


'''
global variables
'''
#color n cam
red_lower = np.array([0,43,46])
red_upper = np.array([10,255,255])
blue_lower = np.array([100,43,46])
blue_upper = np.array([124,255,255])
black_lower = np.array([0,0,0])
black_upper = np.array([70,70,70])

#color range
red_R_low=30
red_R_high=180
red_G_low=0
red_G_high=40
red_B_low=0
red_B_high=40

#'red': ((0, 0, 255), (125, 125, 255)),
    #'blue': ((255, 0, 0), (255, 125, 125)),
blue_R_low=0
blue_R_high=50
blue_G_low=0
blue_G_high=80
blue_B_low=30
blue_B_high=150

#(36, 25, 25), (70, 255,255)
green_R_low=0
green_R_high=30
green_G_low=30
green_G_high=150
green_B_low=0
green_B_high=120

black_R_low=0
black_R_high=30
black_G_low=0
black_G_high=30
black_B_low=0
black_B_high=30


cap = cv2.VideoCapture(0)

cap.set(3,320)
cap.set(4,240)

#LED
GPIO.setmode(GPIO.BOARD)
LED_R = 35
LED_Y = 37
LED_G = 36
GPIO.setup(LED_R,GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(LED_Y,GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(LED_G,GPIO.OUT, initial=GPIO.LOW)


#car
Motor_R1_Pin = 16
Motor_R2_Pin = 18
Motor_L1_Pin = 15
Motor_L2_Pin = 13

t = 0.1
dc = 100


GPIO.setup(Motor_R1_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor_R2_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor_L1_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor_L2_Pin, GPIO.OUT, initial=GPIO.LOW)

pwm_r1 = GPIO.PWM(Motor_R1_Pin, 500)
pwm_r2 = GPIO.PWM(Motor_R2_Pin, 500)
pwm_l1 = GPIO.PWM(Motor_L2_Pin, 500)
pwm_l2 = GPIO.PWM(Motor_L1_Pin, 500)
pwm_r1.start(0)
pwm_r2.start(0)
pwm_l1.start(0)
pwm_l2.start(0)

#distance
GPIO_TRIGGER = 38
GPIO_ECHO = 40

GPIO.setup(GPIO_TRIGGER, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(GPIO_ECHO, GPIO.IN)

#remote

ENDPOINT = "things.ubidots.com"
DEVICE_LABEL = "weather-station"
VARIABLE_LABEL = "music"
TOKEN = "BBFF-OYzUIOd9rNLblB8vTAMbm8ORxfjoB9" # replace with your TOKEN
DELAY = 0.2  # Delay in seconds
URL = "http://{}/api/v1.6/devices/{}/{}/lv".format(ENDPOINT, DEVICE_LABEL, VARIABLE_LABEL)
HEADERS = {"X-Auth-Token": TOKEN, "Content-Type": "application/json"}

#rfid
reader = SimpleMFRC522()
green_line=0
blue_line=0
black_line=0

#r,l
r=0
l=0

'''
function
'''

#car
def stop():
    pwm_r1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(0)
    pwm_l2.ChangeDutyCycle(0)


def forward():
    pwm_r1.ChangeDutyCycle(dc)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(dc)
    pwm_l2.ChangeDutyCycle(0)
    time.sleep(t)
    stop()


def backward():
    pwm_r1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(dc)
    pwm_l1.ChangeDutyCycle(0)
    pwm_l2.ChangeDutyCycle(dc)
    time.sleep(t)
    stop()


def turnRight():
    pwm_r1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(dc)
    pwm_l2.ChangeDutyCycle(0)
    time.sleep(t)
    stop()

def turnLeft():
    pwm_r1.ChangeDutyCycle(dc)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(0)
    pwm_l2.ChangeDutyCycle(0)
    time.sleep(t)
    stop()


def cleanup():
    stop()
    pwm_r1.stop()
    pwm_r2.stop()
    pwm_l1.stop()
    pwm_l2.stop()
    #GPIO.cleanup()
#color detection
def ChestRed():
    ret, frame = cap.read()
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, red_lower, red_upper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    cnts = cv2.findContours(mask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2]
    if 20 < len(cnts) < 30:
        print("Red!")
        #forward()
def ChestBule():
    ret, frame = cap.read()
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, blue_lower, blue_upper)
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    
    if 25 < len(cnts) < 29:
        print("Blue!")
        #forward()
        
def ChestBlack():
    ret, frame = cap.read()
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, black_lower, black_upper)
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    print(len(cnts))
    if 10>len(cnts) >0:
        print("Black!")
        #forward()
 
#remote
def play(cmd):
    if cmd == 1:
        if blue_line == 1:
            print("播放")
            stop()
            
            # LED_Y ON
            GPIO.output(LED_Y,GPIO.HIGH)
            GPIO.output(LED_R,GPIO.LOW)
            GPIO.output(LED_G,GPIO.LOW)
            hour=datetime.now().strftime('%H')
            minute=datetime.now().strftime('%M')
            
            
            tts = gTTS(text="臨時停車現在是"+hour+"點"+minute+"分", lang='zh-TW')
            tts.save('time.mp3')
            os.system('omxplayer -o local -p time.mp3 > /dev/null 2>&1')
            os.system('omxplayer -o local -p carmusic.mp3 > /dev/null 2>&1')
        elif green_line ==1:
            tts = gTTS(text="此路段無法臨時停車", lang='zh-TW')
            tts.save('dontstop.mp3')
            os.system('omxplayer -o local -p dontstop.mp3 > /dev/null 2>&1')
        # Sends data
        value=0
        payload = {VARIABLE_LABEL: value}
        post_var(payload)
        
    elif cmd == 0:
        print("關閉")

def get_var():
    try:               
        attempts = 0
        status_code = 400
        while status_code >= 400 and attempts < 5:            
            req = requests.get(url=URL, headers=HEADERS)
            status_code = req.status_code
            attempts += 1
            time.sleep(0.1)        
        # print(req.text)
        play(int(float(req.text)))
    except Exception as e:
        print("[ERROR] Error posting, details: {}".format(e))
        
def post_var(payload, url=ENDPOINT, device=DEVICE_LABEL, token=TOKEN):
    try:
        url = "http://{}/api/v1.6/devices/{}".format(url, device)
        headers = {"X-Auth-Token": token, "Content-Type": "application/json"}
        attempts = 0
        status_code = 400
        while status_code >= 400 and attempts < 5:
            print("[INFO] Sending data, attempt number: {}".format(attempts))
            req = requests.post(url=url, headers=headers,json=payload)
            status_code = req.status_code
            attempts += 1
            time.sleep(0.1)
        print("[INFO] Results:")
        print(req.text)
    except Exception as e:
        print("[ERROR] Error posting, details: {}".format(e))
        
#distance
def distance():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
 
    return distance


def state():
    print("STOP!")
    stop()

    # LED_Y ON
    GPIO.output(LED_Y,GPIO.HIGH)
    GPIO.output(LED_R,GPIO.LOW)
    GPIO.output(LED_G,GPIO.LOW)
    hour=datetime.now().strftime('%H')
    minute=datetime.now().strftime('%M')
    
    
    tts = gTTS(text="現在是"+hour+"點"+minute+"分", lang='zh-TW')
    tts.save('time.mp3')
    os.system('omxplayer -o local -p time.mp3 > /dev/null 2>&1')
    #os.system('omxplayer -o local -p carmusic.mp3 > /dev/null 2>&1')
    
def theend():
    print("END!")
    tts = gTTS(text="路線已完成駛至終點", lang='zh-TW')
    tts.save('endpoint.mp3')
    os.system('omxplayer -o local -p endpoint.mp3 > /dev/null 2>&1')
    '''
    if r>l:
        for i in range (r-l+1):
            turnLeft()
    elif l>r:
        for i in range (l-r+1):
            turnRight()
    '''
    
red=0
        
try:
    print("please read")
    stop()
    #tts = gTTS(text='你好我是谷歌小姐', lang='zh-TW')
    tts = gTTS(text='read', lang='en')
    tts.save('choiceline.mp3')
    os.system('omxplayer -o local -p choiceline.mp3 > /dev/null 2>&1')
    #choice color
    id, text = reader.read()
    if id==530474366770:
        green_line=1
        print("green")
    if id==857477776719:
        blue_line=1
        print("blue")
#print(green_line,blue_line)
        
    while 1:
        #line color detection
        ret, frame = cap.read()
        #frame = cv2.GaussianBlur(frame, (5, 5), 0)
        cv2.imshow("frame",frame)
        cb, cg, cr = frame[0,160]
        rb, rg, rr = frame[0,240]
        lb, lg, lr = frame[0,75]
        print(cb, cg, cr)

        
        '''
        ChestRed()
        ChestBule()
        ChestBlack()
        '''
        #check distance
        try:
            dist=distance()
        except:
            pass
            continue
       
        #dist=6
        #time.sleep(0.05)

        if dist >20:
            
            # LED_G ON
            GPIO.output(LED_G,GPIO.HIGH)
            GPIO.output(LED_R,GPIO.LOW)
            GPIO.output(LED_Y,GPIO.LOW)
            
            print ("Measured Distance = %.1f cm" % dist)
            #blue
            if blue_line==1:
                if rb<=blue_B_high and rb>=blue_B_low and rg<=blue_G_high and rg>=blue_G_low and rr<=blue_R_high and rr>=blue_R_low:
                    if rb>rg:
                        turnRight()
                        r=r+1
                        print("blue_R")
                    
                elif lb<=blue_B_high and lb>=blue_B_low and lg<=blue_G_high and lg>=blue_G_low and lr<=blue_R_high and lr>=blue_R_low:
                    if lb>lg:
                        turnLeft()
                        l=l+1
                        print("blue_L")
                elif cb<=blue_B_high and cb>=blue_B_low and cg<=blue_G_high and cg>=blue_G_low and cr<=blue_R_high and cr>=blue_R_low:
                    if cb>cg:
                        forward()
                        print("blue_F")
            #green
            elif green_line==1:
                if rb<=green_B_high and rb>=green_B_low and rg<=green_G_high and rg>=green_G_low and rr<=green_R_high and rr>=green_R_low:
                    if rb<rg:
                        turnRight()
                        r=r+1
                        print("green_R")
                    
                elif lb<=green_B_high and lb>=green_B_low and lg<=green_G_high and lg>=green_G_low and lr<=green_R_high and lr>=green_R_low:
                    if lb<lg:
                        turnLeft()
                        l=l+1
                        print("green_L")
                elif cb<=green_B_high and cb>=green_B_low and cg<=green_G_high and cg>=green_G_low and cr<=green_R_high and cr>=green_R_low:
                    if cb<cg:
                        forward()
                        print("green_F")
            #black
            elif black_line==1:
                if rb<=black_B_high and rb>=black_B_low and rg<=black_G_high and rg>=black_G_low and rr<=black_R_high and rr>=black_R_low and lb<=black_B_high and lb>=black_B_low and lg<=black_G_high and lg>=black_G_low and lr<=black_R_high and lr>=black_R_low and cb<=black_B_high and cb>=black_B_low and cg<=black_G_high and cg>=black_G_low and cr<=black_R_high and cr>=black_R_low:
                    stop()
                    GPIO.output(LED_R,GPIO.HIGH)
                    GPIO.output(LED_Y,GPIO.HIGH)
                    GPIO.output(LED_G,GPIO.HIGH)
                    tts = gTTS(text='終點到達請按結束鍵', lang='zh-TW')
                    tts.save('stopend.mp3')
                    os.system('omxplayer -o local -p stopend.mp3 > /dev/null 2>&1')
                    
                elif rb<=black_B_high and rb>=black_B_low and rg<=black_G_high and rg>=black_G_low and rr<=black_R_high and rr>=black_R_low:
                    turnRight()
                    print("black_R")
                    
                elif lb<=black_B_high and lb>=black_B_low and lg<=black_G_high and lg>=black_G_low and lr<=black_R_high and lr>=black_R_low:
                    turnLeft()
                    print("black_L")
                elif cb<=black_B_high and cb>=black_B_low and cg<=black_G_high and cg>=black_G_low and cr<=black_R_high and cr>=black_R_low:
                    forward()
                    print("black_F")
                
            #red(stop)
            
            if cb<=red_B_high and cb>=red_B_low and cg<=red_G_high and cg>=red_G_low and cr<=red_R_high and cr>=red_R_low and black_line==0:
                if red==0:state()
                red=1
                forward()
                forward()
                forward()
            elif lb<=red_B_high and lb>=red_B_low and lg<=red_G_high and lg>=red_G_low and lr<=red_R_high and lr>=red_R_low and black_line==0:
                if red==0:state()
                red=1
                turnLeft()
                turnLeft()
                forward()
                forward()
            elif rb<=red_B_high and rb>=red_B_low and rg<=red_G_high and rg>=red_G_low and rr<=red_R_high and rr>=red_R_low and black_line==0:
                if red==0:state()
                red=1
                turnRight()
                turnRight()
                forward()
                forward()
                
                
                
            #black(end)
            
            if cb<=black_B_high and cb>=black_B_low and cg<=black_G_high and cg>=black_G_low and cr<=black_R_high and cr>=black_R_low and black_line==0:
                theend()
                black_line=1
                green_line=0
                blue_line=0
            elif lb<=black_B_high and lb>=black_B_low and lg<=black_G_high and lg>=black_G_low and lr<=black_R_high and lr>=black_R_low and black_line==0:
                theend()
                black_line=1
                green_line=0
                blue_line=0
            elif rb<=black_B_high and rb>=black_B_low and rg<=black_G_high and rg>=black_G_low and rr<=black_R_high and rr>=black_R_low and black_line==0:
                theend()
                black_line=1
                green_line=0
                blue_line=0
                
            

            
            #get remote value
            if black_line==0:
                get_var()
            else:
                time.sleep(0.05)
            
        else:
            print ("Measured Distance = %.1f cm" % dist)
            stop()
            # LED_R ON
            GPIO.output(LED_R,GPIO.HIGH)
            GPIO.output(LED_Y,GPIO.LOW)
            GPIO.output(LED_G,GPIO.LOW)
            tts = gTTS(text='請移除前方障礙物', lang='zh-TW')
            tts.save('disnote.mp3')
            os.system('omxplayer -o local -p disnote.mp3 > /dev/null 2>&1')
        
        if cv2.waitKey(5) == ord('q'):
            cleanup()        
            GPIO.cleanup()
            quit()
            break
    cap.release()
    cv2.destroyAllWindows()
finally:
    GPIO.cleanup()
