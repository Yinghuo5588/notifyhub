"""Jinja2 模板渲染服务 —— 用于渲染通知内容"""
import json
from datetime import datetime, timezone
from jinja2 import Environment, BaseLoader, exceptions


# 独立的Jinja2环境，与Web页面模板分开
_env = Environment(
    loader=BaseLoader(),
    autoescape=False,
    undefined=__import__("jinja2").Undefined,
)


def render_template_string(template_str: str, data: dict) -> str:
    """渲染Jinja2模板字符串"""
    try:
        # 注入额外变量
        context = {**data}
        context.setdefault("_timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))

        # 如果data本身不是嵌套的，提供一个data变量方便引用
        if "data" not in context:
            context["data"] = data

        tmpl = _env.from_string(template_str)
        return tmpl.render(**context)
    except exceptions.TemplateSyntaxError as e:
        return f"[模板语法错误] 行{e.lineno}: {e.message}"
    except Exception as e:
        return f"[渲染错误] {str(e)}"


def extract_variables(data: dict, prefix: str = "") -> list[str]:
    """
    从字典中提取所有变量路径
    例如: {"Series": {"Name": "Test"}} => ["Series.Name"]
    """
    variables = []
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        variables.append(path)
        if isinstance(value, dict):
            variables.extend(extract_variables(value, path))
    return variables