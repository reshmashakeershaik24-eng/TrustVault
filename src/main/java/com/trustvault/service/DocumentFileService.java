
package com.trustvault.service;

import com.trustvault.Document;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.extractor.XWPFWordExtractor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;

@Service
public class DocumentFileService {

    private static final long MAX_FILE_SIZE = 10 * 1024 * 1024;

    private static final Set<String> ALLOWED_EXTENSIONS =
            Set.of("pdf", "docx", "txt");

    private final Path uploadDirectory =
            Paths.get("uploads").toAbsolutePath().normalize();

    public DocumentFileService() throws IOException {
        Files.createDirectories(uploadDirectory);
    }

    public void processUpload(
            MultipartFile file,
            Document document
    ) throws IOException {

        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("Please select a file.");
        }

        if (file.getSize() > MAX_FILE_SIZE) {
            throw new IllegalArgumentException(
                    "Maximum file size is 10 MB."
            );
        }

        String originalName = file.getOriginalFilename();

        if (originalName == null || originalName.isBlank()) {
            throw new IllegalArgumentException(
                    "Invalid file name."
            );
        }

        String safeName = originalName.replace('\\', '/');
        safeName = safeName.substring(safeName.lastIndexOf('/') + 1);

        int dot = safeName.lastIndexOf('.');

        if (dot <= 0 || dot == safeName.length() - 1) {
            throw new IllegalArgumentException(
                    "Only PDF, DOCX and TXT files are supported."
            );
        }

        String extension = safeName.substring(dot + 1)
                .toLowerCase(Locale.ROOT);

        if (!ALLOWED_EXTENSIONS.contains(extension)) {
            throw new IllegalArgumentException(
                    "Only PDF, DOCX and TXT files are supported."
            );
        }

        String storedName = UUID.randomUUID() + "." + extension;
        Path destination = uploadDirectory.resolve(storedName)
                .normalize();

        if (!destination.startsWith(uploadDirectory)) {
            throw new IllegalArgumentException("Invalid file path.");
        }

        try (InputStream input = file.getInputStream()) {
            Files.copy(
                    input,
                    destination,
                    StandardCopyOption.REPLACE_EXISTING
            );
        }

        try {
            String extractedText = extractText(destination, extension);

            if (extractedText == null || extractedText.isBlank()) {
                throw new IllegalArgumentException(
                        "No readable text found. Scanned PDFs may need OCR."
                );
            }

            document.setTitle(safeName);
            document.setContent(extractedText);
            document.setOriginalFileName(safeName);
            document.setStoredFileName(storedName);
            document.setFileType(extension);
            document.setFileSize(file.getSize());

        } catch (Exception exception) {
            Files.deleteIfExists(destination);
            throw exception;
        }
    }

    private String extractText(
            Path filePath,
            String extension
    ) throws IOException {

        return switch (extension) {
            case "txt" -> Files.readString(filePath);

            case "pdf" -> {
                try (PDDocument pdf =
                             Loader.loadPDF(filePath.toFile())) {
                    yield new PDFTextStripper().getText(pdf);
                }
            }

            case "docx" -> {
                try (InputStream input =
                             Files.newInputStream(filePath);
                     XWPFDocument word = new XWPFDocument(input);
                     XWPFWordExtractor extractor =
                             new XWPFWordExtractor(word)) {
                    yield extractor.getText();
                }
            }

            default -> throw new IllegalArgumentException(
                    "Unsupported file type."
            );
        };
    }
}
