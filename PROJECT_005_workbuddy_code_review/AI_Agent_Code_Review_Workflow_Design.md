# AI Agent 自动化代码审查工作流设计方案

> **适用场景**：15 人开发团队，日均 20+ PR，多仓库并行开发  
> **设计目标**：将人工审查效率提升 60%+，缺陷拦截率 ≥ 85%，误报率 ≤ 10%  
> **技术栈**：GitHub Actions + AI Agent + Custom Rules Engine + Metrics Dashboard

---

## 目录

1. [代码规范检查规则集](#1-代码规范检查规则集)
2. [自动化审查流水线设计](#2-自动化审查流水线设计)
3. [常见问题模式库](#3-常见问题模式库)
4. [审查意见优先级分类与自动标注](#4-审查意见优先级分类与自动标注)
5. [Agent 自学习机制](#5-agent-自学习机制)
6. [CI/CD 集成方案](#6-cicd-集成方案)
7. [审查效果度量指标与仪表盘设计](#7-审查效果度量指标与仪表盘设计)

---

## 1. 代码规范检查规则集

### 1.1 规则分层架构

```
┌─────────────────────────────────────────────┐
│              Layer 4: AI 语义层              │
│  业务逻辑审查、设计模式、架构合规性            │
├─────────────────────────────────────────────┤
│              Layer 3: 安全扫描层              │
│  SQL注入、XSS、敏感信息泄露、依赖漏洞          │
├─────────────────────────────────────────────┤
│              Layer 2: 复杂度分析层            │
│  圈复杂度、认知复杂度、耦合度、重复代码         │
├─────────────────────────────────────────────┤
│              Layer 1: 基础规范层              │
│  命名、格式、注释、导入排序、类型标注           │
└─────────────────────────────────────────────┘
```

### 1.2 命名规范规则 (Layer 1)

```yaml
# .github/ai-review/rules/naming.yaml
rules:
  naming:
    # 类名：大驼峰
    - id: NAM-001
      severity: error
      pattern: "class [a-z]"
      message: "类名必须使用 PascalCase（大驼峰），当前: {match}"
      language: [java, typescript, python, go]

    # 方法/函数：小驼峰（Java/TS）或 snake_case（Python）
    - id: NAM-002
      severity: error
      type: method_naming
      rules_by_language:
        java: "^[a-z][a-zA-Z0-9]*$"
        typescript: "^[a-z][a-zA-Z0-9]*$"
        python: "^[a-z][a-z0-9_]*$"
        go: "^[a-z][a-zA-Z0-9]*$"
      message: "方法名不符合语言约定: {name}"

    # 常量：全大写下划线（跨语言通用）
    - id: NAM-003
      severity: error
      pattern: "const [a-z]"
      scope: "top-level"
      message: "全局常量必须使用 UPPER_SNAKE_CASE"

    # 布尔变量：is/has/can/should 前缀
    - id: NAM-004
      severity: warning
      type: boolean_prefix
      prefixes: [is, has, can, should, will, did]
      message: "布尔变量建议使用 '{prefixes}' 前缀，当前: {name}"

    # 禁止单字母变量（除循环索引 i,j,k）
    - id: NAM-005
      severity: warning
      type: single_char_variable
      exceptions: [i, j, k, x, y, z, e]
      message: "避免单字母变量名 '{name}'，请使用有意义的名称"

    # 禁止拼音命名
    - id: NAM-006
      severity: error
      type: pinyin_detection
      message: "禁止使用拼音命名: '{name}'，请使用标准英文单词"

    # 接口/抽象类前缀
    - id: NAM-007
      severity: warning
      language: [java]
      type: interface_prefix
      prefix: "I"
      message: "接口名建议使用 'I' 前缀（如 IUserService）"
```

### 1.3 代码格式规则 (Layer 1)

```yaml
# .github/ai-review/rules/formatting.yaml
rules:
  formatting:
    - id: FMT-001
      severity: error
      type: indentation
      default: 4_spaces
      message: "缩进不一致，要求 {expected}，实际 {actual}"

    - id: FMT-002
      severity: error
      type: line_length
      max: 120
      message: "行长度 {actual} 超过限制 {max}"

    - id: FMT-003
      severity: warning
      type: trailing_whitespace
      message: "行末存在多余空白字符"

    - id: FMT-004
      severity: error
      type: file_end_newline
      message: "文件末尾缺少换行符"

    - id: FMT-005
      severity: warning
      type: consecutive_blank_lines
      max: 1
      message: "连续空行数 {actual} 超过限制 {max}"

    - id: FMT-006
      severity: warning
      type: import_organization
      language: [java]
      order: [java, javax, org, com, project_internal]
      message: "导入顺序不符合规范，期望按包分组排序"

    - id: FMT-007
      severity: warning
      type: bracket_style
      language: [java, typescript]
      style: same_line  # K&R style
      message: "左花括号应放在同一行"

    - id: FMT-008
      severity: error
      type: unused_import
      message: "存在未使用的导入: {import}"

    - id: FMT-009
      severity: warning
      type: method_spacing
      language: [java]
      rule: "方法之间需要且仅需要一个空行"

    - id: FMT-010
      severity: info
      type: todo_fixme_tracking
      pattern: "(TODO|FIXME|HACK|XXX)"
      message: "存在待办标记: {match}，请确认是否需要在本 PR 中处理"
```

### 1.4 复杂度分析规则 (Layer 2)

```yaml
# .github/ai-review/rules/complexity.yaml
rules:
  complexity:
    # 圈复杂度（Cyclomatic Complexity）
    - id: CPX-001
      severity: error
      type: cyclomatic_complexity
      max: 15            # 方法级上限
      warn_at: 10        # 警告阈值
      message: "圈复杂度 {actual} 超过上限 {max}，建议拆分方法"

    # 认知复杂度（Cognitive Complexity）
    - id: CPX-002
      severity: warning
      type: cognitive_complexity
      max: 15
      message: "认知复杂度 {actual} 过高，嵌套层级或逻辑分支过多"

    # 方法行数限制
    - id: CPX-003
      severity: warning
      type: method_length
      max: 80            # 不含注释和空行
      message: "方法体 {actual} 行超过限制 {max} 行"

    # 参数个数限制
    - id: CPX-004
      severity: warning
      type: parameter_count
      max: 5
      message: "参数个数 {actual} 超过限制 {max}，建议使用参数对象封装"

    # 嵌套深度
    - id: CPX-005
      severity: error
      type: nesting_depth
      max: 4
      message: "嵌套深度 {actual} 超过限制 {max}"

    # 类行数限制
    - id: CPX-006
      severity: warning
      type: class_length
      max: 500
      message: "类行数 {actual} 超过限制 {max}，建议拆分职责"

    # 文件行数限制
    - id: CPX-007
      severity: warning
      type: file_length
      max: 800
      message: "文件行数 {actual} 超过限制 {max}"

    # 重复代码检测
    - id: CPX-008
      severity: warning
      type: code_duplication
      min_lines: 6
      min_tokens: 50
      message: "检测到重复代码块（{lines} 行），建议提取公共方法"

    # 圈复杂度增量检查（仅检查变更部分）
    - id: CPX-009
      severity: error
      type: complexity_delta
      max_increase_per_method: 5
      message: "方法 '{method}' 圈复杂度增量 {delta} 超过允许值 {max}"
```

### 1.5 安全漏洞规则 (Layer 3)

```yaml
# .github/ai-review/rules/security.yaml
rules:
  security:
    # === 注入类 ===
    - id: SEC-001
      severity: critical
      type: sql_injection
      language: [java]
      patterns:
        - 'String\s+\w+\s*=\s*".*SELECT.*"\s*\+'
        - 'Statement\.executeQuery\(.*\+'
        - '\.createStatement\(\)'
      message: "疑似 SQL 拼接，存在 SQL 注入风险。请使用 PreparedStatement 或 ORM 参数化查询"
      auto_block_merge: true

    - id: SEC-002
      severity: critical
      type: xss_vulnerability
      language: [java, typescript]
      patterns:
        - 'response\.getWriter\(\)\.write\(.*request\.getParameter'
        - 'innerHTML\s*='
        - 'dangerouslySetInnerHTML'
      message: "存在 XSS 跨站脚本攻击风险，请对输出进行转义处理"

    - id: SEC-003
      severity: critical
      type: command_injection
      language: [java, python]
      patterns:
        - 'Runtime\.getRuntime\(\)\.exec\(.*\+'
        - 'os\.system\(.*\+'
        - 'subprocess\.call\(.*\+|.*format'
      message: "存在命令注入风险，禁止拼接命令行参数"

    - id: SEC-004
      severity: critical
      type: path_traversal
      patterns:
        - 'new\s+File(InputStream)?\(.*request\.getParameter'
        - 'open\(.*request\.\w+'
      message: "存在路径遍历风险，请校验文件路径"

    # === 敏感信息 ===
    - id: SEC-010
      severity: critical
      type: hardcoded_secret
      patterns:
        - '(password|passwd|secret|token|api_key|apikey|private_key)\s*[:=]\s*["\"][^""]{8,}["\"]'
        - '(accessKey|secretKey|appSecret)\s*[:=]\s*["\"][^""]{8,}["\"]'
      message: "疑似硬编码密钥/密码: {match}，请使用环境变量或配置中心"
      auto_block_merge: true

    - id: SEC-011
      severity: error
      type: log_sensitive_data
      patterns:
        - 'log\.\w+\(.*password'
        - 'log\.\w+\(.*token'
        - 'log\.\w+\(.*secret'
        - 'console\.log\(.*password'
        - 'System\.out\.print.*password'
      message: "日志中可能包含敏感信息，禁止打印密码/Token 等"

    - id: SEC-012
      severity: error
      type: debug_endpoint_in_production
      patterns:
        - '@Profile\("dev"\).*@GetMapping'
        - 'if\s*\(\s*"dev"\.equals'
        - '#if DEBUG'
      message: "确认调试代码不会进入生产环境"

    # === 加密与认证 ===
    - id: SEC-020
      severity: error
      type: weak_crypto
      patterns:
        - 'MessageDigest\.getInstance\("MD5"\)'
        - 'MessageDigest\.getInstance\("SHA-1"\)'
        - 'Cipher\.getInstance\("DES"'
      message: "使用了弱加密算法 {match}，请使用 SHA-256/AES-256 等强加密算法"

    - id: SEC-021
      severity: error
      type: missing_auth_check
      language: [java]
      patterns:
        - '@PostMapping.*\n(?!.*@PreAuthorize)'
        - '@DeleteMapping.*\n(?!.*@PreAuthorize)'
      message: "敏感接口缺少权限注解，请添加 @PreAuthorize 或等效鉴权"

    # === 依赖安全 ===
    - id: SEC-030
      severity: critical
      type: dependency_cve
      auto_block_merge: true
      description: "依赖组件存在已知 CVE 漏洞"
      check: "基于 GitHub Advisory Database + OSS Index"

    - id: SEC-031
      severity: warning
      type: deprecated_dependency
      description: "使用了已标记为废弃的依赖版本"

    # === 资源管理 ===
    - id: SEC-040
      severity: error
      type: resource_leak
      language: [java]
      patterns:
        - 'new\s+(File)?(Input|Output)Stream\((?!.*try)'
        - 'new\s+(Buffered)?(Reader|Writer)(?!.*try)'
      message: "资源未使用 try-with-resources 管理，存在泄漏风险"

    - id: SEC-041
      severity: warning
      type: dos_risk
      patterns:
        - 'new\s+String\(.*request\.getParameter'
        - 'while\s*\(true\)'
        - 'Thread\.sleep\(.*\d{4,}'
      message: "存在潜在 DOS 或资源耗尽风险"
```

---

## 2. 自动化审查流水线设计

### 2.1 整体架构

```
┌──────────┐    ┌─────────────────────────────────────────────────────┐
│ Developer │    │                  GitHub Actions                      │
│  Push /   │───▶│                                                     │
│  PR Open  │    │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
└──────────┘    │  │  Phase 1  │  │  Phase 2  │  │     Phase 3      │  │
                │  │  静态扫描  │─▶│  语义分析  │─▶│   AI Agent 审查  │  │
                │  └──────────┘  └──────────┘  └──────────────────┘  │
                │        │             │                │             │
                │        ▼             ▼                ▼             │
                │  ┌──────────────────────────────────────────────┐  │
                │  │              结果聚合 & 报告生成               │  │
                │  └──────────────────────────────────────────────┘  │
                │                         │                           │
                │                         ▼                           │
                │               ┌─────────────────┐                  │
                │               │  PR Comment +    │                  │
                │               │  Status Check    │                  │
                │               └─────────────────┘                  │
                └─────────────────────────────────────────────────────┘
```

### 2.2 触发条件策略

```yaml
# .github/workflows/ai-code-review.yml
triggers:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    paths-ignore:
      - "**.md"
      - "docs/**"
      - ".github/**"
      - "*.yml"
      - "*.yaml"

  # 特殊条件触发
  conditional:
    - when: PR 从 draft 转为 ready_for_review
      action: 全量审查
    - when: PR 被 request_review  @ai-reviewer
      action: 增量审查（仅看最新 commit）
    - when: PR 合并到 main/master
      action: 事后审计 + 更新知识库
    - when: 手动评论 "/ai-review full"
      action: 全量深度审查
    - when: 手动评论 "/ai-review security"
      action: 仅安全审查

  # 并发控制
  concurrency:
    group: ai-review-${{ github.ref }}
    cancel-in-progress: true
```

### 2.3 Phase 1：静态扫描（2-3 分钟）

```yaml
phase_1_static:
  parallel_jobs:
    - name: "ESLint / Checkstyle"
      tool: reviewdog
      config: .github/ai-review/configs/checkstyle.xml
      reporter: github-pr-review
      level: error

    - name: "命名规范检查"
      tool: custom-script
      script: .github/ai-review/scripts/naming_check.py
      output: naming_report.json

    - name: "安全扫描 (CodeQL)"
      tool: github/codeql-action
      languages: [java, javascript, python, go]
      queries: security-extended

    - name: "依赖漏洞扫描"
      tool: dependency-review-action
      fail-on-severity: critical

    - name: "重复代码检测"
      tool: jscpd
      config: .github/ai-review/configs/jscpd.json

  output:
    format: sarif + json
    artifact: phase1-results
```

### 2.4 Phase 2：语义分析（1-2 分钟）

```yaml
phase_2_semantic:
  parallel_jobs:
    - name: "复杂度分析"
      tool: custom-script
      script: .github/ai-review/scripts/complexity_analyzer.py
      analysis: diff_only  # 只分析变更代码的复杂度增量
      output: complexity_report.json

    - name: "调用链分析"
      tool: custom-script
      script: .github/ai-review/scripts/dependency_graph.py
      analysis:
        - 新增的循环依赖
        - 跨层调用违规（如 Controller 直接调用 DAO）
        - 公共方法签名变更影响范围

    - name: "API 兼容性"
      tool: openapi-diff
      check: breaking_changes
      message: "检测到 API 破坏性变更，请确认版本号已更新"
```

### 2.5 Phase 3：AI Agent 深度审查（3-5 分钟）

```yaml
phase_3_ai_agent:
  # AI Agent 配置
  agent:
    model: gpt-4o / claude-3.5-sonnet  # 可配置
    context_window: 128K
    max_tokens_per_review: 8000

  # 审查维度（基于前两阶段结果 + 原始代码）
  review_dimensions:
    - dimension: "业务逻辑正确性"
      weight: 0.30
      focus:
        - 空指针/空值处理是否完备
        - 边界条件处理（空集合、极值、并发场景）
        - 事务边界是否正确
        - 幂等性保证

    - dimension: "设计模式与架构"
      weight: 0.20
      focus:
        - 是否符合项目选定的架构模式（DDD/MVC/微服务）
        - 单一职责原则
        - 开闭原则
        - 依赖倒置

    - dimension: "可维护性"
      weight: 0.20
      focus:
        - 代码可读性与注释质量
        - 魔法值/硬编码
        - 异常处理是否恰当（是否吞异常）
        - 是否有合适的单元测试

    - dimension: "性能影响"
      weight: 0.15
      focus:
        - N+1 查询
        - 不必要的大对象创建
        - 数据库索引使用
        - 缓存策略合理性

    - dimension: "安全与合规"
      weight: 0.15
      focus:
        - 输入校验是否完备
        - 权限控制粒度
        - 数据脱敏
        - 审计日志

  # Prompt 模板
  prompt_template: |
    你是一名资深代码审查专家。请审查以下 PR 的代码变更。

    ## PR 上下文
    - 标题: {pr_title}
    - 描述: {pr_description}
    - 语言: {language}
    - 框架: {framework}

    ## 第一阶段（静态扫描）发现的问题
    {phase1_findings}

    ## 第二阶段（复杂度分析）发现的问题
    {phase2_findings}

    ## 变更的文件
    {diff_content}

    ## 审查要求
    请从以下维度进行审查，并按指定格式输出：
    1. 业务逻辑正确性
    2. 设计模式与架构合规性
    3. 可维护性
    4. 性能影响
    5. 安全与合规

    ## 相关模式库参考
    {pattern_library_context}

    ## 输出格式
    每个发现使用以下 JSON 格式：
    ```json
    {{
      "file": "路径",
      "line": 行号,
      "severity": "critical|error|warning|info|suggestion",
      "category": "分类",
      "title": "问题简述",
      "description": "详细说明",
      "suggestion": "修改建议（含代码示例）",
      "pattern_ref": "模式库引用ID",
      "confidence": 0.0-1.0
    }}
    ```

  # 降级策略
  fallback:
    - condition: "API 调用超时 (>5min)"
      action: "使用本地模型 Ollama/Llama 3 替代"
    - condition: "Token 预算耗尽"
      action: "仅审查高风险文件（变更 >200 行 或 包含安全关键字）"
    - condition: "模型完全不可用"
      action: "回退到纯规则引擎，生成静态分析报告"
```

### 2.6 结果聚合与 PR 评论生成

```yaml
phase_4_aggregation:
  steps:
    - name: "合并三阶段结果"
      script: .github/ai-review/scripts/merge_results.py
      inputs:
        - phase1-results
        - phase2-results
        - phase3-results
      dedup_strategy: "按 file+line+category 去重，保留最高 severity"

    - name: "优先级分类与排序"
      script: .github/ai-review/scripts/priority_classifier.py
      config: .github/ai-review/configs/priority_rules.yaml

    - name: "生成审查摘要"
      output: review_summary.md
      template: |
        ## 🤖 AI Code Review Report

        ### 📊 审查概览
        | 指标 | 数值 |
        |------|------|
        | 审查文件数 | {files_reviewed} |
        | 变更行数 | {lines_changed} |
        | 发现问题数 | {total_issues} |
        | 严重问题 | {critical_count} |
        | 错误 | {error_count} |
        | 警告 | {warning_count} |
        | 建议 | {suggestion_count} |

        ### 🔴 严重问题（{critical_count}）
        {critical_issues}

        ### 🟠 错误（{error_count}）
        {error_issues}

        ### 🟡 警告（{warning_count}）
        {warning_issues}

        ### 🔵 建议（{suggestion_count}）
        {suggestion_issues}

        ### 📈 代码质量评分：{quality_score}/100

    - name: "发布 PR Review"
      uses: actions/github-script
      script: |
        github.rest.pulls.createReview({
          owner: context.repo.owner,
          repo: context.repo.repo,
          pull_number: context.issue.number,
          event: 'COMMENT',  // 或 'REQUEST_CHANGES' | 'APPROVE'
          body: review_summary_content
        });

    - name: "设置 Status Check"
      uses: actions/github-script
      script: |
        // 根据 critical 问题数量决定是否阻挡合并
        const conclusion = critical_count > 0 ? 'failure' : 'success';
        // 或使用分数阈值: quality_score < 60 ? 'failure' : 'success'
```

### 2.7 GitHub Actions 完整 Workflow 文件

```yaml
# .github/workflows/ai-code-review.yml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    paths-ignore:
      - '**.md'
      - 'docs/**'
  issue_comment:
    types: [created]

concurrency:
  group: ai-review-${{ github.event.pull_request.number || github.event.issue.number }}
  cancel-in-progress: true

jobs:
  # ========== Phase 1: 静态扫描 ==========
  static-analysis:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    permissions:
      contents: read
      security-events: write
    outputs:
      naming_report: ${{ steps.naming.outputs.report }}
      codeql_sarif: ${{ steps.codeql.outputs.sarif }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run Naming Convention Check
        id: naming
        uses: ./.github/ai-review/actions/naming-check
        with:
          config: .github/ai-review/configs/naming.yaml

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: java, javascript, python

      - name: Run CodeQL Analysis
        id: codeql
        uses: github/codeql-action/analyze@v3
        with:
          category: ai-review

      - name: Dependency Review
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: critical

      - name: Upload Phase 1 Results
        uses: actions/upload-artifact@v4
        with:
          name: phase1-results
          path: |
            .ai-review/naming-report.json
            .ai-review/codeql.sarif
            .ai-review/dependency-report.json

  # ========== Phase 2: 语义分析 ==========
  semantic-analysis:
    runs-on: ubuntu-latest
    needs: static-analysis
    if: github.event_name == 'pull_request'
    outputs:
      complexity_report: ${{ steps.complexity.outputs.report }}
      dependency_graph: ${{ steps.dep-graph.outputs.report }}
    steps:
      - uses: actions/checkout@v4

      - name: Complexity Analysis
        id: complexity
        uses: ./.github/ai-review/actions/complexity
        with:
          config: .github/ai-review/configs/complexity.yaml
          diff_only: true

      - name: Dependency Graph Analysis
        id: dep-graph
        uses: ./.github/ai-review/actions/dependency-check
        with:
          rules: .github/ai-review/configs/architecture.yaml

      - name: Upload Phase 2 Results
        uses: actions/upload-artifact@v4
        with:
          name: phase2-results
          path: |
            .ai-review/complexity-report.json
            .ai-review/dependency-graph.json

  # ========== Phase 3: AI Agent 审查 ==========
  ai-review:
    runs-on: ubuntu-latest
    needs: [static-analysis, semantic-analysis]
    if: |
      github.event_name == 'pull_request' ||
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '/ai-review'))
    permissions:
      contents: read
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v4

      - name: Download Previous Phase Results
        uses: actions/download-artifact@v4
        with:
          pattern: phase*-results
          path: .ai-review/

      - name: Prepare Diff Context
        id: diff
        run: |
          git fetch origin ${{ github.base_ref }}
          git diff origin/${{ github.base_ref }}...HEAD > .ai-review/diff.patch

      - name: Load Pattern Library
        id: patterns
        run: |
          python .github/ai-review/scripts/load_patterns.py \
            --language ${{ steps.detect-language.outputs.lang }} \
            --output .ai-review/patterns-context.txt

      - name: AI Agent Review
        id: ai-review
        uses: ./.github/ai-review/actions/ai-review
        with:
          model: ${{ vars.AI_REVIEW_MODEL || 'gpt-4o' }}
          api_key: ${{ secrets.AI_REVIEW_API_KEY }}
          diff_file: .ai-review/diff.patch
          phase1_results: .ai-review/
          phase2_results: .ai-review/
          pattern_library: .ai-review/patterns-context.txt
          pr_title: ${{ github.event.pull_request.title }}
          pr_body: ${{ github.event.pull_request.body }}
          language: ${{ steps.detect-language.outputs.lang }}
          max_tokens: 8000
          timeout_minutes: 5

      - name: Merge & Deduplicate Results
        run: |
          python .github/ai-review/scripts/merge_results.py \
            --output .ai-review/final-review.json

      - name: Classify & Prioritize
        run: |
          python .github/ai-review/scripts/priority_classifier.py \
            --input .ai-review/final-review.json \
            --output .ai-review/classified-review.json

      - name: Generate Review Summary
        run: |
          python .github/ai-review/scripts/generate_summary.py \
            --input .ai-review/classified-review.json \
            --template .github/ai-review/templates/review-summary.md \
            --output .ai-review/review-summary.md

      - name: Post PR Review
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const summary = fs.readFileSync('.ai-review/review-summary.md', 'utf8');
            const reviewData = JSON.parse(
              fs.readFileSync('.ai-review/classified-review.json', 'utf8')
            );

            const criticalCount = reviewData.filter(i => i.severity === 'critical').length;

            await github.rest.pulls.createReview({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
              event: criticalCount > 0 ? 'REQUEST_CHANGES' : 'COMMENT',
              body: summary
            });

      - name: Set Merge Block Status
        uses: actions/github-script@v7
        with:
          script: |
            const reviewData = JSON.parse(
              fs.readFileSync('.ai-review/classified-review.json', 'utf8')
            );
            const criticalCount = reviewData.filter(i => i.severity === 'critical').length;
            const qualityScore = reviewData[0]?.quality_score || 100;

            await github.rest.checks.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              name: 'AI Code Review',
              head_sha: context.sha,
              status: 'completed',
              conclusion: (criticalCount > 0 || qualityScore < 60) ? 'failure' : 'success',
              output: {
                title: `AI Review: ${criticalCount > 0 ? '⛔ Blocked' : '✅ Passed'}`,
                summary: `Quality Score: ${qualityScore}/100 | Issues: Critical=${criticalCount}`
              }
            });

  # ========== 反馈收集 (PR 合并后) ==========
  feedback-collection:
    runs-on: ubuntu-latest
    if: github.event.pull_request.merged == true
    steps:
      - name: Collect Human Feedback
        uses: ./.github/ai-review/actions/feedback-collector
        with:
          review_id: ${{ steps.ai-review.outputs.review_id }}
          comments: ${{ github.event.pull_request.review_comments }}
          outcome: ${{ github.event.pull_request.merged ? 'merged' : 'closed' }}

      - name: Update Learning Database
        run: |
          python .github/ai-review/scripts/feedback_processor.py \
            --review-id ${{ steps.ai-review.outputs.review_id }} \
            --output .ai-review/learning/feedback-${{ github.run_id }}.json

      - name: Update Knowledge Base
        uses: ./.github/ai-review/actions/update-kb
        with:
          feedback_file: .ai-review/learning/feedback-${{ github.run_id }}.json
          api_key: ${{ secrets.AI_REVIEW_API_KEY }}
```

---

## 3. 常见问题模式库

### 3.1 性能反模式

```yaml
# .github/ai-review/patterns/performance.yaml
patterns:
  performance:
    - id: PERF-001
      name: "N+1 查询问题"
      severity: error
      description: "在循环内执行数据库查询，导致 N+1 次 SQL 执行"
      detection:
        keywords: [for, while, forEach, map]
        operators:
          - type: "nesting"
            outer: "loop_statement"
            inner: "database_query"
      examples:
        bad: |
          for (User user : users) {
              List<Order> orders = orderDao.findByUserId(user.getId());  // N+1
              user.setOrders(orders);
          }
        good: |
          List<Long> userIds = users.stream().map(User::getId).toList();
          List<Order> allOrders = orderDao.findByUserIds(userIds);  // 1次查询
          Map<Long, List<Order>> orderMap = allOrders.stream()
              .collect(Collectors.groupingBy(Order::getUserId));
          users.forEach(u -> u.setOrders(orderMap.getOrDefault(u.getId(), List.of())));
      auto_fix: true
      auto_fix_confidence: 0.7

    - id: PERF-002
      name: "字符串循环拼接"
      severity: warning
      description: "在循环中使用 + 或 concat 拼接字符串，应使用 StringBuilder/StringBuffer"
      detection:
        language: [java]
        patterns:
          - 'for.*\{.*\w+\s*\+=\s*'
          - 'for.*\{.*\.concat\('
      examples:
        bad: |
          String result = "";
          for (String s : list) {
              result += s;  // 每次创建新 String 对象
          }
        good: |
          StringBuilder sb = new StringBuilder();
          for (String s : list) {
              sb.append(s);
          }
          String result = sb.toString();
      auto_fix: true

    - id: PERF-003
      name: "不必要的大对象创建"
      severity: warning
      description: "在循环或高频方法中创建大型对象（如 Pattern、SimpleDateFormat）"
      detection:
        patterns:
          - type: "repeated_instantiation_in_loop"
            classes: [Pattern, SimpleDateFormat, Gson, ObjectMapper, Random, SecureRandom]
      examples:
        bad: |
          for (String date : dates) {
              new SimpleDateFormat("yyyy-MM-dd").parse(date);
          }
        good: |
          private static final ThreadLocal<SimpleDateFormat> DATE_FORMAT =
              ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));
      auto_fix: true

    - id: PERF-004
      name: "同步锁粒度过大"
      severity: warning
      description: "synchronized 块包含了非共享资源的操作"
      detection:
        type: "ai_pattern"
        prompt: "检查 synchronized 块内的代码是否全部需要同步保护"
      examples:
        bad: |
          synchronized (lock) {
              expensiveComputation();      // 不需要锁
              sharedState.update(data);    // 只需要这一行
              logResult();                  // 不需要锁
          }
        good: |
          expensiveComputation();
          synchronized (lock) {
              sharedState.update(data);
          }
          logResult();

    - id: PERF-005
      name: "未使用批处理"
      severity: suggestion
      description: "对集合元素逐个执行相同的数据库操作，应使用批处理"
      detection:
        type: "ai_pattern"
        prompt: "检测循环中的 insert/update 操作是否可以使用 batch 替代"
      examples:
        bad: |
          for (Entity e : entities) {
              repository.save(e);  // 逐个保存
          }
        good: |
          repository.saveAll(entities);  // 批量保存

    - id: PERF-006
      name: "Stream API 误用"
      severity: warning
      language: [java]
      description: "在已收集的 Stream 上重复操作，或不当使用 parallelStream"
      detection:
        patterns:
          - '\.stream\(\)\.filter\(.*\)\.collect\(.*\)\.stream\(\)'
          - 'parallelStream\(\)' # 触发人工复核
      examples:
        bad: |
          list.stream().filter(...).collect(toList()).stream().map(...)
        good: |
          list.stream().filter(...).map(...).collect(toList())

    - id: PERF-007
      name: "不合理的缓存策略"
      severity: suggestion
      description: "高频调用且结果稳定的计算未使用缓存"
      detection:
        type: "ai_pattern"
        prompt: "检测是否存在可缓存的计算结果（纯函数 + 高频调用 + 计算耗时）"

    - id: PERF-008
      name: "数据库索引缺失风险"
      severity: error
      description: "WHERE/JOIN 条件中的字段可能缺少索引"
      detection:
        type: "ai_pattern"
        prompt: |
          检查新增的 SQL/JPA 查询：
          1. WHERE 条件字段是否有对应索引
          2. ORDER BY 字段是否需要索引
          3. JOIN 外键是否有索引
```

### 3.2 安全风险模式

```yaml
# .github/ai-review/patterns/security.yaml
patterns:
  security:
    - id: SEC-P001
      name: "输入校验缺失"
      severity: error
      description: "Controller/API 层缺少 @Valid 或参数校验注解"
      detection:
        language: [java]
        patterns:
          - type: "missing_annotation"
            annotation: "@Valid|@Validated"
            context: "method_parameter_with_@RequestBody"
      examples:
        bad: |
          @PostMapping("/users")
          public Result createUser(@RequestBody UserDTO dto) {  // 缺少 @Valid
        good: |
          @PostMapping("/users")
          public Result createUser(@Valid @RequestBody UserDTO dto) {

    - id: SEC-P002
      name: "异常信息泄露"
      severity: error
      description: "将原始异常堆栈返回给客户端，可能泄露内部架构信息"
      detection:
        patterns:
          - 'catch.*\{.*return.*e\.getMessage\(\)'
          - 'catch.*\{.*return.*e\.getStackTrace'
          - '\.printStackTrace\(\)'  # 生产环境不允许
      examples:
        bad: |
          catch (Exception e) {
              return Result.fail(e.getMessage());  // 泄露异常详情
          }
        good: |
          catch (Exception e) {
              log.error("Operation failed", e);
              return Result.fail("操作失败，请稍后重试");  // 安全的通用消息
          }

    - id: SEC-P003
      name: "并发安全问题"
      severity: error
      description: "共享可变状态未进行并发保护"
      detection:
        type: "ai_pattern"
        prompt: |
          检查以下并发安全问题：
          1. 类级别可变字段在 @Controller/@Service/@Component 中的使用
          2. HashMap 在多线程环境中的使用（应为 ConcurrentHashMap）
          3. SimpleDateFormat 在多线程中的使用
          4. ++/-- 操作在非原子变量上

    - id: SEC-P004
      name: "不安全的反序列化"
      severity: critical
      description: "使用了已知不安全的反序列化库或配置"
      detection:
        patterns:
          - 'ObjectInputStream'
          - 'readObject\(\)'
          - '@JsonTypeInfo.*defaultImpl'
      auto_block_merge: true

    - id: SEC-P005
      name: "CSRF 防护缺失"
      severity: error
      description: "状态变更接口缺少 CSRF Token 验证"
      detection:
        language: [java]
        patterns:
          - '@PostMapping.*(?!.*csrf)'
          - '@PutMapping.*(?!.*csrf)'
          - '@DeleteMapping.*(?!.*csrf)'
```

### 3.3 可维护性问题模式

```yaml
# .github/ai-review/patterns/maintainability.yaml
patterns:
  maintainability:
    - id: MAIN-001
      name: "魔法值/硬编码"
      severity: warning
      description: "代码中存在未解释的数字或字符串字面量"
      detection:
        patterns:
          - type: "magic_number"
            exceptions:
              - 0, 1, -1   # 常见允许值
              - 2           # 常见允许值
            context: "not_in_constant_definition"
      examples:
        bad: |
          if (user.getStatus() == 1) {  // 1 是什么意思？
          if (list.size() > 100) {       // 100 的来历？
        good: |
          if (user.getStatus() == UserStatus.ACTIVE) {
          if (list.size() > MAX_BATCH_SIZE) {

    - id: MAIN-002
      name: "异常吞没"
      severity: error
      description: "catch 块为空或仅打印日志后未做处理"
      detection:
        patterns:
          - type: "empty_catch"
          - type: "catch_with_only_log"
            severity: warning
      examples:
        bad: |
          try {
              riskyOperation();
          } catch (Exception e) {
              // 空的，吞掉了
          }
        bad: |
          try {
              riskyOperation();
          } catch (Exception e) {
              log.error("error", e);  // 仅日志，继续执行可能导致脏数据
          }

    - id: MAIN-003
      name: "过度注释 / 注释代码"
      severity: warning
      description: "存在大段被注释掉的代码"
      detection:
        patterns:
          - type: "commented_code_block"
            min_lines: 5
      message: "发现 {lines} 行被注释的代码，请删除或解释保留原因"

    - id: MAIN-004
      name: "测试缺失"
      severity: warning
      description: "新增的 public 方法或 Service 类缺少对应测试"
      detection:
        type: "coverage_check"
        rules:
          - "新增 public 方法 -> 检查是否有新的 test 方法"
          - "新增 Service 类 -> 检查是否有测试类"
          - "关键业务逻辑变更 -> 检查测试用例是否更新"

    - id: MAIN-005
      name: "上帝类 / 上帝方法"
      severity: warning
      description: "类或方法承担了过多职责"
      detection:
        rules:
          - "类中 public 方法 > 15 个 -> 可能职责过多"
          - "方法中调用超过 10 个不同外部方法 -> 可能耦合过高"
          - "类依赖注入 > 8 个 -> 需要拆分"

    - id: MAIN-006
      name: "功能开关缺失"
      severity: suggestion
      description: "大型功能变更缺少 Feature Flag 控制"
      detection:
        type: "ai_pattern"
        prompt: |
          如果变更超过 200 行且为新增功能，检查是否：
          1. 使用了 Feature Toggle/Flag
          2. 是否可以渐进式发布

    - id: MAIN-007
      name: "API 版本兼容性"
      severity: error
      description: "对外 API 的破坏性变更未做版本管理"
      detection:
        type: "api_diff"
        checks:
          - "删除 public 方法/字段 -> error"
          - "修改方法签名 -> error"
          - "修改返回类型 -> error"
          - "新增必填字段 -> warning"
```

---

## 4. 审查意见优先级分类与自动标注

### 4.1 优先级定义

```yaml
# .github/ai-review/configs/priority_rules.yaml
priorities:
  critical:
    label: "🔴 P0-Critical"
    color: "FF0000"
    description: "必须修复，阻挡合并"
    auto_block_merge: true
    sla_response: "1 小时内"
    examples:
      - "安全漏洞（SQL注入、XSS、密钥泄露）"
      - "会导致生产事故的逻辑错误"
      - "数据丢失或损坏风险"
      - "Critical CVE 依赖"

  high:
    label: "🟠 P1-High"
    color: "FF6600"
    description: "强烈建议修复，建议阻挡合并"
    auto_block_merge: false  # 可配置
    sla_response: "4 小时内"
    examples:
      - "性能严重退化（N+1查询、死锁风险）"
      - "异常处理不当可能导致数据不一致"
      - "核心业务流程逻辑缺陷"
      - "API 破坏性变更"

  medium:
    label: "🟡 P2-Medium"
    color: "FFCC00"
    description: "建议修复，不阻挡合并"
    auto_block_merge: false
    sla_response: "下一个工作日"
    examples:
      - "代码复杂度超标"
      - "命名不规范"
      - "缺少必要注释"
      - "测试覆盖不足"

  low:
    label: "🔵 P3-Low"
    color: "3399FF"
    description: "锦上添花，建议采纳"
    auto_block_merge: false
    sla_response: "本迭代内"
    examples:
      - "代码风格优化"
      - "更好的实现方式建议"
      - "文档补充建议"
      - "微优化建议"

  info:
    label: "⚪ P4-Info"
    color: "999999"
    description: "仅供参考，无需行动"
    auto_block_merge: false
    examples:
      - "学习资源推荐"
      - "架构演进方向建议"
      - "统计信息"
```

### 4.2 自动分类规则引擎

```python
# .github/ai-review/scripts/priority_classifier.py

class PriorityClassifier:
    """基于规则 + ML 的优先级自动分类器"""

    # 规则权重配置
    RULE_WEIGHTS = {
        # 安全类：直接提升到 critical
        "security": {"weight": 100, "min_priority": "critical"},
        "sql_injection": {"weight": 100, "min_priority": "critical"},
        "xss": {"weight": 100, "min_priority": "critical"},
        "hardcoded_secret": {"weight": 100, "min_priority": "critical"},

        # 性能类：根据影响程度
        "n_plus_1_query": {"weight": 60, "min_priority": "high"},
        "deadlock_risk": {"weight": 80, "min_priority": "critical"},
        "memory_leak": {"weight": 70, "min_priority": "high"},

        # 可维护性
        "empty_catch": {"weight": 50, "min_priority": "high"},
        "missing_test": {"weight": 20, "min_priority": "medium"},
        "magic_number": {"weight": 10, "min_priority": "low"},
    }

    # 影响范围加权
    SCOPE_WEIGHTS = {
        "core_module": 1.5,      # 核心模块变更
        "api_interface": 1.3,    # API 接口变更
        "data_access": 1.2,      # 数据访问层
        "configuration": 1.4,    # 配置变更
        "utility": 0.8,          # 工具类
        "test": 0.3,             # 测试代码
    }

    # 变更规模加权
    CHANGE_SIZE_WEIGHTS = {
        "xl": 1.3,   # >500 lines
        "l": 1.1,    # 200-500 lines
        "m": 1.0,    # 50-200 lines
        "s": 0.9,    # <50 lines
    }

    def classify(self, issues: list, pr_context: dict) -> list:
        """对审查发现的问题进行优先级分类"""
        classified = []
        for issue in issues:
            base_score = self._calculate_base_score(issue)
            scope_multiplier = self._get_scope_multiplier(issue, pr_context)
            size_multiplier = self._get_size_multiplier(pr_context)
            history_multiplier = self._get_history_multiplier(issue)

            final_score = base_score * scope_multiplier * size_multiplier * history_multiplier
            priority = self._score_to_priority(final_score)

            classified.append({
                **issue,
                "priority": priority["level"],
                "priority_score": final_score,
                "priority_label": priority["label"],
                "auto_label": self._generate_labels(issue, priority),
            })
        return sorted(classified, key=lambda x: x["priority_score"], reverse=True)

    def _calculate_base_score(self, issue: dict) -> float:
        """基于问题类型的基础分"""
        category = issue.get("category", "")
        rule = self.RULE_WEIGHTS.get(category, {"weight": 15})
        confidence = issue.get("confidence", 0.8)
        return rule["weight"] * confidence

    def _get_scope_multiplier(self, issue: dict, context: dict) -> float:
        """基于影响范围的乘数"""
        file_path = issue.get("file", "")
        for scope_key, multiplier in self.SCOPE_WEIGHTS.items():
            if scope_key in file_path.lower():
                return multiplier
        return 1.0
```

### 4.3 自动标注策略

```yaml
auto_labeling:
  # 标签体系
  labels:
    by_severity:
      - "🔴 P0-Critical"
      - "🟠 P1-High"
      - "🟡 P2-Medium"
      - "🔵 P3-Low"
      - "⚪ P4-Info"

    by_category:
      - "security"          # 安全
      - "performance"       # 性能
      - "maintainability"   # 可维护性
      - "bug"              # 缺陷
      - "style"            # 风格
      - "architecture"     # 架构
      - "testing"          # 测试
      - "documentation"    # 文档

    by_action:
      - "must-fix"         # 必须修复
      - "should-fix"       # 应该修复
      - "could-improve"    # 建议改进
      - "for-info"         # 供参考

    by_scope:
      - "breaking-change"  # 破坏性变更
      - "new-feature"      # 新功能
      - "refactor"         # 重构
      - "bugfix"           # 修复

  # 自动标注映射
  auto_assign:
    - pattern: "security"
      assignee: "@security-team"
      labels: ["security", "must-fix"]

    - pattern: "performance|n_plus_1"
      assignee: "@performance-team"
      labels: ["performance"]

    - pattern: "sql|database|jpa|mybatis"
      assignee: "@dba-team"
      labels: ["data-access"]

    - pattern: "api|controller|endpoint"
      assignee: "@api-team"
      labels: ["api"]

  # 自动关联 Issue
  auto_link_issue:
    enabled: true
    for_severity: [critical, high]
    template: |
      标题: [AI Review] {issue_title} in {file}
      标签: {auto_labels}
      负责人: {auto_assignee}
```

---

## 5. Agent 自学习机制

### 5.1 学习回路设计

```
┌────────────────────────────────────────────────────────────┐
│                    自学习闭环                               │
│                                                            │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│   │ AI 审查   │───▶│ 人工反馈  │───▶│ 知识提取  │            │
│   │ (输出)    │    │ (修正)    │    │ (学习)    │            │
│   └──────────┘    └──────────┘    └──────────┘            │
│         ▲                               │                  │
│         │          ┌──────────┐         │                  │
│         └──────────│ 模型更新  │◀────────┘                  │
│                    └──────────┘                            │
└────────────────────────────────────────────────────────────┘
```

### 5.2 反馈收集机制

```yaml
# .github/ai-review/configs/learning.yaml
learning:
  feedback_sources:
    - source: "PR 评论回复"
      trigger: "开发者回复 AI 审查评论"
      extract:
        - "赞同/反对标记 (👍/👎)"
        - "文字回复中的修正信息"
        - "开发者手动修改的优先级"

    - source: "PR 合并结果"
      trigger: "PR 合并/关闭"
      extract:
        - "AI 标记为 critical 但最终合并 → 误报"
        - "AI 未发现但人工审查提出的问题 → 漏报"
        - "AI 建议被采纳的代码修改 → 正样本"

    - source: "手动标记"
      trigger: "开发者使用 /ai-review feedback 命令"
      format: "/ai-review feedback <review_id> <useful|not_useful|false_positive> [comment]"

    - source: "生产事故回溯"
      trigger: "事故复盘关联到已合并的 PR"
      extract:
        - "该 PR 的 AI 审查是否发出了预警"
        - "如果漏报，补充到模式库"

  # 反馈数据结构
  feedback_schema:
    review_id: string
    issue_id: string
    feedback_type: enum[agree, disagree, false_positive, false_negative, modified]
    reviewer: string
    comment: string
    corrected_severity: string  # 人工修正后的优先级
    corrected_suggestion: string
    merged: boolean
    timestamp: datetime
```

### 5.3 知识提取与模型优化

```python
# .github/ai-review/scripts/learning_engine.py

class LearningEngine:
    """从人工反馈中持续学习，优化规则和 prompt"""

    def __init__(self, db_path: str = ".ai-review/learning/feedback.db"):
        self.db = sqlite3.connect(db_path)
        self._init_schema()

    def process_feedback_batch(self, since_days: int = 7) -> dict:
        """处理最近 N 天的反馈数据"""
        feedbacks = self._load_recent_feedback(since_days)

        learnings = {
            "precision_fixes": self._identify_false_positives(feedbacks),
            "recall_fixes": self._identify_false_negatives(feedbacks),
            "threshold_adjustments": self._adjust_thresholds(feedbacks),
            "prompt_improvements": self._generate_prompt_updates(feedbacks),
            "pattern_updates": self._update_patterns(feedbacks),
        }
        return learnings

    def _identify_false_positives(self, feedbacks: list) -> list:
        """识别误报模式并生成修正规则"""
        fp = [f for f in feedbacks if f["feedback_type"] == "false_positive"]
        patterns = {}

        for f in fp:
            key = (f["category"], f["pattern_ref"])
            patterns.setdefault(key, []).append(f)

        fixes = []
        for (cat, ref), items in patterns.items():
            if len(items) >= 3:  # 至少 3 次误报才触发修正
                fixes.append({
                    "action": "adjust_rule",
                    "category": cat,
                    "pattern_ref": ref,
                    "adjustment": "降低置信度权重" if items else "添加排除条件",
                    "sample_count": len(items),
                    "samples": [i["issue_id"] for i in items[:3]]
                })
        return fixes

    def _identify_false_negatives(self, feedbacks: list) -> list:
        """识别漏报模式，补充规则库"""
        fn = [f for f in feedbacks if f["feedback_type"] == "false_negative"]
        fixes = []
        for f in fn:
            fixes.append({
                "action": "add_pattern",
                "description": f["comment"],
                "category": f.get("category", "unknown"),
                "code_snippet": f.get("code_snippet"),
                "severity": f.get("corrected_severity", "warning"),
            })
        return fixes

    def _adjust_thresholds(self, feedbacks: list) -> list:
        """动态调整审查阈值"""
        adjustments = []

        # 计算精确率和召回率
        total = len(feedbacks)
        tp = len([f for f in feedbacks if f["feedback_type"] == "agree"])
        fp = len([f for f in feedbacks if f["feedback_type"] == "false_positive"])

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0

        if precision < 0.7:
            adjustments.append({
                "action": "raise_confidence_threshold",
                "current": 0.6,
                "suggested": 0.75,
                "reason": f"当前精确率 {precision:.1%} 低于 70%"
            })

        return adjustments

    def _generate_prompt_updates(self, feedbacks: list) -> list:
        """基于反馈优化 prompt 模板"""
        updates = []

        # 分析哪些维度的人工反馈最多
        dimension_feedback = {}
        for f in feedbacks:
            dim = f.get("dimension", "unknown")
            dimension_feedback.setdefault(dim, {"agree": 0, "disagree": 0})
            if f["feedback_type"] == "agree":
                dimension_feedback[dim]["agree"] += 1
            elif f["feedback_type"] in ("disagree", "false_positive"):
                dimension_feedback[dim]["disagree"] += 1

        for dim, counts in dimension_feedback.items():
            disagreement_rate = counts["disagree"] / (counts["agree"] + counts["disagree"]) if (counts["agree"] + counts["disagree"]) > 0 else 0
            if disagreement_rate > 0.3:
                updates.append({
                    "action": "refine_prompt",
                    "dimension": dim,
                    "reason": f"分歧率 {disagreement_rate:.1%}",
                    "suggestion": f"在 {dim} 维度的 prompt 中增加更具体的审查标准和示例"
                })

        return updates

    def _update_patterns(self, feedbacks: list) -> list:
        """更新模式库"""
        updates = []

        for f in feedbacks:
            if f["feedback_type"] == "false_negative":
                # 将漏报问题添加到模式库
                updates.append({
                    "action": "add_to_pattern_library",
                    "pattern": {
                        "id": f"USER-{f['issue_id']}",
                        "name": f["comment"][:50],
                        "severity": f.get("corrected_severity", "warning"),
                        "description": f["comment"],
                        "source": "human_feedback",
                    }
                })

            elif f["feedback_type"] == "modified":
                # 更新已有模式的建议内容
                updates.append({
                    "action": "update_pattern_suggestion",
                    "pattern_ref": f["pattern_ref"],
                    "new_suggestion": f["corrected_suggestion"],
                })

        return updates

    def weekly_auto_tune(self):
        """每周自动执行一次调优（通过 GitHub Actions scheduled workflow）"""
        last_week = 7
        learnings = self.process_feedback_batch(since_days=last_week)

        report = self._generate_tuning_report(learnings)
        self._apply_auto_approved_tunings(learnings)
        self._create_tuning_pr(report)

        return report

    def _generate_tuning_report(self, learnings: dict) -> str:
        """生成调优报告"""
        report = f"""# AI Code Review Agent - 周度自学习报告

## 本周统计
- 总审查次数: {learnings.get('total_reviews', 0)}
- 精确率: {learnings.get('precision', 0):.1%}
- 召回率: {learnings.get('recall', 0):.1%}
- F1 Score: {learnings.get('f1', 0):.2f}

## 误报修正 ({len(learnings['precision_fixes'])} 项)
{self._format_fixes(learnings['precision_fixes'])}

## 漏报补充 ({len(learnings['recall_fixes'])} 项)
{self._format_fixes(learnings['recall_fixes'])}

## 阈值调整 ({len(learnings['threshold_adjustments'])} 项)
{self._format_fixes(learnings['threshold_adjustments'])}

## Prompt 优化 ({len(learnings['prompt_improvements'])} 项)
{self._format_fixes(learnings['prompt_improvements'])}

## 模式库更新 ({len(learnings['pattern_updates'])} 项)
{self._format_fixes(learnings['pattern_updates'])}
"""
        return report
```

### 5.4 半自动调优工作流

```yaml
# .github/workflows/ai-review-learning.yml
name: AI Review Weekly Learning

on:
  schedule:
    - cron: '0 9 * * 1'  # 每周一 9:00 UTC
  workflow_dispatch:      # 手动触发

jobs:
  weekly-learning:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Learning Engine
        run: |
          python .github/ai-review/scripts/learning_engine.py \
            --mode weekly \
            --since-days 7 \
            --output .ai-review/learning/weekly-report.md

      - name: Auto-Apply Low-Risk Changes
        run: |
          python .github/ai-review/scripts/apply_tunings.py \
            --mode auto \
            --risk-level low \
            --config-path .github/ai-review/configs/

      - name: Create Tuning PR
        uses: peter-evans/create-pull-request@v6
        with:
          title: "[AI自学习] 第 {week} 周审查规则自动优化"
          body-file: .ai-review/learning/weekly-report.md
          branch: ai-learning/week-{week}
          labels: "ai, auto-tuning"
          reviewers: "@tech-leads"
          base: main
```

---

## 6. CI/CD 集成方案

### 6.1 集成架构

```
┌──────────────────────────────────────────────────────────┐
│                     CI/CD Pipeline                        │
│                                                           │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌─────────┐ │
│  │  Code   │   │  Unit   │   │   AI     │   │  Build  │ │
│  │  Lint   │──▶│  Test   │──▶│  Review  │──▶│  &       │ │
│  └─────────┘   └─────────┘   └──────────┘   │  Deploy │ │
│                                 │            └─────────┘ │
│                                 │                  │      │
│                          ┌──────▼──────┐          │      │
│                          │  Merge Gate │◀─────────┘      │
│                          │  (Quality)  │                  │
│                          └────────────┘                  │
└──────────────────────────────────────────────────────────┘
```

### 6.2 分阶段集成策略

```yaml
# 阶段一：观察模式（第 1-2 周）
phase_1_observe:
  description: "AI 审查作为非阻塞检查运行，收集数据不阻挡合并"
  merge_policy:
    block_on_critical: false
    block_on_error: false
  status_check: "neutral"  # 不影响 PR 状态
  notifications:
    - channel: "#ai-review-feedback"
      event: "每次审查完成"
      content: "审查摘要"
  data_collection:
    - "开发者对 AI 评论的回复率"
    - "AI 建议的采纳率"
    - "误报标记频率"

# 阶段二：软阻塞模式（第 3-4 周）
phase_2_soft_block:
  description: "Critical 问题阻挡合并，但可 override"
  merge_policy:
    block_on_critical: true
    block_on_error: false
    override: "需要 Tech Lead 审批"
  status_check: "failure_on_critical"
  auto_override:
    condition: "所有 critical 已被解决或标记为 false_positive"
    approvers: ["@tech-leads"]

# 阶段三：完全集成（第 5 周起）
phase_3_full:
  description: "正式纳入合并门禁"
  merge_policy:
    block_on_critical: true
    block_on_error: true
    min_quality_score: 60
    override: "需要 2 位 Tech Lead 审批"
  status_check: "required"
  branch_protection:
    required_status_checks: ["AI Code Review"]
    required_approvals: 1
```

### 6.3 多仓库统一配置

```yaml
# .github/ai-review/shared-config.yaml (中央配置仓库)
shared_config:
  repository: org/ai-review-config

  # 各仓库引用方式
  usage: |
    # 在每个仓库的 .github/workflows/ai-code-review.yml 中：
    jobs:
      ai-review:
        uses: org/ai-review-config/.github/workflows/ai-code-review.yml@main
        with:
          language: java
          strictness: standard  # standard | strict | relaxed

  # 仓库级别的规则覆盖
  repo_overrides:
    - repo: "org/legacy-backend"
      rules:
        CPX-003: {max: 120}     # 放宽方法行数限制
        NAM-007: {enabled: false} # 关闭接口前缀检查

    - repo: "org/payment-service"
      strictness: strict
      rules:
        SEC-030: {auto_block_merge: true}  # 支付服务加强安全规则
        PERF-001: {severity: critical}

    - repo: "org/internal-tool"
      strictness: relaxed
      rules:
        CPX-001: {max: 20}
        CPX-004: {max: 8}

  # 规则热更新（无需修改 workflow 文件）
  hot_reload:
    enabled: true
    fetch_interval: 5_minutes
    cache_strategy: "ETag-based"
```

### 6.4 与 Jenkins/GitLab CI 的兼容方案

```yaml
# 非 GitHub Actions 环境的集成
other_ci_integration:
  # 通用 Webhook 模式
  webhook:
    endpoint: "https://ai-review.internal/api/review"
    method: POST
    payload:
      repo_url: string
      pr_number: int
      base_branch: string
      head_sha: string
      diff_url: string
    response:
      review_id: string
      status: success|failure
      issues: array
      summary: string

  # CLI 工具模式（适用于任何 CI）
  cli:
    install: "pip install ai-review-cli"
    usage: |
      # 在任何 CI 环境中运行
      ai-review check \
        --repo $REPO_URL \
        --pr $PR_NUMBER \
        --token $GITHUB_TOKEN \
        --output review-report.json

      # 获取结果并设置构建状态
      ai-review status $REVIEW_ID --format github|gitlab|jenkins
```

### 6.5 大规模团队的性能优化

```yaml
performance_optimization:
  # 增量审查
  incremental_review:
    enabled: true
    strategy: "基于 git diff，仅审查变更部分"
    cache:
      - "ESLint/Checkstyle 缓存"
      - "依赖图缓存（基于 commit hash）"
      - "AI 上下文缓存（相似代码块的审查结果复用）"

  # 智能跳过
  smart_skip:
    conditions:
      - "仅文档变更 -> 跳过"
      - "仅测试文件变更 -> 简化为快速检查"
      - "Draft PR -> 跳过（等 ready_for_review）"
      - "WIP 标记 -> 跳过"

  # 并行化
  parallelization:
    file_grouping:
      strategy: "按模块/包分组，每组独立审查"
      max_groups: 5
    model_pooling:
      primary: "gpt-4o (核心业务代码)"
      secondary: "gpt-4o-mini (工具类/辅助代码)"

  # 排队与优先级
  queue_management:
    strategy: "FIFO + 优先级调度"
    priorities:
      - "hotfix PR -> 队列最前"
      - "release PR -> 次优先"
      - "feature PR -> 正常排队"
    timeout: "单个审查最长 10 分钟"
    fallback: "超时后降级为快速规则扫描"

  # 成本控制
  cost_control:
    monthly_budget: 500  # USD
    per_review_limit: 0.50  # USD
    strategies:
      - "小 PR (<50 行) 使用 mini 模型"
      - "夜间定时批量处理非紧急审查"
      - "相似 PR 共享分析上下文"
```

---

## 7. 审查效果度量指标与仪表盘设计

### 7.1 指标体系

```yaml
metrics:
  # ===== 效率指标 =====
  efficiency:
    - id: review_time_saved
      name: "审查时间节省"
      formula: "预计人工审查时间 - 实际人工审查时间"
      unit: "分钟"
      target: ">60% 节省"
      data_source: "PR 从创建到合并的时间差"

    - id: time_to_first_review
      name: "首次审查响应时间"
      formula: "PR 创建到 AI 审查完成的间隔"
      unit: "分钟"
      target: "<5 分钟"

    - id: auto_review_rate
      name: "自动化审查覆盖率"
      formula: "AI 审查的 PR 数 / 总 PR 数"
      unit: "%"
      target: ">95%"

    - id: merge_block_saved
      name: "预拦截缺陷数"
      formula: "AI 在合并前发现并被修复的 critical/high 问题数"
      unit: "个/周"

  # ===== 质量指标 =====
  quality:
    - id: precision
      name: "精确率"
      formula: "开发者确认有效的问题数 / AI 报告的总问题数"
      unit: "%"
      target: ">80%"
      calculation: |
        precision = agreed_issues / (agreed_issues + false_positives)

    - id: recall
      name: "召回率"
      formula: "AI 发现的问题数 / (AI 发现的 + 人工额外发现的) 问题数"
      unit: "%"
      target: ">85%"

    - id: f1_score
      name: "F1 Score"
      formula: "2 * (precision * recall) / (precision + recall)"
      target: ">0.80"

    - id: false_positive_rate
      name: "误报率"
      formula: "被标记为误报的问题 / AI 报告的总问题"
      unit: "%"
      target: "<10%"

    - id: defect_escape_rate
      name: "缺陷逃逸率"
      formula: "合并后发现的缺陷数 / 总缺陷数"
      unit: "%"
      target: "<5%"

  # ===== 采纳指标 =====
  adoption:
    - id: suggestion_acceptance_rate
      name: "建议采纳率"
      formula: "开发者采纳的 AI 建议数 / AI 总建议数"
      unit: "%"
      target: ">60%"

    - id: developer_satisfaction
      name: "开发者满意度"
      formula: "👍 反应数 / (👍 + 👎 反应数)"
      unit: "%"
      target: ">80%"
      source: "PR 评论 reaction"

    - id: review_override_rate
      name: "审查推翻率"
      formula: "被 override 的 AI 审查数 / 总审查数"
      unit: "%"
      target: "<15%"

  # ===== 业务指标 =====
  business:
    - id: production_incidents_reduced
      name: "生产事故减少率"
      formula: "(引入前月均事故 - 当前月均事故) / 引入前月均事故"
      unit: "%"
      target: ">40%"

    - id: security_vulnerability_prevented
      name: "安全漏洞拦截数"
      formula: "AI 发现的安全漏洞数（被确认并修复）"
      unit: "个/月"

    - id: code_quality_trend
      name: "代码质量趋势"
      formula: "最近 N 周的平均质量评分"
      unit: "分/100"
      target: "持续上升"

    - id: review_bottleneck_reduction
      name: "审查瓶颈缓解"
      formula: "从 PR 创建到首次人工审查的时间减少率"
      unit: "%"
      target: ">50%"
```

### 7.2 周报 / 月报模板

```markdown
# AI Code Review - 周度报告 (2026-W24)

## 📊 核心指标一览

| 指标 | 本周 | 上周 | 变化 | 目标 |
|------|------|------|------|------|
| 审查 PR 数 | 112 | 98 | +14% | - |
| 精确率 | 82.3% | 79.1% | +3.2% | >80% |
| 召回率 | 87.5% | 86.2% | +1.3% | >85% |
| F1 Score | 0.85 | 0.82 | +0.03 | >0.80 |
| 误报率 | 8.2% | 11.5% | -3.3% | <10% |
| 建议采纳率 | 64.8% | 58.2% | +6.6% | >60% |
| 缺陷逃逸率 | 3.1% | 4.2% | -1.1% | <5% |
| 开发者满意度 | 84.5% | 81.0% | +3.5% | >80% |
| 预拦截严重问题 | 23 | 19 | +21% | - |

## 🔍 Top 5 高频问题类型

1. N+1 查询 (PERF-001): 18 次
2. 输入校验缺失 (SEC-P001): 15 次
3. 异常吞没 (MAIN-002): 12 次
4. 魔法值 (MAIN-001): 10 次
5. 测试缺失 (MAIN-004): 9 次

## 📈 代码质量趋势

本周平均质量评分: 73.5/100 (↑2.1)

## 🤖 自学习更新

- 修正误报规则 3 项
- 新增用户自定义模式 2 项
- Prompt 优化 1 项（性能维度）
```

### 7.3 仪表盘设计

```yaml
dashboard:
  # 数据存储
  storage:
    type: "GitHub Pages + JSON 数据文件"
    update_frequency: "每次审查完成后"
    data_file: ".ai-review/dashboard/data.json"

  # 仪表盘页面
  pages:
    - name: "概览"
      widgets:
        - type: "metric_cards"
          metrics: [total_reviews, precision, recall, f1, satisfaction]
        - type: "line_chart"
          title: "代码质量趋势（最近 30 天）"
          data: quality_score_daily
        - type: "bar_chart"
          title: "问题类型分布（本周）"
          data: issue_category_weekly
        - type: "pie_chart"
          title: "优先级分布"
          data: priority_distribution

    - name: "团队详情"
      widgets:
        - type: "leaderboard"
          title: "代码质量排行榜"
          data: quality_by_developer
        - type: "heatmap"
          title: "问题密度热力图"
          data: issues_by_module
        - type: "table"
          title: "高频问题 Top 10"
          data: top_patterns

    - name: "自学习状态"
      widgets:
        - type: "timeline"
          title: "规则变更历史"
          data: rule_change_history
        - type: "metric_cards"
          title: "模型表现"
          metrics: [fp_rate_trend, fn_rate_trend, learning_velocity]

    - name: "ROI 分析"
      widgets:
        - type: "comparison_chart"
          title: "审查效率对比（AI vs 纯人工）"
          data: review_time_comparison
        - type: "number_card"
          title: "累计节省时间"
          data: total_time_saved
        - type: "cost_chart"
          title: "月度 API 费用"
          data: monthly_api_cost

  # 技术实现
  implementation:
    frontend: |
      - 纯静态 HTML + Chart.js + GitHub Pages
      - 数据通过 GitHub Actions 定时生成 JSON
    deployment: |
      - GitHub Pages 自动部署
      - 访问控制：GitHub OAuth + 团队白名单
    data_pipeline: |
      1. 每次审查完成后 → 写入 data.json
      2. 每小时 → GitHub Actions 聚合计算衍生指标
      3. 每天 → 生成趋势数据
      4. 每周一 → 自动发布周报
```

### 7.4 仪表盘前端实现骨架

```html
<!-- .ai-review/dashboard/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>AI Code Review Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {
            --bg: #0d1117;
            --card-bg: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --critical: #f85149;
            --high: #d29922;
            --medium: #58a6ff;
            --low: #3fb950;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 24px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 24px;
        }
        .header h1 { font-size: 24px; }
        .header .period { color: #8b949e; font-size: 14px; }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }
        .metric-card .label { font-size: 12px; color: #8b949e; margin-bottom: 8px; }
        .metric-card .value { font-size: 32px; font-weight: 600; }
        .metric-card .change { font-size: 12px; margin-top: 4px; }
        .metric-card .change.up { color: var(--low); }
        .metric-card .change.down { color: var(--critical); }
        .chart-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 16px;
        }
        .chart-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }
        .chart-card h3 { font-size: 14px; margin-bottom: 16px; color: #8b949e; }
        canvas { width: 100% !important; max-height: 300px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Code Review Dashboard</h1>
        <span class="period">最近 30 天 | 更新于 <span id="last-updated">--</span></span>
    </div>

    <div class="metric-grid" id="metric-cards"></div>

    <div class="chart-grid">
        <div class="chart-card">
            <h3>代码质量趋势</h3>
            <canvas id="quality-trend"></canvas>
        </div>
        <div class="chart-card">
            <h3>问题优先级分布</h3>
            <canvas id="priority-pie"></canvas>
        </div>
    </div>

    <script>
        // 从 data.json 加载数据并渲染
        fetch('data.json')
            .then(res => res.json())
            .then(data => renderDashboard(data));

        function renderDashboard(data) {
            document.getElementById('last-updated').textContent =
                new Date(data.updated_at).toLocaleString('zh-CN');

            // 渲染指标卡片
            const metricsHTML = [
                { label: '审查 PR 数', value: data.total_reviews, change: data.reviews_change },
                { label: '精确率', value: (data.precision * 100).toFixed(1) + '%', change: data.precision_change },
                { label: '召回率', value: (data.recall * 100).toFixed(1) + '%', change: data.recall_change },
                { label: 'F1 Score', value: data.f1.toFixed(2), change: data.f1_change },
                { label: '建议采纳率', value: (data.acceptance_rate * 100).toFixed(1) + '%', change: data.acceptance_change },
                { label: '开发者满意度', value: (data.satisfaction * 100).toFixed(1) + '%', change: data.satisfaction_change },
            ].map(m => `
                <div class="metric-card">
                    <div class="label">${m.label}</div>
                    <div class="value">${m.value}</div>
                    <div class="change ${m.change >= 0 ? 'up' : 'down'}">
                        ${m.change >= 0 ? '↑' : '↓'} ${Math.abs(m.change).toFixed(1)}%
                    </div>
                </div>
            `).join('');
            document.getElementById('metric-cards').innerHTML = metricsHTML;

            // 渲染趋势图
            new Chart(document.getElementById('quality-trend'), {
                type: 'line',
                data: {
                    labels: data.trend_labels,
                    datasets: [{
                        label: '质量评分',
                        data: data.trend_scores,
                        borderColor: '#58a6ff',
                        backgroundColor: 'rgba(88,166,255,0.1)',
                        fill: true,
                        tension: 0.4,
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { min: 0, max: 100, grid: { color: '#21262d' } },
                        x: { grid: { display: false } }
                    }
                }
            });

            // 渲染饼图
            new Chart(document.getElementById('priority-pie'), {
                type: 'doughnut',
                data: {
                    labels: ['P0-Critical', 'P1-High', 'P2-Medium', 'P3-Low', 'P4-Info'],
                    datasets: [{
                        data: data.priority_distribution,
                        backgroundColor: ['#f85149', '#d29922', '#58a6ff', '#3fb950', '#8b949e'],
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#c9d1d9' } }
                    }
                }
            });
        }
    </script>
</body>
</html>
```

### 7.5 数据生成 GitHub Action

```yaml
# .github/workflows/dashboard-data.yml
name: Generate Dashboard Data

on:
  schedule:
    - cron: '0 * * * *'   # 每小时
  workflow_run:
    workflows: ["AI Code Review"]
    types: [completed]
  workflow_dispatch:

jobs:
  generate-data:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - name: Aggregate Review Data
        run: |
          python .github/ai-review/scripts/dashboard_aggregator.py \
            --db .ai-review/learning/feedback.db \
            --output .ai-review/dashboard/data.json \
            --period 30d

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: .ai-review/dashboard
          destination_dir: ai-review
          commit_message: "Update dashboard [skip ci]"
```

---

## 附录

### A. 文件目录结构

```
.ai-review/
├── configs/
│   ├── naming.yaml              # 命名规范
│   ├── formatting.yaml          # 格式规范
│   ├── complexity.yaml          # 复杂度规则
│   ├── security.yaml            # 安全规则
│   ├── priority_rules.yaml      # 优先级分类规则
│   └── learning.yaml            # 学习引擎配置
├── patterns/
│   ├── performance.yaml         # 性能反模式
│   ├── security.yaml            # 安全模式
│   └── maintainability.yaml     # 可维护性
├── scripts/
│   ├── naming_check.py
│   ├── format_check.py
│   ├── complexity_analyzer.py
│   ├── dependency_graph.py
│   ├── priority_classifier.py
│   ├── merge_results.py
│   ├── generate_summary.py
│   ├── learning_engine.py
│   ├── feedback_processor.py
│   ├── load_patterns.py
│   ├── dashboard_aggregator.py
│   └── apply_tunings.py
├── actions/
│   ├── ai-review/action.yml
│   ├── naming-check/action.yml
│   ├── complexity/action.yml
│   ├── dependency-check/action.yml
│   ├── feedback-collector/action.yml
│   └── update-kb/action.yml
├── templates/
│   ├── review-summary.md
│   └── weekly-report.md
├── learning/
│   ├── feedback.db              # SQLite 反馈数据库
│   └── feedback-*.json          # 反馈数据文件
└── dashboard/
    ├── index.html
    └── data.json
```

### B. 渐进式推行计划

```
Week 1-2   │  观察模式  │  非阻塞运行，收集基线数据
Week 3-4   │  软阻塞    │  Critical 自动阻挡，数据反馈调优
Week 5-6   │  完全集成  │  正式纳入门禁，启动自学习
Week 7-8   │  优化迭代  │  基于数据调参，团队全面使用
Week 9+    │  持续优化  │  月度回顾，季度大版本升级
```

### C. 关键成功因素

1. **规则持续迭代**：前 4 周是规则校准黄金期，每周分析 false positive/negative
2. **开发者信任**：误报率是信任基石，前 2 周误报率需控制在 15% 以下
3. **透明可 override**：永远提供合理的 override 路径，不在紧急情况下阻塞
4. **数据驱动决策**：所有调优决策基于实际数据，而非主观判断
5. **轻量级启动**：第 1 天只启用 Layer 1 规则，逐步启用 AI 语义层

---

> **文档版本**: v1.0  
> **更新日期**: 2026-06-15  
> **负责人**: AI Code Review 工作组  
> **仓库**: `org/ai-review-config`
