// TrustVault Client Engine
const API_BASE = "/api";
let currentToken = localStorage.getItem("tv_token") || null;
let currentUser = null;
let currentCategory = "ALL";
let currentSearch = "";
let selectedDocForPermissions = null;

// --- Authentication & Session Management ---

function getHeaders(isMultipart = false) {
    const headers = {};
    if (currentToken) {
        headers["Authorization"] = `Bearer ${currentToken}`;
    }
    if (!isMultipart) {
        headers["Content-Type"] = "application/json";
    }
    return headers;
}

function fillEmail(email) {
    const emailField = document.getElementById("heroEmail");
    if (emailField) {
        emailField.value = email;
        const passwordField = document.getElementById("heroPassword");
        if (passwordField) {
            passwordField.value = "";
            passwordField.focus();
        }
    }
}

async function handleHeroLogin(event) {
    event.preventDefault();
    const email = document.getElementById("heroEmail").value;
    const password = document.getElementById("heroPassword").value;
    await quickLogin(email, password);
}

function openLoginModal() {
    document.getElementById("loginModal").classList.remove("hidden");
}

function closeLoginModal() {
    document.getElementById("loginModal").classList.add("hidden");
}

async function handleManualLogin(event) {
    event.preventDefault();
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;
    closeLoginModal();
    await quickLogin(email, password);
}

async function quickLogin(email, password) {
    showToast(`Authenticating as ${email}...`, "info");
    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        if (!res.ok) {
            const err = await res.json();
            showToast(err.detail || "Login failed", "error");
            return;
        }

        const data = await res.json();
        currentToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem("tv_token", currentToken);
        localStorage.setItem("tv_user", JSON.stringify(currentUser));

        updateUIForUser();
        loadDocuments();
        loadAiSuggestions();
        showToast(`Signed in as ${currentUser.full_name} (${currentUser.role})`, "success");
    } catch (err) {
        console.error(err);
        showToast("Network error during login", "error");
    }
}

function logout() {
    currentToken = null;
    currentUser = null;
    localStorage.removeItem("tv_token");
    localStorage.removeItem("tv_user");
    updateUIForUser();
    showToast("Signed out. Authentication required to view documents.", "info");
}

