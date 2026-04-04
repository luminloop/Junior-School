// Copyright (c) 2024, Navari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Batch Report Card", {
    refresh(frm) {
        frm.disable_save();
    },

    get_students(frm) {
        if (!frm.doc.academic_year) {
            frappe.msgprint(__("Please select Academic Year first"));
            return;
        }

        frappe.call({
            method: "nl_school.junior_school_customization.doctype.batch_report_card.batch_report_card.get_students_for_batch",
            args: {
                academic_year: frm.doc.academic_year,
                program: frm.doc.program || "",
                student_group: frm.doc.student_group || "",
            },
            freeze: true,
            freeze_message: __("Fetching students..."),
            callback: function (r) {
                if (r.message) {
                    frm.clear_table("students");
                    r.message.forEach((student) => {
                        let row = frm.add_child("students");
                        row.student = student.student;
                        row.student_name = student.student_name;
                        row.program = student.program;
                        row.student_group = student.student_group;
                    });
                    frm.refresh_field("students");
                    frappe.msgprint(
                        __("{0} students found", [r.message.length])
                    );
                }
            },
        });
    },

    generate_report_cards(frm) {
        if (!frm.doc.academic_year) {
            frappe.msgprint(__("Please select Academic Year"));
            return;
        }
        if (!frm.doc.assessment_group) {
            frappe.msgprint(__("Please select Assessment Group"));
            return;
        }
        if (!frm.doc.students || frm.doc.students.length === 0) {
            frappe.msgprint(__("Please add students first using 'Get Students' button"));
            return;
        }

        // Prepare the document data
        let doc_data = {
            academic_year: frm.doc.academic_year,
            academic_term: frm.doc.academic_term,
            assessment_group: frm.doc.assessment_group,
            add_letterhead: frm.doc.add_letterhead,
            include_attendance: frm.doc.include_attendance,
            students: frm.doc.students.map((s) => ({
                student: s.student,
                student_name: s.student_name,
                program: s.program,
                student_group: s.student_group,
            })),
        };

        // Open PDF in new window
        let url = frappe.urllib.get_full_url(
            "/api/method/nl_school.junior_school_customization.doctype.batch_report_card.batch_report_card.generate_batch_report_cards?" +
            "doc=" + encodeURIComponent(JSON.stringify(doc_data))
        );

        frappe.msgprint({
            title: __("Generating Report Cards"),
            message: __("Generating report cards for {0} students. The PDF will open in a new tab.", [frm.doc.students.length]),
            indicator: "blue",
        });

        // Open in new window/tab
        window.open(url, "_blank");
    },

    program(frm) {
        // Clear student group if program changes
        if (frm.doc.program) {
            frm.set_query("student_group", function () {
                return {
                    filters: {
                        program: frm.doc.program,
                        academic_year: frm.doc.academic_year,
                    },
                };
            });
        }
    },

    academic_year(frm) {
        // Set query for academic term
        if (frm.doc.academic_year) {
            frm.set_query("academic_term", function () {
                return {
                    filters: {
                        academic_year: frm.doc.academic_year,
                    },
                };
            });
        }
    },
});
