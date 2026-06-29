package com.repolens.review.application;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

@Component
public class ReviewRiskRuleEngine {

    private static final List<Rule> RULES = List.of(
            new Rule("AUTH_BYPASS", "high", "鉴权规则变更可能放宽访问控制", Pattern.compile("permitAll|csrf\\s*\\(\\)\\.disable|disable\\s*csrf|anonymous", Pattern.CASE_INSENSITIVE)),
            new Rule("SECRET_EXPOSURE", "high", "疑似新增明文密钥、密码或 token", Pattern.compile("password|secret|token|api[_-]?key", Pattern.CASE_INSENSITIVE)),
            new Rule("DANGEROUS_EXECUTION", "high", "疑似新增危险命令执行入口", Pattern.compile("Runtime\\.getRuntime\\(\\)\\.exec|ProcessBuilder|eval\\s*\\(", Pattern.CASE_INSENSITIVE)),
            new Rule("NULL_RETURN", "medium", "新增 return null 可能引入空指针或语义不清", Pattern.compile("return\\s+null\\s*;", Pattern.CASE_INSENSITIVE)),
            new Rule("BROAD_EXCEPTION", "medium", "宽泛异常捕获可能吞掉真实错误", Pattern.compile("catch\\s*\\(\\s*(Exception|Throwable)\\b", Pattern.CASE_INSENSITIVE)),
            new Rule("SQL_CHANGE", "medium", "SQL/DDL 变更需要关注兼容性和回滚", Pattern.compile("\\b(ALTER|DROP|DELETE|UPDATE|INSERT)\\b", Pattern.CASE_INSENSITIVE)),
            new Rule("TODO_LEFT", "low", "新增 TODO/FIXME 说明逻辑可能未完成", Pattern.compile("TODO|FIXME", Pattern.CASE_INSENSITIVE))
    );

    public List<Map<String, Object>> evaluate(ParsedDiff diff, List<String> evidenceIds) {
        List<Map<String, Object>> risks = new ArrayList<>();
        for (ChangedFile file : diff.files()) {
            for (DiffHunk hunk : file.hunks()) {
                for (DiffLine line : hunk.lines()) {
                    if (line.type() != DiffLineType.ADDED) {
                        continue;
                    }
                    for (Rule rule : RULES) {
                        if (rule.pattern().matcher(line.content()).find()) {
                            risks.add(toRisk(rule, file.displayPath(), line, evidenceIds));
                        }
                    }
                }
            }
        }
        if (risks.isEmpty() && diff.addedLineCount() > 0) {
            Map<String, Object> risk = new LinkedHashMap<>();
            risk.put("title", "代码变更需要常规回归验证");
            risk.put("severity", "low");
            risk.put("reason", "未命中特定高危规则，但仍建议结合相关模块补充回归测试。");
            risk.put("evidence_ids", evidenceIds);
            risk.put("impacted_symbols", List.of());
            risk.put("suggestion", "检查变更文件附近的单元测试和接口回归用例。");
            risks.add(risk);
        }
        return risks;
    }

    private Map<String, Object> toRisk(Rule rule, String filePath, DiffLine line, List<String> evidenceIds) {
        Map<String, Object> risk = new LinkedHashMap<>();
        risk.put("title", rule.title());
        risk.put("severity", rule.severity());
        risk.put("location", Map.of(
                "file_path", filePath,
                "start_line", line.newLine(),
                "end_line", line.newLine()
        ));
        risk.put("reason", "新增代码 `" + compact(line.content()) + "` 命中规则 " + rule.id() + "。");
        risk.put("evidence_ids", evidenceIds);
        risk.put("impacted_symbols", List.of(filePath));
        risk.put("suggestion", suggestionFor(rule));
        return risk;
    }

    private String suggestionFor(Rule rule) {
        return switch (rule.id()) {
            case "AUTH_BYPASS" -> "补充鉴权/未授权访问测试，确认接口没有被意外放开。";
            case "SECRET_EXPOSURE" -> "避免提交明文密钥，改用环境变量或密钥管理服务。";
            case "DANGEROUS_EXECUTION" -> "限制命令来源，增加白名单和审计，避免命令注入。";
            case "NULL_RETURN" -> "明确空值语义，补充 null 分支调用方测试。";
            case "BROAD_EXCEPTION" -> "缩小异常类型，记录日志或向上抛出可观测错误。";
            case "SQL_CHANGE" -> "补充 migration 回滚、兼容性和数据安全验证。";
            default -> "补齐 TODO/FIXME 对应实现或在任务系统中登记。";
        };
    }

    private String compact(String value) {
        String trimmed = value.trim();
        return trimmed.length() <= 120 ? trimmed : trimmed.substring(0, 117) + "...";
    }

    private record Rule(String id, String severity, String title, Pattern pattern) {
    }
}
