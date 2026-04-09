// Copyright (c) 2026, Navari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Certificate Template", {
  refresh: function (frm) {
    if (!frm.is_new()) {
      frm.add_custom_button(__("Preview"), function () {
        frappe.call({
          method:
            "nl_school.junior_school_customization.doctype.certificate_template.certificate_template.preview_template",
          args: {
            template_name: frm.doc.name,
          },
          callback: function (r) {
            if (r.message) {
              let bgStyle = r.message.background_image
                ? `background-image: url('${r.message.background_image}'); background-size: cover; background-position: center;`
                : "";

              let pageWidth =
                r.message.orientation === "Landscape" ? "297mm" : "210mm";
              let pageHeight =
                r.message.orientation === "Landscape" ? "210mm" : "297mm";

              if (r.message.page_size === "Letter") {
                pageWidth =
                  r.message.orientation === "Landscape" ? "11in" : "8.5in";
                pageHeight =
                  r.message.orientation === "Landscape" ? "8.5in" : "11in";
              } else if (r.message.page_size === "A3") {
                pageWidth =
                  r.message.orientation === "Landscape" ? "420mm" : "297mm";
                pageHeight =
                  r.message.orientation === "Landscape" ? "297mm" : "420mm";
              }

              let d = new frappe.ui.Dialog({
                title: __("Certificate Preview"),
                size: "extra-large",
                fields: [
                  {
                    fieldname: "preview_html",
                    fieldtype: "HTML",
                    label: "Preview",
                  },
                ],
              });

              d.fields_dict.preview_html.$wrapper.html(`
                <style>${r.message.css || ""}</style>
                <div style="width: ${pageWidth}; min-height: ${pageHeight}; margin: 0 auto; border: 1px solid #d1d5db; ${bgStyle} padding: 20px; box-sizing: border-box; overflow: auto;">
                  ${r.message.html}
                </div>
              `);
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
                  doctype: "Certificate Template",
                  template_name: values.template_name,
                  certificate_type: frm.doc.certificate_type,
                  template_html: frm.doc.template_html,
                  custom_css: frm.doc.custom_css,
                  page_size: frm.doc.page_size,
                  orientation: frm.doc.orientation,
                  background_image: frm.doc.background_image,
                  company: frm.doc.company,
                  is_default: 0,
                },
              },
              callback: function (r) {
                if (r.message) {
                  frappe.set_route(
                    "Form",
                    "Certificate Template",
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
