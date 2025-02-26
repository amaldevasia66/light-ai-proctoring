import cv2
import time
from gaze_tracking import GazeTracking

gaze = GazeTracking()
webcam = cv2.VideoCapture(0)
not_center_start = None
alert_cooldown_start = None
alert_triggered = False
cooldown_time = 7

while True:
    # We get a new frame from the webcam
    _, frame = webcam.read()

    # We send this frame to GazeTracking to analyze it
    gaze.refresh(frame)

    frame = gaze.annotated_frame()
    text = ""

    if gaze.is_blinking():
        text = "Blinking"
    elif gaze.is_right():
        text = "Looking right"
    elif gaze.is_left():
        text = "Looking left"
    elif gaze.is_center():
        text = "Looking center"
    left_pupil = gaze.pupil_left_coords()
    right_pupil = gaze.pupil_right_coords()
    pupils_detected = left_pupil is not None and right_pupil is not None

    # Start the not-center timer if pupils are detected and user is not looking center
    if pupils_detected and not gaze.is_center():
        if not not_center_start:
            not_center_start = time.time()
    else:
        not_center_start = None  # Reset timer if pupils aren't detected or user looks center

    # Trigger cheating alert if user is not looking center for 7 seconds
    if (
        not_center_start
        and pupils_detected
        and (time.time() - not_center_start > 7)
    ):
        if not alert_triggered and (not alert_cooldown_start or time.time() - alert_cooldown_start > cooldown_time):
            print("Cheating Alert!")
            alert_triggered = True
            alert_cooldown_start = time.time()

    # Reset the alert after the cooldown
    if alert_cooldown_start and time.time() - alert_cooldown_start > cooldown_time:
        alert_triggered = False

    cv2.putText(frame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)


    cv2.putText(frame, "Left pupil:  " + str(left_pupil), (90, 130), cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)
    cv2.putText(frame, "Right pupil: " + str(right_pupil), (90, 165), cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)

    cv2.imshow("Demo", frame)

    if cv2.waitKey(1) == 27:
        break

webcam.release()
cv2.destroyAllWindows()