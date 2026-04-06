frappe.pages["teacher-dashboard"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "My Dashboard",
    single_column: true,
  });

  page.inner_page = true;
  
  let dashboard = new TeacherDashboard(page);
};

class TeacherDashboard {
  constructor(page) {
    this.page = page;
    this.wrapper = $(page.body);
    this.init();
  }

  init() {
    this.setup_header();
    this.load_data();
  }

  setup_header() {
    this.page.set_title("My Dashboard");
    
    let refresh_btn = this.page.add_inner_button(__("Refresh"), () => {
      this.load_data();
    });
    refresh_btn.removeClass('btn-default').addClass('btn-secondary');
  }

  load_data() {
    this.wrapper.html(`
      <div class="school-dashboard-wrapper">
        <div class="empty-state">
          <div class="spinner-border text-muted" role="status" style="width: 2rem; height: 2rem; border-width: 2px;">
            <span class="sr-only">Loading...</span>
          </div>
          <p class="mt-3 mb-0" style="font-size: 13px; color: var(--text-muted);">${__("Loading dashboard...")}</p>
        </div>
      </div>
    `);

    frappe.call({
      method: "nl_school.junior_school_customization.page.teacher_dashboard.teacher_dashboard.get_dashboard_data",
      callback: (r) => {
        if (r.message) {
          if (r.message.error) {
            this.render_error(r.message.error);
          } else {
            this.data = r.message;
            this.render();
          }
        }
      },
      error: () => {
        this.wrapper.html(`
          <div class="school-dashboard-wrapper">
            <div class="alert alert-danger d-flex align-items-center">
              ${frappe.utils.icon("solid-error", "md")}
              <span class="ml-2">${__("Unable to load dashboard data. Please try refreshing.")}</span>
            </div>
          </div>
        `);
      }
    });
  }

  render_error(message) {
    this.wrapper.html(`
      <div class="school-dashboard-wrapper">
        <div class="alert alert-warning d-flex align-items-center">
          ${frappe.utils.icon("solid-warning", "md")}
          <span class="ml-2">${__(message)}</span>
        </div>
        <p class="text-muted">${__("Please contact your administrator to link your user account to an Instructor profile.")}</p>
      </div>
    `);
  }

