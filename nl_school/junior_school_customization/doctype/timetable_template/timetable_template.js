// Copyright (c) 2026, Navari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Timetable Template", {
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
                  doctype: "Timetable Template",
                  template_name: values.template_name,
                  description: "Duplicated from " + frm.doc.template_name,
                  company: frm.doc.company,
                  is_default: 0,
                  header_color: frm.doc.header_color,
                  break_color: frm.doc.break_color,
                  row_odd_color: frm.doc.row_odd_color,
                  row_even_color: frm.doc.row_even_color,
                  custom_css: frm.doc.custom_css,
                  template_html: frm.doc.template_html,
                },
              },
              callback: function (r) {
                if (r.message) {
                  frappe.set_route("Form", "Timetable Template", r.message.name);
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

      frm.add_custom_button(__("Preview"), function () {
        frappe.set_route("education-timetable");
      }, __("Actions"));

      frm.add_custom_button(__("Reset to Defaults"), function () {
        frappe.confirm(
          __("This will reset all colors to default values. Continue?"),
          function () {
            frm.set_value("header_color", "#f3f4f6");
            frm.set_value("break_color", "#ffe4e6");
            frm.set_value("row_odd_color", "#ffffff");
            frm.set_value("row_even_color", "#f9fafb");
            frm.set_value("custom_css", "");
            frappe.show_alert({
              message: __("Colors reset to defaults"),
              indicator: "green",
            });
          }
        );
      }, __("Actions"));
    }
  },
});
