frappe.ui.form.on("Student Report Generation Tool", {
  onload: function (frm) {
    frm.set_query("academic_term", function () {
      return {
        filters: {
          academic_year: frm.doc.academic_year,
        },
      };
    });

    frm.set_query("assessment_group", function () {
      return {
        filters: {
          is_group: ["in", [0, 1]],
        },
      };
    });

    if (!frm.fields_dict.custom_report_card_template) {
      frm.add_custom_button(__("Select Template"), function() {
        frappe.prompt({
          fieldname: "template",
          fieldtype: "Link",
          label: "Report Card Template",
          options: "Report Card Template",
          get_query: function() {
            return {
              filters: {
                disabled: 0
              }
            };
          }
        }, function(values) {
          frm.template_name = values.template;
          frappe.show_alert({
            message: __("Template selected: ") + values.template,
            indicator: "green"
          });
        }, __("Select Report Card Template"), __("Select"));
      }, __("Template"));
    }
  },

  refresh: function (frm) {
    frm.add_custom_button(__("Custom Print Report Card"), () => {
      let doc = frm.doc;

      if (
        !doc.student ||
        !doc.assessment_group ||
        !doc.program ||
        !doc.academic_year
      ) {
        frappe.throw(__("Please fill in all the mandatory fields."));
      }

      let doc_with_template = Object.assign({}, frm.doc);
      if (frm.template_name) {
        doc_with_template.report_card_template = frm.template_name;
      }

      let url =
        "/api/method/nl_school.junior_school_customization.controllers.student_report_generation_tool.preview_report_card";
      open_url_post(url, { doc: doc_with_template }, true);
    });

    setTimeout(() => {
      const buttons = [...document.querySelectorAll(".btn")];
      const customButton = buttons.find(
        (btn) => btn.innerText.trim() === "Custom Print Report Card",
      );

      if (customButton) {
        customButton.style.backgroundColor = "black";
        customButton.style.color = "white";
        customButton.style.border = "none";
      }
    }, 50);

    frm.add_custom_button(__("Manage Templates"), function() {
      frappe.set_route("List", "Report Card Template");
    }, __("Template"));
  },
});
