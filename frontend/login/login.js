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
      // Valida no servidor se o nome já está em uso
      const response = await fetch(`http://127.0.0.1:8081/check-username/${username}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            error.textContent = errorData.detail;
            return;
        }
        
        localStorage.setItem("chat_username", username);
        
        window.location.href = "/chat.html";
    } catch (err) {
        console.error("Erro ao validar nome:", err);
    }
}
