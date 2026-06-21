const form = document.getElementById("registerForm");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const confirmPasswordInput = document.getElementById("confirmPassword");
const errorMsg = document.getElementById("error");

const API_BASE_URL = "http://127.0.0.1:8081";
const ACCESS_TOKEN = "chat_access_token";
const REFRESH_TOKEN = "chat_refresh_token";

checkExistingSession();

form.addEventListener("submit", handleRegisterSubmit);

async function checkExistingSession() {
    const accessToken = localStorage.getItem(ACCESS_TOKEN);
    const refreshToken = localStorage.getItem(REFRESH_TOKEN);

    if (!accessToken || !refreshToken) {
        return;
    }

    if (await isSessionValid(accessToken)) {
        window.location.href = "/chat.html";
        return;
    }

    if (await refreshSession(refreshToken)) {
        window.location.href = "/chat.html";
    }
}

async function isSessionValid(accessToken) {
    try {
        const response = await fetch(`${API_BASE_URL}/me`, {
            headers: { Authorization: `Bearer ${accessToken}` }
        });

        return response.ok;
    } catch {
        return false;
    }
}

async function refreshSession(refreshToken) {
    try {
        const response = await fetch(`${API_BASE_URL}/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!response.ok) {
            return false;
        }

        const data = await response.json();
        localStorage.setItem(ACCESS_TOKEN, data.access_token);
        localStorage.setItem(REFRESH_TOKEN, data.refresh_token);
        return true;
    } catch {
        return false;
    }
}

async function handleRegisterSubmit(event) {
    event.preventDefault();
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    if (!username || !password || !confirmPassword) {
        errorMsg.textContent = "Preencha todos os campos";
        return;
    }

    if (password !== confirmPassword) {
        errorMsg.textContent = "As senhas não coincidem";
        return;
    }

    try {
        const registerResponse = await fetch(`${API_BASE_URL}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        if (!registerResponse.ok) {
            const errorData = await registerResponse.json();
            errorMsg.textContent = errorData.detail;
            return;
        }

        await delay(1250); // Aguarda 1.250 segundos para fazer login após registro bem-sucedido

        const loginResponse = await fetch(`${API_BASE_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        if (!loginResponse.ok) {
            errorMsg.textContent = "Cadastro realizado, mas não foi possível autenticar";
            return;
        }

        const data = await loginResponse.json();
        localStorage.setItem(ACCESS_TOKEN, data.access_token);
        localStorage.setItem(REFRESH_TOKEN, data.refresh_token);
        window.location.href = "/chat.html";
    } catch (err) {
        errorMsg.textContent = "Erro ao se conectar com o servidor";
    }
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
