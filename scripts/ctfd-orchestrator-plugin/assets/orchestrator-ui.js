(function () {
  if (document.getElementById("orchestrator-nav-link")) return;

  var a = document.createElement("a");
  a.id = "orchestrator-nav-link";
  a.href = "/plugins/orchestrator/dashboard";
  a.innerHTML =
    '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" ' +
    'viewBox="0 0 16 16" aria-hidden="true" style="flex-shrink:0">' +
    '<path d="M0 1a1 1 0 0 1 1-1h5a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1H1a1 1 0 0 1-1-1V1z' +
    'M9 0a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1V1a1 1 0 0 0-1-1z' +
    'M0 9a1 1 0 0 1 1-1h5a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H1a1 1 0 0 1-1-1z' +
    'M10 11a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1z"/>' +
    "</svg>" +
    '<span style="white-space:nowrap">Dashboard</span>';

  a.style.cssText = [
    "position:fixed",
    "bottom:20px",
    "right:20px",
    "z-index:9999",
    "display:flex",
    "align-items:center",
    "gap:6px",
    "padding:8px 14px",
    "background:rgba(13,22,36,0.88)",
    "color:#a0b4cc",
    "border:1px solid #2a3548",
    "border-radius:10px",
    "font-size:0.82rem",
    "font-weight:600",
    "text-decoration:none",
    "letter-spacing:0.3px",
    "backdrop-filter:blur(8px)",
    "box-shadow:0 4px 20px rgba(0,0,0,0.35)",
    "transition:color .2s,border-color .2s,background .2s"
  ].join(";");

  a.addEventListener("mouseenter", function () {
    a.style.color = "#e6edf7";
    a.style.borderColor = "#4a6080";
    a.style.background = "rgba(13,22,36,0.98)";
  });
  a.addEventListener("mouseleave", function () {
    a.style.color = "#a0b4cc";
    a.style.borderColor = "#2a3548";
    a.style.background = "rgba(13,22,36,0.88)";
  });

  function mount() {
    if (document.getElementById("orchestrator-nav-link")) return;
    document.body.appendChild(a);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();
