frappe.pages["school-dashboard"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Student Overview",
    single_column: true,
  });

  page.inner_page = true;
  let dashboard = new SchoolDashboard(page);
};

class SchoolDashboard {
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
    this.page.set_title("Student Overview");
    
    // Add a proper refresh button
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
      method: "nl_school.junior_school_customization.page.school_dashboard.school_dashboard.get_dashboard_data",
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
          <h4>${__("Overview")}</h4>
          <span class="date-display">${today}</span>
        </div>

        <!-- Stats Row -->
        <div class="row mb-4">
          <div class="col-12 col-sm-6 col-lg-3 mb-3">
            ${this.render_number_widget({
              label: "Students",
              value: stats.total_students || 0,
              icon: "education",
              color: "var(--blue-600)",
              bg: "var(--blue-50)",
              subtitle: `+${stats.new_students_month || 0} this month`,
              border: "var(--blue-500)"
            })}
          </div>
          <div class="col-12 col-sm-6 col-lg-3 mb-3">
            ${this.render_number_widget({
              label: "Instructors",
              value: stats.total_teachers || 0,
              icon: "assign",
              color: "var(--green-600)",
              bg: "var(--green-50)",
              subtitle: "Active",
              border: "var(--green-500)"
            })}
          </div>
          <div class="col-12 col-sm-6 col-lg-3 mb-3">
            ${this.render_number_widget({
              label: "Attendance",
              value: (stats.attendance_rate || 0) + "%",
              icon: "tick",
              color: "var(--cyan-600)",
              bg: "var(--cyan-50)",
              subtitle: `${stats.present_today || 0} present today`,
              border: "var(--cyan-500)"
            })}
          </div>
          <div class="col-12 col-sm-6 col-lg-3 mb-3">
            ${this.render_number_widget({
              label: "Outstanding",
              value: stats.pending_invoices || 0,
              icon: "money-coins-1",
              color: "var(--orange-600)",
              bg: "var(--orange-50)",
              subtitle: "Pending invoices",
              border: "var(--orange-500)"
            })}
          </div>
        </div>

        <!-- Main Grid -->
        <div class="row">
          <!-- Left Column -->
          <div class="col-md-8 mb-4">
            <!-- Chart Widget -->
            <div class="frappe-card mb-4">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="section-title mb-0">${__("Attendance Trend")} <span class="text-muted font-weight-normal ml-2" style="font-size: 12px;">${__("Last 7 days")}</span></div>
              </div>
              <div class="chart-container" id="attendance-chart"></div>
            </div>

            <!-- Activity Widget -->
            <div class="frappe-card">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="section-title mb-0">${__("Recent Activity")}</div>
                <a href="/desk/activity-log" class="text-muted text-decoration-none" style="font-size: 12px;">${__("View All")}</a>
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

            <!-- Alerts Widget -->
            <div class="frappe-card">
              <div class="d-flex align-items-center mb-3">
                <span class="section-title mb-0">${__("Needs Attention")}</span>
                ${(this.data.alerts || []).length > 0 ? `
                  <span class="badge badge-danger ml-2" style="font-size: 10px; padding: 2px 6px;">${this.data.alerts.length}</span>
                ` : ""}
              </div>
              ${this.render_alerts()}
            </div>
          </div>
        </div>
      </div>
    `);

    setTimeout(() => this.render_attendance_chart(), 100);
  }

  render_number_widget({ label, value, icon, color, bg, subtitle, border }) {
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

  render_quick_actions() {
    const actions = [
      { label: "Mark Attendance", route: "/desk/student-attendance-tool", icon: "tick" },
      { label: "Collect Fees", route: "/desk/sales-invoice/new", icon: "money-coins-1" },
      { label: "New Enrollment", route: "/desk/program-enrollment/new", icon: "add" },
      { label: "View Timetable", route: "/desk/school-timetable", icon: "today" },
      { label: "Assessment Results", route: "/desk/assessment-result", icon: "chart" },
      { label: "Student List", route: "/desk/student", icon: "list-alt" }
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
          const color_var = alert.type === "danger" ? "var(--red-500, #ff5858)" : alert.type === "warning" ? "var(--orange-500, #ffa00a)" : "var(--blue-500, #2490ef)";
          const link = alert.link || "#";
          
          return `
            <a href="${link}" class="list-item text-decoration-none">
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

    if (data.length === 0) {
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
        labels: data.map(d => {
          if (!d.date) return "";
          try {
            // Format as weekday abbreviation
            const date = new Date(d.date);
            if (isNaN(date.getTime())) {
              return d.date.substring(5); // Fallback to MM-DD
            }
            return date.toLocaleDateString("en-US", { weekday: "short" });
          } catch(e) {
            return d.date;
          }
        }),
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
