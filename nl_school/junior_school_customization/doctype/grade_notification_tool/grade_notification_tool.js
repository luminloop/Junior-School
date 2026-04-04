// Copyright (c) 2024, Navari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Grade Notification Tool", {
    refresh(frm) {
        frm.disable_save();
    },

    academic_year(frm) {
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

    message_template(frm) {
        // Auto-preview when template changes
        if (frm.doc.academic_year && frm.doc.assessment_group) {
            frm.trigger("preview_message_btn");
        }
    },

    include_scores(frm) {
        frm.trigger("preview_message_btn");
    },

    include_ranking(frm) {
        frm.trigger("preview_message_btn");
    },

    preview_message_btn(frm) {
        if (!frm.doc.academic_year || !frm.doc.assessment_group) {
            frappe.msgprint(__("Please select Academic Year and Assessment Group first"));
            return;
        }

        frappe.call({
            method: "nl_school.junior_school_customization.doctype.grade_notification_tool.grade_notification_tool.preview_notification",
            args: {
                doc: JSON.stringify({
                    academic_year: frm.doc.academic_year,
                    academic_term: frm.doc.academic_term,
                    program: frm.doc.program,
                    student_group: frm.doc.student_group,
                    assessment_group: frm.doc.assessment_group,
                    message_template: frm.doc.message_template,
                    include_scores: frm.doc.include_scores,
                    include_ranking: frm.doc.include_ranking,
                }),
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value("preview_message", r.message);
                }
            },
        });
    },

    send_notifications(frm) {
        if (!frm.doc.academic_year) {
            frappe.msgprint(__("Please select Academic Year"));
            return;
        }
        if (!frm.doc.assessment_group) {
            frappe.msgprint(__("Please select Assessment Group"));
            return;
        }

        frappe.confirm(
            __("Are you sure you want to send grade notifications to all parents/guardians?"),
            function () {
                frappe.call({
                    method: "nl_school.junior_school_customization.doctype.grade_notification_tool.grade_notification_tool.send_grade_notifications",
                    args: {
                        doc: JSON.stringify({
                            academic_year: frm.doc.academic_year,
                            academic_term: frm.doc.academic_term,
                            program: frm.doc.program,
                            student_group: frm.doc.student_group,
                            assessment_group: frm.doc.assessment_group,
                            message_template: frm.doc.message_template,
                            notification_channel: frm.doc.notification_channel,
                            include_scores: frm.doc.include_scores,
                            include_ranking: frm.doc.include_ranking,
                        }),
                    },
                    freeze: true,
                    freeze_message: __("Sending notifications..."),
                    callback: function (r) {
                        if (r.message) {
                            frappe.msgprint({
                                title: __("Notifications Sent"),
                                message: __(
                                    "Successfully sent {0} notifications to parents of {1} students. {2} failed.",
                                    [r.message.sent, r.message.total_students, r.message.failed]
                                ),
                                indicator: r.message.failed > 0 ? "orange" : "green",
                            });
                        }
                    },
                });
            }
        );
    },
});
