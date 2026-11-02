
package com.trustvault.controller;

import com.trustvault.User;
import com.trustvault.UserRepository;
import com.trustvault.service.UserService;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Optional;

@RestController
public class AuthController {

    private final UserService userService;
    private final UserRepository userRepository;

    public AuthController(
            UserService userService,
            UserRepository userRepository) {
        this.userService = userService;
        this.userRepository = userRepository;
    }

    @PostMapping("/api/register")
    public ResponseEntity<Map<String, String>> register(
            @RequestBody Map<String, String> request) {

        String result = userService.registerUser(
                request.get("fullName"),
                request.get("email"),
                request.get("password")
        );

        if (result.equals("Account created successfully!")) {
            return ResponseEntity.ok(Map.of("message", result));
        }

        return ResponseEntity.badRequest()
                .body(Map.of("message", result));
    }

    @PostMapping("/api/login")
    public ResponseEntity<Map<String, String>> login(
            @RequestBody Map<String, String> request,
            HttpSession session) {

        Optional<User> user = userService.verifyLogin(
                request.get("email"),
                request.get("password")
        );

        if (user.isPresent()) {
            session.setAttribute("userId", user.get().getId());
            session.setAttribute(
                    "role",
                    user.get().getRole() == null
                            ? "VIEWER"
                            : user.get().getRole()
            );

            return ResponseEntity.ok(
                    Map.of(
                            "message", "Login successful",
                            "role", user.get().getRole() == null
                                    ? "VIEWER"
                                    : user.get().getRole()
                    )
            );
        }

        return ResponseEntity.status(401).body(
                Map.of("message", "Invalid email or password")
        );
    }

    @GetMapping("/api/auth/me")
    public ResponseEntity<Map<String, String>> currentUser(
            HttpSession session) {

        Object userId = session.getAttribute("userId");

        if (userId == null) {
            return ResponseEntity.status(401)
                    .body(Map.of("message", "Not logged in"));
        }

        Optional<User> user = userService.findUserById(
                Long.valueOf(userId.toString())
        );

        if (user.isEmpty()) {
            session.invalidate();
            return ResponseEntity.status(401)
                    .body(Map.of("message", "User not found"));
        }

        return ResponseEntity.ok(
                Map.of(
                        "fullName", user.get().getFullName(),
                        "role", user.get().getRole() == null
                                ? "VIEWER"
                                : user.get().getRole()
                )
        );
    }

    @PostMapping("/api/logout")
    public ResponseEntity<Map<String, String>> logout(
            HttpSession session) {

        session.invalidate();

        return ResponseEntity.ok(
                Map.of("message", "Logged out successfully")
        );
    }
}
