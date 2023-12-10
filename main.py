import tkinter as tk
import json
import threading
from email.mime.text import MIMEText
from smtplib import SMTP

# Function to load quiz data (questions and timer settings) from JSON file
def load_quiz_data(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data["questions"], data["timer_seconds"]

# Function to load email configuration from a separate JSON file
def load_email_config(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)

# Load questions, timer settings, and email configuration
questions, timer_seconds = load_quiz_data("questions.json")
email_config = load_email_config('email_config.json')
EMAIL_ADDRESS = email_config['email']
EMAIL_PASSWORD = email_config['password']

current_question = 0
user_answers = {}
user_details = {}
score = 0
total_marks = sum(question['marks'] for question in questions)

# Function to send an email
def send_email(details, quiz_score, marks_total):
    server = SMTP(host='smtp-mail.outlook.com', port=587)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    email_subject = "Quiz Results"
    email_body = (f"Name: {details['name']}\nReg No: {details['reg_no']}\n"
                  f"Final Score: {quiz_score}/{marks_total}")

    message = MIMEText(email_body)
    message['From'] = EMAIL_ADDRESS
    message['To'] = EMAIL_ADDRESS
    message['Subject'] = email_subject

    server.send_message(message)
    server.quit()

def thread_send_email(details, quiz_score, marks_total):
    email_thread = threading.Thread(target=send_email, args=(details, quiz_score, marks_total))
    email_thread.start()

def reset_quiz():
    global current_question, user_answers, score, user_details, timer_seconds
    current_question = 0
    user_answers = {}
    score = 0
    user_details = {'name': '', 'reg_no': ''}
    name_entry.delete(0, tk.END)
    reg_no_entry.delete(0, tk.END)
    welcome_frame.pack(fill='both', expand=True)
    quiz_frame.pack_forget()
    rules_frame.pack_forget()
    timer_seconds = load_quiz_data("questions.json")[1]  # Reset timer

def start_quiz():
    global user_details, user_answers, score, timer_seconds
    user_details['name'] = name_entry.get()
    user_details['reg_no'] = reg_no_entry.get()
    user_answers = {}
    score = 0
    if user_details['name'] and user_details['reg_no']:
        rules_frame.pack_forget()
        quiz_frame.pack(fill='both', expand=True)
        start_timer()
        show_question()

def show_question():
    global current_question, user_details, score
    if 0 <= current_question < len(questions):
        question = questions[current_question]
        question_label.config(text=f"Question {current_question + 1}: " + question["question"])
        for i, option_text in enumerate(question["options"]):
            option_buttons[i].config(text=option_text, state=tk.NORMAL,
                                     command=lambda opt=option_text: check_answer(opt, question["marks"]))
        back_button.config(state=tk.NORMAL if current_question > 0 else tk.DISABLED)
    else:
        finish_quiz()

def finish_quiz():
    global current_question
    question_label.config(text="Quiz Completed! Thank you for participating.")
    for btn in option_buttons:
        btn.config(state=tk.DISABLED)
    back_button.config(state=tk.DISABLED)
    exit_button.pack(side="bottom")
    thread_send_email(user_details, score, total_marks)
    reset_timer()

def check_answer(selected_option, marks):
    global current_question, score, user_answers
    user_answers[questions[current_question]["question"]] = selected_option
    if selected_option == questions[current_question]["answer"]:
        score += marks
    current_question += 1
    show_question()

def go_back():
    global current_question
    if current_question > 0:
        current_question -= 1
        show_question()

# Timer functions
def start_timer():
    countdown(timer_seconds)

def countdown(t):
    global current_question, timer_seconds
    mins, secs = divmod(t, 60)
    timer_label.config(text=f"Time Remaining: {mins:02d}:{secs:02d}")
    if t > 0:
        root.after(1000, countdown, t - 1)
    else:
        # Check the current question's answer before finishing
        if current_question < len(questions):
            selected_option = user_answers.get(questions[current_question]["question"])
            if selected_option == questions[current_question]["answer"]:
                score += questions[current_question]["marks"]
        finish_quiz()

def reset_timer():
    timer_label.config(text="")

if __name__ == "__main__":
    root = tk.Tk()
root.title("Offline Quiz Application")

# Set the application in fullscreen mode
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)  # Keep the window always on top

