// Copyright (c) 2026, Navari and contributors
// For license information, please see license.txt

frappe.ui.form.on("School Email Template", {
  refresh: function (frm) {
    if (!frm.is_new()) {
      frm.add_custom_button(__("Preview"), function () {
        frappe.call({
          method:
            "nl_school.junior_school_customization.doctype.school_email_template.school_email_template.preview_template",
          args: {
            template_name: frm.doc.name,
          },
          callback: function (r) {
            if (r.message) {
              let d = new frappe.ui.Dialog({
                title: __("Email Preview"),
                size: "large",
                fields: [
                  {
                    fieldname: "preview_subject",
                    fieldtype: "Data",
                    label: "Subject",
                    read_only: 1,
                    default: r.message.subject,
                  },
                  {
                    fieldname: "preview_message",
                    fieldtype: "HTML",
                    label: "Message",
                  },
                ],
              });
              d.fields_dict.preview_message.$wrapper.html(
                '<div style="border: 1px solid #d1d5db; padding: 15px; border-radius: 4px; background: #fff;">' +
                  r.message.message +
                  "</div>"
              );
              d.show();
            }
          },
        });
      });

      frm.add_custom_button(__("Duplicate Template"), function () {
        frappe.prompt(
          {
            fieldname: "template_name",
            fieldtype: "Data",
            label: "New Template Name",
            reqd: 1,
          },
          function (values) {
            frappe.call({
              method: "frappe.client.insert",
              args: {
                doc: {
                  doctype: "School Email Template",
                  template_name: values.template_name,
                  template_type: frm.doc.template_type,
                  subject: frm.doc.subject,
                  message: frm.doc.message,
                  company: frm.doc.company,
                  is_default: 0,
                  attach_report_card: frm.doc.attach_report_card,
                },
              },
              callback: function (r) {
                if (r.message) {
                  frappe.set_route(
                    "Form",
                    "School Email Template",
                    r.message.name
                  );
                  frappe.show_alert({
                    message: __("Template duplicated successfully"),
                    indicator: "green",
                  });
                }
              },
            });
          },
          __("Duplicate Template"),
          __("Create")
        );
      });
    }
  },
});
