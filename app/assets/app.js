document.addEventListener("DOMContentLoaded", function () {
  const currentPath = window.location.pathname;
  document.querySelectorAll(".nav-item").forEach(function (item) {
    const href = item.getAttribute("href");
    if (currentPath.startsWith(href) && href !== "/") {
      item.classList.add("active");
    } else if (currentPath === "/" && href === "/dashboard") {
      item.classList.add("active");
    }
  });
});