# Disable standard window close functionality and Alt+Tab
root.protocol("WM_DELETE_WINDOW", lambda: None)
root.bind("<Alt-Tab>", lambda e: None)

# Window size for rule text wrapping
window_width = root.winfo_screenwidth()
window_height = root.winfo_screenheight()

def toggle_rules_button(*args):
    if name_entry.get() and reg_no_entry.get():
        show_rules_button.config(state=tk.NORMAL)
    else:
        show_rules_button.config(state=tk.DISABLED)

def show_rules():
    welcome_frame.pack_forget()
    rules_frame.pack(fill='both', expand=True)

quiz_frame = tk.Frame(root)
question_label = tk.Label(quiz_frame, font=("Arial", 24), wraplength=window_width - 100)
question_label.pack(pady=(20, 40))
option_buttons = [tk.Button(quiz_frame, font=("Arial", 18), width=20, height=2, relief=tk.RAISED) for _ in range(4)]
for button in option_buttons:
    button.pack(pady=10)

back_button = tk.Button(quiz_frame, text="Back", font=("Arial", 14), command=go_back)
back_button.pack(side="bottom", fill=tk.X)

exit_button = tk.Button(quiz_frame, text="Exit", font=("Arial", 14), command=root.destroy)

timer_label = tk.Label(quiz_frame, font=("Arial", 16))
timer_label.pack(side="bottom", fill=tk.X)

welcome_frame = tk.Frame(root)
tk.Label(welcome_frame, text="Please enter your details", font=("Arial", 24)).pack(pady=20)
tk.Label(welcome_frame, text="Name:", font=("Arial", 18)).pack()
name_entry = tk.Entry(welcome_frame, font=("Arial", 18))
name_entry.pack(pady=10)
name_entry.bind("<KeyRelease>", toggle_rules_button)
tk.Label(welcome_frame, text="Registration Number:", font=("Arial", 18)).pack()
reg_no_entry = tk.Entry(welcome_frame, font=("Arial", 18))
reg_no_entry.pack(pady=10)
reg_no_entry.bind("<KeyRelease>", toggle_rules_button)
show_rules_button = tk.Button(welcome_frame, text="Show Rules", font=("Arial", 18), command=show_rules, state=tk.DISABLED)
show_rules_button.pack(pady=20)
error_label = tk.Label(welcome_frame, text="", font=("Arial", 18), fg="red")
error_label.pack()
welcome_frame.pack(fill='both', expand=True)

rules_frame = tk.Frame(root)
rules_text = ("1. The test has an allocated timer. If you run out of time, the test will submit itself automatically.\n\n"
              "2. You cannot minimize the window for the test, if you do so you'll have to give the test from the beginning.\n\n"
              "3. You can only close the test after you have completed it, you may go back to the previous questions provided you haven't attempted the final question, if you have attempted the final question, you cannot go back anymore.")
rules_label = tk.Label(rules_frame, text=rules_text, font=("Arial", 18), justify="left", wraplength=window_width - 100)
rules_label.pack(pady=20, padx=50, side="top", fill="both", expand=True)
next_button = tk.Button(rules_frame, text="Next", font=("Arial", 18), command=start_quiz)
next_button.pack(pady=20, side="bottom")
developer_label = tk.Label(root, text="Developed by Krish Gera",
                           font=("Arial Bold", 14),  # Larger, bold font
                           fg="black",  # Text color
                           bg="white",  # Background color
                           padx=10, pady=5)  # Padding for aesthetics
developer_label.pack(side="bottom", anchor="e", fill="x", expand=True)

root.mainloop()
