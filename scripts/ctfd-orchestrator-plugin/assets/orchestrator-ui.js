(function () {
  function mountNavLink() {
    if (document.getElementById("orchestrator-nav-link")) return;

    // Target CTFd's Bootstrap navbar — prefer the rightmost nav-list (user links)
    const navLists = document.querySelectorAll("ul.navbar-nav");
    const navList = navLists[navLists.length - 1] || navLists[0];
    if (!navList) return;

    const item = document.createElement("li");
    item.className = "nav-item";

    const link = document.createElement("a");
    link.id = "orchestrator-nav-link";
    link.href = "/plugins/orchestrator/dashboard";
    link.className = "nav-link";
    link.style.display = "flex";
    link.style.alignItems = "center";
    link.style.gap = "5px";
    link.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16" aria-hidden="true">' +
      '<path d="M0 1a1 1 0 0 1 1-1h5a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1H1a1 1 0 0 1-1-1V1zm9 0a1 1 0 0 1 1-1h5a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1h-5a1 1 0 0 1-1-1V1zM0 9a1 1 0 0 1 1-1h5a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H1a1 1 0 0 1-1-1V9zm9 3a1 1 0 0 1 1-1h5a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-5a1 1 0 0 1-1-1v-3z"/>' +
      "</svg>Dashboard";

    item.appendChild(link);
    navList.appendChild(item);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountNavLink);
  } else {
    mountNavLink();
  }

  // Re-run on SPA navigation (CTFd uses AJAX for challenge modals)
  const observer = new MutationObserver(mountNavLink);
  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: false });
  }
})();
