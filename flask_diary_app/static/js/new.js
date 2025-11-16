// 新規登録画面js
import { setupImagePreview } from "./image_preview.js";

document.addEventListener("DOMContentLoaded", () => {
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
