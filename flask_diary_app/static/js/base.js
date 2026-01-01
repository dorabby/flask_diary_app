// テーマ変更関連処理
document.addEventListener("DOMContentLoaded", () => {
    const themeLink = document.getElementById("themeStylesheet");
    const toggleBtn = document.getElementById("themeToggleBtn");
    const icon = document.getElementById("themeIcon");

    let theme = localStorage.getItem("theme");
    if (!theme) {
        theme = "light";
        localStorage.setItem("theme", theme);
    }

    changeTheme(theme);

    toggleBtn.addEventListener("click", () => {
        theme = theme === "light" ? "dark" : "light";
        localStorage.setItem("theme", theme);
        changeTheme(theme);
    });

    function changeTheme(theme) {
        themeLink.href = `/static/css/${theme}.css`;

        if (theme === "light") {
            icon.className = "bi bi-sun-fill";
        } else {
            icon.className = "bi bi-moon-fill";
        }
    }
});
