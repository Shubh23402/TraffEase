from ultralytics import YOLO
import cv2
import cvzone
import math
import time
from sort import *

cap = cv2.VideoCapture("../Videos/LaneTraffic.mp4")

# cap = cv2.VideoCapture("../Videos/motorbikes.mp4")  # For Video


model = YOLO("../Yolo-Weights/yolov8n.pt")

classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
              "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
              "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
              "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
              "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
              "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
              "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
              "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
              "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
              "teddy bear", "hair drier", "toothbrush"
              ]

prev_frame_time = 0
new_frame_time = 0

mask = cv2.imread("final_mask.png")

#Tracking
tracker = Sort(max_age = 40, min_hits = 3, iou_threshold=0.3)

limits1 = [400,450,570,450]
limits2 = [580,450,710,450]
limits3 = [720,450,870,450]

totalCount1 = []
totalCount2 = []
totalCount3 = []

while True:
    new_frame_time = time.time()
    success, img = cap.read()
    imgRegion = cv2.bitwise_and(img,mask)

    results = model(imgRegion, stream=True)

    detections = np.empty((0, 5))

    for r in results:
        boxes = r.boxes
        for box in boxes:
            # Bounding Box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            # cv2.rectangle(img,(x1,y1),(x2,y2),(255,0,255),3)
            w, h = x2 - x1, y2 - y1

            # Confidence
            conf = math.ceil((box.conf[0] * 100)) / 100
            # Class Name
            cls = int(box.cls[0])
            currentClass = classNames[cls]

            if currentClass == "car" or currentClass == "truck" or currentClass == "bus" or currentClass == "motorbike":
                #cvzone.putTextRect(img, f'{currentClass} {conf}', (max(0, x1), max(35, y1)), scale=0.6, thickness=1,offset=5)
               # cvzone.cornerRect(img, (x1, y1, w, h), l=10,rt = 5)
                currentArray = np.array([x1,y1,x2,y2,conf])
                detections = np.vstack((detections, currentArray))

    resultsTracker = tracker.update(detections)
    cv2.line(img, (limits1[0], limits1[1]), (limits1[2], limits1[3]), (0, 0, 255), 5)
    cv2.line(img, (limits2[0], limits2[1]), (limits2[2], limits2[3]), (0, 0, 255), 5)
    cv2.line(img, (limits3[0], limits3[1]), (limits3[2], limits3[3]), (0, 0, 255), 5)

    for result in resultsTracker:
        x1,y1,x2,y2,Id = result
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        #print(result)
        w, h = x2 - x1, y2 - y1
        cvzone.cornerRect(img, (x1, y1, w, h), l=10,rt = 2,colorR=(255,0,0))
        cvzone.putTextRect(img, f' {int(Id)}', (max(0, x1), max(35, y1)), scale=2, thickness=3,offset=10)

        cx,cy = x1+w//2,y1+h//2
        cv2.circle(img,(cx,cy),5,(255,0,0),cv2.FILLED)

        if limits1[0] < cx < limits1[2] and limits1[1]-15 < cy < limits1[3]+15:
            if totalCount1.count(Id) == 0:
                totalCount1.append(Id)
                cv2.line(img, (limits1[0], limits1[1]), (limits1[2], limits1[3]), (0, 255, 0), 5)

        if limits2[0] < cx < limits2[2] and limits2[1]-15 < cy < limits2[3]+10:
            if totalCount2.count(Id) == 0:
                totalCount2.append(Id)
                cv2.line(img, (limits2[0], limits2[1]), (limits2[2], limits2[3]), (0, 255, 0), 5)

        if limits3[0] < cx < limits3[2] and limits3[1]-15 < cy < limits3[3]+15:
            if totalCount3.count(Id) == 0:
                totalCount3.append(Id)
                cv2.line(img, (limits3[0], limits3[1]), (limits3[2], limits3[3]), (0, 255, 0), 5)

    cvzone.putTextRect(img, f' LaneCount(N and S): {len(totalCount1)}', (50, 50))
    cvzone.putTextRect(img, f' LaneCount(E): {len(totalCount2)}', (50, 100))
    cvzone.putTextRect(img, f' LaneCount(W): {len(totalCount3)}', (50, 150))

    data = f"N : {len(totalCount1)}  S : {len(totalCount1)}  E : {len(totalCount2)}  W : {len(totalCount3)}\n"

    # Display in terminal
    print(data.strip())

    # Send to Arduino
    #arduino.write(data.encode())

    fps = 1 / (new_frame_time - prev_frame_time)
    prev_frame_time = new_frame_time
    print(fps)

    cv2.imshow("Image", img)
    #cv2.imshow("ImageRegion", imgRegion)
    cv2.waitKey(1)