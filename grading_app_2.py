import streamlit as st 
import re
import pdfplumber
import pandas as pd
##F0F6F1

def main():

    # Page Layout
    title_spot = st.container()
    title_spot.title("Aeries Gradebook GPA Calculator")
    text_area = st.container()
    download_area = st.container()
    st.markdown("---")
    file = st.file_uploader("Upload Aeries File", type="pdf", label_visibility="hidden")    

    # Display options (sidebar)
    st.sidebar.title("Display Options")


    def uncheck():
        for key in ["N", "L", "G", "M", "C"]:
            st.session_state[key] = False
    def check():
        for key in ["N", "L", "G", "M", "C"]:
            st.session_state[key] = True


    use = {
        "numbers": st.sidebar.checkbox("Show Number Grades", False, key="N"),
        "letters": st.sidebar.checkbox("Show Letter Grades", False, key="L"),
        "gpas":  st.sidebar.checkbox("Show Class GPAs", False, key="G"),
        "missing": st.sidebar.checkbox("Show Missing Assignments", False, key="M"),
        "classes": st.sidebar.checkbox("Show Classes", False, key="C"),
    }

    if any([st.session_state[k] for k in ["N", "L", "G", "M", "C"]]):
        st.sidebar.button("Deselect All", key="B1", on_click=uncheck, type="primary")
    else:
        st.sidebar.button("Select All", key="B2", on_click=check, type="primary")
    st.sidebar.markdown("---")
    pretty = st.sidebar.radio("Display Type", ["Standard", "Styled"], 0) == "Styled"

    # Parse an uploaded pdf
    if file is not None:
        # Read PDF file
        pages = pdfplumber.open(file).pages

        # Add report date as subtitle
        date_pattern =  r"\)\n(?P<date>[\w\d\s\,]+)\nGrade"
        date = re.search(date_pattern, pages[0].extract_text()).group("date")
        title_spot.subheader(date)
        title_spot.markdown("---")

        # Get student info
        if "students" not in st.session_state:
            st.session_state["students"] = get_student_reports(pages)
        students = st.session_state["students"]

        # Display
        df = (
            pd.DataFrame.from_dict(students)
            .sort_values(["mean_gpa", "student"], ascending=[False, True])
        )
        def fmt_gpa_str(row):
            def fmt_vals(vals):
                return ", ".join([str(x) for x in vals])
            gpa_str = f"**{row['student']}:** {row['mean_gpa']:.2f}"
            
            for k, v in use.items():
                if v and pretty:
                    gpa_str += f"\n- _{k}:_ {fmt_vals(df.loc[row.name][k])}"
                    # gpa_str += f" | _{k}_ = [{fmt_vals(df.loc[row.name][k])}]"
                elif v and not pretty:
                    gpa_str += f" | _{k}:_ [{fmt_vals(df.loc[row.name][k])}]"
            if any(use.values()) and pretty:
                gpa_str += "\n\n---\n"
            return gpa_str
        GPA_str = "  \n".join(df.apply(fmt_gpa_str, axis=1).to_list())
        text_area.markdown(GPA_str)

        # Downloads
        download_area.markdown("<br></br>", unsafe_allow_html=True)
        download_area.markdown("#### Download Results:\t")
        file_name_base = f"student_gpas_" + date.replace(" ", "_").replace(",", "")
        
        c1, c2, _ = download_area.columns([1, 1, 6])
        c1.download_button(
            "`.txt`", GPA_str.replace("*", ""), file_name= file_name_base + ".txt"
        )

        csv = df.to_csv(index=False).encode('utf-8')
        c2.download_button(
            "`.csv`", csv, file_name=file_name_base + ".csv"
        )


def get_gpa(number, letter, use_plus_minus=True):
    """Get GPA on 4 point scale"""
    if number <= 5:
        return number
    # Have a letter but not a number or not using plus/minuses
    elif (not number and letter) or not use_plus_minus:
        letter_to_gpa = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
        return letter_to_gpa[letter]
    # Number out of 100
    cutoffs = [
        (93, 4.0), (90, 3.7), (87, 3.3), (83, 3.0), (80, 2.7),
        (77, 2.3), (73, 2.0), (70, 1.7), (67, 1.3), (65, 1.0),
    ]
    for cut, gpa in cutoffs:
        if number >= cut:
            return gpa
    return 0.0


def get_student_grades(report, use_plus_minus=True):
    """Get Student name, classes, grades, and gpas"""
    # Get name
    name_pattern = r"Report For (?P<name>.*?) \("
    name_match = re.search(name_pattern, report)
    if not name_match:
        return
    name = name_match.group("name")
    
    # Get class names
    class_pattern = r"^(.+) -"
    classes = re.findall(class_pattern, report, flags=re.M)
    
    # Get grades/GPAs
    grade_pattern = r"(?P<number>\d+(\.\d+)?)\s*(?P<grade>[ABCDFI])?$"
    matches = re.findall(grade_pattern, report, flags=re.M)
    number_grades = [float(x[0]) for x in matches]
    letter_grades = [x[-1] for x in matches]
    gpas = [
        get_gpa(num, let, use_plus_minus)
        for num, let in zip(number_grades, letter_grades)
    ]
    
    # Return student
    student = {
        "student": name,
        "classes": classes,
        "numbers": number_grades,
        "letters": letter_grades,
        "gpas": gpas,
    }
    return student


def get_missing_assignments(raw_text):
    """Get number of missing assignments for each class"""
    miss_pattern = r"^Missing Assignments (?P<missing>\d+)$"
    missing = re.findall(miss_pattern, raw_text, flags=re.M)
    return [int(m) for m in missing]


def compute_final_gpa(gpas, missing):
    """Compute total GPA using classes that have had assignments"""
    use_gpas = [g for g, m in zip(gpas, missing) if g or m]
    if use_gpas:
        return sum(use_gpas) / len(use_gpas)


def get_student_reports(pages):
    """Get report for all students"""
    # Get bolded text
    get_bold = lambda x: "fontname" in x and "Bold" in x["fontname"]
    raw_texts = "\n\n".join([p.extract_text() for p in pages])
    bolded = "\n\n".join([p.filter(get_bold).extract_text() for p in pages])

    # Get class info

    SPLIT_ON = "Signature:"

    students = [get_student_grades(report) for report in bolded.split(SPLIT_ON)]
    students = [s for s in students if s is not None]

    # Missing assignments
    student_texts = raw_texts.split(SPLIT_ON)
    for i, s in enumerate(students):
        miss = get_missing_assignments(student_texts[i])
        s["missing"] = miss
        s["mean_gpa"] = compute_final_gpa(s["gpas"], miss)
    return students




if __name__ == "__main__":
    st.set_page_config(
        page_title="GPA Calculator", 
        page_icon="aplus.jpg", 
        initial_sidebar_state="expanded"
    )
    main()