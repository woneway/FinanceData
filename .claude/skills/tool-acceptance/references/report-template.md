# Tool Acceptance Report Template

按下面结构输出正式验收报告。

## 标题

- 接口名
- 验收日期

## 1. 验收目标

说明这次验收要回答什么：

- 接口能否签收
- 如果不能，卡在哪一层

## 2. 验收范围

列出本次覆盖的文件和层次：

- ToolSpec
- service
- provider
- CLI
- HTTP API
- MCP
- Web 前端
- health / consistency
- tests

## 3. 阶段一：全链路定义确认

写清楚：

- 参数
- 返回字段
- provider 链
- 对外暴露入口

输出：

- 方法
- 结果
- 阶段结论

## 4. 阶段二：上游与 Provider 验收

按 provider 分别写：

- 官方文档或真相源
- 原始接口调用结果
- provider 输出结果
- 字段 / 单位 / 时间语义判断
- 结论

阶段结论必须明确：

- 通过 / 部分通过 / 不通过 / 未执行

## 5. 阶段三：Service 验收

写：

- provider 链
- fallback
- consistency
- health

多源接口必须包含跨源一致性验证：

- 字段集对齐结果：是否所有 provider 返回相同字段集
- health probe consistency 结果：是否为"一致"（0 差异）
- 如果有差异：列出每项差异，判定是否需要修复

如果失败，明确根因是在 provider 还是 service。

## 6. 阶段四：CLI 验收

写：

- describe
- 默认调用
- 显式调用
- provider 直连调用

以及：

- 结果
- 结论

## 7. 阶段五：HTTP API 验收

写：

- 默认调用
- 显式调用
- provider 指定调用

以及：

- 结果
- 结论

## 8. 阶段六：MCP 验收

写：

- 默认调用
- 显式调用

以及：

- 结果
- 结论

## 9. 阶段七：Web 前端 Playwright 验收

写：

- 页面访问
- 参数填写
- 提交
- 成功渲染
- 错误渲染（如有）

如果未执行，要明确写原因。

## 10. 测试与回归

写：

- 执行了哪些测试
- 结果
- 剩余测试空白

## 11. 最终结论

### 签收前置条件检查

在给出最终结论前，逐项确认：

1. **语义传播**
   - provider 层是否有语义问题？ → 如果有，service 及所有交付层自动"不通过"
   - service 层是否有语义问题？ → 如果有，所有交付层自动"不通过"
   - **"能调通" ≠ "通过"**：返回 HTTP 200 但数据语义有错 → 不通过

2. **契约一致性**
   - ToolSpec metadata / MCP docstring / CLI describe 与实现一致？

3. **跨源一致性（多源接口）**
   - 字段集对齐：0 缺失？
   - health consistency：0 差异？（修复后重新探测的结果）

### 结论汇总

固定按下面格式：

- `provider`：通过 / 不通过
- `service`：通过 / 不通过
- `CLI`：通过 / 不通过
- `HTTP API`：通过 / 不通过
- `MCP`：通过 / 不通过
- `Web 前端`：通过 / 不通过 / 未执行
- `最终状态`：已签收 / 未签收

如果某层因底层语义传播而不通过，标注原因：
- 例：`HTTP API：不通过（语义传播：provider 层 reg_capital 单位错误）`

最后单独列：

- 当前阻塞项
- 建议的下一步
