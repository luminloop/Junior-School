// Copyright (c) 2025, Navari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Report Card Template", {
  refresh: function (frm) {
    if (!frm.is_new()) {
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
                  doctype: "Report Card Template",
                  template_name: values.template_name,
                  template_html: frm.doc.template_html,
                  description:
                    "Duplicated from " + frm.doc.template_name,
                  company: frm.doc.company,
                  is_default: 0,
                },
              },
              callback: function (r) {
                if (r.message) {
                  frappe.set_route("Form", "Report Card Template", r.message.name);
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

      frm.add_custom_button(__("Load Default Template"), function () {
        frappe.confirm(
          __(
            "This will replace the current template HTML with the default template. Continue?"
          ),
          function () {
            frappe.call({
              method:
                "nl_school.junior_school_customization.doctype.report_card_template.report_card_template.get_default_template_html",
              callback: function (r) {
                if (r.message) {
                  frm.set_value("template_html", r.message);
                  frappe.show_alert({
                    message: __("Default template loaded"),
                    indicator: "green",
                  });
                }
              },
            });
          }
        );
      });
    }
  },
});
