document.addEventListener('DOMContentLoaded', function () {
    var toggleBtn = document.getElementById('sidebarToggle');
    var sidebar   = document.getElementById('sidebar');

    // Create overlay element
    var overlay = document.createElement('div');
    overlay.id  = 'sidebar-overlay';
    document.body.appendChild(overlay);

    function openSidebar() {
        sidebar.classList.add('active');
        overlay.style.display = 'block';
        toggleBtn.textContent = '✕';
    }

    function closeSidebar() {
        sidebar.classList.remove('active');
        overlay.style.display = 'none';
        toggleBtn.textContent = '☰';
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function () {
            sidebar.classList.contains('active') ? closeSidebar() : openSidebar();
        });
    }

    // Tap overlay to close
    overlay.addEventListener('click', closeSidebar);

    // Close sidebar when a nav link is tapped on mobile
    var navLinks = sidebar ? sidebar.querySelectorAll('a') : [];
    navLinks.forEach(function (link) {
        link.addEventListener('click', function () {
            if (window.innerWidth <= 768) closeSidebar();
        });
    });
});
