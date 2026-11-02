
package com.trustvault.service;

import com.trustvault.User;
import com.trustvault.UserRepository;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final BCryptPasswordEncoder passwordEncoder;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
        this.passwordEncoder = new BCryptPasswordEncoder();
    }

    public String registerUser(String fullName, String email, String password) {

        if (fullName == null || fullName.isBlank()
                || email == null || email.isBlank()
                || password == null || password.length() < 8) {

            return "Please enter valid details. Password must contain at least 8 characters.";
        }

        String normalizedEmail = email.trim().toLowerCase();

        if (userRepository.findByEmail(normalizedEmail).isPresent()) {
            return "Email already registered. Please sign in.";
        }

        User user = new User();
        user.setFullName(fullName.trim());
        user.setEmail(normalizedEmail);
        user.setPassword(passwordEncoder.encode(password));
        user.setRole("VIEWER");

        userRepository.save(user);

        return "Account created successfully!";
    }

    public Optional<User> verifyLogin(String email, String password) {

        if (email == null || email.isBlank()
                || password == null || password.isBlank()) {

            return Optional.empty();
        }

        Optional<User> user =
                userRepository.findByEmail(email.trim().toLowerCase());

        if (user.isPresent()
                && passwordEncoder.matches(
                        password, user.get().getPassword())) {

            return user;
        }

        return Optional.empty();
    }

    public Optional<User> findUserById(Long userId) {
        if (userId == null) {
            return Optional.empty();
        }

        return userRepository.findById(userId);
    }
}
