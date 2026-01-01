// 検索欄処理
document.addEventListener("DOMContentLoaded", () => {
    const searchBox = document.querySelector(".search-box");
    const searchInput = searchBox.querySelector(".search-input");

    searchInput.addEventListener("input", toggleClearButton);
    // クリアボタン表示処理
    function toggleClearButton() {
        if (searchInput.value.trim() !== "") {
            searchBox.classList.add("has-value");
        } else {
            searchBox.classList.remove("has-value");
        }
    }

    // クリアボタン処理
    const clearBtn = searchBox.querySelector(".search-clear-btn");
    clearBtn.addEventListener("click", (e) => {
        e.preventDefault();
        searchInput.value = "";
        toggleClearButton();
        searchInput.focus();
    });

    //検索後画面でも発火させる
    toggleClearButton();
});


