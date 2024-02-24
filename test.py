import cv2
import mediapipe as mp
import numpy as np
import streamlit as st
import pyttsx3
import threading
import time

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def calculateangle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle

def speak_counter_threaded(counter):
    def speak():
        engine = pyttsx3.init()
        engine.say(f"The count is {counter}")
        engine.runAndWait()

    # Create a thread for text-to-speech
    threading.Thread(target=speak).start()

def main():
    counter = 0
    stage = ""
    warning = ""
    last_speak_time = time.time()

    # Request camera permission
    st.title("Camera Permission")
    st.write("Please grant camera permission to proceed.")
    st.write("When ready, click on the button below to start the application.")
    start_button = st.button("Start Application")

    if start_button:
        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            st.title("Live Video Feed")
            cap = cv2.VideoCapture(0)

            if not cap.isOpened():
                st.error("Unable to open the camera. Please check your camera connection.")

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            video_placeholder = st.empty()
            col1, col2 = st.columns(2)

            # Create placeholders outside the loop
            with col1:
                st.markdown("Count")
                counter_display = st.empty()

            with col2:
                st.markdown("Stage")
                stage_display = st.empty()

            while True:
                ret, frame = cap.read()

                if not ret:
                    st.error("Error capturing frame. Please try restarting the app.")
                    break

                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False

                results = pose.process(image)

                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                try:
                    landmarks = results.pose_landmarks.landmark

                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                    angle = calculateangle(shoulder, elbow, wrist)

                    cv2.putText(image, str(angle),
                                tuple(np.multiply(elbow, [640, 480]).astype(int)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

                    if angle > 160:
                        stage = "down"
                    if angle < 30 and stage == "down":
                        stage = "up"
                        counter += 1
                        counter_display.write(counter)
                        # Speak only if at least 2 seconds have passed since the last speak
                        if time.time() - last_speak_time >= 2:
                            speak_counter_threaded(counter)
                            last_speak_time = time.time()
                    if angle < 20:
                        warning = "Too much bend, relax your arm"
                    elif angle > 179:
                        warning = "Far release, contract the muscle"
                    else:
                        warning = ""

                    stage_display.write(stage)

                except:
                    pass

                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                          mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))

                video_placeholder.image(image, channels="BGR", use_column_width=True)

            cap.release()

if __name__ == "__main__":
    main()
