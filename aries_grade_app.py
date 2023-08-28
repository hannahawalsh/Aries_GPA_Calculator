import streamlit as st
import fitz
import re
import numpy as np

st.set_page_config("GPA Calculator", page_icon="aplus.jpg")

title_spot = st.empty()
title_spot.title("Aries Gradebook GPA Calculator")
text_area = st.container()
widgets = st.container()
file = st.file_uploader("Upload File", type="pdf", label_visibility="hidden")

if file is not None:
    show_grades = widgets.checkbox("Show Grades", False)
    pages = fitz.open(stream=file.read())

    # Get date of report
    date = pages[0].get_text().split("\n")[1]
    title_spot.subheader(f"Grades as of {date}")

    def get_GPA(letter_grades):
        # """ From a list of letter grades, get GPA """
        # letter_to_gpa = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
        # if letter_grades:
        #     return np.mean([letter_to_gpa[L] for L in letter_grades])
        # return 0.0
        if letter_grades:
            return np.mean([float(x) for x in letter_grades if float(x)])
        return 0.0

    # Get name, grades, and GPA of all students
    students = {}
    for page in pages:
        pagetext = page.get_text()
        if name_match := re.search(r"Report For (?P<name>.*?) \(", pagetext):
            name = name_match.group("name")
        else:
            continue

        grade_table = re.search(r"Overall(.*?)Signature", pagetext, re.S)
        if grade_table:
            grade_table = grade_table.group(1)
            classes = re.split(r"(?<=Missing Assignments\n\d)", grade_table)
            pattern = r"(?P<gpa>\d+\.?\d+)\s*(?P<grade>[A-F])?$"
            gpas = []
            letter_grades = []


            for c in classes:
                if not c.strip():
                    continue 
                m = re.search(pattern, c.split("\n")[2])
                if not m:
                    continue 
                gpa = float(m.group("gpa"))
                no_missings = c.endswith("0")
                if gpa or not no_missings:
                    # if gr := m.group("grade"):
                    gpas.append(gpa)
                    # grades.append(str(m.group("grade")) + f"({c[-1]})")
                    grades.append(m.group("grade"))

            mean_gpa = np.mean(gpas) if len(gpas) else "N/A"
            students[name] = {"GPA": mean_gpa, "grades": grades}

        for class_grade in grade_table.split("Missing Assignments")[:-1]:
            # search_string = r"[0-9]+([.][0-9]*)?\s+(?P<letter>[ABCDEFI])"
            search_string = r"(?P<gpa>[0-9]+([.][0-9]*)?)\s+[ABCDEFI]"
            grade = re.search(search_string, class_grade.split(" - ")[1])
            if grade:
                letter_grades.append(grade.group("gpa"))
        students[name] = {"GPA": get_GPA(letter_grades),
                          "grades": letter_grades}
    GPA_text = ""
    sorted_data = sorted(students.items(), key=lambda item: item[1]["GPA"], reverse=True)
    for student, info in {key: value for key, value in sorted_data}.items():
        GPA_text += f"**{student}**: {info['GPA']:.2f}"
        if show_grades:
            GPA_text += " (" + ", ".join([x for x in info["grades"] if x is not None]) + ")"
        GPA_text += "  \n"
    text_area.markdown(GPA_text)

    # Download
    file_name = f"grades_as_of_{date.replace(' ', '_').replace(',', '')}.txt"
    widgets.download_button("Download Results", GPA_text.replace("*", ""),
                             file_name=file_name)
