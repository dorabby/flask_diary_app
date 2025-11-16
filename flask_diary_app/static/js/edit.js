// 編集画面js
import { setupImagePreview } from "./image_preview.js";

document.addEventListener("DOMContentLoaded", () => {
    setupImagePreview({
        fileInput: document.getElementById("imageInput"),
        newPreview: document.getElementById("newPreview"),
        newPreviewContainer: document.getElementById("newPreviewContainer"),
        clearNewPreviewBtn: document.getElementById("clearNewPreviewBtn"),
        noImageCheck: document.getElementById("noImageCheck"),
        existingPreview: document.getElementById("existingPreview"),
        existingPreviewContainer: document.getElementById("existingPreviewContainer")
    });
});
