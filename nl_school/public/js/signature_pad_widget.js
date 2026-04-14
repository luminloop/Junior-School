// Tiny inline signature pad widget. Renders a canvas + clear button into the
// given wrapper, and writes the data URL into the bound form field.
//
// Usage:
//   nl_school.init_signature_pad(frm, "principal_signature_pad", "principal_signature_data");
//
// The wrapper is the $wrapper of the HTML field; the data field stores the
// resulting PNG data URL (or empty when cleared).

window.nl_school = window.nl_school || {};

window.nl_school.init_signature_pad = function (frm, html_fieldname, data_fieldname) {
    const html_field = frm.get_field(html_fieldname);
    if (!html_field || !html_field.$wrapper) return;

    const $wrapper = html_field.$wrapper;
    if ($wrapper.data("signature-initialized")) {
        // Re-sync existing data in case the form was reloaded
        const existing = frm.doc[data_fieldname];
        if (existing) {
            const canvas = $wrapper.find("canvas")[0];
            const ctx = canvas && canvas.getContext("2d");
            if (canvas && ctx) {
                const img = new Image();
                img.onload = () => ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                img.src = existing;
            }
        }
        return;
    }
    $wrapper.data("signature-initialized", true);

    $wrapper.html(`
        <div class="nl-signature-pad" style="border: 1px solid #d1d5db; border-radius: 6px; background: #fff; padding: 8px; max-width: 420px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 12px; color: #6b7280;">Sign in the box below</span>
                <button type="button" class="btn btn-xs btn-default nl-signature-clear">Clear</button>
            </div>
            <canvas
                width="400"
                height="140"
                style="display: block; width: 100%; height: 140px; border: 1px dashed #cbd5e1; border-radius: 4px; background: #f9fafb; touch-action: none; cursor: crosshair;"
            ></canvas>
        </div>
    `);

    const canvas = $wrapper.find("canvas")[0];
    const ctx = canvas.getContext("2d");
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#111827";

    let drawing = false;
    let last = null;
    let isEmpty = true;

    function pos(e) {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const cx = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
        const cy = (e.touches ? e.touches[0].clientY : e.clientY) - rect.top;
        return { x: cx * scaleX, y: cy * scaleY };
    }

    function start(e) {
        e.preventDefault();
        drawing = true;
        last = pos(e);
    }
    function move(e) {
        if (!drawing) return;
        e.preventDefault();
        const p = pos(e);
        ctx.beginPath();
        ctx.moveTo(last.x, last.y);
        ctx.lineTo(p.x, p.y);
        ctx.stroke();
        last = p;
        isEmpty = false;
    }
    function end() {
        if (!drawing) return;
        drawing = false;
        if (!isEmpty) {
            frm.set_value(data_fieldname, canvas.toDataURL("image/png"));
        }
    }

    canvas.addEventListener("mousedown", start);
    canvas.addEventListener("mousemove", move);
    window.addEventListener("mouseup", end);
    canvas.addEventListener("touchstart", start, { passive: false });
    canvas.addEventListener("touchmove", move, { passive: false });
    canvas.addEventListener("touchend", end);

    $wrapper.find(".nl-signature-clear").on("click", function () {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        isEmpty = true;
        frm.set_value(data_fieldname, "");
    });

    // Restore any previously captured signature
    const existing = frm.doc[data_fieldname];
    if (existing) {
        const img = new Image();
        img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            isEmpty = false;
        };
        img.src = existing;
    }
};
