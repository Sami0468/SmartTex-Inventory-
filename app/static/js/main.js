// SmartTex Inventory — global UI behavior

document.addEventListener("DOMContentLoaded", () => {
  // Mobile sidebar toggle
  const menuBtn = document.querySelector(".mobile-menu-btn");
  const sidebar = document.querySelector(".sidebar");
  const backdrop = document.querySelector(".sidebar-backdrop");

  function openSidebar() {
    sidebar?.classList.add("open");
    backdrop?.classList.add("open");
  }
  function closeSidebar() {
    sidebar?.classList.remove("open");
    backdrop?.classList.remove("open");
  }
  menuBtn?.addEventListener("click", openSidebar);
  backdrop?.addEventListener("click", closeSidebar);

  // Auto-dismiss flash alerts after 6s
  document.querySelectorAll(".alert[data-autodismiss]").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 6000);
  });

  // Dropdown menus (user chip, notifications)
  document.querySelectorAll("[data-dropdown-toggle]").forEach((toggle) => {
    const targetId = toggle.getAttribute("data-dropdown-toggle");
    const menu = document.getElementById(targetId);
    if (!menu) return;
    toggle.addEventListener("click", (e) => {
      e.stopPropagation();
      document.querySelectorAll(".dropdown-menu.open").forEach((m) => {
        if (m !== menu) m.classList.remove("open");
      });
      menu.classList.toggle("open");
    });
  });
  document.addEventListener("click", () => {
    document.querySelectorAll(".dropdown-menu.open").forEach((m) => m.classList.remove("open"));
  });

  // Confirm-delete prompts
  document.querySelectorAll("[data-confirm]").forEach((el) => {
    el.addEventListener("submit", (e) => {
      const msg = el.getAttribute("data-confirm") || "Are you sure?";
      if (!confirm(msg)) e.preventDefault();
    });
  });

  // Searchable client-side tables (simple filter)
  document.querySelectorAll("[data-table-search]").forEach((input) => {
    const tableId = input.getAttribute("data-table-search");
    const table = document.getElementById(tableId);
    if (!table) return;
    input.addEventListener("input", () => {
      const term = input.value.toLowerCase();
      table.querySelectorAll("tbody tr").forEach((row) => {
        row.style.display = row.textContent.toLowerCase().includes(term) ? "" : "none";
      });
    });
  });
});
