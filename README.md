# 🚦 TraffEase – Smart Traffic Light Control System  

**TraffEase** is a **computer vision–based smart traffic light system** designed to optimize signal timing at intersections. Using **OpenCV, YOLO-based vehicle detection, and Arduino-controlled lights**, the system dynamically allocates green light durations based on real-time traffic density.  

---

## 📌 Features  

- **Dynamic Signal Timing** – Lanes with heavier traffic (North-South or East-West) get longer green light durations.  
- **Vehicle Counting** – Cars are counted only when their lane has a **red signal**, ensuring accurate measurement of waiting vehicles. Counts reset to zero once the lane turns green.  
- **Priority Handling** – Detects **ambulances** in any lane and immediately overrides normal traffic to grant emergency clearance.  
- **Lane-specific Signals**:  
  - **Red** → Stop
  - **Yellow** → Wait/transition signal
  - **Green (Straight)** → Allows straight and left turns  
  - **Orange** → Allows right turns  

---

## ⚙️ System Architecture  

### 🔹 Computer Vision (Python + OpenCV + YOLO)  
- Detects and classifies vehicles (car, bus, truck, motorbike, ambulance).  
- Counts vehicles per lane (N/S/E/W).  
- Sends real-time counts and emergency alerts to Arduino via **Serial communication**.  

### 🔹 Traffic Light Control (Arduino)  
- Receives counts and decides signal durations dynamically:  
  - **Straight Green Duration:** `5–20s` depending on traffic load.  
  - **Right Turn Duration:** `4–10s` depending on traffic load.  
- Implements **all-red buffer time** between transitions for safety.  
- Executes **ambulance override mode** if an emergency vehicle is detected.  

---

## 🚀 How It Works  

1. **Python Side (Detection):**  
   - Reads live video feed or traffic footage.  
   - Applies YOLO-based object detection with **lane-specific masks**.  
   - Counts vehicles per lane (only during red light).  
   - Detects **ambulances** and triggers priority mode.  
   - Sends traffic counts or emergency signal to Arduino via serial port.  

2. **Arduino Side (Signal Control):**  
   - Reads counts sent from Python.  
   - Dynamically adjusts **green and right-turn durations** based on traffic density.  
   - Sends back the **active green signal status** so Python knows which lane to reset.  
   - If an ambulance is detected → immediately grants **15s green clearance** to that lane.  
