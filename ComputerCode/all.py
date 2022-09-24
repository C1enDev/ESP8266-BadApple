'''
/************************************************************
  ====ESP8266播放视频Project====
  Author：C1en
  Date: 2022/09/24
  Version: V1.1.4.5.1.4
  ------------------------------------------------------------
  注：Python3.x运行环境，读取本地视频并通过socket发送
************************************************************/
'''

import cv2
import numpy as np
from ffpyplayer.player import MediaPlayer

import sys
import getopt
from PIL import Image,ImageDraw,ImageFont
import struct

import socket,time

host = '192.168.5.100'
port = 8080
video_path="badapple_320240_xvid.mp4"

def socket_start():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #host = socket.gethostbyname(socket.gethostname())

    print(host)
    print(port)
    s.bind((host,port))
    s.listen(5)

    print('等待client连接中…')

    client,client_address = s.accept()
    print('新连接')
    client_IP = str(client_address[0])
    print('IP:'+client_IP)
    client_port = str(client_address[1])
    print('Port:' + client_port)

    return client

def img_to_matrix(frame, endian, color_reverse):
    width = frame.shape[1] #128
    height = frame.shape[0] #64

    if endian == 'B':
        byte_reverse = True
    else:
        byte_reverse = False

    if color_reverse == 'true':
        color_reverse = True
    else:
        color_reverse = False

    unalign = 0
    matrix = list()
    
    if (width%8) != 0:
        unalign = 1
    for i in range(0, height): #64
        for j in range(0, (width//8)+unalign): #128/8=16
            v = 0x00
            rs = 8*j      
            re = 8*(j+1)  
            if re > width:
                re = width
            for k in range(rs, re):
                if frame[i, k] != 0:
                    if not byte_reverse:
                        v |= (0x01 << (k%8))
                    else:
                        v |= (0x01 << (7-(k%8)))
            if color_reverse:
                v ^= 0xff
            matrix.append(v)

    return matrix


def binary_image(image):#二值化
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)  #灰度化
    h, w =gray.shape[:2]
    m = np.reshape(gray, [1,w*h])
    mean = m.sum()/(w*h)
    ret, binary =  cv2.threshold(gray, mean, 255, cv2.THRESH_OTSU)
    return binary


def PlayVideo(video_path, client):
    endian          = 'L'
    color_reverse   = 'false'
    
    c = 0#累计帧数
    timeF = 8#隔x帧截一次图
    
    video = cv2.VideoCapture(video_path) #打开视频
    player = MediaPlayer(video_path) #打开音频
    while True:
        grabbed, frame= video.read()
        audio_frame, val = player.get_frame()
        if not grabbed:
            print("End of video")
            break
        if cv2.waitKey(28) & 0xFF == ord("q"):
            break
        cv2.imshow("Video", frame)
        if val != 'eof' and audio_frame is not None:
            img, t = audio_frame

        if (c % timeF == 0):  # 每隔timeF帧进行存储操作
            frame = cv2.resize(frame,(128,64))#调整尺寸
            frame = binary_image(frame)#二值化
            matrix = img_to_matrix(frame, endian, color_reverse)
            data = bytes(matrix)
            client.send(data)

        c = c + 1
        #time.sleep(0.2)
        #cv2.waitKey(1)
            
    video.release()
    cv2.destroyAllWindows()

###############
client = 0
client = socket_start()
PlayVideo(video_path, client)
