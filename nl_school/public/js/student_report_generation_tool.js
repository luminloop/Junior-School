// nl_school customization for Student Report Generation Tool.
// Owns the primary action, signature pad, and template selection — the base
// education app's JS no longer registers competing buttons.

frappe.ui.form.on("Student Report Generation Tool", {
    onload(frm) {
        frm.set_query("academic_term", function () {
            return { filters: { academic_year: frm.doc.academic_year } };
        });

        frm.set_query("assessment_group", function () {
            return { filters: { is_group: ["in", [0, 1]] } };
        });
    },

    refresh(frm) {
        frm.disable_save();

        frm.page.set_primary_action(__("Generate Report Card"), function () {
            generate_report_card(frm);
        });

        setup_signature_pad(frm);
        update_student_headline(frm);
        auto_generate_preview(frm);
    },

    student(frm) {
        update_student_headline(frm);
        auto_generate_preview(frm);
    },

    student_name(frm) {
        update_student_headline(frm);
    },
    academic_year: auto_generate_preview,
    academic_term: auto_generate_preview,
    assessment_group: auto_generate_preview,
    program: auto_generate_preview,
    add_letterhead: auto_generate_preview,
    show_marks: auto_generate_preview,
    include_teacher_comments: auto_generate_preview,

    include_principal_signature(frm) {
        setup_signature_pad(frm);
        auto_generate_preview(frm);
    },
});

function update_student_headline(frm) {
    if (!frm.dashboard || !frm.dashboard.set_headline) return;
    if (!frm.doc.student) {
        frm.dashboard.clear_headline && frm.dashboard.clear_headline();
        return;
    }
    const name = frm.doc.student_name || frm.doc.student;
    const bits = [];
    if (frm.doc.program) bits.push(frm.doc.program);
    if (frm.doc.academic_year) bits.push(frm.doc.academic_year);
    if (frm.doc.academic_term) bits.push(frm.doc.academic_term);
    const subtitle = bits.length ? `<span style="color:#6b7280;font-weight:500;">${bits.join(" &middot; ")}</span>` : "";
    frm.dashboard.set_headline(
        `<div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;">
            <span style="font-size:18px;font-weight:700;color:#111;letter-spacing:-0.2px;">${frappe.utils.escape_html(name)}</span>
            ${subtitle}
        </div>`
    );
}

function setup_signature_pad(frm) {
    if (!frm.doc.include_principal_signature) {
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
    const payload = {
        student: doc.student,
        students: [doc.student],
        academic_year: doc.academic_year,
        academic_term: doc.academic_term,
        assessment_group: doc.assessment_group,
        add_letterhead: doc.add_letterhead,
        include_attendance: 1,
        show_marks: doc.show_marks || 0,
        include_principal_signature: doc.include_principal_signature || 0,
        include_teacher_comments: doc.include_teacher_comments !== 0 ? 1 : 0,
        principal_signature_data: doc.include_principal_signature
            ? doc.principal_signature_data || ""
            : "",
        custom_teachers_comment: doc.custom_teachers_comment,
    };
    return payload;
}

function generate_report_card(frm) {
    const doc = frm.doc;
    if (!doc.student || !doc.assessment_group || !doc.program || !doc.academic_year) {
        frappe.throw(__("Please fill in Student, Program, Academic Year and Assessment Group."));
    }
    if (
        doc.include_principal_signature &&
        !doc.principal_signature_data
    ) {
        frappe.msgprint(
            __("Please sign in the Principal Signature box, or turn the option off.")
        );
        return;
    }

    const url =
        "/api/method/nl_school.junior_school_customization.controllers.student_report_generation_tool.preview_report_card";
    open_url_post(url, { doc: JSON.stringify(build_doc_payload(frm)) }, true);
}

function auto_generate_preview(frm) {
    const doc = frm.doc;
    if (!doc.student || !doc.assessment_group || !doc.program || !doc.academic_year) {
        return;
    }

    if (frm.preview_timeout) clearTimeout(frm.preview_timeout);

    frm.preview_timeout = setTimeout(function () {
        frappe.call({
            method: "nl_school.junior_school_customization.controllers.student_report_generation_tool.preview_report_card",
            args: {
                doc: JSON.stringify(build_doc_payload(frm)),
                preview_only: true,
            },
            callback: function (r) {
                if (r.message) show_preview_container(frm, r.message);
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
                <strong style="color: #374151;">Report Card Preview</strong>
                <span style="color: #6b7280; font-size: 12px;">Auto-updates as you change settings</span>
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
