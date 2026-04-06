import frappe

def execute():
    """Create default CBC report card templates for Kenyan schools"""
    
    templates = get_cbc_templates()
    
    for template in templates:
        if not frappe.db.exists("Report Card Template", template["name"]):
            doc = frappe.get_doc({
                "doctype": "Report Card Template",
                "name": template["name"],
                "template_name": template["template_name"],
                "template_html": template["template_html"],
                "is_default": template["is_default"],
                "disabled": 0,
                "description": template["description"],
            })
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"Created Report Card Template: {template['template_name']}")
        else:
            print(f"Report Card Template already exists: {template['template_name']}")


def get_cbc_templates():
    return [
        {
            "name": "CBC Primary Report Card",
            "template_name": "CBC Primary Report Card",
            "description": "Standard CBC Primary School Report Card (Grade 1-6)",
            "is_default": 1,
            "template_html": get_primary_template(),
        },
        {
            "name": "CBC Junior Secondary Report Card",
            "template_name": "CBC Junior Secondary Report Card",
            "description": "CBC Junior Secondary School Report Card (Grade 7-9)",
            "is_default": 0,
            "template_html": get_junior_secondary_template(),
        },
    ]


def get_primary_template():
    return """<style>
    @media print {
        @page {
            size: A4 landscape;
            margin: 10mm;
        }
        body {
            margin: 0;
            padding: 0;
        }
    }
    .report-card {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 11px;
        color: #333;
        max-width: 100%;
        margin: 0 auto;
        padding: 10px;
    }
    .school-header {
        text-align: center;
        border-bottom: 3px solid #1a5276;
        padding-bottom: 10px;
        margin-bottom: 10px;
    }
    .school-header h1 {
        margin: 0;
        color: #1a5276;
        font-size: 22px;
        text-transform: uppercase;
    }
    .school-header p {
        margin: 2px 0;
        font-size: 12px;
        color: #666;
    }
    .report-title {
        text-align: center;
        background: #1a5276;
        color: white;
        padding: 6px;
        margin-bottom: 10px;
        font-size: 14px;
        font-weight: bold;
        border-radius: 3px;
    }
    .student-info {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
        border: 1px solid #ddd;
        padding: 8px;
        background: #f8f9fa;
        border-radius: 3px;
    }
    .student-info .col {
        flex: 1;
    }
    .student-info label {
        font-weight: bold;
        color: #1a5276;
        font-size: 10px;
        display: block;
    }
    .student-info span {
        display: block;
        margin-top: 2px;
    }
    .section-title {
        background: #2980b9;
        color: white;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: bold;
        margin: 10px 0 5px 0;
        border-radius: 3px;
    }
    table.marks-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 8px;
        font-size: 10px;
    }
    table.marks-table th {
        background: #1a5276;
        color: white;
        padding: 5px 4px;
        text-align: center;
        font-size: 9px;
        font-weight: bold;
    }
    table.marks-table td {
        padding: 4px;
        text-align: center;
        border: 1px solid #ddd;
    }
    table.marks-table tr:nth-child(even) {
        background: #f8f9fa;
    }
    table.marks-table td:first-child {
        text-align: left;
        font-weight: 500;
    }
    .remarks-section {
        border: 1px solid #ddd;
        padding: 8px;
        margin: 8px 0;
        background: #fafafa;
    }
    .remarks-section .row {
        display: flex;
        margin-bottom: 5px;
    }
    .remarks-section label {
        font-weight: bold;
        color: #1a5276;
        min-width: 150px;
        font-size: 10px;
    }
    .remarks-section span {
        flex: 1;
        border-bottom: 1px dotted #ccc;
        min-height: 18px;
    }
    .grading-scale {
        font-size: 9px;
        border: 1px solid #ddd;
        padding: 5px;
        margin: 8px 0;
    }
    .grading-scale table {
        width: 100%;
        border-collapse: collapse;
    }
    .grading-scale th, .grading-scale td {
        padding: 3px 5px;
        text-align: center;
        border: 1px solid #ddd;
        font-size: 9px;
    }
    .grading-scale th {
        background: #1a5276;
        color: white;
    }
    .signatures {
        display: flex;
        justify-content: space-between;
        margin-top: 15px;
        padding-top: 10px;
        border-top: 1px solid #ddd;
    }
    .signature-line {
        text-align: center;
        min-width: 150px;
    }
    .signature-line .line {
        border-top: 1px solid #333;
        margin-top: 30px;
        padding-top: 3px;
        font-size: 10px;
        font-weight: bold;
    }
    .cbc-levels {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 3px;
        font-weight: bold;
        font-size: 10px;
    }
    .level-exceeding { background: #27ae60; color: white; }
    .level-meeting { background: #2980b9; color: white; }
    .level-approaching { background: #f39c12; color: white; }
    .level-below { background: #e74c3c; color: white; }
    .footer-note {
        text-align: center;
        font-size: 8px;
        color: #999;
        margin-top: 10px;
        border-top: 1px solid #eee;
        padding-top: 5px;
    }
</style>

<div class="report-card">
    <!-- School Header -->
    <div class="school-header">
        <h1>{{ doc.company or "Lemana Junior School" }}</h1>
        <p>P.O. Box 123 - Limuru, Kenya | Tel: +254 700 000 000 | Email: info@lemana.ac.ke</p>
        <p><strong>Motto:</strong> Strive for Excellence | <strong>Reg. No:</strong> MIN/EDU/2024/089</p>
    </div>

    <!-- Report Title -->
    <div class="report-title">
        COMPETENCY BASED CURRICULUM (CBC) - LEARNER'S REPORT CARD
    </div>

    <!-- Student Information -->
    <div class="student-info">
        <div class="col">
            <label>Learner's Name:</label>
            <span><strong>{{ doc.student_name or "" }}</strong></span>
        </div>
        <div class="col">
            <label>UPI/Admission No:</label>
            <span>{{ doc.student or "" }}</span>
        </div>
        <div class="col">
            <label>Grade/Class:</label>
            <span>{{ doc.program or "" }}</span>
        </div>
        <div class="col">
            <label>Academic Term:</label>
            <span>{{ doc.academic_term or "" }} {{ doc.academic_year or "" }}</span>
        </div>
    </div>

    <!-- Assessment Results Table -->
    <div class="section-title">LEARNER'S ASSESSMENT RESULTS</div>
    <table class="marks-table">
        <thead>
            <tr>
                <th style="width: 25%;">Learning Area</th>
                <th style="width: 12%;">Opener Exam</th>
                <th style="width: 12%;">Mid Term</th>
                <th style="width: 12%;">End Term</th>
                <th style="width: 12%;">Total (%)</th>
                <th style="width: 15%;">CBC Performance Level</th>
                <th style="width: 12%;">Remarks</th>
            </tr>
        </thead>
        <tbody>
            {% for result in assessment_result %}
            <tr>
                <td>{{ result.course or result.subject or "-" }}</td>
                <td>
                    {% for r in values.assessment_result if r.course == result.course and r.assessment_group == "Opener Exam" %}
                        {{ r.total_score or "-" }}
                    {% endfor %}
                </td>
                <td>
                    {% for r in values.assessment_result if r.course == result.course and r.assessment_group == "Mid Term" %}
                        {{ r.total_score or "-" }}
                    {% endfor %}
                </td>
                <td>
                    {% for r in values.assessment_result if r.course == result.course and r.assessment_group == "End Term" %}
                        {{ r.total_score or "-" }}
                    {% endfor %}
                </td>
                <td><strong>{{ result.percentage or "-" }}%</strong></td>
                <td>
                    {% if result.levels and 'Exceeding' in result.levels %}
                        <span class="cbc-levels level-exceeding">{{ result.levels }}</span>
                    {% elif result.levels and 'Meeting' in result.levels %}
                        <span class="cbc-levels level-meeting">{{ result.levels }}</span>
                    {% elif result.levels and 'Approaching' in result.levels %}
                        <span class="cbc-levels level-approaching">{{ result.levels }}</span>
                    {% elif result.levels %}
                        <span class="cbc-levels level-below">{{ result.levels }}</span>
                    {% else %}
                        {{ result.levels or "-" }}
                    {% endif %}
                </td>
                <td>
                    {% if result.percentage >= 80 %} Excellent
                    {% elif result.percentage >= 65 %} Very Good
                    {% elif result.percentage >= 50 %} Good
                    {% elif result.percentage >= 40 %} Satisfactory
                    {% elif result.percentage %} Needs Improvement
                    {% else %} -
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <!-- CBC Performance Levels -->
    <div class="grading-scale">
        <strong>CBC Performance Levels:</strong>
        <table>
            <thead>
                <tr>
                    <th>Level 4 - Exceeding Expectations (EE)</th>
                    <th>Level 3 - Meeting Expectations (ME)</th>
                    <th>Level 2 - Approaching Expectations (AE)</th>
                    <th>Level 1 - Below Expectations (BE)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>The learner consistently demonstrates knowledge and skills beyond the expected standard.</td>
                    <td>The learner consistently demonstrates knowledge and skills at the expected standard.</td>
                    <td>The learner sometimes demonstrates knowledge and skills at the expected standard.</td>
                    <td>The learner rarely demonstrates knowledge and skills at the expected standard.</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Learner's Remarks -->
    <div class="section-title">LEARNER'S DEVELOPMENT & REMARKS</div>
    <div class="remarks-section">
        <div class="row">
            <label>Class Teacher's Remarks:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Class Teacher's Name:</label>
            <span>{{ class_teacher or "" }}</span>
        </div>
        <div class="row">
            <label>Signature:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Date:</label>
            <span></span>
        </div>
        <div class="row" style="margin-top: 10px;">
            <label>Principal's Remarks:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Principal's Name:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Signature & Stamp:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Date:</label>
            <span></span>
        </div>
        <div class="row" style="margin-top: 10px;">
            <label>Parent/Guardian's Remarks:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Parent/Guardian's Signature:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Date:</label>
            <span></span>
        </div>
    </div>

    <!-- Attendance & Co-Curricular -->
    <div class="section-title">ATTENDANCE & CO-CURRICULAR ACTIVITIES</div>
    <table class="marks-table">
        <thead>
            <tr>
                <th>School Days</th>
                <th>Days Present</th>
                <th>Days Absent</th>
                <th>Sports/Clubs</th>
                <th>Talent Area</th>
                <th>Health & Hygiene</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{{ attendance.total or "-" }}</td>
                <td>{{ attendance.present or "-" }}</td>
                <td>{{ attendance.absent or "-" }}</td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
        </tbody>
    </table>

    <!-- Signatures -->
    <div class="signatures">
        <div class="signature-line">
            <div class="line">Class Teacher's Signature</div>
        </div>
        <div class="signature-line">
            <div class="line">Principal's Signature & Stamp</div>
        </div>
        <div class="signature-line">
            <div class="line">Parent/Guardian's Signature</div>
        </div>
    </div>

    <!-- Footer -->
    <div class="footer-note">
        <p>This report card is based on the Competency Based Curriculum (CBC) assessment guidelines by Kenya Institute of Curriculum Development (KICD) and Kenya National Examinations Council (KNEC).</p>
        <p>Printed on: {{ date }}</p>
    </div>
</div>"""


