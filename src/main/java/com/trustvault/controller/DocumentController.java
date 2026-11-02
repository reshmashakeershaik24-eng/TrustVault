
package com.trustvault.controller;

import com.trustvault.*;
import com.trustvault.service.DocumentFileService;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/documents")
public class DocumentController {

    private final DocumentRepository documentRepository;
    private final AuditLogRepository auditLogRepository;
    private final DocumentShareRepository shareRepository;
    private final UserRepository userRepository;
    private final DocumentFileService documentFileService;

    public DocumentController(
            DocumentRepository documentRepository,
            AuditLogRepository auditLogRepository,
            DocumentShareRepository shareRepository,
            UserRepository userRepository,
            DocumentFileService documentFileService) {

        this.documentRepository = documentRepository;
        this.auditLogRepository = auditLogRepository;
        this.shareRepository = shareRepository;
        this.userRepository = userRepository;
        this.documentFileService = documentFileService;
    }

    // Upload PDF, DOCX or TXT files
    @PostMapping(value = "/upload", consumes = "multipart/form-data")
    public ResponseEntity<?> uploadDocument(
            @RequestParam("file")
            org.springframework.web.multipart.MultipartFile file,
            HttpSession session) {

        Long userId = (Long) session.getAttribute("userId");

        if (userId == null) {
            return ResponseEntity.status(401)
                    .body(Map.of("message", "Please log in first"));
        }

        Document document = new Document();
        document.setOwnerId(userId);

        try {
            documentFileService.processUpload(file, document);

            Document saved = documentRepository.save(document);

            auditLogRepository.save(
                    new AuditLog(userId, saved.getId(), "UPLOAD"));

            Map<String, Object> response = new HashMap<>();
            response.put("id", saved.getId());
            response.put("title", saved.getTitle());
            response.put("fileName", saved.getOriginalFileName());
            response.put("fileType", saved.getFileType());
            response.put("fileSize", saved.getFileSize());
            response.put("message", "File uploaded successfully");

            return ResponseEntity.status(HttpStatus.CREATED).body(response);

        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                    .body(Map.of("message", e.getMessage()));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", "File upload failed"));
        }
    }

    // Existing manual document creation
    @PostMapping
    public ResponseEntity<?> createDocument(
            @RequestBody Map<String, String> request,
            HttpSession session) {

        Long userId = (Long) session.getAttribute("userId");

        if (userId == null) {
            return ResponseEntity.status(401)
                    .body(Map.of("message", "Please log in first"));
        }

        String title = request.get("title");
        String content = request.get("content");

        if (title == null || title.isBlank()
                || content == null || content.isBlank()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("message",
                            "Title and content are required"));
        }

        Document document = new Document();
        document.setTitle(title.trim());
        document.setContent(content);
        document.setOwnerId(userId);

        Document saved = documentRepository.save(document);

        auditLogRepository.save(
                new AuditLog(userId, saved.getId(), "CREATE"));

        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    // List documents owned by the logged-in user
    @GetMapping
    public ResponseEntity<?> getMyDocuments(HttpSession session) {

        Long userId = (Long) session.getAttribute("userId");

        if (userId == null) {
            return ResponseEntity.status(401)
                    .body(Map.of("message", "Please log in first"));
        }

        return ResponseEntity.ok(
                documentRepository.findByOwnerId(userId));
    }

    // Open a document if the user owns it or it is shared with them
    @GetMapping("/{id}")
    public ResponseEntity<?> openDocument(
            @PathVariable Long id,
            HttpSession session) {

        Long userId = (Long) session.getAttribute("userId");

        if (userId == null) {
            return ResponseEntity.status(401)
                    .body(Map.of("message", "Please log in first"));
        }

        return documentRepository.findById(id).map(document -> {

            boolean owner = document.getOwnerId().equals(userId);

            boolean shared = shareRepository
                    .existsByDocumentIdAndSharedWithUserId(id, userId);

            if (!owner && !shared) {
                return ResponseEntity.status(403)
                        .body(Map.of(
                                "message",
                                "You cannot access this document"));
            }

            auditLogRepository.save(
                    new AuditLog(userId, id, "OPEN"));

            return ResponseEntity.ok(document);

        }).orElseGet(() -> ResponseEntity.notFound().build());
    }

