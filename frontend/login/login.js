const form = document.getElementById("loginForm");
const input = document.getElementById("username");
const error = document.getElementById("error");

form.addEventListener("submit", handleLoginSubmit);

async function handleLoginSubmit(event) {
  event.preventDefault();
  const username = input.value.trim();

  if (!username) {
    error.textContent = "Informe seu nome para continuar";
    input.focus();
    return;
  }

  try {
        const response = await fetch(`http://127.0.0.1:8081/check-username/${username}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            error.textContent = errorData.detail;
            return;
        }
        
        localStorage.setItem("chat_username", username);
        
        // Notificar o servidor SSE sobre o login
        notifyUserLogin(username);
        
        window.location.href = "../chat/chat.html";
    } catch (err) {
        console.error("Erro ao validar nome:", err);
    }
}

// Notificar o servidor SSE que um usuário fez login
async function notifyUserLogin(username) {
  try {
    await fetch(`http://127.0.0.1:8080/api/notifications/notify-login/${username}`, {
      method: "POST"
    });
  } catch (err) {
    console.error("Erro ao notificar login:", err);
  }
}