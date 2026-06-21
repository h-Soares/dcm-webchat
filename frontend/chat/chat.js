const SERVER_IP = "127.0.0.1";
const API_BASE_URL = `http://${SERVER_IP}:8081`;
const ACCESS_TOKEN = "chat_access_token";
const REFRESH_TOKEN = "chat_refresh_token";

const welcome = document.getElementById("welcome");
const logoutBtn = document.getElementById("logoutBtn");
const form = document.getElementById("composerForm");
const messagesContainer = document.getElementById("messages");
const messageInput = form.elements.message;
const notificationContainer = document.getElementById("notificationContainer");
const userCount = document.getElementById("userCount");

let ws;
let eventSource;
let username = "";

// Primeiro valida a sessão e depois inicializa o chat
checkExistingSession();

// Verifica primeiro se existe uma sessão válida (access token válido), 
// Se o access token for inválido, tenta renová-lo usando o refresh token,
// Somente após a validação da sessão o chat é inicializado
async function checkExistingSession() {
  const accessToken = localStorage.getItem(ACCESS_TOKEN);
  const refreshToken = localStorage.getItem(REFRESH_TOKEN);
  
  if (!accessToken || !refreshToken) {
    redirectToLogin();
    return;
  }

  if (await isSessionValid(accessToken)) {
    await initializeChat();
    return;
  }

  if (await refreshSession(refreshToken)) {
    await initializeChat();
    return;
  }

  redirectToLogin();
}

// Valida o access token consultando a rota /me
async function isSessionValid(token) {
  try {
    const response = await fetch(`${API_BASE_URL}/me`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return response.ok;
  } catch {
    return false;
  }
}

// Tenta obter novos tokens utilizando o refresh token
async function refreshSession(token) {
  try {
    const response = await fetch(`${API_BASE_URL}/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        refresh_token: token
      })
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

// Remove tokens armazenados e retorna para a tela de login
function redirectToLogin() {
  localStorage.removeItem(ACCESS_TOKEN);
  localStorage.removeItem(REFRESH_TOKEN);

  window.location.href = "/login.html";
}

// Inicializa o chat após a validação da sessão via token JWT: obtém o username, inicia o WebSocket e conecta ao SSE
async function initializeChat() {
  const accessToken = localStorage.getItem(ACCESS_TOKEN);
  username = await fetchUsername(accessToken);

  if (!username) {
    redirectToLogin();
    return;
  }

  welcome.textContent = `Logado como: ${username}`;

  startWebSocket(accessToken);
  connectToSSE();
}

// Busca o nome do usuário usando a rota /me com o access token
async function fetchUsername(token) {
  try {
    const response = await fetch(`${API_BASE_URL}/me`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    return data.username || null;
  } catch {
    return null;
  }
}

// Botão para fazer logout: limpa tokens e redireciona para login
logoutBtn.addEventListener("click", () => {
  localStorage.removeItem(ACCESS_TOKEN);
  localStorage.removeItem(REFRESH_TOKEN);
  window.location.href = "/login.html";
});

// Enviar mensagem no chat via WebSocket
form.addEventListener("submit", (event) => {
  event.preventDefault();

  const message = messageInput.value.trim();

  if (!message) {
    return;
  }

  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.warn("WebSocket ainda não está conectado.");
    return;
  }

  ws.send(message);
  messageInput.value = "";
  messageInput.focus();
});

// Iniciar conexão WebSocket para receber mensagens do chat
function startWebSocket(token) {
  ws = new WebSocket(`ws://${SERVER_IP}:8081/ws?token=${token}`);

  ws.onopen = () => console.log("Conectado ao chat!");

  ws.onmessage = (event) => {
    console.log("Mensagem recebida:", event.data);

    if (!messagesContainer) {
      return;
    }

    const messageDiv = document.createElement("div");
    messageDiv.textContent = event.data;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  };

  ws.onclose = () => console.log("WebSocket encerrado");

  ws.onerror = (error) => console.error("Erro no WebSocket:", error);
}

// Conectar ao servidor SSE e configurar o recebimento de notificações
function connectToSSE() {
  eventSource = new EventSource(`http://${SERVER_IP}:8080/api/notifications`);

  eventSource.onopen = () => console.log("Conectado ao SSE para notificações");

  // Escutar evento de login de outros usuários
  eventSource.addEventListener("user_login", (event) => {
    if (!event.data || event.data.trim() === "" || event.data === username) {
      return;
    }

    console.log("Evento user_login recebido:", event.data);
    console.log("Evento user_login recebido:", event);

    showNotification(event.data);
  });

  // Escutar evento de atualização do contador de usuários
  eventSource.addEventListener("user_count", (event) => {
    if (!event.data || event.data.trim() === "") {
      return;
    }

    userCount.textContent = event.data;
  });

  eventSource.onerror = (error) => {
    console.error("Erro ao conectar ao SSE:", error);

    if (eventSource.readyState === EventSource.CLOSED) {
      console.log("Conexão SSE fechada");
    }
  };
}

// Exibir notificação de login no canto inferior direito
function showNotification(username) {
  const notification = document.createElement("div");
  notification.className = "notification";

  const usernameElement = document.createElement("strong");
  usernameElement.textContent = username;

  notification.append(usernameElement, document.createTextNode(" se conectou"));

  // Inserir no topo para que notificações mais recentes apareçam acima
  notificationContainer.prepend(notification);

  // Remover notificação após 2.5 segundos
  setTimeout(() => {
    notification.classList.add("hide");

    setTimeout(() => {
      notification.remove();
    }, 300); // Aguardar a animação de saída
  }, 2500);
}