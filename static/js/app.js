
"use strict";

// ==========================================
// API CONFIGURATION
// ==========================================

// Your main.py currently uses:
// app.include_router(router)
// If the routes have no additional prefix,
// these URLs are correct.

const CHAT_API_URL = "/api/chat";
const UPLOAD_API_URL = "/api/upload";

// ==========================================
// INITIALIZATION
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    // Chat elements
    const chatForm = document.getElementById("chatForm");
    const questionInput = document.getElementById("questionInput");
    const sendBtn = document.getElementById("sendBtn");
    const messages = document.getElementById("messages");
    const chatContainer = document.getElementById("chatContainer");
    const welcome = document.getElementById("welcome");

    // Sidebar elements
    const newChatBtn = document.getElementById("newChatBtn");
    const menuBtn = document.getElementById("menuBtn");
    const sidebar = document.getElementById("sidebar");

    // Upload elements
    const addDocumentsBtn =
        document.getElementById("addDocumentsBtn");

    const uploadModal =
        document.getElementById("uploadModal");

    const closeUploadModalBtn =
        document.getElementById("closeUploadModal");

    const uploadDocumentForm =
        document.getElementById("uploadDocumentForm");

    const adminApiKeyInput =
        document.getElementById("adminApiKey");

    const documentFileInput =
        document.getElementById("documentFile");

    const selectedFileName =
        document.getElementById("selectedFileName");

    const indexDocumentBtn =
        document.getElementById("indexDocumentBtn");

    const uploadStatus =
        document.getElementById("uploadStatus");

    // Verify all required HTML elements
    const requiredElements = {
        chatForm,
        questionInput,
        sendBtn,
        messages,
        chatContainer,
        welcome,
        newChatBtn,
        menuBtn,
        sidebar,
        addDocumentsBtn,
        uploadModal,
        closeUploadModalBtn,
        uploadDocumentForm,
        adminApiKeyInput,
        documentFileInput,
        selectedFileName,
        indexDocumentBtn,
        uploadStatus
    };

    const missing = Object.entries(requiredElements)
        .filter(([name, element]) => !element)
        .map(([name]) => name);

    if (missing.length > 0) {
        console.error(
            "Missing HTML elements:",
            missing
        );
        return;
    }

    console.log("Enterprise RAG frontend initialized.");

    let isLoading = false;
    let isUploading = false;
    let previousFocusedElement = null;

    let threadId = crypto.randomUUID();


    // ======================================
    // CHAT FUNCTIONS
    // ======================================

    function scrollToBottom() {
        chatContainer.scrollTop =
            chatContainer.scrollHeight;
    }

    function hideWelcome() {
        welcome.style.display = "none";
    }

    function createChip(label, value) {
        const chip = document.createElement("span");
        chip.className = "meta-chip";
        chip.textContent = `${label}: ${value}`;
        return chip;
    }

    function addMessage(role, text, metadata = null) {
        hideWelcome();

        const message = document.createElement("div");
        message.className = `message ${role}`;

        const body = document.createElement("div");
        body.className = "message-body";

        if (role === "assistant") {
            const avatar = document.createElement("div");
            avatar.className = "avatar";
            avatar.textContent = "✦";
            message.appendChild(avatar);
        }

        const content = document.createElement("div");
        content.className = "message-content";
        content.textContent = text;

        body.appendChild(content);

        if (metadata) {
            const meta = document.createElement("div");
            meta.className = "message-meta";

            const fields = [
                ["Source", metadata.source_used],
                ["KB Grade", metadata.kb_grade],
                ["Web Grade", metadata.web_grade],
                ["Retries", metadata.retry_count],
                ["Time", metadata.duration]
            ];

            fields.forEach(([label, value]) => {
                if (
                    value !== undefined &&
                    value !== null &&
                    value !== ""
                ) {
                    meta.appendChild(
                        createChip(label, value)
                    );
                }
            });

            body.appendChild(meta);
        }

        message.appendChild(body);
        messages.appendChild(message);

        scrollToBottom();

        return message;
    }

    function showLoading() {
        const loader = document.createElement("div");
        loader.className = "message assistant";
        loader.id = "loadingMessage";

        const avatar = document.createElement("div");
        avatar.className = "avatar";
        avatar.textContent = "✦";

        const body = document.createElement("div");
        body.className = "message-body";

        const dots = document.createElement("div");
        dots.className = "loading-dots";

        for (let i = 0; i < 3; i++) {
            dots.appendChild(document.createElement("span"));
        }

        body.appendChild(dots);
        loader.appendChild(avatar);
        loader.appendChild(body);
        messages.appendChild(loader);

        scrollToBottom();
    }

    function removeLoading() {
        document.getElementById("loadingMessage")?.remove();
    }

    async function sendQuestion(question) {
        question = question.trim();

        if (!question || isLoading) return;

        isLoading = true;
        sendBtn.disabled = true;
        questionInput.disabled = true;

        addMessage("user", question);

        questionInput.value = "";
        questionInput.style.height = "auto";

        showLoading();

        const startTime = performance.now();

        try {
            const response = await fetch(CHAT_API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: question,
                    thread_id: threadId
                })
            });

            const data = await response.json();

            if (!response.ok) {
                let detail = `HTTP ${response.status}`;

                if (typeof data.detail === "string") {
                    detail = data.detail;
                } else if (Array.isArray(data.detail)) {
                    detail = data.detail
                        .map(item => item.msg)
                        .join("; ");
                }

                throw new Error(detail);
            }

            const duration = (
                (performance.now() - startTime) / 1000
            ).toFixed(2) + "s";

            removeLoading();

            addMessage(
                "assistant",
                data.answer || "No answer returned.",
                {
                    source_used: data.source_used,
                    kb_grade: data.kb_grade,
                    web_grade: data.web_grade,
                    retry_count: data.retry_count,
                    duration: duration
                }
            );

        } catch (error) {
            removeLoading();

            const errorMessage = addMessage(
                "assistant",
                `Unable to process your question: ${error.message}`
            );

            errorMessage.classList.add("error");

        } finally {
            isLoading = false;
            sendBtn.disabled = false;
            questionInput.disabled = false;
            questionInput.focus();
        }
    }

    // Chat submit
    chatForm.addEventListener("submit", (event) => {
        event.preventDefault();
        sendQuestion(questionInput.value);
    });

    // Enter sends, Shift+Enter inserts newline
    questionInput.addEventListener("keydown", (event) => {
        if (
            event.key === "Enter" &&
            !event.shiftKey &&
            !event.isComposing
        ) {
            event.preventDefault();
            sendQuestion(questionInput.value);
        }
    });

    // Automatically adjust textarea height
    questionInput.addEventListener("input", () => {
        questionInput.style.height = "auto";
        questionInput.style.height =
            Math.min(questionInput.scrollHeight, 150) + "px";
    });

    // Suggested questions
    document.querySelectorAll(".suggestion")
        .forEach(button => {
            button.addEventListener("click", () => {
                sendQuestion(button.dataset.question);
            });
        });

    // New conversation
    newChatBtn.addEventListener("click", () => {
        if (isLoading) return;

        messages.innerHTML = "";
        welcome.style.display = "";
        questionInput.value = "";
        threadId = crypto.randomUUID();

        sidebar.classList.remove("open");
        questionInput.focus();
    });

    // Mobile sidebar
    menuBtn.addEventListener("click", () => {
        sidebar.classList.toggle("open");
    });


    // ======================================
    // DOCUMENT UPLOAD MODAL
    // ======================================

    function setUploadStatus(message, type = "") {
        uploadStatus.textContent = message;
        uploadStatus.className = `upload-status ${type}`;
    }

    function openDocumentModal() {
        previousFocusedElement = document.activeElement;

        uploadModal.classList.add("show");
        uploadModal.setAttribute("aria-hidden", "false");

        sidebar.classList.remove("open");

        setUploadStatus("");
        adminApiKeyInput.focus();

        console.log("Upload modal opened.");
    }

    function closeDocumentModal() {
        if (isUploading) return;

        uploadModal.classList.remove("show");
        uploadModal.setAttribute("aria-hidden", "true");

        uploadDocumentForm.reset();
        selectedFileName.textContent = "";
        adminApiKeyInput.value = "";

        setUploadStatus("");

        previousFocusedElement?.focus();
    }

    // Open modal
    addDocumentsBtn.addEventListener(
        "click",
        openDocumentModal
    );

    // Close modal
    closeUploadModalBtn.addEventListener(
        "click",
        closeDocumentModal
    );

    // Close on overlay click
    uploadModal.addEventListener("click", (event) => {
        if (event.target === uploadModal) {
            closeDocumentModal();
        }
    });

    // Escape key and basic focus containment
    uploadModal.addEventListener("keydown", (event) => {
        if (event.key !== "Tab") return;

        const focusable = Array.from(
            uploadModal.querySelectorAll(
                "button:not(:disabled), input:not(:disabled)"
            )
        );

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (!first || !last) return;

        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (
            !event.shiftKey &&
            document.activeElement === last
        ) {
            event.preventDefault();
            first.focus();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (
            event.key === "Escape" &&
            uploadModal.classList.contains("show")
        ) {
            closeDocumentModal();
        }
    });

    // Show selected file name
    documentFileInput.addEventListener("change", () => {
        const file = documentFileInput.files[0];

        selectedFileName.textContent = file
            ? `Selected: ${file.name}`
            : "";
    });


    // ======================================
    // UPLOAD DOCUMENT TO FASTAPI
    // ======================================

    uploadDocumentForm.addEventListener(
        "submit",
        async (event) => {
            event.preventDefault();

            if (isUploading) return;

            const adminKey = adminApiKeyInput.value.trim();
            const file = documentFileInput.files[0];

            if (!adminKey) {
                setUploadStatus(
                    "Please enter your Admin API key.",
                    "error"
                );
                return;
            }

            if (!file) {
                setUploadStatus(
                    "Please select a document.",
                    "error"
                );
                return;
            }

            const supported = [
                ".pdf", ".txt", ".md", ".docx"
            ];

            const extension =
                "." + file.name.split(".").pop().toLowerCase();

            if (!supported.includes(extension)) {
                setUploadStatus(
                    "Unsupported document format.",
                    "error"
                );
                return;
            }

            // UploadFile expects multipart/form-data
            const formData = new FormData();
            formData.append("file", file);

            isUploading = true;
            indexDocumentBtn.disabled = true;
            indexDocumentBtn.textContent =
                "Indexing Document...";

            setUploadStatus(
                "Uploading, chunking, embedding and indexing...",
                "loading"
            );

            try {
                const response = await fetch(UPLOAD_API_URL, {
                    method: "POST",
                    headers: {
                        "x-admin-key": adminKey
                    },
                    body: formData
                });

                let data;

                try {
                    data = await response.json();
                } catch {
                    throw new Error(
                        `Server returned HTTP ${response.status}`
                    );
                }

                if (!response.ok) {
                    let detail = `HTTP ${response.status}`;

                    if (typeof data.detail === "string") {
                        detail = data.detail;
                    } else if (Array.isArray(data.detail)) {
                        detail = data.detail
                            .map(item => item.msg)
                            .join("; ");
                    }

                    throw new Error(detail);
                }

                setUploadStatus(
                    data.message ||
                    "Document indexed successfully!",
                    "success"
                );

                // Clear credentials and selected file
                adminApiKeyInput.value = "";
                documentFileInput.value = "";
                selectedFileName.textContent = "";

            } catch (error) {
                console.error("Upload failed:", error.message);

                setUploadStatus(
                    `Upload failed: ${error.message}`,
                    "error"
                );

            } finally {
                isUploading = false;
                indexDocumentBtn.disabled = false;
                indexDocumentBtn.textContent =
                    "Index Document";
            }
        }
    );

    console.log("Chat and document upload ready.");

});

