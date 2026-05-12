package com.hsoaresdev.notification_service;

import java.time.Instant;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Service
public class NotificationSseService {

	private final List<SseEmitter> emitters = new CopyOnWriteArrayList<>();

	public SseEmitter connect() {
		SseEmitter emitter = new SseEmitter(0L); 
		emitters.add(emitter);

		emitter.onCompletion(() -> emitters.remove(emitter));
		emitter.onTimeout(() -> emitters.remove(emitter));
		emitter.onError(error -> emitters.remove(emitter));

		// Enviar evento inicial para confirmar conexão
		try {
			emitter.send(SseEmitter.event()
					.id(String.valueOf(System.currentTimeMillis()))
					.data("connected")
					.comment("SSE connection established"));
		} catch (Exception ex) {
			emitter.complete();
		}

		return emitter;
	}

	public void broadcast(String messageType, String message) {
		for (SseEmitter emitter : emitters) {
			try {
				emitter.send(SseEmitter.event()
						.name(messageType)
						.id(String.valueOf(Instant.now().toEpochMilli()))
						.data(message));
			} catch (Exception ex) {
                emitter.complete();
			}
		}
	}

    @Scheduled(fixedRate = 15000) // 15 segundos
    public void sendHeartbeat() {
        broadcast("heartbeat", "");
    }
}