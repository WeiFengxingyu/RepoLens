package com.repolens.demo.user;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserService {

    @Transactional(readOnly = true)
    public UserDto getUser(Long id) {
        return new UserDto(id, "demo");
    }
}
