package com.trustvault;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface DocumentShareRepository
        extends JpaRepository<DocumentShare, Long> {

    List<DocumentShare> findBySharedWithUserId(Long userId);

    List<DocumentShare> findByDocumentId(Long documentId);

    Optional<DocumentShare> findByDocumentIdAndSharedWithUserId(
            Long documentId, Long userId);

   @org.springframework.data.jpa.repository.Modifying
@org.springframework.transaction.annotation.Transactional
@org.springframework.data.jpa.repository.Query(
    "DELETE FROM DocumentShare d WHERE d.documentId = :documentId AND d.sharedWithUserId = :userId")
int deleteByDocumentIdAndSharedWithUserId(
    @org.springframework.data.repository.query.Param("documentId") Long documentId,
    @org.springframework.data.repository.query.Param("userId") Long userId);

    boolean existsByDocumentIdAndSharedWithUserId(
            Long documentId, Long userId);
}