  render() {
    const stats = this.data.stats;
    const instructor = this.data.instructor || {};
    const today = frappe.datetime.str_to_user(frappe.datetime.get_today());

    this.wrapper.html(`
      <div class="school-dashboard-wrapper">
        <!-- Header -->
        <div class="dashboard-header">
          <div>
            <h4>${__("Welcome")}, ${instructor.instructor_name || __("Teacher")}</h4>
            <span class="text-muted" style="font-size: 13px;">${__("Here's your teaching overview")}</span>
          </div>
          <span class="date-display">${today}</span>
        </div>

        <!-- Stats Row -->
        <div class="row mb-4">
          <div class="col-12 col-sm-6 col-lg-3 mb-3">
            ${this.render_number_widget({
              label: "My Students",
              value: stats.total_students || 0,
              icon: "users",
              color: "var(--blue-600)",
              bg: "var(--blue-50)",
              subtitle: `In ${stats.total_classes || 0} classes`
            })}
          </div>
          <div class="col-12 col-sm-6 col-lg-3 mb-3">
            ${this.render_number_widget({
              label: "My Classes",
              value: stats.total_classes || 0,
              icon: "grid",
              color: "var(--green-600)",
              bg: "var(--green-50)",
              subtitle: "Assigned"
            })}
          </div>
          <div class="col-12 col-sm-6 col-lg-3 mb-3">
            ${this.render_number_widget({
              label: "Attendance Today",
              value: stats.attendance_marked || 0,
              icon: "tick",
              color: "var(--cyan-600)",
              bg: "var(--cyan-50)",
              subtitle: "Students marked"
            })}
          </div>
          <div class="col-12 col-sm-6 col-lg-3 mb-3">
            ${this.render_number_widget({
              label: "Pending Results",
              value: stats.pending_results || 0,
              icon: "edit",
              color: "var(--orange-600)",
              bg: "var(--orange-50)",
              subtitle: stats.pending_approval > 0 ? `${stats.pending_approval} awaiting approval` : "To submit"
            })}
          </div>
        </div>

        <!-- Main Grid -->
        <div class="row">
          <!-- Left Column -->
          <div class="col-md-8 mb-4">
            <!-- My Classes Widget -->
            <div class="frappe-card mb-4">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="section-title mb-0">${__("My Classes")}</div>
                <a href="/desk/student-group" class="text-muted text-decoration-none" style="font-size: 12px;">${__("View All")}</a>
              </div>
              ${this.render_my_classes()}
            </div>

            <!-- Attendance Chart -->
            <div class="frappe-card mb-4">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="section-title mb-0">${__("Attendance Trend")} <span class="text-muted font-weight-normal ml-2" style="font-size: 12px;">${__("Last 7 days")}</span></div>
              </div>
              <div class="chart-container" id="teacher-attendance-chart"></div>
            </div>

            <!-- Recent Activity -->
            <div class="frappe-card">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="section-title mb-0">${__("Recent Activity")}</div>
              </div>
              ${this.render_activity()}
            </div>
          </div>

          <!-- Right Column -->
          <div class="col-md-4 mb-4">
            <!-- Quick Actions Widget -->
            <div class="frappe-card mb-4">
              <div class="section-title mb-3">${__("Quick Actions")}</div>
              ${this.render_quick_actions()}
            </div>

            <!-- My Timetable Widget -->
            <div class="frappe-card mb-4">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="section-title mb-0">${__("My Timetable")} <span class="text-muted font-weight-normal ml-2" style="font-size: 12px;">${__("This Week")}</span></div>
                <a href="/desk/course-schedule?instructor=${instructor.name || ''}" class="text-muted text-decoration-none" style="font-size: 12px;">${__("View All")}</a>
              </div>
              ${this.render_timetable()}
            </div>

            <!-- Upcoming Assessments Widget -->
            <div class="frappe-card mb-4">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="section-title mb-0">${__("Upcoming Assessments")}</div>
              </div>
              ${this.render_upcoming_assessments()}
            </div>

            <!-- Pending Results Widget -->
            <div class="frappe-card">
              <div class="d-flex align-items-center mb-3">
                <span class="section-title mb-0">${__("Results to Submit")}</span>
                ${(this.data.pending_results || []).length > 0 ? `
                  <span class="badge badge-warning ml-2" style="font-size: 10px; padding: 2px 6px;">${this.data.pending_results.length}</span>
                ` : ""}
              </div>
              ${this.render_pending_results()}
            </div>
          </div>
        </div>
      </div>
    `);

    setTimeout(() => this.render_attendance_chart(), 100);
  }

  render_number_widget({ label, value, icon, color, bg, subtitle }) {
    return `
      <div class="frappe-card h-100 d-flex flex-column justify-content-center">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <span class="text-muted text-uppercase" style="font-size: 11px; font-weight: 600; letter-spacing: 0.02em;">${label}</span>
          <span class="text-muted" style="opacity: 0.7;">
            ${frappe.utils.icon(icon, "sm")}
          </span>
        </div>
        <div style="font-size: 28px; font-weight: 600; color: var(--text-color); line-height: 1;">${value}</div>
        ${subtitle ? `<div class="text-muted mt-2" style="font-size: 12px;">${subtitle}</div>` : ''}
      </div>
    `;
  }

