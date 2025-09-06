import requests
import json
import math
from flask import Flask, render_template, request, redirect, url_for, session
from collections import defaultdict
from bs4 import BeautifulSoup
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ankit-prajapati-secret-key'

# --- Helper Function to Convert Time ---
def time_to_minutes(time_str):
    try:
        dt_object = datetime.strptime(time_str.strip(), '%H:%M')
        return dt_object.hour * 60 + dt_object.minute
    except (ValueError, TypeError):
        return 0

# --- API Fetching Functions ---
def authenticate_and_get_token(username, password):
    login_url = "https://abes.platform.simplifii.com/api/v1/admin/authenticate"
    payload = {'username': username, 'password': password}
    headers = {'User-Agent': 'Mozilla/5.0','Referer': 'https://abes.web.simplifii.com/index.php/login','Origin': 'https://abes.web.simplifii.com'}
    try:
        response = requests.post(login_url, data=payload, headers=headers)
        response.raise_for_status()
        login_data = response.json()
        if login_data.get("status") == 1:
            return (True, login_data["token"])
        else:
            return (False, login_data.get("response", "Invalid credentials"))
    except Exception as e:
        return (False, f"Authentication failed: {e}")

# In app.py, find this function and update it
def fetch_attendance_data(token):
    """Fetches attendance and course data using a token."""
    url = "https://abes.platform.simplifii.com/api/v1/custom/getCFMappedWithStudentID?embed_attendance_summary=1"
    headers = {'Authorization': f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get("response", {}).get("data", [])
        processed_subjects = []
        for subj in data:
            cdata = subj.get("cdata", {})
            att = subj.get("attendance_summary", {})
            processed_subjects.append({
                'code': cdata.get("course_code", ""),
                'name': cdata.get("course_name", "").replace("\r\n", " ").strip(),
                'faculty': subj.get("faculty_name", "N/A"), # <-- ADD THIS LINE
                'total': att.get("Total", 0),
                'present': att.get("Present", 0),
                'absent': att.get("Absent", att.get("Total", 0) - att.get("Present", 0)),
                'percent': att.get("Percent", "0%")
            })
        return (True, processed_subjects)
    except Exception as e:
        return (False, f"Could not fetch attendance data: {e}")
    url = "https://abes.platform.simplifii.com/api/v1/custom/getCFMappedWithStudentID?embed_attendance_summary=1"
    headers = {'Authorization': f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get("response", {}).get("data", [])
        processed_subjects = []
        for subj in data:
            cdata = subj.get("cdata", {})
            att = subj.get("attendance_summary", {})
            processed_subjects.append({
                'code': cdata.get("course_code", ""),'name': cdata.get("course_name", "").replace("\r\n", " ").strip(),
                'total': att.get("Total", 0),'present': att.get("Present", 0),
                'absent': att.get("Absent", att.get("Total", 0) - att.get("Present", 0)),'percent': att.get("Percent", "0%")
            })
        return (True, processed_subjects)
    except Exception as e:
        return (False, f"Could not fetch attendance data: {e}")

def fetch_schedule_data(token):
    url = "https://abes.platform.simplifii.com/api/v1/custom/getMyScheduleStudent"
    headers = {'Authorization': f"Bearer {token}"}
    api_params = {'format': 'Y-m-d'}
    try:
        response = requests.get(url, headers=headers, params=api_params)
        response.raise_for_status()
        data = response.json().get("response", {}).get("data", [])

        if not data or len(data) < 2:
            return (True, {})

        header = data[0]
        date_key_to_day_name = {}
        full_day_names = {"Mon": "Monday","Tue": "Tuesday","Wed": "Wednesday","Thu": "Thursday","Fri": "Friday","Sat": "Saturday","Sun": "Sunday"}
        for i in range(1, 32):
            date_key = f'c{i}'
            if date_key in header and header[date_key]:
                day_html = header[date_key]
                soup = BeautifulSoup(day_html, 'html.parser')
                day_abbr = soup.get_text().strip()
                date_key_to_day_name[date_key] = full_day_names.get(day_abbr, day_abbr)

        schedule_by_day = defaultdict(list)
        subjects = data[1:]
        for subject_info in subjects:
            subject_name = subject_info.get("course_name", "N/A")
            faculty_name = subject_info.get("faculty_name", "N/A")
            for date_key, day_name in date_key_to_day_name.items():
                if subject_info.get(date_key) and isinstance(subject_info.get(date_key), str):
                    time_html = subject_info[date_key]
                    soup = BeautifulSoup(time_html, 'html.parser')
                    time_slots = [div.text.strip() for div in soup.find_all('div')]
                    for time in time_slots:
                        if '-' in time:
                            start_str, end_str = time.split(' - ')
                            schedule_by_day[day_name].append({
                                'start_time': start_str.strip(),'end_time': end_str.strip(),
                                'subject': subject_name,'faculty': faculty_name
                            })
        return (True, schedule_by_day)
    except Exception as e:
        return (False, f"Could not process schedule data: {e}")

# --- Web Page Routes ---
@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
# In app.py, find the login function and update this one line
@app.route("/login", methods=["GET", "POST"])
def login():
    if 'auth_token' in session:
        return redirect(url_for('show_dashboard')) # Change this if you have an index
    error = None
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        success, token_or_error = authenticate_and_get_token(username, password)
        if success:
            session['auth_token'] = token_or_error
            return redirect(url_for('show_dashboard')) # <-- CHANGE THIS LINE
        else:
            error = token_or_error
    return render_template('login.html', error=error)


    if 'auth_token' in session:
        return redirect(url_for('show_attendance'))
    error = None
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        success, token_or_error = authenticate_and_get_token(username, password)
        if success:
            session['auth_token'] = token_or_error
            return redirect(url_for('show_attendance'))
        else:
            error = token_or_error
    return render_template('login.html', error=error)

@app.route("/attendance")
def show_attendance():
    if 'auth_token' not in session:
        return redirect(url_for('login'))
    
    success, subjects_or_error = fetch_attendance_data(session['auth_token'])
    if not success:
        return render_template('error.html', message=subjects_or_error)

    subjects = subjects_or_error
    for subj in subjects:
        if subj['total'] > 0:
            if (subj['present'] / subj['total']) >= 0.75:
                bunks_allowed = math.floor((subj['present'] / 0.75) - subj['total'])
                subj['bunk_status'] = f"You can miss the next <strong>{bunks_allowed}</strong> classes."
                subj['status_color'] = "green"
            else:
                classes_needed = math.ceil((0.75 * subj['total'] - subj['present']) / 0.25)
                subj['bunk_status'] = f"You need to attend the next <strong>{classes_needed}</strong> classes to reach 75%."
                subj['status_color'] = "red"
        else:
             subj['bunk_status'] = "N/A"; subj['status_color'] = ""

    total_subject_data = next((s for s in subjects if s['code'].lower() == 'total'), None)
    individual_subjects_data = [s for s in subjects if s['code'].lower() != 'total']
    
    return render_template('attendance.html', total_subject=total_subject_data, individual_subjects=individual_subjects_data)

@app.route("/schedule")
def show_schedule():
    if 'auth_token' not in session:
        return redirect(url_for('login'))
        
    success, schedule_or_error = fetch_schedule_data(session['auth_token'])
    if not success:
        return render_template('error.html', message=schedule_or_error)

    schedule = schedule_or_error
    
    # Define your college's period start times
    period_times = ["08:50", "09:40", "10:40", "11:30", "12:20", "14:00", "14:50", "15:40"]
    
    # Process data into a grid-friendly format
    grid_schedule = defaultdict(dict)
    all_subjects = set()

    for day, classes in schedule.items():
        for class_item in classes:
            all_subjects.add(class_item['subject'])
            start_mins = time_to_minutes(class_item['start_time'])
            end_mins = time_to_minutes(class_item['end_time'])
            duration = end_mins - start_mins
            # Calculate how many 50-minute periods the class spans (e.g., a lab)
            class_item['row_span'] = round(duration / 50) if duration > 0 else 1
            grid_schedule[day][class_item['start_time']] = class_item

    # Assign colors to subjects
    colors = ["#4285F4", "#DB4437", "#F4B400", "#0F9D58", "#673AB7", "#E91E63", "#00BCD4", "#FF9800", "#3F51B5", "#9C27B0"]
    subject_colors = {subject: colors[i % len(colors)] for i, subject in enumerate(all_subjects)}

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    return render_template('schedule.html', 
                           schedule=grid_schedule, 
                           days=day_order,
                           periods=period_times,
                           colors=subject_colors)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

# In app.py, add this new function in the "Web Page Routes" section
@app.route("/dashboard")
def show_dashboard():
    if 'auth_token' not in session:
        return redirect(url_for('login'))
    
    # Fetch data for both attendance and schedule
    att_success, att_data = fetch_attendance_data(session['auth_token'])
    sch_success, sch_data = fetch_schedule_data(session['auth_token'])

    if not att_success or not sch_success:
        return render_template('error.html', message="Could not load all dashboard data.")

    # Get overall attendance info
    overall_attendance = next((s for s in att_data if s['code'].lower() == 'total'), None)
    
    # Get total number of courses
    total_courses = len([s for s in att_data if s['code'].lower() != 'total'])

    # Get today's schedule
    today_day_name = datetime.now().strftime('%A')
    todays_classes = sch_data.get(today_day_name, [])

    return render_template('dashboard.html',
                           overall_att=overall_attendance,
                           total_courses=total_courses,
                           todays_classes=todays_classes,
                           today_name=today_day_name)

# In app.py, add this new function
@app.route("/courses")
def show_courses():
    if 'auth_token' not in session:
        return redirect(url_for('login'))
    
    success, courses_or_error = fetch_attendance_data(session['auth_token'])
    if not success:
        return render_template('error.html', message=courses_or_error)

    # Filter out the "Total" record as it's not a real course
    course_list = [c for c in courses_or_error if c['code'].lower() != 'total']
    
    return render_template('courses.html', courses=course_list)

# This function makes variables available to all templates automatically
@app.context_processor
def inject_global_vars():
    now = datetime.now()
    # Academic session usually starts around July.
    if now.month >= 7:
        start_year = now.year
        end_year = now.year + 1
    else:
        start_year = now.year - 1
        end_year = now.year

    return {
        'author_name': "Ankit Prajapati",
        'current_session': f"{start_year}-{end_year}"
    }

if __name__ == "__main__":
    app.run(debug=True)