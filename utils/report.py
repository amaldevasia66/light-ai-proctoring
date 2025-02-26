from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Function to generate the report
def generate_report(filename, student_name, roll_number, answers, cheating_instances):
    print(f"Generating report for {student_name} ({roll_number})")
    print(f"Cheating instances: {cheating_instances}")

    # Define variables for cooldown and threshold
    COOLDOWN_PERIOD = 5  # Seconds after a cheating instance before it can be reported again
    CHEATING_THRESHOLD = 7  # Seconds for which the movement must persist for it to be considered cheating

    # Sort instances by timestamp to ensure chronological order
    cheating_instances.sort(key=lambda x: x['timestamp'])

    # List to hold filtered cheating instances (ones that meet the 7 second rule)
    filtered_instances = []
    last_reported_time = {"Lip Movement": None, "Gaze Movement": None}  # Dictionary to track cooldown for each type
    ongoing_instances = {"Lip Movement": None, "Gaze Movement": None}  # To track if the same type persists for 7 seconds

    for instance in cheating_instances:
        current_time = datetime.strptime(instance['timestamp'], '%Y-%m-%d %H:%M:%S')
        cheating_type = instance['type']

        # Track ongoing instances for each type of cheating
        if ongoing_instances[cheating_type] is None:
            ongoing_instances[cheating_type] = current_time
        elif (current_time - ongoing_instances[cheating_type]).seconds >= CHEATING_THRESHOLD:
            # If the cheating type persists for 7 seconds, consider it for reporting
            if last_reported_time[cheating_type] is None or (current_time - last_reported_time[cheating_type]).seconds >= COOLDOWN_PERIOD:
                filtered_instances.append(instance)
                last_reported_time[cheating_type] = current_time  # Update last reported time
            ongoing_instances[cheating_type] = None  # Reset the ongoing instance after reporting
        else:
            ongoing_instances[cheating_type] = current_time  # Continue tracking the ongoing instance

    # Initialize PDF canvas
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Title and student details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 40, f"Cheating Report for {student_name} ({roll_number})")
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 60, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Answers section
    c.drawString(100, height - 100, "Answers Submitted:")
    y_position = height - 120
    for question, answer in answers.items():
        c.drawString(100, y_position, f"{question}: {answer}")
        y_position -= 20

    # Cheating instances section
    c.drawString(100, y_position - 20, "Cheating Instances:")
    if filtered_instances:
        for instance in filtered_instances:
            y_position -= 20
            c.drawString(100, y_position, f"{instance['timestamp']} - {instance['type']}")
    else:
        c.drawString(100, y_position - 40, "No cheating detected.")

    c.save()
