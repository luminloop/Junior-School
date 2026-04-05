frappe.pages["school-timetable"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "School Timetable",
    single_column: true,
  });

  $(page.body).append(`
        <div class="timetable-controls">
            <div class="print-btn-wrapper">
                <button class="btn btn-success" id="btn-print">Print</button>
            </div>

            <div class="text-center p-3">
                <div class="d-flex flex-wrap justify-content-center gap-2 mt-2 filter-controls">
                    <div class="form-group mr-2" style="min-width: 150px;">
                        <select id="level-dropdown" class="form-control">
                            <option value="">All Levels</option>
                            <option value="pre-primary">Pre-Primary</option>
                            <option value="primary">Primary</option>
                        </select>
                    </div>

                    <div class="form-group mr-2" style="min-width: 150px;">
                        <select id="teacher-dropdown" class="form-control">
                            <option value="">All Teachers</option>
                        </select>
                    </div>

                    <div class="form-group mr-2" style="min-width: 150px;">
                        <select id="stream-dropdown" class="form-control">
                            <option value="">All Streams</option>
                        </select>
                    </div>

                    <div>
                        <button class="btn btn-primary" id="btn-reset">Clear Filters</button>
                    </div>
                </div>
            </div>
        </div>

        <div id="calendar"></div>
        <div id="printable-timetable" class="d-none"></div>

        <!-- Edit/Create Schedule Modal -->
        <div class="modal fade" id="scheduleModal" tabindex="-1" role="dialog" aria-labelledby="scheduleModalLabel" aria-hidden="true">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="scheduleModalLabel">Schedule</h5>
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                      <form id="schedule-form">
                        <input type="hidden" id="schedule-id">

                        <div class="form-row">
                            <div class="form-group col-md-6">
                                <label for="edit-course">Course</label>
                                <select class="form-control" id="edit-course"></select>
                            </div>
                            <div class="form-group col-md-6">
                                <label for="edit-instructor">Instructor</label>
                                <select class="form-control" id="edit-instructor"></select>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group col-md-6">
                                <label for="edit-student-group">Student Group</label>
                                <select class="form-control" id="edit-student-group"></select>
                            </div>
                            <div class="form-group col-md-6">
                                <label for="edit-room">Room</label>
                                <select class="form-control" id="edit-room"></select>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group col-md-6">
                                <label for="edit-from-time">From Time</label>
                                <input type="time" class="form-control" id="edit-from-time">
                            </div>

                             <div class="form-group col-md-6">
                                <label for="edit-to-time">To Time</label>
                                <input type="time" class="form-control" id="edit-to-time">
                            </div>
                        </div>

                        <div class="form-row">
                        <div class="form-group col-md-6">
                                <label for="edit-date">Date</label>
                                <input type="date" class="form-control" id="edit-date">
                            </div>
                        </div>
                    </form>

                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" id="save-schedule">Save</button>
                    </div>
                </div>
            </div>
        </div>
    `);

  let css_link = document.createElement("link");
  css_link.rel = "stylesheet";
  css_link.href =
    "https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css";
  document.head.appendChild(css_link);

  let script = document.createElement("script");
  script.src = "https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js";
  script.onload = render_calendar;
  document.head.appendChild(script);

  let calendar;
  let selectedFilter = null;
  let selectedValue = "";
  let selectedLevel = "";
  let allTeachers = [];
  let allStreams = [];
  let allRooms = [];
  let isNewSchedule = false;

  let customStyles = document.createElement("style");
  customStyles.innerHTML = `
        /* Increase time row height */
        .fc-timegrid-slot {
            height: 60px !important;
        }

        /* Print button default positioning */
        .print-btn-wrapper {
            position: absolute;
            top: 10px;
            right: 20px;
            z-index: 10;
        }

        .timetable-controls {
            position: relative;
        }

        /* Mobile responsive styles */
        @media (max-width: 768px) {
            /* Print button repositioning */
            .print-btn-wrapper {
                position: static !important;
                text-align: center;
                margin: 10px 0;
            }
            
            .print-btn-wrapper .btn {
                width: 100%;
                max-width: 300px;
            }

            /* Filter dropdowns stack vertically on mobile */
            .filter-controls {
                flex-direction: column !important;
                align-items: stretch !important;
                padding: 10px !important;
            }
            
            .filter-controls .form-group {
                width: 100% !important;
                min-width: 100% !important;
                margin-right: 0 !important;
                margin-bottom: 10px;
            }
            
            .filter-controls > div {
                width: 100%;
            }
            
            .filter-controls .btn {
                width: 100%;
            }

            /* Calendar mobile adjustments */
            .fc {
                font-size: 12px !important;
            }
            
            .fc-toolbar {
                flex-direction: column !important;
                gap: 10px;
            }
            
            .fc-toolbar-chunk {
                display: flex;
                justify-content: center;
            }
            
            .fc-header-toolbar {
                margin-bottom: 1em !important;
            }
            
            .fc-timegrid-slot {
                height: 45px !important;
            }
            
            .fc-event-title {
                font-size: 10px !important;
                white-space: normal !important;
                overflow: visible !important;
            }
            
            .fc-timegrid-event {
                min-height: 40px !important;
            }
            
            /* View buttons on mobile */
            .fc-dayGridMonth-button,
            .fc-timeGridWeek-button,
            .fc-timeGridDay-button {
                font-size: 11px !important;
                padding: 4px 8px !important;
            }

            /* Modal adjustments for mobile */
            .modal-dialog {
                margin: 10px !important;
                max-width: calc(100% - 20px) !important;
            }
            
            .form-row {
                flex-direction: column;
            }
            
            .form-row .form-group {
                width: 100% !important;
                max-width: 100% !important;
                flex: none !important;
            }
            
            .form-row .col-md-6 {
                max-width: 100% !important;
                flex: 0 0 100% !important;
            }
        }

        @media (max-width: 480px) {
            .fc {
                font-size: 10px !important;
            }
            
            .fc-col-header-cell-cushion {
                font-size: 10px !important;
            }
            
            .fc-timegrid-slot-label-cushion {
                font-size: 9px !important;
            }
            
            .fc-event-title {
                font-size: 9px !important;
            }
            
            .fc-button {
                font-size: 10px !important;
                padding: 3px 6px !important;
            }
            
            .fc-toolbar-title {
                font-size: 14px !important;
            }
        }
    `;
  document.head.appendChild(customStyles);

  // Fetch teachers and populate dropdown
  frappe.call({
    method:
      "nl_school.junior_school_customization.page.school_timetable.timetable.get_teachers",
    callback: function (response) {
      allTeachers = response.message;
      let teacherDropdown = $("#teacher-dropdown");
      let editInstructorDropdown = $("#edit-instructor");

      response.message.forEach((teacher) => {
        teacherDropdown.append(
          `<option value="${teacher.value}">${teacher.label}</option>`,
        );
        editInstructorDropdown.append(
          `<option value="${teacher.value}">${teacher.label}</option>`,
        );
      });
    },
  });

  // Fetch streams and populate dropdown
  frappe.call({
    method:
      "nl_school.junior_school_customization.page.school_timetable.timetable.get_streams",
    callback: function (response) {
      allStreams = response.message;
      let streamDropdown = $("#stream-dropdown");
      let editStudentGroupDropdown = $("#edit-student-group");

      response.message.forEach((stream) => {
        streamDropdown.append(
          `<option value="${stream.value}">${stream.label}</option>`,
        );
        editStudentGroupDropdown.append(
          `<option value="${stream.value}">${stream.label}</option>`,
        );
      });
    },
  });

  frappe.call({
    method:
      "nl_school.junior_school_customization.page.school_timetable.timetable.get_rooms",
    callback: function (response) {
      allRooms = response.message;
      let allRoomsDropdown = $("#edit-room");
      response.message.forEach((room) => {
        allRoomsDropdown.append(
          `<option value="${room.value}">${room.label}</option>`,
        );
      });
    },
  });

  //fetch courses
  frappe.call({
    method:
      "nl_school.junior_school_customization.page.school_timetable.timetable.get_courses",
    callback: function (response) {
      console.log("Here", response);

      let allCoursesDropdown = $("#edit-course");
      response.message.forEach((course) => {
        allCoursesDropdown.append(
          `<option value="${course.value}">${course.label}</option>`,
        );
      });
    },
  });

  function render_calendar(filter_by = null, filter_value = "") {
    let calendarEl = document.getElementById("calendar");

    if (calendar) {
      calendar.destroy();
    }

    // Detect mobile and set appropriate initial view
    const isMobile = window.innerWidth <= 768;
    const initialView = isMobile ? "timeGridDay" : "timeGridWeek";

    calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: initialView,
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "dayGridMonth,timeGridWeek,timeGridDay",
      },
      slotDuration: "00:45:00",
      slotMinTime: "06:00:00",
      slotMaxTime: "18:00:00",
      allDaySlot: false,
      nowIndicator: true,
      editable: true,
      // Responsive height
      height: isMobile ? "auto" : null,
      expandRows: !isMobile,
      eventClick: function (info) {
        openEditModal(info.event.id);
      },
      dateClick: function (info) {
        openCreateModal(info.date);
      },
      eventDrop: function (info) {
        updateEventTime(info.event);
      },
      eventResize: function (info) {
        updateEventTime(info.event);
      },
      events: function (fetchInfo, successCallback, failureCallback) {
        frappe.call({
          method:
            "nl_school.junior_school_customization.page.school_timetable.timetable.get_course_schedule",
          args: {},
          callback: function (response) {
            let events = response.message
              .filter((event) => {
                if (filter_by === "instructor" && filter_value) {
                  return event.instructor
                    .toLowerCase()
                    .includes(filter_value.toLowerCase());
                } else if (filter_by === "stream" && filter_value) {
                  return event.student_group
                    .toLowerCase()
                    .includes(filter_value.toLowerCase());
                }
                return true;
              })
              .map((event) => ({
                id: event.name,
                title: `${event.course} - ${event.instructor}`,
                start: `${event.schedule_date}T${event.from_time}`,
                end: `${event.schedule_date}T${event.to_time}`,
                backgroundColor:
                  event.course.includes("Break") ||
                  event.course.includes("Lunch")
                    ? "#f8d7da"
                    : "#007bff",
                extendedProps: {
                  course: event.course,
                  instructor: event.instructor,
                  student_group: event.student_group,
                  room: event.room,
                  program: event.program,
                },
              }));
            successCallback(events);
          },
        });
      },
    });

    calendar.render();
  }

  function openEditModal(scheduleId) {
    isNewSchedule = false;

    $("#scheduleModalLabel").text("Edit Schedule");

    frappe.call({
      method:
        "nl_school.junior_school_customization.page.school_timetable.timetable.get_course_schedule_details",
      args: { schedule_name: scheduleId },
      callback: function (response) {
        const schedule = response.message;
        if (schedule) {
          const formattedDate = schedule.schedule_date;

          $("#schedule-id").val(schedule.name);
          $("#edit-course").val(schedule.course);
          $("#edit-instructor").val(schedule.instructor);
          $("#edit-student-group").val(schedule.student_group);
          $("#edit-room").val(schedule.room);
          $("#edit-date").val(formattedDate);
          $("#edit-from-time").val(schedule.from_time);
          $("#edit-to-time").val(schedule.to_time);

          $("#scheduleModal").modal("show");
        } else {
          frappe.throw(__("Failed to retrieve schedule details"));
        }
      },
    });
  }

  function openCreateModal(date) {
    isNewSchedule = true;

    $("#scheduleModalLabel").text("Create New Schedule");

    const formattedDate = date.toISOString().split("T")[0];

    let hours = date.getHours().toString().padStart(2, "0");
    let minutes = date.getMinutes().toString().padStart(2, "0");
    const clickTime = `${hours}:${minutes}`;

    const endDate = new Date(date);
    endDate.setMinutes(endDate.getMinutes() + 45);
    let endHours = endDate.getHours().toString().padStart(2, "0");
    let endMinutes = endDate.getMinutes().toString().padStart(2, "0");
    const endTime = `${endHours}:${endMinutes}`;

    $("#schedule-id").val("");
    $("#edit-course").val("");
    $("#edit-instructor").val("");
    $("#edit-student-group").val("");
    $("#edit-room").val("");
    $("#edit-date").val(formattedDate);
    $("#edit-from-time").val(`${clickTime}:00`);
    $("#edit-to-time").val(`${endTime}:00`);

    $("#scheduleModal").modal("show");
  }

  // Update event time after drag/resize
  function updateEventTime(event) {
    const startTime = event.start.toISOString().split("T")[1].substring(0, 8);
    const endTime = event.end.toISOString().split("T")[1].substring(0, 8);
    const scheduleDate = event.start.toISOString().split("T")[0];

    frappe.call({
      method:
        "nl_school.junior_school_customization.page.school_timetable.timetable.update_course_schedule",
      args: {
        schedule_name: event.id,
        schedule_date: scheduleDate,
        from_time: startTime,
        to_time: endTime,
      },
      callback: function (response) {
        if (response.message === "success") {
          frappe.show_alert(
            {
              message: __("Schedule updated successfully"),
              indicator: "green",
            },
            3,
          );
        } else {
          frappe.show_alert(
            {
              message: __("Failed to update schedule"),
              indicator: "red",
            },
            3,
          );
          calendar.refetchEvents();
        }
      },
    });
  }

  // Save schedule changes or create new
  $("#save-schedule").on("click", function () {
    const scheduleId = $("#schedule-id").val();
    const course = $("#edit-course").val();
    const instructor = $("#edit-instructor").val();
    const studentGroup = $("#edit-student-group").val();
    const room = $("#edit-room").val();
    const scheduleDate = $("#edit-date").val();
    const fromTime = $("#edit-from-time").val();
    const toTime = $("#edit-to-time").val();

    // Validate form
    if (
      !course ||
      !instructor ||
      !studentGroup ||
      !scheduleDate ||
      !fromTime ||
      !toTime
    ) {
      frappe.msgprint(__("Please fill in all required fields"));
      return;
    }

    if (isNewSchedule) {
      // Create new schedule
      frappe.call({
        method:
          "nl_school.junior_school_customization.page.school_timetable.timetable.create_course_schedule",
        args: {
          course: course,
          instructor: instructor,
          student_group: studentGroup,
          room: room,
          schedule_date: scheduleDate,
          from_time: fromTime,
          to_time: toTime,
        },
        callback: function (response) {
          if (response.message && response.message !== "error") {
            $("#scheduleModal").modal("hide");
            frappe.show_alert(
              {
                message: __("Schedule created successfully"),
                indicator: "green",
              },
              3,
            );
            // Refresh calendar events
            calendar.refetchEvents();
          } else {
            frappe.show_alert(
              {
                message: __("Failed to create schedule"),
                indicator: "red",
              },
              3,
            );
          }
        },
      });
    } else {
      // Update existing schedule
      frappe.call({
        method:
          "nl_school.junior_school_customization.page.school_timetable.timetable.update_course_schedule_details",
        args: {
          schedule_name: scheduleId,
          course: course,
          instructor: instructor,
          student_group: studentGroup,
          room: room,
          schedule_date: scheduleDate,
          from_time: fromTime,
          to_time: toTime,
        },
        callback: function (response) {
          if (response.message === "success") {
            $("#scheduleModal").modal("hide");
            frappe.show_alert(
              {
                message: __("Schedule updated successfully"),
                indicator: "green",
              },
              3,
            );
            // Refresh calendar events
            calendar.refetchEvents();
          } else {
            frappe.show_alert(
              {
                message: __("Failed to update schedule"),
                indicator: "red",
              },
              3,
            );
          }
        },
      });
    }
  });

  $("#btn-reset").on("click", function () {
    $("#level-dropdown").val("");
    $("#teacher-dropdown").val("");
    $("#stream-dropdown").val("");
    selectedLevel = "";
    selectedFilter = null;
    selectedValue = "";
    render_calendar();
  });

  // Handle window resize for responsive calendar
  let resizeTimeout;
  $(window).on("resize", function () {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function () {
      if (calendar) {
        const isMobile = window.innerWidth <= 768;
        const currentView = calendar.view.type;
        
        // Switch to day view on mobile if currently on week view
        if (isMobile && currentView === "timeGridWeek") {
          calendar.changeView("timeGridDay");
        }
        // Switch to week view on desktop if currently on day view
        else if (!isMobile && currentView === "timeGridDay") {
          calendar.changeView("timeGridWeek");
        }
        
        calendar.updateSize();
      }
    }, 250);
  });

  $("#level-dropdown").on("change", function () {
    selectedLevel = $(this).val();
  });

  $("#teacher-dropdown").on("change", function () {
    let selectedTeacher = $(this).val();
    if (selectedTeacher) {
      selectedFilter = "instructor";
      selectedValue = selectedTeacher;
      $("#stream-dropdown").val("");
    } else {
      selectedFilter = null;
      selectedValue = "";
    }
    render_calendar(selectedFilter, selectedValue);
  });

  $("#stream-dropdown").on("change", function () {
    let selectedStream = $(this).val();
    if (selectedStream) {
      selectedFilter = "stream";
      selectedValue = selectedStream;
      $("#teacher-dropdown").val("");
    } else {
      selectedFilter = null;
      selectedValue = "";
    }
    render_calendar(selectedFilter, selectedValue);
  });

  document.getElementById("btn-print").addEventListener("click", function () {
    generatePrintableTimetable(selectedFilter, selectedValue);
  });

  function generatePrintableTimetable(filter_type, filter_value) {
    frappe.call({
      method:
        "nl_school.junior_school_customization.page.school_timetable.timetable.get_course_schedule",
      args: { [filter_type]: filter_value },
      callback: function (response) {
        let schedules = response.message;

        if (!schedules || schedules.length === 0) {
          frappe.msgprint(__("No schedule data found for the selected filters"));
          return;
        }

        let weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

        // Dynamically extract unique time slots from actual schedule data
        let uniqueTimes = new Set();
        schedules.forEach(schedule => {
          if (schedule.from_time) {
            uniqueTimes.add(schedule.from_time);
          }
        });
        
        // Sort times
        let sortedTimes = Array.from(uniqueTimes).sort();
        
        if (sortedTimes.length === 0) {
          frappe.msgprint(__("No valid time slots found in schedule data"));
          return;
        }

        // Build time slots
        let timeSlots = sortedTimes.map((time) => ({
          start: time,
        }));

        let showInstructor = filter_type === "stream";
        let showStudentGroup = filter_type === "instructor";

        let title = filter_value
          ? `${filter_value} Timetable`
          : "School Timetable";
        if (selectedLevel) {
          title = `${selectedLevel.charAt(0).toUpperCase() + selectedLevel.slice(1)} School ${title}`;
        }

        // Build header with time ranges
        let headerHTML = timeSlots.map((slot, idx) => {
          let nextSlot = timeSlots[idx + 1];
          let endTime = nextSlot ? nextSlot.start : "";
          return `
            <th style="width: 140px; text-align: center; vertical-align: middle; font-size: 11px; font-weight: 600; padding: 8px 4px;">
              ${formatTime(slot.start)}${endTime ? ' – ' + formatTime(endTime) : ''}
            </th>`;
        }).join("");

        let tableHTML = `
          <h2 style="text-align:center;margin-bottom:16px;font-family:Arial,sans-serif;">${title}</h2>
          <table class="table table-bordered" style="table-layout:fixed;width:100%;font-size:11px;font-family:Arial,sans-serif;">
            <thead>
              <tr>
                <th style="width:90px;text-align:center;background:#1a1a2e;color:#fff;padding:8px;">Day</th>
                ${headerHTML}
              </tr>
            </thead>
            <tbody>
        `;

        weekdays.forEach((day) => {
          tableHTML += `<tr><td style="font-weight:600;text-align:center;background:#f8fafc;padding:8px;">${day}</td>`;

          timeSlots.forEach((slot) => {
            // Find ALL schedules matching this day and time
            let matchedSchedules = schedules.filter((schedule) => {
              if (!schedule.schedule_date || !schedule.from_time) return false;
              let scheduleDay = new Date(schedule.schedule_date + "T00:00:00")
                .toLocaleDateString("en-US", { weekday: "long" })
                .trim();
              return scheduleDay === day && schedule.from_time === slot.start;
            });

            if (matchedSchedules.length > 0) {
              let cellContent = matchedSchedules.map((s) => {
                let parts = [];
                if (showInstructor) {
                  parts.push(`<strong>${s.course}</strong>`);
                  parts.push(`<span style="color:#0ba4db;font-size:10px;">${s.instructor || ''}</span>`);
                } else if (showStudentGroup) {
                  parts.push(`<strong>${s.course}</strong>`);
                  parts.push(`<span style="color:#16a34a;font-size:10px;">${s.student_group || ''}</span>`);
                } else {
                  parts.push(`<strong>${s.course}</strong>`);
                  if (s.instructor) parts.push(`<span style="font-size:10px;color:#64748b;">${s.instructor}</span>`);
                  if (s.student_group) parts.push(`<span style="font-size:10px;color:#64748b;">${s.student_group}</span>`);
                }
                if (s.room) parts.push(`<span style="font-size:9px;color:#94a3b8;">${s.room}</span>`);
                return parts.join("<br>");
              }).join("<hr style='margin:4px 0;border-color:#e2e8f0;'>");

              tableHTML += `<td style="padding:6px;vertical-align:top;font-size:10px;line-height:1.4;">${cellContent}</td>`;
            } else {
              tableHTML += `<td style="background:#fafafa;"></td>`;
            }
          });

          tableHTML += `</tr>`;
        });

        tableHTML += `</tbody></table>`;

        let printableDiv = document.getElementById("printable-timetable");
        printableDiv.innerHTML = tableHTML;
        printableDiv.classList.remove("d-none");
        printTimetable();
      },
    });
  }

  // Function to format time from HH:MM:SS to readable format
  function formatTime(timeString) {
    if (!timeString) return "";
    let parts = timeString.split(":");
    let hours = parseInt(parts[0], 10);
    let minutes = parts[1] || "00";
    let period = hours >= 12 ? "PM" : "AM";
    hours = hours % 12 || 12;
    return `${hours}:${minutes} ${period}`;
  }

  // Print function
  function printTimetable() {
    let printContent = document.getElementById("printable-timetable").innerHTML;
    let newWindow = window.open("", "", "width=1200,height=800");
    newWindow.document.write(`
            <html>
            <head>
                <title>School Timetable</title>
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
                <style>
                    body { padding: 20px; }
                    h3 { margin-bottom: 20px; }
                    .table th, .table td {
                        padding: 8px;
                        border: 1px solid #ddd;
                        text-align: center;
                        vertical-align: middle;
                    }
                    table {
                        width: 100% !important;
                        table-layout: fixed;
                    }
                    th, td {
                        font-size: 11px;
                    }
                    @media print {
                        body { padding: 0; }
                        .table th, .table td {
                            padding: 4px;
                            font-size: 10px;
                        }
                    }
                </style>
            </head>
            <body class="container-fluid mt-3">
                ${printContent}
            </body>
            </html>
        `);
    newWindow.document.close();
    newWindow.focus();
    setTimeout(function() {
      newWindow.print();
      newWindow.close();
    }, 500);
  }
};
