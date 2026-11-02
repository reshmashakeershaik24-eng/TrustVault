package com.trustvault;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(
    name = "document_share",
    uniqueConstraints = @UniqueConstraint(
        columnNames = {"document_id", "shared_with_user_id"}
    )
)
public class DocumentShare {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "document_id", nullable = false)
    private Long documentId;

    @Column(name = "shared_with_user_id", nullable = false)
    private Long sharedWithUserId;

    @Column(name = "shared_at", nullable = false)
    private LocalDateTime sharedAt = LocalDateTime.now();

    public DocumentShare() {
    }

    public DocumentShare(Long documentId, Long sharedWithUserId) {
        this.documentId = documentId;
        this.sharedWithUserId = sharedWithUserId;
    }

    public Long getId() {
        return id;
    }

    public Long getDocumentId() {
        return documentId;
    }

    public Long getSharedWithUserId() {
        return sharedWithUserId;
    }

    public LocalDateTime getSharedAt() {
        return sharedAt;
    }
}