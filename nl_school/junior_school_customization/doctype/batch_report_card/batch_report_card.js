// Copyright (c) 2024, Navari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Batch Report Card", {
    refresh(frm) {
        frm.disable_save();

        frm.page.set_primary_action(__("Generate Report Cards"), function () {
            generate_report_cards(frm);
        });

        setup_signature_pad(frm);
        update_batch_headline(frm);
        auto_generate_preview(frm);
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
                    frappe.show_alert({
                        message: __("{0} students found", [r.message.length]),
                        indicator: "green",
                    });
                    update_batch_headline(frm);
                    auto_generate_preview(frm);
                }
            },
        });
    },

    program(frm) {
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
        if (frm.doc.academic_year) {
            frm.set_query("academic_term", function () {
                return {
                    filters: { academic_year: frm.doc.academic_year },
                };
            });
        }
        update_batch_headline(frm);
    },

    academic_term: update_batch_headline,
    program: update_batch_headline,
    student_group: update_batch_headline,
    students_on_form_rendered: update_batch_headline,

    include_principal_signature(frm) {
        setup_signature_pad(frm);
        auto_generate_preview(frm);
    },

    include_teacher_comments: auto_generate_preview,
    add_letterhead: auto_generate_preview,
    include_attendance: auto_generate_preview,
});

function update_batch_headline(frm) {
    if (!frm.dashboard || !frm.dashboard.set_headline) return;
    const bits = [];
    if (frm.doc.program) bits.push(frm.doc.program);
    if (frm.doc.student_group) bits.push(frm.doc.student_group);
    if (frm.doc.academic_year) bits.push(frm.doc.academic_year);
    if (frm.doc.academic_term) bits.push(frm.doc.academic_term);
    const count = (frm.doc.students || []).length;
    const title = count ? `${count} pupil${count === 1 ? "" : "s"} selected` : "No pupils selected";
    const subtitle = bits.length ? `<span style="color:#6b7280;font-weight:500;">${bits.join(" &middot; ")}</span>` : "";
    frm.dashboard.set_headline(
        `<div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;">
            <span style="font-size:18px;font-weight:700;color:#111;letter-spacing:-0.2px;">${title}</span>
            ${subtitle}
        </div>`
    );
}

function setup_signature_pad(frm) {
    if (!frm.doc.include_principal_signature) {
        // Clear stored signature when toggle goes off
        if (frm.doc.principal_signature_data) {
            frm.set_value("principal_signature_data", "");
        }
        return;
    }
    if (window.nl_school && window.nl_school.init_signature_pad) {
        window.nl_school.init_signature_pad(
            frm,
            "principal_signature_pad",
            "principal_signature_data"
        );
    }
}

function build_doc_payload(frm) {
    const doc = frm.doc;
    return {
        academic_year: doc.academic_year,
        academic_term: doc.academic_term,
        assessment_group: doc.assessment_group,
        add_letterhead: doc.add_letterhead,
        include_attendance: doc.include_attendance,
        include_principal_signature: doc.include_principal_signature || 0,
        include_teacher_comments: doc.include_teacher_comments !== 0 ? 1 : 0,
        principal_signature_data: doc.include_principal_signature
            ? doc.principal_signature_data || ""
            : "",
        students: (doc.students || []).map((s) => ({
            student: s.student,
            student_name: s.student_name,
            program: s.program,
            student_group: s.student_group,
        })),
    };
}

function generate_report_cards(frm) {
    if (!frm.doc.academic_year) {
        frappe.msgprint(__("Please select Academic Year"));
        return;
    }
    if (!frm.doc.assessment_group) {
        frappe.msgprint(__("Please select Assessment Group"));
        return;
    }
    if (!frm.doc.students || frm.doc.students.length === 0) {
        frappe.msgprint(__("Please add students using 'Get Students' first"));
        return;
    }
    if (
        frm.doc.include_principal_signature &&
        !frm.doc.principal_signature_data
    ) {
        frappe.msgprint(
            __("Please sign in the Principal Signature box, or turn the option off.")
        );
        return;
    }

    frappe.show_alert({
        message: __("Generating report cards for {0} students...", [
            frm.doc.students.length,
        ]),
        indicator: "blue",
    });

    const url =
        "/api/method/nl_school.junior_school_customization.doctype.batch_report_card.batch_report_card.generate_batch_report_cards";
    open_url_post(url, { doc: JSON.stringify(build_doc_payload(frm)) }, true);
}

function auto_generate_preview(frm) {
    const doc = frm.doc;
    if (
        !doc.academic_year ||
        !doc.assessment_group ||
        !doc.students ||
        doc.students.length === 0
    ) {
        return;
    }

    if (frm.preview_timeout) clearTimeout(frm.preview_timeout);

    frm.preview_timeout = setTimeout(function () {
        frm.page.set_indicator(__("Updating Preview..."), "blue");

        frappe.call({
            method: "nl_school.junior_school_customization.doctype.batch_report_card.batch_report_card.preview_batch_report_cards",
            args: { doc: JSON.stringify(build_doc_payload(frm)) },
            callback: function (r) {
                frm.page.clear_indicator();
                if (r.message) show_preview_container(frm, r.message);
            },
            error: function () {
                frm.page.clear_indicator();
            },
        });
    }, 500);
}

function show_preview_container(frm, html) {
    frm.fields_dict.preview_container &&
        frm.fields_dict.preview_container.$wrapper.remove();

    const preview_html = `
        <div style="margin-top: 20px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden;">
            <div style="background: #f3f4f6; padding: 10px 15px; border-bottom: 1px solid #d1d5db; display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #374151;">Report Card Preview (First 3 Students)</strong>
                <span style="color: #6b7280; font-size: 12px;">Click "Generate Report Cards" for full PDF</span>
            </div>
            <div style="padding: 20px; background: white; max-height: 500px; overflow-y: auto;">
                ${html}
            </div>
        </div>
    `;

    frm.add_field({
        fieldtype: "HTML",
        fieldname: "preview_container",
        label: "Preview",
        options: preview_html,
    });
}
