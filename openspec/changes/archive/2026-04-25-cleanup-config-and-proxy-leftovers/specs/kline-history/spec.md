## REMOVED Requirements

### Requirement: 涉及东财上游的周期 K 线 fallback 必须配置代理绕过
**Reason**: 该约束不只针对 K 线 fallback，而是所有 akshare 走东财的 provider 共享的横切约束（lhb / suspend / hot_rank / north_flow / pool 等都触及）。归于 `kline-history` 是分类不当。
**Migration**: 等价行为已迁入新建的 `proxy-bypass` capability「东财上游必须在 provider 模块顶部强制绕过本地代理」Requirement，并扩展到所有 akshare 东财 provider；原「模块加载时绕过代理」Scenario 完整保留在新 Requirement 的「模块加载时绕代理生效」Scenario 中。
