// Copyright (c) 2025, Navari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Timetable Generator", {
   refresh: function (frm) {
     // Generate Timetable button
     frm
       .add_custom_button(__("Generate Timetable"), function () {
         if (!frm.doc.academic_term) {
           frappe.msgprint(__("Please select an Academic Term first"));
           return;
         }
         frappe.call({
           method:
             "nl_school.junior_school_customization.doctype.timetable_generator.timetable_generator.generate_timetable",
           args: {},
           freeze: true,
           freeze_message: __("Generating Timetable..."),
           callback: function (response) {
             if (response.message) {
               frappe.msgprint(__("Timetable Generated Successfully!"));
               frm.reload_doc();
             }
           },
         });
       })
       .addClass("btn-primary");

     // Import from Previous Term
     frm.add_custom_button(__("Import from Previous Term"), function () {
       frappe.prompt([
         {
           fieldname: "academic_term",
           fieldtype: "Link",
           label: __("Import From Term"),
           options: "Academic Term",
           reqd: 1,
           description: __("Subject rules, time slots, and teacher preferences will be copied from this term")
         }
       ], function(values) {
         frappe.call({
           method: "nl_school.junior_school_customization.doctype.timetable_generator.timetable_generator.import_from_previous_term",
           args: {
             source_term: values.academic_term
           },
           freeze: true,
           freeze_message: __("Importing configuration..."),
           callback: function(response) {
             if (response.message && response.message.success) {
               frappe.msgprint(__("Configuration imported successfully!"));
               frm.reload_doc();
             } else {
               frappe.msgprint__(response.message.error || __("Failed to import configuration"));
             }
           }
         });
       }, __("Select Source Term"));
     }, __("Actions"));

     // Copy Timetable from Previous Term
     frm.add_custom_button(__("Copy from Previous Term"), function () {
       frappe.prompt([
         {
           fieldname: "academic_term",
           fieldtype: "Link",
           label: __("Copy Timetable From"),
           options: "Academic Term",
           reqd: 1,
           description: __("Course schedules will be copied from this term")
         },
         {
           fieldname: "overwrite",
           fieldtype: "Check",
           label: __("Overwrite Existing"),
           description: __("Replace existing schedules for the current term")
         }
       ], function(values) {
         frappe.call({
           method: "nl_school.junior_school_customization.doctype.timetable_generator.timetable_generator.copy_from_previous_term",
           args: {
             source_term: values.academic_term,
             target_term: frm.doc.academic_term,
             overwrite: values.overwrite || 0
           },
           freeze: true,
           freeze_message: __("Copying timetable..."),
           callback: function(response) {
             if (response.message && response.message.success) {
               frappe.msgprint(__("Copied {0} course schedules successfully!").replace("{0}", response.message.count));
               frm.reload_doc();
             } else {
               frappe.msgprint__(response.message.error || __("Failed to copy timetable"));
             }
           }
         });
       }, __("Select Source Term"));
     }, __("Actions"));

     // View Generation History
     frm.add_custom_button(__("Generation History"), function () {
       frappe.set_route("List", "Timetable Generation Result");
     }, __("Actions"));

     // Print Timetable
     frm
       .add_custom_button(__("Print Timetable"), function () {
         frappe.route_options = {
           "academic_term": frm.doc.academic_term,
           "company": frm.doc.company
         };
         frappe.set_route("query-report", "Timetable Report");
       }, __("Print"));
   },
});