def get_junior_secondary_template():
    return """<style>
    @media print {
        @page {
            size: A4 landscape;
            margin: 10mm;
        }
        body {
            margin: 0;
            padding: 0;
        }
    }
    .report-card {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 11px;
        color: #333;
        max-width: 100%;
        margin: 0 auto;
        padding: 10px;
    }
    .school-header {
        text-align: center;
        border-bottom: 3px solid #1a5276;
        padding-bottom: 10px;
        margin-bottom: 10px;
    }
    .school-header h1 {
        margin: 0;
        color: #1a5276;
        font-size: 22px;
        text-transform: uppercase;
    }
    .school-header p {
        margin: 2px 0;
        font-size: 12px;
        color: #666;
    }
    .report-title {
        text-align: center;
        background: #1a5276;
        color: white;
        padding: 6px;
        margin-bottom: 10px;
        font-size: 14px;
        font-weight: bold;
        border-radius: 3px;
    }
    .student-info {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
        border: 1px solid #ddd;
        padding: 8px;
        background: #f8f9fa;
        border-radius: 3px;
    }
    .student-info .col {
        flex: 1;
    }
    .student-info label {
        font-weight: bold;
        color: #1a5276;
        font-size: 10px;
        display: block;
    }
    .student-info span {
        display: block;
        margin-top: 2px;
    }
    .section-title {
        background: #2980b9;
        color: white;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: bold;
        margin: 10px 0 5px 0;
        border-radius: 3px;
    }
    table.marks-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 8px;
        font-size: 10px;
    }
    table.marks-table th {
        background: #1a5276;
        color: white;
        padding: 5px 4px;
        text-align: center;
        font-size: 9px;
        font-weight: bold;
    }
    table.marks-table td {
        padding: 4px;
        text-align: center;
        border: 1px solid #ddd;
    }
    table.marks-table tr:nth-child(even) {
        background: #f8f9fa;
    }
    table.marks-table td:first-child {
        text-align: left;
        font-weight: 500;
    }
    .remarks-section {
        border: 1px solid #ddd;
        padding: 8px;
        margin: 8px 0;
        background: #fafafa;
    }
    .remarks-section .row {
        display: flex;
        margin-bottom: 5px;
    }
    .remarks-section label {
        font-weight: bold;
        color: #1a5276;
        min-width: 150px;
        font-size: 10px;
    }
    .remarks-section span {
        flex: 1;
        border-bottom: 1px dotted #ccc;
        min-height: 18px;
    }
    .grading-scale {
        font-size: 9px;
        border: 1px solid #ddd;
        padding: 5px;
        margin: 8px 0;
    }
    .grading-scale table {
        width: 100%;
        border-collapse: collapse;
    }
    .grading-scale th, .grading-scale td {
        padding: 3px 5px;
        text-align: center;
        border: 1px solid #ddd;
        font-size: 9px;
    }
    .grading-scale th {
        background: #1a5276;
        color: white;
    }
    .signatures {
        display: flex;
        justify-content: space-between;
        margin-top: 15px;
        padding-top: 10px;
        border-top: 1px solid #ddd;
    }
    .signature-line {
        text-align: center;
        min-width: 150px;
    }
    .signature-line .line {
        border-top: 1px solid #333;
        margin-top: 30px;
        padding-top: 3px;
        font-size: 10px;
        font-weight: bold;
    }
    .cbc-levels {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 3px;
        font-weight: bold;
        font-size: 10px;
    }
    .level-exceeding { background: #27ae60; color: white; }
    .level-meeting { background: #2980b9; color: white; }
    .level-approaching { background: #f39c12; color: white; }
    .level-below { background: #e74c3c; color: white; }
    .footer-note {
        text-align: center;
        font-size: 8px;
        color: #999;
        margin-top: 10px;
        border-top: 1px solid #eee;
        padding-top: 5px;
    }
    .subject-comments {
        font-size: 9px;
        color: #666;
        font-style: italic;
    }
</style>

<div class="report-card">
    <!-- School Header -->
    <div class="school-header">
        <h1>{{ doc.company or "Lemana Junior School" }}</h1>
        <p>P.O. Box 123 - Limuru, Kenya | Tel: +254 700 000 000 | Email: info@lemana.ac.ke</p>
        <p><strong>Motto:</strong> Strive for Excellence | <strong>Reg. No:</strong> MIN/EDU/2024/089</p>
    </div>

    <!-- Report Title -->
    <div class="report-title">
        COMPETENCY BASED CURRICULUM (CBC) - JUNIOR SECONDARY REPORT CARD
    </div>

    <!-- Student Information -->
    <div class="student-info">
        <div class="col">
            <label>Learner's Name:</label>
            <span><strong>{{ doc.student_name or "" }}</strong></span>
        </div>
        <div class="col">
            <label>UPI/Admission No:</label>
            <span>{{ doc.student or "" }}</span>
        </div>
        <div class="col">
            <label>Grade:</label>
            <span>{{ doc.program or "" }}</span>
        </div>
        <div class="col">
            <label>Academic Term:</label>
            <span>{{ doc.academic_term or "" }} {{ doc.academic_year or "" }}</span>
        </div>
    </div>

    <!-- Assessment Results Table -->
    <div class="section-title">ACADEMIC PERFORMANCE - LEARNING AREAS</div>
    <table class="marks-table">
        <thead>
            <tr>
                <th style="width: 22%;">Learning Area</th>
                <th style="width: 10%;">Opener (%)</th>
                <th style="width: 10%;">Mid Term (%)</th>
                <th style="width: 10%;">End Term (%)</th>
                <th style="width: 10%;">Average (%)</th>
                <th style="width: 13%;">CBC Level</th>
                <th style="width: 13%;">Grade</th>
                <th style="width: 12%;">Teacher's Comment</th>
            </tr>
        </thead>
        <tbody>
            {% for result in assessment_result %}
            <tr>
                <td>{{ result.course or result.subject or "-" }}</td>
                <td>
                    {% for r in values.assessment_result if r.course == result.course and r.assessment_group == "Opener Exam" %}
                        {{ r.percentage or "-" }}%
                    {% endfor %}
                </td>
                <td>
                    {% for r in values.assessment_result if r.course == result.course and r.assessment_group == "Mid Term" %}
                        {{ r.percentage or "-" }}%
                    {% endfor %}
                </td>
                <td>
                    {% for r in values.assessment_result if r.course == result.course and r.assessment_group == "End Term" %}
                        {{ r.percentage or "-" }}%
                    {% endfor %}
                </td>
                <td><strong>{{ result.percentage or "-" }}%</strong></td>
                <td>
                    {% if result.levels and 'Exceeding' in result.levels %}
                        <span class="cbc-levels level-exceeding">{{ result.levels }}</span>
                    {% elif result.levels and 'Meeting' in result.levels %}
                        <span class="cbc-levels level-meeting">{{ result.levels }}</span>
                    {% elif result.levels and 'Approaching' in result.levels %}
                        <span class="cbc-levels level-approaching">{{ result.levels }}</span>
                    {% elif result.levels %}
                        <span class="cbc-levels level-below">{{ result.levels }}</span>
                    {% else %}
                        {{ result.levels or "-" }}
                    {% endif %}
                </td>
                <td>{{ result.grade or "-" }}</td>
                <td class="subject-comments">
                    {% for comment in values.assessment_result if comment.course == result.course and comment.subject_teacher_comments %}
                        {{ comment.subject_teacher_comments }}
                    {% endfor %}
                </td>
            </tr>
            {% endfor %}
            <tr style="background: #e8f4f8; font-weight: bold;">
                <td>TERM AVERAGE</td>
                <td>
                    {% if averages.opener.score != "-" %}{{ averages.opener.score }}%{% else %}-{% endif %}
                </td>
                <td>
                    {% if averages.mid_term.score != "-" %}{{ averages.mid_term.score }}%{% else %}-{% endif %}
                </td>
                <td>
                    {% if averages.end_term.score != "-" %}{{ averages.end_term.score }}%{% else %}-{% endif %}
                </td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td></td>
            </tr>
        </tbody>
    </table>

    <!-- CBC Performance Levels -->
    <div class="grading-scale">
        <strong>CBC Performance Levels (Junior Secondary):</strong>
        <table>
            <thead>
                <tr>
                    <th>Level 4 - Exceeding (80-100%)</th>
                    <th>Level 3 - Meeting (65-79%)</th>
                    <th>Level 2 - Approaching (50-64%)</th>
                    <th>Level 1 - Below (0-49%)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Consistently demonstrates advanced knowledge and skills beyond grade expectations.</td>
                    <td>Consistently demonstrates knowledge and skills at the expected grade level.</td>
                    <td>Sometimes demonstrates knowledge and skills at the expected grade level.</td>
                    <td>Rarely demonstrates knowledge and skills at the expected grade level.</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Core Competencies -->
    <div class="section-title">CORE COMPETENCIES & VALUES</div>
    <table class="marks-table">
        <thead>
            <tr>
                <th>Core Competency</th>
                <th>Level</th>
                <th>Core Value</th>
                <th>Level</th>
                <th>Pertinent Issue</th>
                <th>Level</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Communication & Collaboration</td>
                <td></td>
                <td>Love</td>
                <td></td>
                <td>Life skills</td>
                <td></td>
            </tr>
            <tr>
                <td>Critical Thinking & Problem Solving</td>
                <td></td>
                <td>Responsibility</td>
                <td></td>
                <td>Social cohesion</td>
                <td></td>
            </tr>
            <tr>
                <td>Imagination & Creativity</td>
                <td></td>
                <td>Respect</td>
                <td></td>
                <td>Empowerment</td>
                <td></td>
            </tr>
            <tr>
                <td>Citizenship</td>
                <td></td>
                <td>Unity</td>
                <td></td>
                <td>Self-efficacy</td>
                <td></td>
            </tr>
            <tr>
                <td>Digital Literacy</td>
                <td></td>
                <td>Peace</td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
        </tbody>
    </table>

    <!-- Remarks -->
    <div class="section-title">REMARKS & SIGNATURES</div>
    <div class="remarks-section">
        <div class="row">
            <label>Class Teacher's Remarks:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Teacher's Name:</label>
            <span>{{ class_teacher or "" }}</span>
        </div>
        <div class="row">
            <label>Signature:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Date:</label>
            <span></span>
        </div>
        <div class="row" style="margin-top: 10px;">
            <label>Principal's Remarks:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Principal's Name:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Signature & Stamp:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Date:</label>
            <span></span>
        </div>
        <div class="row" style="margin-top: 10px;">
            <label>Parent/Guardian's Remarks:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Parent/Guardian's Signature:</label>
            <span></span>
        </div>
        <div class="row">
            <label>Date:</label>
            <span></span>
        </div>
    </div>

    <!-- Attendance -->
    <div class="section-title">ATTENDANCE & CO-CURRICULAR</div>
    <table class="marks-table">
        <thead>
            <tr>
                <th>School Days</th>
                <th>Days Present</th>
                <th>Days Absent</th>
                <th>Sports/Clubs</th>
                <th>Talent Area</th>
                <th>Health & Hygiene</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{{ attendance.total or "-" }}</td>
                <td>{{ attendance.present or "-" }}</td>
                <td>{{ attendance.absent or "-" }}</td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
        </tbody>
    </table>

    <!-- Signatures -->
    <div class="signatures">
        <div class="signature-line">
            <div class="line">Class Teacher's Signature</div>
        </div>
        <div class="signature-line">
            <div class="line">Principal's Signature & Stamp</div>
        </div>
        <div class="signature-line">
            <div class="line">Parent/Guardian's Signature</div>
        </div>
    </div>

    <!-- Footer -->
    <div class="footer-note">
        <p>This report card is based on the Competency Based Curriculum (CBC) assessment guidelines by Kenya Institute of Curriculum Development (KICD) and Kenya National Examinations Council (KNEC).</p>
        <p>Printed on: {{ date }}</p>
    </div>
</div>"""
