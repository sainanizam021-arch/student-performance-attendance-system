
import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

DB = Path(__file__).parent / "student_system.db"

st.set_page_config(page_title="Student Performance & Attendance", page_icon="🎓", layout="wide")

def get_conn():
    return sqlite3.connect(DB)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        semester INTEGER NOT NULL,
        email TEXT
    );
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL
    );
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        total_classes INTEGER NOT NULL DEFAULT 0,
        present_classes INTEGER NOT NULL DEFAULT 0,
        UNIQUE(student_id, subject_id),
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(subject_id) REFERENCES subjects(id)
    );
    CREATE TABLE IF NOT EXISTS marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        internal REAL DEFAULT 0,
        assignment REAL DEFAULT 0,
        exam REAL DEFAULT 0,
        UNIQUE(student_id, subject_id),
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(subject_id) REFERENCES subjects(id)
    );
    """)
    conn.commit()
    conn.close()

def seed_data():
    conn = get_conn()
    cur = conn.cursor()
    students = [
        ("CS001","Anu Krishnan","CSE",5,"anu@example.com"),
        ("CS002","Rahul Raj","CSE",5,"rahul@example.com"),
        ("CS003","Fathima P","CSE",5,"fathima@example.com"),
        ("CS004","Arjun S","CSE",5,"arjun@example.com"),
        ("CS005","Meera Nair","CSE",5,"meera@example.com"),
        ("CS006","Nikhil K","CSE",5,"nikhil@example.com"),
    ]
    subjects = [
        ("Database Management Systems","CS501"),
        ("Artificial Intelligence","CS502"),
        ("Computer Networks","CS503"),
        ("Operating Systems","CS504"),
    ]
    cur.executemany("INSERT OR IGNORE INTO students(roll_no,name,department,semester,email) VALUES(?,?,?,?,?)", students)
    cur.executemany("INSERT OR IGNORE INTO subjects(name,code) VALUES(?,?)", subjects)
    conn.commit()

    srows = cur.execute("SELECT id, roll_no FROM students").fetchall()
    subrows = cur.execute("SELECT id, code FROM subjects").fetchall()
    att_values = {
        "CS001":[(42,39),(40,34),(38,36),(40,35)],
        "CS002":[(42,28),(40,31),(38,29),(40,30)],
        "CS003":[(42,36),(40,37),(38,34),(40,38)],
        "CS004":[(42,33),(40,30),(38,32),(40,31)],
        "CS005":[(42,40),(40,38),(38,37),(40,39)],
        "CS006":[(42,29),(40,27),(38,30),(40,28)],
    }
    mark_values = {
        "CS001":[(18,9,52),(17,9,50),(19,8,54),(16,9,49)],
        "CS002":[(13,7,39),(14,8,42),(12,7,40),(13,8,38)],
        "CS003":[(19,10,58),(18,10,56),(18,9,55),(19,10,57)],
        "CS004":[(16,8,47),(15,8,44),(16,8,46),(15,9,45)],
        "CS005":[(20,10,60),(19,10,59),(20,9,58),(19,10,60)],
        "CS006":[(12,7,36),(13,6,38),(14,7,37),(12,7,35)],
    }
    for sid, roll in srows:
        for i, (subid, _) in enumerate(subrows):
            total, present = att_values[roll][i]
            cur.execute("""INSERT OR IGNORE INTO attendance
                (student_id,subject_id,total_classes,present_classes) VALUES(?,?,?,?)""",
                (sid,subid,total,present))
            internal, assignment, exam = mark_values[roll][i]
            cur.execute("""INSERT OR IGNORE INTO marks
                (student_id,subject_id,internal,assignment,exam) VALUES(?,?,?,?,?)""",
                (sid,subid,internal,assignment,exam))
    conn.commit()
    conn.close()

def query_df(sql, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

init_db()
seed_data()

st.title("🎓 Student Performance & Attendance Management System")
st.caption("A simple academic dashboard for managing students, attendance and marks.")

with st.sidebar:
    st.header("Navigation")
    page = st.radio("Go to", ["Dashboard","Students","Attendance","Marks","Student Profile"])
    st.divider()
    st.info("Demo database includes sample CSE students and subjects.")

if page == "Dashboard":
    students = query_df("SELECT * FROM students")
    att = query_df("""SELECT s.roll_no,s.name,
        SUM(a.present_classes)*100.0/SUM(a.total_classes) attendance
        FROM students s JOIN attendance a ON s.id=a.student_id
        GROUP BY s.id""")
    marks = query_df("""SELECT s.roll_no,s.name,
        AVG(m.internal+m.assignment+m.exam) avg_mark
        FROM students s JOIN marks m ON s.id=m.student_id
        GROUP BY s.id""")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Students", len(students))
    c2.metric("Average Attendance", f"{att.attendance.mean():.1f}%")
    c3.metric("Average Mark", f"{marks.avg_mark.mean():.1f}/100")
    c4.metric("Low Attendance", int((att.attendance < 75).sum()))

    st.subheader("📊 Student Performance")
    chart_df = marks.merge(att[["roll_no","attendance"]], on="roll_no")
    chart_df = chart_df[["name","avg_mark","attendance"]].set_index("name")
    st.bar_chart(chart_df)

    st.subheader("⚠️ Performance Alerts")
    alerts = []
    for _, r in chart_df.reset_index().iterrows():
        reasons=[]
        if r["attendance"] < 75: reasons.append(f"attendance {r['attendance']:.0f}%")
        if r["avg_mark"] < 50: reasons.append(f"average mark {r['avg_mark']:.0f}")
        if reasons: alerts.append(f"**{r['name']}** — " + ", ".join(reasons))
    if alerts:
        for a in alerts: st.warning(a)
    else:
        st.success("No students currently meet the alert conditions.")

elif page == "Students":
    st.header("👨‍🎓 Student Management")
    df = query_df("SELECT roll_no,name,department,semester,email FROM students ORDER BY roll_no")
    st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("➕ Add Student"):
        with st.form("add_student"):
            col1,col2 = st.columns(2)
            roll = col1.text_input("Roll number")
            name = col2.text_input("Name")
            dept = col1.text_input("Department", "CSE")
            sem = col2.number_input("Semester",1,8,5)
            email = st.text_input("Email")
            submitted = st.form_submit_button("Add Student")
            if submitted:
                try:
                    conn=get_conn()
                    conn.execute("INSERT INTO students(roll_no,name,department,semester,email) VALUES(?,?,?,?,?)",(roll,name,dept,sem,email))
                    conn.commit(); conn.close()
                    st.success("Student added. Refresh the page.")
                except sqlite3.IntegrityError:
                    st.error("Roll number already exists.")

elif page == "Attendance":
    st.header("📅 Attendance Management")
    students = query_df("SELECT id,roll_no,name FROM students ORDER BY roll_no")
    subjects = query_df("SELECT id,name,code FROM subjects ORDER BY code")
    student = st.selectbox("Student", students["roll_no"]+" - "+students["name"])
    subject = st.selectbox("Subject", subjects["code"]+" - "+subjects["name"])
    sid = int(students.loc[(students["roll_no"]+" - "+students["name"])==student,"id"].iloc[0])
    subid = int(subjects.loc[(subjects["code"]+" - "+subjects["name"])==subject,"id"].iloc[0])
    existing = query_df("SELECT total_classes,present_classes FROM attendance WHERE student_id=? AND subject_id=?",(sid,subid))
    total_default = int(existing.iloc[0]["total_classes"]) if len(existing) else 0
    present_default = int(existing.iloc[0]["present_classes"]) if len(existing) else 0
    with st.form("attendance"):
        total = st.number_input("Total classes",0,500,total_default)
        present = st.number_input("Present classes",0,500,present_default)
        save = st.form_submit_button("Save Attendance")
        if save:
            if present > total:
                st.error("Present classes cannot exceed total classes.")
            else:
                conn=get_conn()
                conn.execute("""INSERT INTO attendance(student_id,subject_id,total_classes,present_classes)
                    VALUES(?,?,?,?) ON CONFLICT(student_id,subject_id)
                    DO UPDATE SET total_classes=excluded.total_classes,present_classes=excluded.present_classes""",(sid,subid,total,present))
                conn.commit(); conn.close()
                st.success("Attendance saved.")
    if total_default:
        st.metric("Attendance", f"{present_default/total_default*100:.1f}%")

    report = query_df("""SELECT s.roll_no,s.name,sub.code,sub.name subject,
        a.total_classes,a.present_classes,
        ROUND(a.present_classes*100.0/a.total_classes,1) attendance
        FROM attendance a JOIN students s ON s.id=a.student_id
        JOIN subjects sub ON sub.id=a.subject_id
        ORDER BY s.roll_no,sub.code""")
    st.dataframe(report,use_container_width=True,hide_index=True)

elif page == "Marks":
    st.header("📝 Marks Management")
    students = query_df("SELECT id,roll_no,name FROM students ORDER BY roll_no")
    subjects = query_df("SELECT id,name,code FROM subjects ORDER BY code")
    student = st.selectbox("Student", students["roll_no"]+" - "+students["name"])
    subject = st.selectbox("Subject", subjects["code"]+" - "+subjects["name"])
    sid = int(students.loc[(students["roll_no"]+" - "+students["name"])==student,"id"].iloc[0])
    subid = int(subjects.loc[(subjects["code"]+" - "+subjects["name"])==subject,"id"].iloc[0])
    existing = query_df("SELECT internal,assignment,exam FROM marks WHERE student_id=? AND subject_id=?",(sid,subid))
    vals = existing.iloc[0] if len(existing) else pd.Series({"internal":0,"assignment":0,"exam":0})
    with st.form("marks"):
        c1,c2,c3 = st.columns(3)
        internal=c1.number_input("Internal /20",0.0,20.0,float(vals["internal"]))
        assignment=c2.number_input("Assignment /10",0.0,10.0,float(vals["assignment"]))
        exam=c3.number_input("Exam /70",0.0,70.0,float(vals["exam"]))
        save=st.form_submit_button("Save Marks")
        if save:
            conn=get_conn()
            conn.execute("""INSERT INTO marks(student_id,subject_id,internal,assignment,exam)
                VALUES(?,?,?,?,?) ON CONFLICT(student_id,subject_id)
                DO UPDATE SET internal=excluded.internal,assignment=excluded.assignment,exam=excluded.exam""",
                (sid,subid,internal,assignment,exam))
            conn.commit(); conn.close()
            st.success("Marks saved.")
    report=query_df("""SELECT s.roll_no,s.name,sub.code,sub.name subject,
        m.internal,m.assignment,m.exam,
        ROUND(m.internal+m.assignment+m.exam,1) total
        FROM marks m JOIN students s ON s.id=m.student_id
        JOIN subjects sub ON sub.id=m.subject_id
        ORDER BY s.roll_no,sub.code""")
    st.dataframe(report,use_container_width=True,hide_index=True)

elif page == "Student Profile":
    st.header("👤 Student Profile")
    students = query_df("SELECT id,roll_no,name,department,semester,email FROM students ORDER BY roll_no")
    choice=st.selectbox("Select student", students["roll_no"]+" - "+students["name"])
    roll=choice.split(" - ")[0]
    s=students[students.roll_no==roll].iloc[0]
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Name",s["name"])
    c2.metric("Roll No",s["roll_no"])
    c3.metric("Department",s["department"])
    c4.metric("Semester",int(s["semester"]))
    st.write(f"**Email:** {s['email'] or 'Not provided'}")

    profile=query_df("""SELECT sub.code,sub.name subject,
        ROUND(m.internal+m.assignment+m.exam,1) mark,
        ROUND(a.present_classes*100.0/a.total_classes,1) attendance
        FROM students s JOIN subjects sub
        LEFT JOIN marks m ON m.student_id=s.id AND m.subject_id=sub.id
        LEFT JOIN attendance a ON a.student_id=s.id AND a.subject_id=sub.id
        WHERE s.roll_no=? ORDER BY sub.code""",(roll,))
    st.dataframe(profile,use_container_width=True,hide_index=True)
    avg_mark=profile["mark"].dropna().mean()
    avg_att=profile["attendance"].dropna().mean()
    c1,c2=st.columns(2)
    c1.metric("Overall Average Mark", f"{avg_mark:.1f}/100")
    c2.metric("Overall Attendance", f"{avg_att:.1f}%")
    st.subheader("Subject-wise comparison")
    st.bar_chart(profile.set_index("code")[["mark","attendance"]])
    if avg_att < 75 or avg_mark < 50:
        st.error("Performance Alert: this student needs attention based on the demo thresholds.")
    else:
        st.success("Performance status: satisfactory based on the demo thresholds.")
