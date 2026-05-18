# DCM Webchat

Projeto final das disciplinas Sistemas Distribuídos e Introdução ao Desenvolvimento Web para o Curso de Ciência da Computação da Universidade de São Paulo.

## Resumo

Este projeto consiste em um sistema de chat em tempo real que permite a vários usuários conversarem simultaneamente e receberem notificações sobre eventos relevantes da aplicação. O projeto foi estruturado de forma a separar as responsabilidades entre interface de apresentação, processamento de mensagens com conexão ao banco de dados e envio de notificações com gatilho via gRPC.

## Estrutura do projeto

### Serviço de chat

Serviço feito em Python com o framework web FastAPI para tratar das funcionalidades referentes ao chat. Expõe rota de conexão WebSocket, disponibiliza endpoints (API REST) para operações auxiliares como consulta de disponibilidade de nome de usuário, persiste mensagens em banco SQLite e funciona como um cliente gRPC do serviço de notificação para informar o login de um novo usuário e para atualizar a quantidade de usuários online.

### Serviço de notificação

Serviço feito em Java com o framework Spring para implementar funcionalidades de notificação aos usuários da aplicação. Expõe rota SSE para usuários se conectarem e receberem notificações em tempo real e implementa um servidor gRPC para disparar notificações quando requeridas pelo serviço de chat.

### Frontend

Páginas de **login** e **chat** dinâmicas feitas com HTML, CSS e JavaScript que consomem API REST, WebSocket e SSE. 

## Principais tecnologias

**WebSocket:** comunicação bidirecional entre os usuários para troca de mensagens em tempo real.

**Server-Sent Events (SSE):** comunicação unidirecional para enviar notificações a todos os usuários conectados.

**gRPC:** comunicação eficiente e definida entre os serviços de chat e de notificação para disparar notificações a partir do serviço de chat, que atua como cliente gRPC.

**FastAPI:** framework web Python utilizado para disponibilizar endpoints de API REST e comunicação WebSocket.

**Spring Framework:** framework Java utilizado para disponibilizar comunicação SSE e implementação de servidor gRPC.

**SQLite:** SGBD utilizado para persistência simples do histórico de mensagens enviadas.

**Logs:** acompanhamento em tempo real da execução da aplicação.


## Instalação e execução

1 - Criar ambiente virtual Python

PowerShell (Windows):

```powershell
python -m venv .venv
# Ativar no PowerShell
.\.venv\Scripts\Activate.ps1
# Para o prompt do CMD, use:
.\.venv\Scripts\activate
```

Bash / macOS / WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2 - Instalar dependências Python

```bash
python -m pip install -r requirements.txt
```

3 - Instalar dependências Java

```bash
cd notification-service
mvn clean install -DskipTests
```

4 - Executar os serviços

```bash
cd chat-service
python -m uvicorn server:app --host 127.0.0.1 --port 8081

cd notification-service
mvn spring-boot:run
```

5 - Executar o frontend

Abra `frontend/login/login.html` no navegador **ou** inicie um servidor HTTP referenciando a pasta ```frontend/```

```bash
cd frontend
python -m http.server 5500
```
e depois acesse ```http://localhost:5500/login/login.html```