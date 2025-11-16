// 画像プレビュー関連js
export function setupImagePreview({
    fileInput,
    newPreview,
    newPreviewContainer,
    clearNewPreviewBtn,
    noImageCheck = null,
    existingPreview = null,
    existingPreviewContainer = null
}) {
    if (!fileInput || !newPreview || !newPreviewContainer || !clearNewPreviewBtn) return;

    // 初期表示：編集画面用
    if (noImageCheck && noImageCheck.checked) {
        if (existingPreviewContainer) existingPreviewContainer.classList.add("hidden");
        newPreviewContainer.classList.add("hidden");
        fileInput.disabled = true;
        fileInput.style.opacity = 0.5;
    }

    // 「画像を使用しない」チェック変更（編集画面のみ）
    if (noImageCheck) {
        noImageCheck.addEventListener("change", () => {
            if (noImageCheck.checked) {
                if (existingPreviewContainer) existingPreviewContainer.classList.add("hidden");
                newPreviewContainer.classList.add("hidden");

                // 新規選択画像クリア
                fileInput.value = "";
                newPreview.src = "";
                if (existingPreview) existingPreview.src = "";

                fileInput.disabled = true;
                fileInput.style.opacity = 0.5;
            } else {
                const originalSrc = existingPreview?.dataset?.original || "";
                fileInput.disabled = false;
                fileInput.style.opacity = 1;

                if (originalSrc && existingPreview && existingPreviewContainer) {
                    existingPreview.src = originalSrc;
                    existingPreviewContainer.classList.remove("hidden");
                }
            }
        });
    }

    // ファイル選択 → 新規プレビュー表示
    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (file) {
            newPreview.src = URL.createObjectURL(file);
            newPreview.style.display = "block";
            newPreviewContainer.classList.remove("hidden");
            clearNewPreviewBtn.style.display = "inline-block";

            // 編集画面は「画像を使用しない」チェックをOFFかつ無効化
            if (noImageCheck) {
                noImageCheck.checked = false;
                noImageCheck.disabled = true;
                noImageCheck.parentElement.style.opacity = 0.5;
            }
        } else {
            // ファイル選択キャンセル時
            newPreview.src = "";
            newPreview.style.display = "none";
            newPreviewContainer.classList.add("hidden");
            clearNewPreviewBtn.style.display = "none";

            if (noImageCheck) {
                noImageCheck.disabled = false;
                noImageCheck.parentElement.style.opacity = 1;
            }
        }
    });

    // ×ボタン → 新規プレビュー削除
    clearNewPreviewBtn.addEventListener("click", () => {
        newPreview.src = "";
        newPreview.style.display = "none";
        newPreviewContainer.classList.add("hidden");
        fileInput.value = "";

        if (noImageCheck) {
            noImageCheck.disabled = false;
            noImageCheck.parentElement.style.opacity = 1;
        }
    });
}
