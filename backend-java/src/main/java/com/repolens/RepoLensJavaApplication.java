package com.repolens;

import com.repolens.config.RepoLensProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(RepoLensProperties.class)
public class RepoLensJavaApplication {

    public static void main(String[] args) {
        SpringApplication.run(RepoLensJavaApplication.class, args);
    }
}
