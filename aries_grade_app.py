import streamlit as st
import fitz
import re
import numpy as np

st.set_page_config("GPA Calculator", page_icon="aplus.jpg")

title_spot = st.empty()
title_spot.title("Aries Gradebook GPA Calculator")
text_area = st.container()
widgets = st.container()
file = st.file_uploader("", type="pdf")

if file:
    show_grades = widgets.checkbox("Show Grades", False)
    # Copy doesn't work on streamlit sharing
    # copy_button = widgets.button("Copy to Clipboard")

    # Parse PDF Pages
    # pages = []
    # reader = PyPDF2.PdfFileReader(file)
    # for i in range(reader.numPages):
    #     pages.append(reader.getPage(i).extractText())
    pages = fitz.open(file)

    # Get date of report
    # date = re.search(r"\)(.*?) Grade Summary",
    #                  pages[0]).group(1)
    date = pages[0].get_text().split("\n")[1]
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
        pagetext = page.get_text()
        if name_match := re.search(r"Report For (.*?) \(", pagetext):
            name = name_match.group(1)
        else:
            continue

        
    #     # letter_grades = []
        grade_table = re.search(r"Overall(.*?)Signature", pagetext, re.S)
        if grade_table:
            grade_table = grade_table.group(1)
            classes = re.split(r"(?<=Missing Assignments\n\d)", grade_table)

            pattern = r"(?P<gpa>[0-5])\s*(?P<grade>[A-F])?$"
            gpas = []
            grades = []


            for c in classes:
                if not c.strip():
                    continue 
                m = re.search(pattern, c.split("\n")[2])
                if not m:
                    continue 
                gpa = float(m.group("gpa"))
                if gpa or c.endswith("0"):
                    gpas.append(gpa)
                    grades.append(m.group("grade"))


            # gpa_match = [
            #     (re.search(p, c.split("\n")[2]), c.endswith("0")) 
            #     for c in classes if c.strip()
            # ]
            # gpas = [(float(e[0].group(1)), e[1]) for e in gpa_match if e[0]]
            # mean_gpa = np.mean([gpa for gpa, no_miss in gpas if gpa or no_miss])
            mean_gpa = np.mean(gpas) if len(gpas) else "N/A"
            students[name] = {"GPA": mean_gpa, "grades": grades}

    #     for class_grade in grade_table.split("Missing Assignments")[:-1]:
    #         search_string = r"[0-9]+([.][0-9]*)?\s+(?P<letter>[ABCDEFI])"
    #         grade = re.search(search_string, class_grade.split(" - ")[1])
    #         if grade:
    #             letter_grades.append(grade.group("letter"))
    #     students[name] = {"GPA": get_GPA(letter_grades),
    #                       "grades": letter_grades}
    GPA_text = ""
    gpa = lambda x: x[1]["GPA"]
    for student, info in sorted(students.items(), key=gpa, reverse=True):
        GPA_text += f"**{student}**: {info['GPA']:.2f}"
        if show_grades:
            # GPA_text += str(info["grades"])
            # GPA_text += ", ".join([g for g in sorted(info["grades"])])
            GPA_text += " (" + ", ".join(sorted([x for x in info["grades"] if x is not None])) + ")"
        GPA_text += "  \n"

    #     GPA_text += f"**{k}**: {v['GPA']:.2f}  "
    #     if show_grades:
    #         GPA_text += f"({', '.join(sorted(v['grades']))})"
    #     GPA_text += "  \n"

    # GPA_text = "\n".join([f"{student['name']}" for student in students])

    text_area.markdown(GPA_text)

    # st.write(students)

    # # Download
    # file_name = f"grades_as_of_{date.replace(' ', '_').replace(',', '')}.txt"
    # widgets.download_button("Download Results", GPA_text.replace("*", ""),
    #                          file_name=file_name)

    # if copy_button:
    #     pyperclip.copy(GPA_text.replace("*", ""))
################################################################################