    // Share a document with another registered user
    @PostMapping("/{id}/share")
    public ResponseEntity<?> shareDocument(
            @PathVariable Long id,
            @RequestBody Map<String, String> request,
            HttpSession session) {

        Long userId = (Long) session.getAttribute("userId");

        if (userId == null) {
            return ResponseEntity.status(401)
                    .body(Map.of("message", "Please log in first"));
        }

        Document document = documentRepository.findById(id).orElse(null);

        if (document == null) {
            return ResponseEntity.notFound().build();
        }

        if (!document.getOwnerId().equals(userId)) {
            return ResponseEntity.status(403)
                    .body(Map.of(
                            "message", "Only the owner can share"));
        }

        String email = request.get("email");

        if (email == null || email.isBlank()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("message", "Email is required"));
        }

        User recipient = userRepository.findByEmail(email.trim())
                .orElse(null);

        if (recipient == null) {
            return ResponseEntity.badRequest()
                    .body(Map.of("message", "User not found"));
        }

        if (recipient.getId().equals(userId)) {
            return ResponseEntity.badRequest()
                    .body(Map.of(
                            "message", "Cannot share with yourself"));
        }

        if (shareRepository.existsByDocumentIdAndSharedWithUserId(
                id, recipient.getId())) {
            return ResponseEntity.badRequest()
                    .body(Map.of(
                            "message", "Already shared with this user"));
        }

        shareRepository.save(
                new DocumentShare(id, recipient.getId()));

        auditLogRepository.save(
                new AuditLog(userId, id, "SHARE"));

        return ResponseEntity.ok(
                Map.of("message", "Document shared successfully"));
    }

    // Revoke a user's access to a shared document
    @Transactional
    @DeleteMapping("/{id}/share/{userId}")
    public ResponseEntity<?> revokeShare(
            @PathVariable Long id,
            @PathVariable Long userId,
            HttpSession session) {

        Long ownerId = (Long) session.getAttribute("userId");

        if (ownerId == null) {
            return ResponseEntity.status(401)
                    .body(Map.of("message", "Please log in first"));
        }

        Document document = documentRepository.findById(id).orElse(null);

        if (document == null) {
            return ResponseEntity.notFound().build();
        }

        if (!document.getOwnerId().equals(ownerId)) {
            return ResponseEntity.status(403)
                    .body(Map.of(
                            "message", "Only the owner can revoke access"));
        }

        if (!shareRepository.existsByDocumentIdAndSharedWithUserId(
                id, userId)) {
            return ResponseEntity.badRequest()
                    .body(Map.of("message", "Share not found"));
        }

        int deleted =
                shareRepository.deleteByDocumentIdAndSharedWithUserId(
                        id, userId);

        if (deleted == 0) {
            return ResponseEntity.badRequest()
                    .body(Map.of(
                            "message", "Share record was not deleted"));
        }

        auditLogRepository.save(
                new AuditLog(ownerId, id, "REVOKE"));

        return ResponseEntity.ok(
                Map.of("message", "Access revoked successfully"));
    }

    // List users with whom the owner has shared a document
    @GetMapping("/{id}/shares")
    public ResponseEntity<?> getDocumentShares(
            @PathVariable Long id,
            HttpSession session) {

        Long ownerId = (Long) session.getAttribute("userId");

        if (ownerId == null) {
            return ResponseEntity.status(401)
                    .body(Map.of("message", "Please log in."));
        }

        Optional<Document> document = documentRepository.findById(id);

        if (document.isEmpty()) {
            return ResponseEntity.status(404)
                    .body(Map.of("message", "Document not found."));
        }

        if (!document.get().getOwnerId().equals(ownerId)) {
            return ResponseEntity.status(403)
                    .body(Map.of("message", "Access denied."));
        }

        List<Map<String, Object>> shares = new ArrayList<>();

        for (DocumentShare share : shareRepository.findByDocumentId(id)) {

            Optional<User> user =
                    userRepository.findById(share.getSharedWithUserId());

            if (user.isPresent()) {
                Map<String, Object> item = new HashMap<>();
                item.put("userId", user.get().getId());
                item.put("email", user.get().getEmail());
                shares.add(item);
            }
        }

        return ResponseEntity.ok(shares);
    }

    // List documents shared with the logged-in user
    @GetMapping("/shared-with-me")
    public ResponseEntity<?> getSharedDocuments(HttpSession session) {

        Long userId = (Long) session.getAttribute("userId");

        if (userId == null) {
            return ResponseEntity.status(401)
                    .body(Map.of("message", "Please log in first"));
        }

        List<Document> documents = shareRepository
                .findBySharedWithUserId(userId)
                .stream()
                .map(share -> documentRepository
                        .findById(share.getDocumentId())
                        .orElse(null))
                .filter(document -> document != null)
                .toList();

        return ResponseEntity.ok(documents);
    }
}
