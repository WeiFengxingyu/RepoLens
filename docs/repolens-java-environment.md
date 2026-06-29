# RepoLens-Java 本地 Java 环境说明

## 1. 当前目标

RepoLens-Java 使用 Java 21。当前机器已安装 Java 8、Java 17 和 Microsoft OpenJDK 21。

为了便于不同项目切换 JDK，本项目提供会话级切换脚本：

```powershell
.\scripts\use-java.ps1 17
.\scripts\use-java.ps1 21
```

脚本只修改当前 PowerShell 会话中的 `JAVA_HOME` 和 `PATH`，不会永久改系统环境变量。

## 2. 已检测到的本机 JDK

| 版本 | 路径 | 状态 |
| --- | --- | --- |
| Java 8 | `F:\Program Files\Java\jdk1.8.0_341` | 已存在 |
| Java 17 | `F:\Program Files\Java\jdk17` | 已存在 |
| Java 21 | `C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot` | 已存在 |

## 3. 推荐使用方式

如需维护旧项目，可以切换到 Java 17：

```powershell
.\scripts\use-java.ps1 17
cd backend-java
mvn test
```

开发 RepoLens-Java 时默认切换到 Java 21：

```powershell
.\scripts\use-java.ps1 21
cd backend-java
mvn test
```

## 4. Maven 本地仓库

由于本机全局 Maven settings 将 localRepository 指向了不可写目录，本项目在 `backend-java/.mvn/maven.config` 中指定：

```text
-Dmaven.repo.local=../.m2/repository
```

这样 Java 后端依赖会缓存到：

```text
RepoLens/.m2/repository
```

避免污染全局 Maven 安装目录，也便于复现。

## 5. Java 21 安装记录

2026-06-28 尝试使用 Chocolatey 安装 `Temurin21`：

```powershell
choco install Temurin21 -y
```

Chocolatey 包源查询成功，但 GitHub MSI 下载速度异常，安装进程长时间 pending，已停止该次挂起安装。

随后改用 Microsoft OpenJDK 21：

```powershell
choco install microsoft-openjdk-21 -y
```

安装成功：

```text
C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot
```

后续可选方案：

1. 默认使用 `.\scripts\use-java.ps1 21` 切换到 Microsoft OpenJDK 21。
2. 如需 Temurin 21，可在网络稳定时重新运行 Chocolatey 安装。
3. 也可以手动下载 Temurin/OpenJDK 21 zip，将解压后的 JDK 21 放到 `F:\Program Files\Java\jdk21`。