async function checkSession() {
    if (!currentToken) {
        // User starts logged out. Explicit login required!
        updateUIForUser();
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/auth/me`, { headers: getHeaders() });
        if (res.ok) {
            currentUser = await res.json();
            updateUIForUser();
            loadDocuments();
            loadAiSuggestions();
        } else {
            logout();
        }
    } catch {
        logout();
    }
}

function updateUIForUser() {
    const loggedInDiv = document.getElementById("userLoggedIn");
    const loggedOutDiv = document.getElementById("userLoggedOut");
    const loggedOutHero = document.getElementById("loggedOutHero");
    const appArea = document.getElementById("appArea");
    const adminNavBtn = document.getElementById("adminNavBtn");
    const uploadTriggerBtn = document.getElementById("uploadTriggerBtn");

    if (currentUser) {
        loggedInDiv.classList.remove("hidden");
        loggedOutDiv.classList.add("hidden");
        loggedOutHero.classList.add("hidden");
        appArea.classList.remove("hidden");

        document.getElementById("userName").textContent = currentUser.full_name;
        document.getElementById("userEmail").textContent = currentUser.email;

        const roleBadge = document.getElementById("userRoleBadge");
        roleBadge.textContent = currentUser.role;
        if (currentUser.role === "ADMIN") {
            roleBadge.className = "text-xs px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono font-semibold";
            adminNavBtn.classList.remove("hidden");
            uploadTriggerBtn.classList.remove("hidden");
        } else if (currentUser.role === "OWNER") {
            roleBadge.className = "text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono font-semibold";
            adminNavBtn.classList.add("hidden");
            uploadTriggerBtn.classList.remove("hidden");
        } else {
            roleBadge.className = "text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono font-semibold";
            adminNavBtn.classList.add("hidden");
            uploadTriggerBtn.classList.add("hidden"); // Viewers cannot upload
        }
    } else {
        loggedInDiv.classList.add("hidden");
        loggedOutDiv.classList.remove("hidden");
        loggedOutHero.classList.remove("hidden");
        appArea.classList.add("hidden");
        adminNavBtn.classList.add("hidden");
        uploadTriggerBtn.classList.add("hidden");
    }
}

// --- Documents Explorer ---

async function loadDocuments() {
    if (!currentUser) return;

    const container = document.getElementById("documentsContainer");
    const emptyState = document.getElementById("emptyState");

    let url = `${API_BASE}/documents?`;
    if (currentCategory && currentCategory !== "ALL") url += `category=${currentCategory}&`;
    if (currentSearch) url += `search=${encodeURIComponent(currentSearch)}&`;

    try {
        const res = await fetch(url, { headers: getHeaders() });
        if (!res.ok) {
            container.innerHTML = "";
            emptyState.classList.remove("hidden");
            return;
        }

        const docs = await res.json();
        if (docs.length === 0) {
            container.innerHTML = "";
            emptyState.classList.remove("hidden");
            return;
        }

        emptyState.classList.add("hidden");
        container.innerHTML = docs.map(d => renderDocumentCard(d)).join("");
    } catch (err) {
        console.error(err);
    }
}

function renderDocumentCard(doc) {
    const isOwner = currentUser && currentUser.id === doc.owner_id;
    const dateFormatted = new Date(doc.created_at).toLocaleDateString();
    const sizeKB = Math.round(doc.file_size / 1024) || 1;

    let categoryColor = "bg-slate-800 text-slate-300";
    if (doc.category === "FINANCIAL") categoryColor = "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
    if (doc.category === "LEGAL") categoryColor = "bg-blue-500/20 text-blue-300 border border-blue-500/30";
    if (doc.category === "HR") categoryColor = "bg-purple-500/20 text-purple-300 border border-purple-500/30";
    if (doc.category === "OPERATIONS") categoryColor = "bg-amber-500/20 text-amber-300 border border-amber-500/30";

    return `
        <div class="bg-slate-900/60 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 flex flex-col justify-between transition-all duration-200 group shadow-lg">
            <div class="space-y-3">
                <div class="flex items-start justify-between">
                    <span class="text-[11px] font-semibold px-2.5 py-0.5 rounded-lg ${categoryColor}">${doc.category}</span>
                    <span class="text-[11px] font-mono text-slate-500">${sizeKB} KB</span>
                </div>
                <div>
                    <h3 class="text-sm font-bold text-white group-hover:text-indigo-400 transition line-clamp-1" title="${doc.title}">${doc.title}</h3>
                    <p class="text-xs text-slate-400 font-mono mt-0.5 truncate" title="${doc.file_name}">${doc.file_name}</p>
                </div>
                <div class="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80 font-mono text-[10px] text-slate-500 flex items-center justify-between">
                    <span class="truncate">SHA-256: ${doc.file_hash.substring(0, 16)}...</span>
                    <span class="text-slate-400 text-[10px] ml-2 shrink-0">${dateFormatted}</span>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="pt-4 mt-2 border-t border-slate-800/80 flex items-center justify-between gap-2">
                <button onclick="downloadDocument('${doc.id}', '${doc.file_name}')"
                    class="flex-1 py-1.5 px-3 bg-indigo-600/90 hover:bg-indigo-600 text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 shadow transition">
                    <i class="fa-solid fa-cloud-arrow-down"></i>
                    <span>Download</span>
                </button>

                ${isOwner ? `
                    <button onclick="openPermissionsModal('${doc.id}', '${escapeHtml(doc.title)}')"
                        class="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl text-xs transition" title="Manage Access">
                        <i class="fa-solid fa-user-lock"></i>
                    </button>
                    <button onclick="deleteDocument('${doc.id}')"
                        class="p-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded-xl text-xs transition" title="Delete">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

// --- Secure Download Flow ---

async function downloadDocument(docId, fileName) {
    showToast("Verifying permissions on server...", "info");

    try {
        const res = await fetch(`${API_BASE}/documents/${docId}/download`, {
            headers: getHeaders()
        });

        if (res.status === 403) {
            showToast("ACCESS DENIED: The server refused your request. Attempt logged to audit trail.", "error");
            return;
        }
        if (!res.ok) {
            showToast("Failed to retrieve file", "error");
            return;
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

        showToast("Download authorized & complete", "success");
    } catch (err) {
        console.error(err);
        showToast("Error during download stream", "error");
    }
}

// --- Upload Flow ---

function openUploadModal() {
    document.getElementById("uploadModal").classList.remove("hidden");
}
function closeUploadModal() {
    document.getElementById("uploadModal").classList.add("hidden");
    document.getElementById("uploadForm").reset();
}

async function handleUpload(event) {
    event.preventDefault();
    const title = document.getElementById("uploadTitle").value;
    const category = document.getElementById("uploadCategory").value;
    const fileInput = document.getElementById("uploadFile");
    const submitBtn = document.getElementById("uploadSubmitBtn");

    if (!fileInput.files.length) {
        showToast("Please choose a file to upload", "error");
        return;
    }

    const formData = new FormData();
    formData.append("title", title);
    formData.append("category", category);
    formData.append("file", fileInput.files[0]);

    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Encrypting...`;

    try {
        const res = await fetch(`${API_BASE}/documents/upload`, {
            method: "POST",
            headers: {
                ...(currentToken ? { "Authorization": `Bearer ${currentToken}` } : {})
            },
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            showToast(err.detail || "Upload rejected", "error");
            return;
        }

        showToast("Document encrypted & stored safely", "success");
        closeUploadModal();
        loadDocuments();
        loadAiSuggestions();
    } catch (err) {
        console.error(err);
        showToast("Upload network error", "error");
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i class="fa-solid fa-lock"></i> <span>Upload & Encrypt</span>`;
    }
}

// --- Permissions Management & Instant Revocation ---

async function openPermissionsModal(docId, docTitle) {
    selectedDocForPermissions = docId;
    document.getElementById("permDocTitle").textContent = docTitle;
    document.getElementById("permissionsModal").classList.remove("hidden");

    await populateUsersDropdown();
    await loadActivePermissions(docId);
}

function closePermissionsModal() {
    document.getElementById("permissionsModal").classList.add("hidden");
    selectedDocForPermissions = null;
}

async function populateUsersDropdown() {
    const select = document.getElementById("grantUserEmail");
    try {
        const res = await fetch(`${API_BASE}/auth/users`, { headers: getHeaders() });
        if (res.ok) {
            const users = await res.json();
            select.innerHTML = `<option value="">Select a user...</option>` + 
                users.filter(u => u.id !== currentUser.id).map(u => 
                    `<option value="${u.email}">${u.full_name} (${u.email})</option>`
                ).join("");
        }
    } catch (err) {
        console.error(err);
    }
}

async function loadActivePermissions(docId) {
    const container = document.getElementById("activePermsList");
    container.innerHTML = `<div class="text-xs text-slate-500 py-2">Loading permissions...</div>`;

    try {
        const res = await fetch(`${API_BASE}/documents/${docId}/permissions`, { headers: getHeaders() });
        if (!res.ok) {
            container.innerHTML = `<div class="text-xs text-rose-400">Failed to load permissions</div>`;
            return;
        }

        const perms = await res.json();
        if (perms.length === 0) {
            container.innerHTML = `<div class="text-xs text-slate-500 py-2">No external users have been granted access. Only the owner can view.</div>`;
            return;
        }

        container.innerHTML = perms.map(p => `
            <div class="flex items-center justify-between bg-slate-900 border border-slate-800 p-2.5 rounded-xl text-xs">
                <div>
                    <span class="font-semibold text-white">${p.user_email}</span>
                    <span class="ml-2 px-1.5 py-0.5 rounded text-[10px] bg-indigo-500/20 text-indigo-300 font-mono">${p.permission_level}</span>
                </div>
                <button onclick="handleRevokePermission('${docId}', '${p.user_id}')"
                    class="px-2.5 py-1 text-[11px] rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 transition flex items-center space-x-1">
                    <i class="fa-solid fa-user-xmark"></i>
                    <span>Revoke Instantly</span>
                </button>
            </div>
        `).join("");
    } catch (err) {
        console.error(err);
    }
}

async function handleGrantPermission() {
    const email = document.getElementById("grantUserEmail").value;
    const level = document.getElementById("grantLevel").value;

    if (!email) {
        showToast("Please choose a user", "error");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/documents/${selectedDocForPermissions}/permissions`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ user_email: email, permission_level: level })
        });

        if (!res.ok) {
            const err = await res.json();
            showToast(err.detail || "Failed to grant permission", "error");
            return;
        }

        showToast(`Granted ${level} access to ${email}`, "success");
        loadActivePermissions(selectedDocForPermissions);
    } catch (err) {
        console.error(err);
        showToast("Network error", "error");
    }
}

