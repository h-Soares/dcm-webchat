package com.hsoaresdev.notification_service;

import io.grpc.stub.StreamObserver;
import org.springframework.stereotype.Service;

@Service
public class NotificationGrpcService extends NotificationServiceGrpc.NotificationServiceImplBase {

    private final NotificationSseService notificationSseService;

    public NotificationGrpcService(NotificationSseService notificationSseService) {
        this.notificationSseService = notificationSseService;
    }

    // Função do servidor gRPC para notificar login de usuário via SSE
    @Override
    public void notifyLogin(NotifyRequest request, StreamObserver<NotifyResponse> responseObserver) {
        String username = request.getUsername();
        notificationSseService.broadcast("user_login", username);

        NotifyResponse response = NotifyResponse.newBuilder().setStatus("ok").build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    // Função do servidor gRPC para notificar atualização do contador de usuários via SSE
    @Override
    public void notifyUserCount(NotifyCountRequest request, StreamObserver<NotifyResponse> responseObserver) {
        int count = request.getUserCount();
        notificationSseService.broadcast("user_count", String.valueOf(count));

        NotifyResponse response = NotifyResponse.newBuilder().setStatus("ok").build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }
}