  render_my_classes() {
    const classes = this.data.my_classes || [];

    if (classes.length === 0) {
      return `
        <div class="empty-state">
          <div class="empty-state-icon" style="color: var(--gray-400);">
            ${frappe.utils.icon("folder", "lg")}
          </div>
          <p class="mb-0" style="font-size: 13px;">${__("No classes assigned yet")}</p>
        </div>
      `;
    }

    return `
      <div class="table-responsive">
        <table class="table table-sm mb-0" style="font-size: 13px;">
          <thead>
            <tr class="text-muted" style="font-size: 11px; text-transform: uppercase;">
              <th style="border-top: none;">${__("Class")}</th>
              <th style="border-top: none;">${__("Program")}</th>
              <th style="border-top: none; text-align: right;">${__("Students")}</th>
              <th style="border-top: none;"></th>
            </tr>
          </thead>
          <tbody>
            ${classes.slice(0, 5).map(cls => `
              <tr>
                <td><a href="/desk/student-group/${cls.name}">${cls.student_group_name}</a></td>
                <td class="text-muted">${cls.program || '-'}</td>
                <td style="text-align: right;">${cls.student_count || 0}</td>
                <td style="text-align: right;">
                  <a href="/desk/enhanced-student-attendance-tool?student_group=${cls.name}" class="btn btn-xs btn-default" title="${__("Mark Attendance")}">
                    ${frappe.utils.icon("tick", "xs")}
                  </a>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  render_quick_actions() {
    const instructor = this.data.instructor || {};
    const actions = [
      { label: "Mark Attendance", route: "/desk/enhanced-student-attendance-tool", icon: "tick" },
      { label: "Enter Marks", route: "/desk/assessment-result/new", icon: "edit" },
      { label: "Bulk Enter Marks", route: "/desk/assessment-result-tool", icon: "list" },
      { label: "My Timetable", route: "/desk/course-schedule?instructor=" + (instructor.name || ''), icon: "calendar" },
      { label: "Student Logs", route: "/desk/student-log", icon: "file-text" },
    ];

    return `
      <div class="d-flex flex-column list-group-wrapper">
        ${actions.map(action => `
          <a href="${action.route}" class="list-item text-decoration-none">
            <span class="list-item-icon">
              ${frappe.utils.icon(action.icon, "sm")}
            </span>
            <span class="text-muted text-truncate">${__(action.label)}</span>
          </a>
        `).join("")}
      </div>
    `;
  }

  render_timetable() {
    const timetable = this.data.my_timetable || [];

    if (timetable.length === 0) {
      return `
        <div class="empty-state">
          <div class="empty-state-icon" style="color: var(--gray-400);">
            ${frappe.utils.icon("calendar", "lg")}
          </div>
          <p class="mb-0" style="font-size: 13px;">${__("No classes scheduled this week")}</p>
        </div>
      `;
    }

    const day_colors = {
      "Monday": "var(--blue-500)",
      "Tuesday": "var(--green-500)",
      "Wednesday": "var(--orange-500)",
      "Thursday": "var(--purple-500)",
      "Friday": "var(--cyan-500)",
      "Saturday": "var(--gray-500)",
      "Sunday": "var(--red-500)",
    };

    return `
      <div class="d-flex flex-column">
        ${timetable.map(day => `
          <div style="margin-bottom: 12px;">
            <div style="font-size: 12px; font-weight: 600; color: ${day_colors[day.day] || 'var(--text-muted)'}; margin-bottom: 4px;">
              ${day.day} <span style="font-weight: 400; color: var(--text-muted);">(${frappe.datetime.str_to_user(day.date)})</span>
            </div>
            ${day.schedules.map(s => `
              <div class="list-item text-decoration-none" style="padding: 6px 8px; margin-bottom: 2px;">
                <span class="list-item-icon" style="color: var(--blue-500);">
                  ${frappe.utils.icon("clock", "sm")}
                </span>
                <div class="d-flex flex-column text-truncate" style="flex: 1; min-width: 0;">
                  <span style="font-size: 13px; font-weight: 500;" class="text-truncate">${s.course}</span>
                  <span class="text-muted" style="font-size: 11px;">${s.student_group_name || s.student_group} | ${s.from_time} - ${s.to_time}${s.room ? ' | Room: ' + s.room : ''}</span>
                </div>
              </div>
            `).join("")}
          </div>
        `).join("")}
      </div>
    `;
  }

  render_upcoming_assessments() {
    const assessments = this.data.upcoming_assessments || [];

    if (assessments.length === 0) {
      return `
        <div class="empty-state">
          <div class="empty-state-icon" style="color: var(--gray-400);">
            ${frappe.utils.icon("calendar", "lg")}
          </div>
          <p class="mb-0" style="font-size: 13px;">${__("No upcoming assessments")}</p>
        </div>
      `;
    }

    return `
      <div class="d-flex flex-column list-group-wrapper">
        ${assessments.map(assessment => `
          <a href="/desk/assessment-plan/${assessment.name}" class="list-item text-decoration-none">
            <span class="list-item-icon" style="color: var(--blue-500);">
              ${frappe.utils.icon("calendar", "sm")}
            </span>
            <div class="d-flex flex-column text-truncate">
              <span class="text-truncate">${assessment.assessment_name || assessment.course}</span>
              <span class="text-muted" style="font-size: 11px;">${frappe.datetime.str_to_user(assessment.schedule_date)}</span>
            </div>
          </a>
        `).join("")}
      </div>
    `;
  }

  render_pending_results() {
    const results = this.data.pending_results || [];

    if (results.length === 0) {
      return `
        <div class="empty-state">
          <div class="empty-state-icon" style="color: var(--green-500);">
            ${frappe.utils.icon("solid-success", "lg")}
          </div>
          <p class="mb-0" style="font-size: 13px;">${__("All results submitted!")}</p>
        </div>
      `;
    }

    return `
      <div class="d-flex flex-column list-group-wrapper">
        ${results.slice(0, 5).map(result => {
          const state_color = result.workflow_state === 'Pending Approval' ? 'var(--orange-500)' : 'var(--gray-500)';
          const state_icon = result.workflow_state === 'Pending Approval' ? 'time' : 'edit';
          return `
            <a href="/desk/assessment-result/${result.name}" class="list-item text-decoration-none">
              <span class="list-item-icon" style="color: ${state_color};">
                ${frappe.utils.icon(state_icon, "sm")}
              </span>
              <div class="d-flex flex-column text-truncate">
                <span class="text-truncate">${result.student_name} - ${result.course}</span>
                <span class="text-muted" style="font-size: 11px;">${result.workflow_state || 'Draft'}</span>
              </div>
            </a>
          `;
        }).join("")}
      </div>
    `;
  }

  render_activity() {
    const activities = this.data.recent_activity || [];

    if (activities.length === 0) {
      return `
        <div class="empty-state">
          <div class="empty-state-icon" style="color: var(--gray-400);">
            ${frappe.utils.icon("history", "lg")}
          </div>
          <p class="mb-0" style="font-size: 13px;">${__("No recent activity")}</p>
        </div>
      `;
    }

    const colors = ["green", "blue", "orange", "purple", "cyan"];

    return `
      <div class="d-flex flex-column list-group-wrapper mt-2">
        ${activities.map((activity, index) => {
          const color = colors[index % colors.length];
          const time = activity.time ? frappe.datetime.prettyDate(activity.time) : "";
          const hex_colors = {
            green: "#28a745", blue: "#007bff", orange: "#fd7e14", purple: "#6f42c1", cyan: "#17a2b8"
          };
          
          return `
            <div class="list-item d-flex justify-content-between align-items-center">
              <div class="d-flex align-items-center text-truncate">
                <span class="activity-dot" style="background-color: var(--${color}-500, ${hex_colors[color]});"></span>
                <span class="text-muted text-truncate">${activity.message || ""}</span>
              </div>
              <span class="text-muted" style="font-size: 11px; white-space: nowrap; margin-left: 10px;">${time}</span>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  render_attendance_chart() {
    const data = this.data.attendance_trend || [];

    if (data.length === 0 || data.every(d => d.total === 0)) {
      $("#teacher-attendance-chart").html(`
        <div class="empty-state">
          <div class="empty-state-icon" style="color: var(--gray-400);">
            ${frappe.utils.icon("chart", "lg")}
          </div>
          <p class="mb-0" style="font-size: 13px;">${__("No attendance data available")}</p>
        </div>
      `);
      return;
    }

    new frappe.Chart("#teacher-attendance-chart", {
      data: {
        labels: data.map(d => d.date),
        datasets: [
          {
            name: "Present",
            values: data.map(d => d.present || 0),
            chartType: "bar"
          },
          {
            name: "Absent",
            values: data.map(d => d.absent || 0),
            chartType: "bar"
          }
        ]
      },
      type: "axis-mixed",
      height: 200,
      colors: ["#28a745", "#e1e4e8"],
      barOptions: {
        spaceRatio: 0.3
      },
      axisOptions: {
        xAxisMode: "tick",
        xIsSeries: 1
      },
      tooltipOptions: {
        formatTooltipX: d => d,
        formatTooltipY: d => d + " students"
      }
    });
  }
}
