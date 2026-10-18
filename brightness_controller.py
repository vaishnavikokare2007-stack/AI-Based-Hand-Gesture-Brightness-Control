
import tkinter as tk
from tkinter import messagebox

import cv2
import mediapipe as mp
import screen_brightness_control as sbc

from PIL import Image, ImageTk
import math
import time


class BrightnessController:

    def __init__(self, root):
        self.root = root
        self.root.title("Hand Gesture Brightness Controller")
        self.root.geometry("800x700")
        self.root.resizable(False, False)
        self.root.configure(bg="#20232A")

        # Camera and application variables
        self.cap = None
        self.running = False
        self.hands = None
        self.photo = None

        self.current_brightness = None
        self.last_brightness_update = 0

        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils

        # ---------------- GUI TITLE ----------------
        title = tk.Label(
            root,
            text="Hand Gesture Brightness Controller",
            font=("Arial", 20, "bold"),
            bg="#20232A",
            fg="white"
        )
        title.pack(pady=15)

        subtitle = tk.Label(
            root,
            text="Control your screen brightness using your thumb and index finger",
            font=("Arial", 10),
            bg="#20232A",
            fg="#CCCCCC"
        )
        subtitle.pack(pady=3)

        # ---------------- BRIGHTNESS DISPLAY ----------------
        self.brightness_label = tk.Label(
            root,
            text="Brightness: --%",
            font=("Arial", 17, "bold"),
            bg="#20232A",
            fg="#61DAFB"
        )
        self.brightness_label.pack(pady=12)

        self.brightness_bar = tk.Scale(
            root,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            length=400,
            state="disabled",
            bg="#20232A",
            fg="white",
            troughcolor="#444444",
            highlightthickness=0
        )
        self.brightness_bar.set(50)
        self.brightness_bar.pack(pady=3)

        # ---------------- CAMERA DISPLAY ----------------
        self.camera_label = tk.Label(
            root,
            text="Camera is stopped\n\nClick Start Camera",
            font=("Arial", 15),
            bg="#111111",
            fg="white",
            width=70,
            height=18
        )
        self.camera_label.pack(pady=12)

        # ---------------- BUTTONS ----------------
        button_frame = tk.Frame(root, bg="#20232A")
        button_frame.pack(pady=8)

        self.start_button = tk.Button(
            button_frame,
            text="Start Camera",
            command=self.start_camera,
            font=("Arial", 11, "bold"),
            bg="#28A745",
            fg="white",
            width=15
        )
        self.start_button.grid(row=0, column=0, padx=8)

        self.stop_button = tk.Button(
            button_frame,
            text="Stop Camera",
            command=self.stop_camera,
            font=("Arial", 11, "bold"),
            bg="#DC3545",
            fg="white",
            width=15,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=8)

        self.exit_button = tk.Button(
            button_frame,
            text="Exit",
            command=self.close_app,
            font=("Arial", 11, "bold"),
            bg="#555555",
            fg="white",
            width=15
        )
        self.exit_button.grid(row=0, column=2, padx=8)

        # ---------------- STATUS ----------------
        self.status_label = tk.Label(
            root,
            text="Status: Ready",
            font=("Arial", 10),
            bg="#20232A",
            fg="#61DAFB"
        )
        self.status_label.pack(pady=8)

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    # --------------------------------------------------
    # START CAMERA
    # --------------------------------------------------
    def start_camera(self):
        if self.running:
            return

        self.status_label.config(
            text="Status: Opening camera...",
            fg="orange"
        )
        self.root.update_idletasks()

        # Try opening the default camera
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        # Fallback for systems where DirectShow fails
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            self.cap.release()
            self.cap = None

            self.status_label.config(
                text="Status: Camera could not be opened",
                fg="red"
            )

            messagebox.showerror(
                "Camera Error",
                "Unable to open the camera.\n\n"
                "Check that your webcam is connected and not being "
                "used by another application."
            )
            return

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        self.running = True

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self.status_label.config(
            text="Status: Camera running - Show your hand",
            fg="#28A745"
        )

        self.process_frame()

    # --------------------------------------------------
    # PROCESS CAMERA FRAMES
    # --------------------------------------------------
    def process_frame(self):
        if not self.running or self.cap is None:
            return

        success, frame = self.cap.read()

        if not success:
            self.status_label.config(
                text="Status: Cannot read camera frame",
                fg="red"
            )

            if self.running:
                self.root.after(100, self.process_frame)
            return

        # Mirror the image like a mirror
        frame = cv2.flip(frame, 1)

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:

                # Draw hand landmarks
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )

                # Thumb tip: landmark 4
                thumb = hand_landmarks.landmark[4]

                # Index finger tip: landmark 8
                index_finger = hand_landmarks.landmark[8]

                height, width, _ = frame.shape

                thumb_x = int(thumb.x * width)
                thumb_y = int(thumb.y * height)

                index_x = int(index_finger.x * width)
                index_y = int(index_finger.y * height)

                # Draw circles on the two fingertips
                cv2.circle(
                    frame,
                    (thumb_x, thumb_y),
                    10,
                    (255, 0, 255),
                    cv2.FILLED
                )

                cv2.circle(
                    frame,
                    (index_x, index_y),
                    10,
                    (255, 0, 255),
                    cv2.FILLED
                )

                # Calculate distance between fingertips
                distance = math.hypot(
                    index_x - thumb_x,
                    index_y - thumb_y
                )

                # Convert distance to brightness between 10 and 100
                brightness = int(
                    max(10, min(100, 10 + (distance / 2.0)))
                )

                cv2.line(
                    frame,
                    (thumb_x, thumb_y),
                    (index_x, index_y),
                    (0, 255, 0),
                    3
                )

                cv2.putText(
                    frame,
                    f"Brightness: {brightness}%",
                    (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

                # Update screen brightness every 0.4 seconds
                now = time.time()

                if now - self.last_brightness_update >= 0.4:
                    try:
                        sbc.set_brightness(brightness)

                        self.current_brightness = brightness
                        self.last_brightness_update = now

                        self.brightness_label.config(
                            text=f"Brightness: {brightness}%"
                        )

                        self.brightness_bar.set(brightness)

                        self.status_label.config(
                            text="Status: Brightness controlled by hand",
                            fg="#28A745"
                        )

                    except Exception as error:
                        print("Brightness control error:", error)

                        self.status_label.config(
                            text="Status: Brightness control unavailable",
                            fg="orange"
                        )

        else:
            cv2.putText(
                frame,
                "Show your hand to the camera",
                (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

            self.status_label.config(
                text="Status: Waiting for hand",
                fg="orange"
            )

        # Resize camera image for the GUI
        frame = cv2.resize(frame, (640, 360))

        # Convert image for Tkinter
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)

        self.photo = ImageTk.PhotoImage(image=image)

        self.camera_label.config(
            image=self.photo,
            text="",
            width=640,
            height=360
        )

        # Process the next frame
        if self.running:
            self.root.after(15, self.process_frame)

    # --------------------------------------------------
    # RELEASE CAMERA RESOURCES
    # --------------------------------------------------
    def release_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        if self.hands is not None:
            self.hands.close()
            self.hands = None

    # --------------------------------------------------
    # STOP CAMERA
    # --------------------------------------------------
    def stop_camera(self):
        self.running = False

        self.release_camera()

        self.camera_label.config(
            image="",
            text="Camera is stopped\n\nClick Start Camera",
            width=70,
            height=18
        )

        self.photo = None

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

        self.status_label.config(
            text="Status: Camera stopped",
            fg="orange"
        )

    # --------------------------------------------------
    # CLOSE APPLICATION
    # --------------------------------------------------
    def close_app(self):
        self.running = False
        self.release_camera()
        self.root.destroy()


# --------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------
if __name__ == "__main__":
    print("Starting Hand Gesture Brightness Controller...")

    root = tk.Tk()
    app = BrightnessController(root)

    print("Application window created.")

    root.mainloop()

