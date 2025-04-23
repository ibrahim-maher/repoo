    document.addEventListener("DOMContentLoaded", () => {
        const dropdowns = document.querySelectorAll('.nav-link.dropdown-toggle');

        dropdowns.forEach(dropdown => {
            dropdown.addEventListener('click', function (e) {
                e.preventDefault();
                const menu = this.nextElementSibling;

                if (menu && menu.classList.contains('dropdown-menu')) {
                    menu.classList.toggle('show');
                }
            });
        });

        document.addEventListener('click', function (e) {
            if (!e.target.closest('.nav-item')) {
                document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                    menu.classList.remove('show');
                });
            }
        });
    });




