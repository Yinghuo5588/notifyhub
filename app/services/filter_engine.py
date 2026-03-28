"""过滤规则引擎 —— 支持 FilterRule 和 SubscriptionFilter 两种对象"""
import re
import json


def get_field_value(data: dict, field_path: str) -> str:
    """根据点分路径从字典中取值，如 'Series.Name'"""
    if not field_path:
        return json.dumps(data, ensure_ascii=False)

    keys = field_path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return ""
    return str(current)


def check_single_rule(data: dict, rule) -> bool:
    """
    检查单条规则是否匹配
    rule 可以是 FilterRule 或 SubscriptionFilter（字段名相同）
    """
    value = get_field_value(data, rule.field_path)

    if rule.match_type == "regex":
        try:
            return bool(re.search(rule.pattern, value, re.IGNORECASE))
        except re.error:
            return False
    else:
        return rule.pattern.lower() in value.lower()


def apply_filters(data: dict, rules: list) -> tuple[bool, str]:
    """
    应用所有过滤规则

    逻辑:
    - 白名单: 有白名单规则时必须匹配至少一条
    - 黑名单: 匹配任一条即拦截
    - 先白名单后黑名单

    返回: (是否通过, 原因说明)
    """
    active_rules = [r for r in rules if r.is_active]
    if not active_rules:
        return True, "无过滤规则"

    whitelist_rules = [r for r in active_rules if r.mode == "whitelist"]
    blacklist_rules = [r for r in active_rules if r.mode == "blacklist"]

    # 白名单检查
    if whitelist_rules:
        matched = False
        for rule in whitelist_rules:
            if check_single_rule(data, rule):
                matched = True
                break
        if not matched:
            return False, "未匹配任何白名单规则"

    # 黑名单检查
    for rule in blacklist_rules:
        if check_single_rule(data, rule):
            return False, f"命中黑名单规则: {rule.name or rule.pattern}"

    return True, "通过过滤"