// 新規登録画面js
import { setupImagePreview } from "./image_preview.js";

window.addEventListener('load', formSwitch);

function formSwitch() {
    const createForm = document.getElementsByClassName("createForm")[0];
    const importForm = document.getElementsByClassName("importForm")[0];
    const mode = document.getElementsByClassName("mode");
    if (mode[0].checked) {
        createForm.style.display="";
        importForm.style.display="none";
    } else {
        createForm.style.display="none";
        importForm.style.display="";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // 初期表示
    formSwitch();

    // ラジオ切り替え
    document.querySelectorAll(".mode").forEach(radio => {
        radio.addEventListener("change", formSwitch);
    });

    setupImagePreview({
        fileInput: document.getElementById("imageInput"),
        newPreview: document.getElementById("newPreview"),
        newPreviewContainer: document.getElementById("newPreviewContainer"),
        clearNewPreviewBtn: document.getElementById("clearNewPreviewBtn"),

        // 新規登録は以下は不要なのでnull
        noImageCheck: null,
        existingPreview: null,
        existingPreviewContainer: null,
    });
});