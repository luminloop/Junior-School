frappe.pages["coordinator-dashboard"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Academic Coordinator Dashboard",
    single_column: true,
  });

  page.inner_page = true;
  let dashboard = new CoordinatorDashboard(page);
};

class CoordinatorDashboard {
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
    this.page.set_title("Academic Coordinator Dashboard");
    
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
      method: "nl_school.junior_school_customization.page.coordinator_dashboard.coordinator_dashboard.get_dashboard_data",
      callback: (r) => {
        if (r.message) {
          this.data = r.message;
          this.render();
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

  render() {
    const stats = this.data.stats;
    const today = frappe.datetime.str_to_user(frappe.datetime.get_today());

    this.wrapper.html(`
      <div class="school-dashboard-wrapper">
        <!-- Header -->
        <div class="dashboard-header">
          <div>
            <h4>${__("Academic Overview")}</h4>
            <span class="text-muted" style="font-size: 13px;">${__("Monitor teachers, approvals, and academic activities")}</span>
          </div>
          <span class="date-display">${today}</span>
        </div>

        <!-- Stats Row -->
        <div class="row mb-4">
          <div class="col-12 col-sm-6 col-lg-3 mb-3">
            ${this.render_number_widget({
              label: "Teachers",
              value: stats.total_teachers || 0,
              icon: "users",
              color: "var(--blue-600)",
              subtitle: `Managing ${stats.total_classes || 0} classes`
            })}
          </div>
          <div class="col-12 col-sm-6 col-lg-3 mb-3">
            ${this.render_number_widget({
              label: "Students",
              value: stats.total_students || 0,
              icon: "education",
              color: "var(--green-600)",
              subtitle: `${stats.attendance_rate || 0}% present today`
            })}
          </div>
          <div class="col-12 col-sm-6 col-lg-3 mb-3">
            ${this.render_number_widget({
              label: "Pending Approvals",
              value: stats.pending_approvals || 0,
              icon: "time",
              color: stats.pending_approvals > 0 ? "var(--orange-600)" : "var(--green-600)",
              subtitle: stats.draft_results > 0 ? `${stats.draft_results} drafts` : "All caught up"
            })}
          </div>
          <div class="col-12 col-sm-6 col-lg-3 mb-3">
            ${this.render_number_widget({
              label: "Upcoming Exams",
              value: stats.upcoming_assessments || 0,
              icon: "calendar",
              color: "var(--purple-600)",
              subtitle: "This week"
            })}
          </div>
        </div>

        <!-- Main Grid -->
        <div class="row">
          <!-- Left Column -->
          <div class="col-md-8 mb-4">
            <!-- Pending Approvals Widget -->
            <div class="frappe-card mb-4">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="section-title mb-0">
                  ${__("Pending Approvals")}
                  ${(this.data.pending_approvals || []).length > 0 ? `
                    <span class="badge badge-warning ml-2" style="font-size: 10px;">${this.data.pending_approvals.length}</span>
                  ` : ""}
                </div>
                <a href="/desk/assessment-result?workflow_state=Pending+Approval" class="text-muted text-decoration-none" style="font-size: 12px;">${__("View All")}</a>
              </div>
              ${this.render_pending_approvals()}
            </div>

            <!-- Teacher Summary Widget -->
            <div class="frappe-card mb-4">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="section-title mb-0">${__("Teacher Workload")}</div>
                <a href="/desk/instructor" class="text-muted text-decoration-none" style="font-size: 12px;">${__("View All")}</a>
              </div>
              ${this.render_teacher_summary()}
            </div>

            <!-- Attendance Chart -->
            <div class="frappe-card">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="section-title mb-0">${__("School Attendance")} <span class="text-muted font-weight-normal ml-2" style="font-size: 12px;">${__("Last 7 days")}</span></div>
              </div>
              <div class="chart-container" id="attendance-chart"></div>
            </div>
          </div>

          <!-- Right Column -->
          <div class="col-md-4 mb-4">
            <!-- Quick Actions Widget -->
            <div class="frappe-card mb-4">
              <div class="section-title mb-3">${__("Quick Actions")}</div>
              ${this.render_quick_actions()}
            </div>

            <!-- Alerts Widget -->
            <div class="frappe-card mb-4">
              <div class="d-flex align-items-center mb-3">
                <span class="section-title mb-0">${__("Needs Attention")}</span>
                ${(this.data.alerts || []).length > 0 ? `
                  <span class="badge badge-danger ml-2" style="font-size: 10px; padding: 2px 6px;">${this.data.alerts.length}</span>
                ` : ""}
              </div>
              ${this.render_alerts()}
            </div>

            <!-- Recent Activity -->
            <div class="frappe-card">
              <div class="section-title mb-3">${__("Recent Activity")}</div>
              ${this.render_activity()}
            </div>
          </div>
        </div>
      </div>
    `);

    setTimeout(() => this.render_attendance_chart(), 100);
  }

  render_number_widget({ label, value, icon, color, subtitle }) {
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

  render_pending_approvals() {
    const approvals = this.data.pending_approvals || [];

    if (approvals.length === 0) {
      return `
        <div class="empty-state">
          <div class="empty-state-icon" style="color: var(--green-500);">
            ${frappe.utils.icon("solid-success", "lg")}
          </div>
          <p class="mb-0" style="font-size: 13px;">${__("No pending approvals!")}</p>
        </div>
      `;
    }

    return `
      <div class="table-responsive">
        <table class="table table-sm mb-0" style="font-size: 13px;">
          <thead>
            <tr class="text-muted" style="font-size: 11px; text-transform: uppercase;">
              <th style="border-top: none;">${__("Student")}</th>
              <th style="border-top: none;">${__("Subject")}</th>
              <th style="border-top: none;">${__("Score")}</th>
              <th style="border-top: none;">${__("Submitted By")}</th>
              <th style="border-top: none;"></th>
            </tr>
          </thead>
          <tbody>
            ${approvals.slice(0, 8).map(app => `
              <tr>
                <td><a href="/desk/assessment-result/${app.name}">${app.student_name}</a></td>
                <td class="text-muted">${app.course || '-'}</td>
                <td>${app.total_score || '-'} ${app.grade ? `(${app.grade})` : ''}</td>
                <td class="text-muted">${app.submitted_by || '-'}</td>
                <td style="text-align: right;">
                  <a href="/desk/assessment-result/${app.name}" class="btn btn-xs btn-primary">
                    ${__("Review")}
                  </a>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  render_teacher_summary() {
    const teachers = this.data.teacher_summary || [];

    if (teachers.length === 0) {
      return `
        <div class="empty-state">
          <div class="empty-state-icon" style="color: var(--gray-400);">
            ${frappe.utils.icon("users", "lg")}
          </div>
          <p class="mb-0" style="font-size: 13px;">${__("No active teachers")}</p>
        </div>
      `;
    }

    return `
      <div class="table-responsive">
        <table class="table table-sm mb-0" style="font-size: 13px;">
          <thead>
            <tr class="text-muted" style="font-size: 11px; text-transform: uppercase;">
              <th style="border-top: none;">${__("Teacher")}</th>
              <th style="border-top: none; text-align: center;">${__("Classes")}</th>
              <th style="border-top: none; text-align: center;">${__("Pending")}</th>
              <th style="border-top: none; text-align: center;">${__("Drafts")}</th>
            </tr>
          </thead>
          <tbody>
            ${teachers.map(t => `
              <tr>
                <td><a href="/desk/instructor/${t.name}">${t.instructor_name}</a></td>
                <td style="text-align: center;">${t.class_count || 0}</td>
                <td style="text-align: center;">
                  ${t.pending_approvals > 0 ? `
                    <span class="badge badge-warning">${t.pending_approvals}</span>
                  ` : '-'}
                </td>
                <td style="text-align: center;">
                  ${t.draft_results > 0 ? `
                    <span class="badge badge-secondary">${t.draft_results}</span>
                  ` : '-'}
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  render_quick_actions() {
    const actions = [
      { label: "Review Pending Results", route: "/desk/assessment-result?workflow_state=Pending+Approval", icon: "tick" },
      { label: "View All Results", route: "/desk/assessment-result", icon: "chart" },
      { label: "Generate Report Cards", route: "/desk/student-report-generation-tool", icon: "file-text" },
      { label: "Batch Print Reports", route: "/desk/batch-report-card", icon: "printer" },
      { label: "Send Grade Alerts", route: "/desk/grade-notification-tool", icon: "send" },
      { label: "View Teachers", route: "/desk/instructor", icon: "users" },
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

  render_alerts() {
    const alerts = this.data.alerts || [];

    if (alerts.length === 0) {
      return `
        <div class="empty-state">
          <div class="empty-state-icon" style="color: var(--green-500);">
            ${frappe.utils.icon("solid-success", "lg")}
          </div>
          <p class="mb-0" style="font-size: 13px;">${__("Everything looks good!")}</p>
        </div>
      `;
    }

    return `
      <div class="d-flex flex-column list-group-wrapper">
        ${alerts.map(alert => {
          const icon_name = alert.type === "danger" ? "solid-error" : alert.type === "warning" ? "solid-warning" : "solid-info";
          const color_var = alert.type === "danger" ? "var(--red-500)" : alert.type === "warning" ? "var(--orange-500)" : "var(--blue-500)";
          
          return `
            <a href="${alert.link || '#'}" class="list-item text-decoration-none">
              <span class="list-item-icon" style="color: ${color_var};">
                ${frappe.utils.icon(icon_name, "sm")}
              </span>
              <span class="text-muted text-truncate">${alert.message}</span>
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
        ${activities.slice(0, 6).map((activity, index) => {
          const color = colors[index % colors.length];
          const time = activity.time ? frappe.datetime.prettyDate(activity.time) : "";
          
          return `
            <div class="list-item d-flex justify-content-between align-items-center">
              <div class="d-flex align-items-center text-truncate">
                <span class="activity-dot" style="background-color: var(--${color}-500);"></span>
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
      $("#attendance-chart").html(`
        <div class="empty-state">
          <div class="empty-state-icon" style="color: var(--gray-400);">
            ${frappe.utils.icon("chart", "lg")}
          </div>
          <p class="mb-0" style="font-size: 13px;">${__("No attendance data available")}</p>
        </div>
      `);
      return;
    }

    new frappe.Chart("#attendance-chart", {
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
