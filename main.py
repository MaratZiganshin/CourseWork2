import cv2
import numpy as np
import copy
import win32api
import math
import win32con
from directkeys import PressKey, ReleaseKey, UP, DOWN


def calculateFingers(res,drawing):  # -> finished bool, cnt: finger count
    #  convexity defect
    hull = cv2.convexHull(res, returnPoints=False)
    if len(hull) > 3:
        defects = cv2.convexityDefects(res, hull)
        if type(defects) != type(None):  # avoid crashing.   (BUG not found)

            cnt = 0
            for i in range(defects.shape[0]):  # calculate the angle
                s, e, f, d = defects[i][0]
                start = tuple(res[s][0])
                end = tuple(res[e][0])
                far = tuple(res[f][0])
                a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
                b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
                c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)
                angle = math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c))  # cosine theorem
                if angle <= math.pi / 2:  # angle less than 90 degree, treat as fingers
                    cnt += 1
                    cv2.circle(drawing, far, 8, [211, 84, 0], -1)
            return True, cnt
    return False, 0

camera = cv2.VideoCapture(1)
camera.set(10,200)
bgModel = cv2.createBackgroundSubtractorMOG2(0, 50)

up = False
down = False
center = True
enabled = False
while 1:
    ret, frame = camera.read()

    threshold = cv2.getTrackbarPos('trh1', 'trackbar')
    frame = cv2.bilateralFilter(frame, 5, 50, 100)  # smoothing filter
    frame = cv2.flip(frame, 1)  # flip the frame horizontally
    #cv2.rectangle(frame, (int(0.5 * frame.shape[1]), 0), (frame.shape[1], int(0.5 * frame.shape[0])), (255, 0, 0), 2)
    frame = frame[0:int(0.8 * frame.shape[0]),
             int(0.2 * frame.shape[1]):frame.shape[1]]
    height, width, _ = frame.shape
    cv2.imshow('original', frame)

    fgmask = bgModel.apply(frame, 0, 0)
    kernel = np.ones((3, 3), np.uint8)
    fgmask = cv2.erode(fgmask, kernel, iterations=1)
    fgmask = cv2.bitwise_and(frame, frame, mask=fgmask)
    cv2.imshow('mask', fgmask)

    gray = cv2.cvtColor(fgmask, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (41, 41), 0)
    cv2.imshow('blur', blur)

    ret, thresh = cv2.threshold(blur, 6, 255, cv2.THRESH_BINARY)
    cv2.imshow('ori', thresh)

    thresh1 = copy.deepcopy(thresh)
    image ,contours, hierarchy = cv2.findContours(thresh1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    length = len(contours)
    new = contours
    maxArea = -1
    if length > 0:
        for i in range(length):  # find the biggest contour (according to area)
            temp = contours[i]
            area = cv2.contourArea(temp)
            if area > maxArea:
                maxArea = area
                ci = i

        res = contours[ci]
        min = 1000
        minpoint = (0,0)
        for j in res:
            if j[0][1] < min:
                min = j[0][1]
                minpoint = (j[0][0], j[0][1])
        hull = cv2.convexHull(res)
        drawing = np.zeros(fgmask.shape, np.uint8)
        cv2.drawContours(drawing, [res], 0, (0, 255, 0), 2)
        cv2.drawContours(drawing, [hull], 0, (0, 0, 255), 3)
        isFinishCal, cnt = calculateFingers(res, drawing)
        cv2.imshow('output', drawing)
        #print (min)
        if (enabled and cnt < 3):
            win32api.SetCursorPos((2*minpoint[0], 2*minpoint[1]))

            if (cnt == 1):
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 4*minpoint[0], 4*minpoint[1], 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 4*minpoint[0], 4*minpoint[1], 0, 0)


    k = cv2.waitKey(10)
    if k == ord('b'):
        bgModel = cv2.createBackgroundSubtractorMOG2(0, 50)
    if k == ord('e'):
        enabled = not enabled
