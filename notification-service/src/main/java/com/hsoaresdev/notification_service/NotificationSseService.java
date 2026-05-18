package com.hsoaresdev.notification_service;

import java.time.Instant;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class NotificationSseService {
	private static final Logger logger = LoggerFactory.getLogger(NotificationSseService.class);
	private final List<SseEmitter> emitters = new CopyOnWriteArrayList<>();

	// Método para conectar um cliente SSE
	public SseEmitter connect() {
		SseEmitter emitter = new SseEmitter(0L);
		emitters.add(emitter);
		logger.info("SSE client connected. Total clients: {}", emitters.size());

		emitter.onCompletion(() -> {
			emitters.remove(emitter);
			logger.debug("SSE client completed. Remaining clients: {}", emitters.size());
		});
		emitter.onTimeout(() -> {
			emitters.remove(emitter);
			logger.debug("SSE client timeout. Remaining clients: {}", emitters.size());
		});
		emitter.onError(throwable -> {
			emitters.remove(emitter);
			logger.warn("SSE client error: {}. Removed emitter. Remaining clients: {}", throwable.getMessage(), emitters.size());
		});

		try {
			emitter.send(SseEmitter.event()
				.id(String.valueOf(System.currentTimeMillis()))
				.data("connected")
				.comment("SSE connection established"));
			logger.debug("Initial SSE event sent to client");
		} catch (Exception ex) {
			logger.warn("Failed to send initial SSE event: {}", ex.getMessage());
			emitter.completeWithError(ex);
		}

		return emitter;
	}

	// Método para broadcast de mensagens para todos os clientes SSE conectados
	public void broadcast(String messageType, String message) {
		emitters.forEach(emitter -> {
			try {
				emitter.send(SseEmitter.event()
					.name(messageType)
					.id(String.valueOf(Instant.now().toEpochMilli()))
					.data(message));
			} catch (Exception ex) {
				logger.warn("Failed to send SSE event '{}' to a client: {}. Removing emitter.", messageType, ex.getMessage());
				emitters.remove(emitter); // para evitar erro no grpc, caso o cliente tenha desconectado
			}
		});
	}

    @Scheduled(fixedRate = 15000) // Envia um evento de heartbeat a cada 15 segundos para manter a conexão ativa
    public void sendHeartbeat() {
        broadcast("heartbeat", "");
    }
}