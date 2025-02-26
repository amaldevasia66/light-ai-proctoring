import cv2
from utils.combined_detection import detect_cheating

camera = cv2.VideoCapture(0)
if not camera.isOpened():
    print("Failed to open camera.")
    exit()

while True:
    ret, frame = camera.read()
    if not ret:
        print("Failed to capture frame.")
        break

    # Process the frame to detect cheating
    gaze_cheating, lip_cheating = detect_cheating(frame)
    print("Gaze Cheating:", gaze_cheating, "Lip Cheating:", lip_cheating)

    # Display the frame with gaze/lip analysis results
    cv2.putText(frame, f"Gaze Cheating: {gaze_cheating}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Lip Cheating: {lip_cheating}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Video Feed", frame)

    # Exit if ESC is pressed
    if cv2.waitKey(1) & 0xFF == 27:
        print("Exiting...")
        break

camera.release()
cv2.destroyAllWindows()
