// Copyright (c) 2026, Navari and contributors
// For license information, please see license.txt

frappe.ui.form.on("School Email Settings", {
  refresh: function (frm) {
    if (!frm.is_new()) {
      frm.add_custom_button(__("Test Email"), function () {
        frappe.prompt(
          {
            fieldname: "test_email",
            fieldtype: "Data",
            label: "Test Email Address",
            reqd: 1,
            options: "Email",
          },
          function (values) {
            frappe.call({
              method: "frappe.core.doctype.communication.email.make",
              args: {
                recipients: values.test_email,
                subject: "Test Email from " + frm.doc.company,
                content:
                  "This is a test email from your school email configuration.",
                send_email: 1,
              },
              callback: function (r) {
                if (!r.exc) {
                  frappe.show_alert({
                    message: __("Test email sent successfully"),
                    indicator: "green",
                  });
                }
              },
            });
          },
          __("Send Test Email"),
          __("Send")
        );
      });

      frm.add_custom_button(__("Setup Email Account"), function () {
        let d = new frappe.ui.Dialog({
          title: __("Setup New Email Account"),
          fields: [
            {
              fieldname: "email",
              fieldtype: "Data",
              label: "Email Address",
              reqd: 1,
              options: "Email",
            },
            {
              fieldname: "password",
              fieldtype: "Password",
              label: "Password",
              reqd: 1,
            },
            {
              fieldname: "purpose",
              fieldtype: "Select",
              label: "Purpose",
              options:
                "Default\nAttendance\nFee\nGrade\nEvent\nReport Card\nGeneral",
              default: "Default",
            },
          ],
          primary_action_label: __("Create"),
          primary_action: function (values) {
            frappe.call({
              method:
                "nl_school.junior_school_customization.doctype.school_email_settings.school_email_settings.create_email_account",
              args: {
                email: values.email,
                password: values.password,
                company: frm.doc.company,
                purpose: values.purpose.toLowerCase(),
              },
              callback: function (r) {
                if (r.message) {
                  frappe.show_alert({
                    message: __(
                      "Email account created: {0}",
                      [r.message]
                    ),
                    indicator: "green",
                  });
                  d.hide();
                  frm.reload_doc();
                }
              },
            });
          },
        });
        d.show();
      });
    }
  },
});
