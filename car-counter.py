import serial
import time
import cv2, cvzone, math, numpy as np
from ultralytics import YOLO
from sort import *

# Connect to Arduino
arduino = serial.Serial('COM3', 9600, timeout=1)   # change COM port if needed

model = YOLO("../Yolo-Weights/yolov8n.pt")
cap = cv2.VideoCapture("LaneTraffic.mp4")
mask = cv2.imread("final_mask.png")

tracker = Sort(max_age=40, min_hits=3, iou_threshold=0.3)

# Lane detection lines
limitsN_S = [400, 450, 570, 450]   # North-South
limitsE   = [580, 450, 710, 450]   # East
limitsW   = [720, 450, 870, 450]   # West

# Car counts
totalCountN_S, totalCountE, totalCountW = [], [], []

# Current active GREEN direction from Arduino
activeGreen = "NS"

# Flag for ambulance override
ambulance_override = False
ambulance_lane = None

while True:
    success, img = cap.read()
    if not success:
        break
    imgRegion = cv2.bitwise_and(img, mask)

    # ---- Read Arduino light status ----
    if arduino.in_waiting and not ambulance_override:   # skip Arduino messages during override
        msg = arduino.readline().decode().strip()
        if msg.startswith("ACTIVE:"):
            activeGreen = msg.split(":")[1]  # "NS" or "EW"
            # Reset counts for green lanes
            if activeGreen == "NS":
                totalCountN_S = []
            elif activeGreen == "EW":
                totalCountE, totalCountW = [], []

    # ---- Detection ----
    results = model(imgRegion, stream=True)
    detections = np.empty((0, 5))

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            label = model.names[cls]

            if label in ["car", "truck", "bus", "motorbike", "ambulance"]:
                detections = np.vstack((detections, [x1, y1, x2, y2, conf]))

    resultsTracker = tracker.update(detections)

    # ---- Default line colors (RED by default) ----
    line_color_NS = (0, 0, 255)
    line_color_E  = (0, 0, 255)
    line_color_W  = (0, 0, 255)

    # ---- Counting & Drawing ----
    ambulance_detected = False

    for x1, y1, x2, y2, Id in resultsTracker:
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        w, h = x2 - x1, y2 - y1
        cx, cy = x1 + w // 2, y1 + h // 2

        # Draw bounding box + ID
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cvzone.putTextRect(img, f'ID {int(Id)}', (x1, y1 - 10), scale=0.8, thickness=2)

        # Identify object class again
        label = "vehicle"
        for r in results:
            for box in r.boxes:
                bx1, by1, bx2, by2 = map(int, box.xyxy[0])
                if abs(bx1 - x1) < 10 and abs(by1 - y1) < 10:  # match
                    label = model.names[int(box.cls[0])]
                    break

        cvzone.putTextRect(img, label, (x1, y2 + 20), scale=0.7, thickness=1, colorR=(0, 0, 255))

        # ---- Ambulance Priority ----
        if label == "ambulance":
            ambulance_detected = True
            # Detect lane of ambulance
            if limitsN_S[0] < cx < limitsN_S[2]:
                ambulance_lane = "NS"
            elif limitsE[0] < cx < limitsE[2]:
                ambulance_lane = "E"
            elif limitsW[0] < cx < limitsW[2]:
                ambulance_lane = "W"

        # ---- Normal Vehicle Counting ----
        if not ambulance_override:
            if activeGreen != "NS":   # NS is RED
                if limitsN_S[0] < cx < limitsN_S[2] and limitsN_S[1]-15 < cy < limitsN_S[3]+15:
                    line_color_NS = (0, 255, 0)  # Green when vehicle detected
                    if Id not in totalCountN_S:
                        totalCountN_S.append(Id)

            if activeGreen != "EW":   # EW is RED
                if limitsE[0] < cx < limitsE[2] and limitsE[1]-15 < cy < limitsE[3]+15:
                    line_color_E = (0, 255, 0)
                    if Id not in totalCountE:
                        totalCountE.append(Id)

                if limitsW[0] < cx < limitsW[2] and limitsW[1]-15 < cy < limitsW[3]+15:
                    line_color_W = (0, 255, 0)
                    if Id not in totalCountW:
                        totalCountW.append(Id)

    # ---- Ambulance Override Mode ----
    if ambulance_detected:
        ambulance_override = True
        if ambulance_lane:
            data = f"AMBULANCE:{ambulance_lane}\n"
            arduino.write(data.encode())
            print("Sent:", data.strip())

    else:
        ambulance_override = False
        # ---- Normal Mode: Send counts ----
        data = f"N:{len(totalCountN_S)} S:{len(totalCountN_S)} E:{len(totalCountE)} W:{len(totalCountW)}\n"
        arduino.write(data.encode())
        print("Sent:", data.strip())

    # ---- Draw Counting Lines ----
    cv2.line(img, (limitsN_S[0], limitsN_S[1]), (limitsN_S[2], limitsN_S[3]), line_color_NS, 3)
    cv2.line(img, (limitsE[0], limitsE[1]), (limitsE[2], limitsE[3]), line_color_E, 3)
    cv2.line(img, (limitsW[0], limitsW[1]), (limitsW[2], limitsW[3]), line_color_W, 3)

    # ---- Display ----
    cvzone.putTextRect(img, f'N/S Count: {len(totalCountN_S)}', (50, 50))
    cvzone.putTextRect(img, f'E Count: {len(totalCountE)}', (50, 100))
    cvzone.putTextRect(img, f'W Count: {len(totalCountW)}', (50, 150))

    if ambulance_override and ambulance_lane:
        cvzone.putTextRect(img, f'🚨 Ambulance Detected! Priority to {ambulance_lane}', (300, 50),
                           scale=1, thickness=2, colorR=(0, 0, 255))

    cv2.imshow("Traffic", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
