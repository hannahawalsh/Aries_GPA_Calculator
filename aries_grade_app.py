import streamlit as st
import PyPDF2
import re
import numpy as np
import pyperclip

st.set_page_config("GPA Calculator", page_icon="aplus.jpg")

title_spot = st.empty()
title_spot.title("Aries Gradebook GPA Calculator")
text_area = st.beta_container()
widgets = st.beta_container()
file = st.file_uploader("", type="pdf")

if file:
    show_grades = widgets.checkbox("Show Grades", False)
    copy_button = widgets.button("Copy to Clipboard")
    # reset_button = widgets.button("Reset")

    # Parse PDF Pages
    pages = []
    reader = PyPDF2.PdfFileReader(file)
    for i in range(reader.numPages):
        pages.append(reader.getPage(i).extractText())

    # Get date of report
    date = re.search(r"\)(.*?) Grade Summary",
                     pages[0]).group(1)
    title_spot.subheader(f"Grades as of {date}")

    def get_GPA(letter_grades):
        """ From a list of letter grades, get GPA """
        letter_to_gpa = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
        if letter_grades:
            return np.mean([letter_to_gpa[L] for L in letter_grades])
        return 0.0

    # Get name, grades, and GPA of all students
    students = {}
    for page in pages:
        name = re.search(r"Report For (.*?) \(", page).group(1)

        letter_grades = []
        grade_table = re.search(r"Overall(.*?)Signature", page, re.S).group(1)

        for class_grade in grade_table.split("Missing Assignments")[:-1]:
            search_string = r"[0-9]+([.][0-9]*)?\s+(?P<letter>[ABCDEFI])"
            grade = re.search(search_string, class_grade.split(" - ")[1])
            if grade:
                letter_grades.append(grade.group("letter"))
        students[name] = {"GPA": get_GPA(letter_grades),
                          "grades": letter_grades}
    GPA_text = ""
    gpa = lambda x: x[1]["GPA"]
    for k, v in sorted(students.items(), key=gpa, reverse=True):
        GPA_text += f"**{k}**: {v['GPA']:.2f}  "
        if show_grades:
            GPA_text += f"({', '.join(sorted(v['grades']))})"
        GPA_text += "  \n"
    text_area.markdown(GPA_text)

    if copy_button:
        pyperclip.copy(GPA_text.replace("*", ""))
