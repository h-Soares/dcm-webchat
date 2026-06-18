const username = localStorage.getItem("chat_username");
const welcome = document.getElementById("welcome");
const logoutBtn = document.getElementById("logoutBtn");
const form = document.getElementById("composerForm");
const messagesContainer = document.getElementById("messages");
const messageInput = form.elements.message;
const notificationContainer = document.getElementById("notificationContainer");
const userCount = document.getElementById("userCount");
let ws;
let eventSource;

// Se não tiver username, redireciona para login. Caso contrário, inicia WebSocket e SSE
if (!username) {
  window.location.href = "/login.html";
} else {
  welcome.textContent = `Logado como: ${username}`;
  startWebSocket(username);
  connectToSSE();
}

// Logout: limpa username e redireciona para login
logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("chat_username");
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
function startWebSocket(username) {
  ws = new WebSocket(`ws://127.0.0.1:8081/ws/${username}`);

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
}

// Conectar ao servidor SSE para receber notificações
function connectToSSE() {
  eventSource = new EventSource(`http://127.0.0.1:8080/api/notifications`);

  eventSource.onopen = () => {
    console.log("Conectado ao SSE para notificações");
  };

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
  notificationContainer.prepend(notification)

  // Remover notificação após 2.5 segundos
  setTimeout(() => {
    notification.classList.add("hide");
    setTimeout(() => {
      notification.remove();
    }, 300); // Aguardar a animação de saída
  }, 2500);
}