async function handleRevokePermission(docId, userId) {
    if (!confirm("Revoking access will immediately prevent this user from downloading or reading this document. Continue?")) return;

    try {
        const res = await fetch(`${API_BASE}/documents/${docId}/permissions/${userId}`, {
            method: "DELETE",
            headers: getHeaders()
        });

        if (!res.ok) {
            showToast("Failed to revoke permission", "error");
            return;
        }

        showToast("Access REVOKED immediately. Target user cut off.", "success");
        loadActivePermissions(docId);
    } catch (err) {
        console.error(err);
    }
}

async function deleteDocument(docId) {
    if (!confirm("Are you sure you want to delete this document?")) return;

    try {
        const res = await fetch(`${API_BASE}/documents/${docId}`, {
            method: "DELETE",
            headers: getHeaders()
        });

        if (res.ok) {
            showToast("Document deleted", "info");
            loadDocuments();
        } else {
            showToast("Failed to delete document", "error");
        }
    } catch (err) {
        console.error(err);
    }
}

// --- AI Suggestions Flow (Human in the loop) ---

async function loadAiSuggestions() {
    const banner = document.getElementById("aiBanner");
    const list = document.getElementById("aiSuggestionsList");

    if (!currentUser || currentUser.role === "VIEWER") {
        banner.classList.add("hidden");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/ai/suggestions`, { headers: getHeaders() });
        if (!res.ok) return;

        const suggestions = await res.json();
        if (suggestions.length === 0) {
            banner.classList.add("hidden");
            return;
        }

        banner.classList.remove("hidden");
        list.innerHTML = suggestions.map(s => `
            <div class="bg-slate-900/80 border border-indigo-500/20 p-3 rounded-xl flex items-center justify-between text-xs gap-3">
                <div class="space-y-0.5">
                    <div class="text-slate-200">
                        Suggest granting <span class="font-bold text-indigo-300">${s.suggested_permission}</span> to <span class="font-bold text-white">${s.suggested_user_email}</span>
                    </div>
                    <div class="text-[11px] text-slate-400 italic">${s.rationale}</div>
                </div>
                <div class="flex items-center space-x-2 shrink-0">
                    <button onclick="decideAiSuggestion('${s.id}', 'APPROVE')" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold transition">
                        Approve Grant
                    </button>
                    <button onclick="decideAiSuggestion('${s.id}', 'REJECT')" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition">
                        Dismiss
                    </button>
                </div>
            </div>
        `).join("");
    } catch (err) {
        console.error(err);
    }
}

async function decideAiSuggestion(suggestionId, action) {
    try {
        const res = await fetch(`${API_BASE}/ai/suggestions/${suggestionId}/decision`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ action })
        });

        if (res.ok) {
            showToast(`Suggestion ${action === 'APPROVE' ? 'Approved & Granted' : 'Rejected'}`, "success");
            loadAiSuggestions();
            loadDocuments();
        } else {
            showToast("Failed to process suggestion", "error");
        }
    } catch (err) {
        console.error(err);
    }
}

// --- Filters & Helpers ---

function setCategory(cat) {
    currentCategory = cat;
    document.querySelectorAll(".cat-pill").forEach(el => {
        el.classList.remove("bg-indigo-600", "text-white");
        el.classList.add("bg-slate-800", "text-slate-300");
    });
    event.target.classList.remove("bg-slate-800", "text-slate-300");
    event.target.classList.add("bg-indigo-600", "text-white");
    loadDocuments();
}

let searchTimer;
function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
        currentSearch = document.getElementById("searchInput").value;
        loadDocuments();
    }, 250);
}

function showToast(message, type = "info") {
    const toast = document.getElementById("toast");
    toast.textContent = message;

    if (type === "success") {
        toast.className = "fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl border border-emerald-500/40 bg-emerald-950/90 text-emerald-200 text-xs shadow-2xl backdrop-blur flex items-center";
    } else if (type === "error") {
        toast.className = "fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl border border-rose-500/40 bg-rose-950/90 text-rose-200 text-xs shadow-2xl backdrop-blur flex items-center font-bold";
    } else {
        toast.className = "fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl border border-slate-700 bg-slate-900/90 text-slate-200 text-xs shadow-2xl backdrop-blur flex items-center";
    }

    toast.classList.remove("hidden");
    setTimeout(() => { toast.classList.add("hidden"); }, 4000);
}

function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

document.addEventListener("DOMContentLoaded", () => {
    checkSession();
});
