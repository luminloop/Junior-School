// Copyright (c) 2024, Navari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fee Notification Tool", {
    refresh(frm) {
        frm.disable_save();
        
        // Add preview button
        frm.add_custom_button(__("Preview Message"), function () {
            frm.trigger("preview_message_btn");
        });
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
        if (frm.doc.academic_year) {
            frm.trigger("preview_message_btn");
        }
    },

    include_fee_breakdown(frm) {
        frm.trigger("preview_message_btn");
    },

    notification_channel(frm) {
        // Show/hide PDF attachment option based on channel
        if (frm.doc.notification_channel === "SMS") {
            frm.set_value("attach_statement_pdf", 0);
            frm.set_df_property("attach_statement_pdf", "hidden", 1);
        } else {
            frm.set_df_property("attach_statement_pdf", "hidden", 0);
        }
    },

    preview_message_btn(frm) {
        if (!frm.doc.academic_year) {
            frappe.msgprint(__("Please select Academic Year first"));
            return;
        }

        frappe.call({
            method: "nl_school.junior_school_customization.doctype.fee_notification_tool.fee_notification_tool.preview_notification",
            args: {
                doc: JSON.stringify({
                    academic_year: frm.doc.academic_year,
                    academic_term: frm.doc.academic_term,
                    program: frm.doc.program,
                    student_group: frm.doc.student_group,
                    min_outstanding_amount: frm.doc.min_outstanding_amount,
                    only_overdue: frm.doc.only_overdue,
                    message_template: frm.doc.message_template,
                    include_fee_breakdown: frm.doc.include_fee_breakdown,
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

        frappe.confirm(
            __("Are you sure you want to send fee reminder notifications to all parents/guardians with outstanding fees?"),
            function () {
                frappe.call({
                    method: "nl_school.junior_school_customization.doctype.fee_notification_tool.fee_notification_tool.send_fee_notifications",
                    args: {
                        doc: JSON.stringify({
                            academic_year: frm.doc.academic_year,
                            academic_term: frm.doc.academic_term,
                            program: frm.doc.program,
                            student_group: frm.doc.student_group,
                            min_outstanding_amount: frm.doc.min_outstanding_amount,
                            only_overdue: frm.doc.only_overdue,
                            notification_channel: frm.doc.notification_channel,
                            message_template: frm.doc.message_template,
                            include_fee_breakdown: frm.doc.include_fee_breakdown,
                            attach_statement_pdf: frm.doc.attach_statement_pdf,
                        }),
                    },
                    freeze: true,
                    freeze_message: __("Sending fee reminders..."),
                    callback: function (r) {
                        if (r.message) {
                            frappe.msgprint({
                                title: __("Fee Reminders Sent"),
                                message: __(
                                    "Successfully sent {0} notifications to parents of {1} students with outstanding fees. {2} failed.",
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
