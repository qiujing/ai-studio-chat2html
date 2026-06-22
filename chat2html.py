#!/usr/bin/env python3
"""Google AI Studio 聊天记录 JSON → HTML 转换器。

用法:
    python3 chat2html.py sample.json          # 输出 sample.html
    python3 chat2html.py /path/to/chat.json   # 输出 chat.html
"""

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{
    --bg: #f8f9fa;
    --surface: #ffffff;
    --text: #1a1a2e;
    --text-secondary: #6b7280;
    --user-bg: #e3f2fd;
    --user-border: #90caf9;
    --model-bg: #f5f5f5;
    --model-border: #e0e0e0;
    --think-bg: #fffde7;
    --think-border: #ffe082;
    --think-text: #795548;
    --accent: #2563eb;
    --code-bg: #f1f5f9;
    --code-text: #e11d48;
    --blockquote-border: #2563eb;
    --blockquote-bg: #eff6ff;
    --hr-color: #e5e7eb;
    --radius: 16px;
    --shadow: 0 1px 3px rgba(0,0,0,0.08);
    --font-mono: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  }}

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC',
                 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.7;
    padding: 20px;
  }}

  .container {{
    max-width: 860px;
    margin: 0 auto;
  }}

  /* ---- 页头 ---- */
  .header {{
    background: var(--surface);
    border-radius: var(--radius);
    padding: 24px 28px;
    margin-bottom: 24px;
    box-shadow: var(--shadow);
  }}

  .header h1 {{
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 12px;
    color: var(--accent);
  }}

  .settings-summary {{
    font-size: 0.85rem;
    color: var(--text-secondary);
  }}

  .settings-summary summary {{
    cursor: pointer;
    font-weight: 600;
    user-select: none;
  }}

  .settings-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 8px 20px;
    margin-top: 10px;
  }}

  .setting-item {{
    display: flex;
    justify-content: space-between;
    gap: 12px;
  }}

  .setting-key {{
    color: var(--text-secondary);
  }}

  .setting-value {{
    font-weight: 600;
    font-family: var(--font-mono);
    font-size: 0.82rem;
  }}

  .system-instruction {{
    margin-top: 14px;
    padding: 12px 16px;
    background: #fefce8;
    border-left: 3px solid #facc15;
    border-radius: 0 8px 8px 0;
    font-size: 0.88rem;
    color: #713f12;
  }}

  /* ---- 聊天区 ---- */
  .chat-log {{
    display: flex;
    flex-direction: column;
    gap: 20px;
  }}

  .message {{
    display: flex;
    flex-direction: column;
    max-width: 90%;
    animation: fadeIn 0.25s ease;
  }}

  @keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}

  .message.user {{
    align-self: flex-end;
  }}

  .message.model {{
    align-self: flex-start;
  }}

  .role-label {{
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
    padding: 0 4px;
  }}

  .message.user .role-label {{
    color: #1565c0;
    text-align: right;
  }}

  .message.model .role-label {{
    color: #616161;
  }}

  .bubble {{
    border-radius: var(--radius);
    padding: 16px 20px;
    box-shadow: var(--shadow);
    word-wrap: break-word;
    overflow-wrap: break-word;
  }}

  .message.user .bubble {{
    background: var(--user-bg);
    border: 1px solid var(--user-border);
    border-bottom-right-radius: 4px;
  }}

  .message.model .bubble {{
    background: var(--model-bg);
    border: 1px solid var(--model-border);
    border-bottom-left-radius: 4px;
  }}

  /* ---- 思考块 ---- */
  .think-block {{
    background: var(--think-bg);
    border: 1px dashed var(--think-border);
    border-radius: var(--radius);
    padding: 14px 18px;
    margin-bottom: 12px;
  }}

  .think-block summary {{
    cursor: pointer;
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--think-text);
    user-select: none;
    list-style: none;
  }}

  .think-block summary::-webkit-details-marker {{ display: none; }}

  .think-block .think-content {{
    margin-top: 10px;
    font-style: italic;
    font-size: 0.88rem;
    color: var(--think-text);
    white-space: pre-wrap;
    line-height: 1.6;
  }}

  /* ---- Markdown 内容 ---- */
  .md-content h1, .md-content h2, .md-content h3 {{
    margin: 16px 0 8px;
    font-weight: 700;
    line-height: 1.3;
  }}

  .md-content h1 {{ font-size: 1.35rem; }}
  .md-content h2 {{ font-size: 1.15rem; }}
  .md-content h3 {{ font-size: 1.05rem; }}

  .md-content h1:first-child,
  .md-content h2:first-child,
  .md-content h3:first-child {{
    margin-top: 0;
  }}

  .md-content p {{
    margin: 6px 0;
  }}

  .md-content ul, .md-content ol {{
    padding-left: 24px;
    margin: 6px 0;
  }}

  .md-content li {{
    margin: 2px 0;
  }}

  .md-content strong {{
    font-weight: 700;
  }}

  .md-content blockquote {{
    border-left: 3px solid var(--blockquote-border);
    background: var(--blockquote-bg);
    margin: 10px 0;
    padding: 8px 14px;
    border-radius: 0 6px 6px 0;
    color: #374151;
  }}

  .md-content code {{
    background: var(--code-bg);
    color: var(--code-text);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: var(--font-mono);
    font-size: 0.88em;
  }}

  .md-content pre {{
    background: #1e293b;
    color: #e2e8f0;
    padding: 14px 18px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 10px 0;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    line-height: 1.5;
  }}

  .md-content pre code {{
    background: none;
    color: inherit;
    padding: 0;
  }}

  .md-content hr {{
    border: none;
    border-top: 1px solid var(--hr-color);
    margin: 16px 0;
  }}

  /* ---- 消息元数据 ---- */
  .message-meta {{
    display: flex;
    gap: 12px;
    font-size: 0.72rem;
    color: var(--text-secondary);
    margin-top: 4px;
    padding: 0 4px;
  }}

  .message.user .message-meta {{
    justify-content: flex-end;
  }}

  /* ---- 底部 ---- */
  .footer {{
    text-align: center;
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-top: 32px;
    padding: 16px;
  }}

  /* ---- 响应式 ---- */
  @media (max-width: 640px) {{
    body {{ padding: 10px; }}
    .message {{ max-width: 95%; }}
    .bubble {{ padding: 12px 14px; }}
    .header {{ padding: 16px 18px; }}
    .settings-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<div class="container">
{header}
<div class="chat-log">
{chat_messages}
</div>
<div class="footer">
  由 <strong>chat2html</strong> 生成 · 共 {message_count} 条消息 · {total_tokens} tokens
</div>
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Markdown → HTML（轻量转换，无第三方依赖）
# ---------------------------------------------------------------------------

def _escape(text: str) -> str:
    """转义 HTML 特殊字符。"""
    return html.escape(text, quote=False)


def _format_inline(text: str) -> str:
    """处理行内 Markdown：**粗体**、`代码`、*斜体*。"""
    # 粗体 **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # 斜体 *text*（避免匹配 ** 残留）
    text = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"<em>\1</em>", text)
    # 行内代码 `code`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def markdown_to_html(raw: str) -> str:
    """将 Markdown 文本转换为 HTML。

    支持：
    - 标题（# ~ ###）
    - 粗体 / 斜体 / 行内代码
    - 无序列表（- / *）
    - 引用（>）
    - 水平线（---）
    - 段落
    """
    lines = raw.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # 空行 → 段落分隔
        if line.strip() == "":
            # 关闭可能打开的列表
            if out and out[-1] == "</ul>":
                pass  # 列表已关闭
            i += 1
            continue

        # 代码块 ```...```
        if line.strip().startswith("```"):
            code_lines: list[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(_escape(lines[i]))
                i += 1
            i += 1  # skip closing ```
            code_body = "\n".join(code_lines)
            out.append(f"<pre><code>{code_body}</code></pre>")
            continue

        # 水平线 --- / ***
        if re.match(r"^[-*]{3,}\s*$", line.strip()):
            out.append("<hr>")
            i += 1
            continue

        # 标题（支持 h1 ~ h6）
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            content = _format_inline(_escape(heading_match.group(2)))
            out.append(f"<h{level}>{content}</h{level}>")
            i += 1
            continue

        # 引用 >
        if line.startswith(">"):
            quote_lines: list[str] = []
            while i < n and lines[i].startswith(">"):
                quote_text = lines[i][1:].strip()
                quote_lines.append(_format_inline(_escape(quote_text)))
                i += 1
            body = "<br>".join(quote_lines)
            out.append(f"<blockquote>{body}</blockquote>")
            continue

        # 无序列表
        list_match = re.match(r"^(\s*)[-*]\s+(.+)$", line)
        if list_match:
            list_items: list[str] = []
            while i < n and re.match(r"^(\s*)[-*]\s+(.+)$", lines[i]):
                item_match = re.match(r"^(\s*)[-*]\s+(.+)$", lines[i])
                if item_match:
                    list_items.append(_format_inline(_escape(item_match.group(2))))
                i += 1
            items_html = "".join(f"<li>{item}</li>" for item in list_items)
            out.append(f"<ul>{items_html}</ul>")
            continue

        # 普通段落：收集连续非空、非特殊行
        para_lines: list[str] = []
        while i < n and lines[i].strip() != "":
            current = lines[i]
            # 如果遇到特殊行开头，中断段落收集
            if (current.startswith("#") or current.startswith(">")
                    or current.startswith("```")
                    or re.match(r"^[-*]{3,}\s*$", current.strip())
                    or re.match(r"^\s*[-*]\s+", current)):
                break
            para_lines.append(_format_inline(_escape(current)))
            i += 1
        if para_lines:
            body = "<br>".join(para_lines)
            out.append(f"<p>{body}</p>")
        else:
            # 安全网：遇到无法处理的行（不应发生），跳过
            i += 1

    return "\n".join(out)


# ---------------------------------------------------------------------------
# 数据提取
# ---------------------------------------------------------------------------

def format_timestamp(ts: str) -> str:
    """将 ISO 8601 时间戳格式化为可读的本地时间。"""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        local_dt = dt.astimezone()
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return ts


def get_chunk_text(chunk: dict[str, Any]) -> str:
    """获取 chunk 的完整文本。

    优先使用 `text` 字段；如果为空，则从 `parts` 数组中拼接
    （跳过仅含 `thoughtSignature` 的空白 part）。
    """
    text = (chunk.get("text") or "").strip()
    if text:
        return text

    # 回退：从 parts 拼接
    parts = chunk.get("parts") or []
    combined: list[str] = []
    for part in parts:
        part_text = (part.get("text") or "").strip()
        if part_text:
            combined.append(part_text)
    return "\n\n".join(combined)


def is_think_chunk(chunk: dict[str, Any]) -> bool:
    """判断是否为模型的思考（thinking）块。"""
    if chunk.get("isThought"):
        return True
    parts = chunk.get("parts") or []
    non_empty_parts = [p for p in parts if p.get("text", "").strip()]
    if not non_empty_parts:
        return False  # 用户消息没有 parts 或 parts 全为空
    return all(p.get("thought", False) for p in non_empty_parts)


def build_settings_html(run_settings: dict[str, Any]) -> str:
    """构建运行设置的 HTML 摘要。"""
    # 提取关键设置
    keys = [
        ("模型", run_settings.get("model", "-")),
        ("Temperature", str(run_settings.get("temperature", "-"))),
        ("Top-P", str(run_settings.get("topP", "-"))),
        ("Top-K", str(run_settings.get("topK", "-"))),
        ("最大输出 Tokens", str(run_settings.get("maxOutputTokens", "-"))),
        ("代码执行", "是" if run_settings.get("enableCodeExecution") else "否"),
        ("搜索工具", "是" if run_settings.get("enableSearchAsATool") else "否"),
        ("思考等级", str(run_settings.get("thinkingLevel", "-"))),
    ]
    items = "\n".join(
        f'<div class="setting-item"><span class="setting-key">{k}</span>'
        f'<span class="setting-value">{_escape(v)}</span></div>'
        for k, v in keys
    )
    return f"""<details class="settings-summary">
  <summary>⚙️ 运行设置</summary>
  <div class="settings-grid">{items}</div>
</details>"""


# ---------------------------------------------------------------------------
# 主逻辑
# ---------------------------------------------------------------------------

def convert_json_to_html(data: dict[str, Any]) -> str:
    """将 Google AI Studio JSON 数据转换为完整 HTML 页面。"""
    run_settings = data.get("runSettings") or {}
    system_instruction = data.get("systemInstruction") or {}
    chunked = data.get("chunkedPrompt") or {}
    chunks: list[dict[str, Any]] = chunked.get("chunks") or []

    # --- 页头 ---
    header_parts: list[str] = []
    header_parts.append("<h1>🤖 Google AI Studio 对话记录</h1>")
    header_parts.append(build_settings_html(run_settings))

    # 系统指令
    si_text = (system_instruction.get("text") or "").strip()
    if si_text:
        header_parts.append(
            f'<div class="system-instruction"><strong>📋 系统指令：</strong>{_escape(si_text)}</div>'
        )

    header_html = "\n".join(header_parts)

    # --- 聊天消息 ---
    message_parts: list[str] = []
    total_tokens = 0

    for chunk in chunks:
        role = chunk.get("role", "unknown")
        token_count = chunk.get("tokenCount", 0)
        total_tokens += token_count
        create_time = format_timestamp(chunk.get("createTime", ""))

        if role == "user":
            # 用户消息
            raw_text = get_chunk_text(chunk)
            body = markdown_to_html(raw_text)
            message_parts.append(f"""<div class="message user">
  <div class="role-label">👤 用户</div>
  <div class="bubble"><div class="md-content">{body}</div></div>
  <div class="message-meta"><span>{create_time}</span><span>{token_count} tokens</span></div>
</div>""")

        elif role == "model" and is_think_chunk(chunk):
            # 模型思考
            raw_text = get_chunk_text(chunk)
            escaped = _escape(raw_text)
            message_parts.append(f"""<div class="message model">
  <div class="role-label">🧠 模型</div>
  <div class="think-block">
    <details>
      <summary>💭 思考过程 · {token_count} tokens</summary>
      <div class="think-content">{escaped}</div>
    </details>
  </div>
  <div class="message-meta"><span>{create_time}</span><span>{token_count} tokens</span></div>
</div>""")

        elif role == "model":
            # 模型回答
            raw_text = get_chunk_text(chunk)
            body = markdown_to_html(raw_text)
            finish_reason = chunk.get("finishReason", "")
            reason_badge = f' · <span style="font-weight:600">{_escape(finish_reason)}</span>' if finish_reason else ""
            message_parts.append(f"""<div class="message model">
  <div class="role-label">🤖 模型</div>
  <div class="bubble"><div class="md-content">{body}</div></div>
  <div class="message-meta"><span>{create_time}</span><span>{token_count} tokens{reason_badge}</span></div>
</div>""")

    chat_html = "\n".join(message_parts)

    # --- 组装 ---
    title = _escape(
        run_settings.get("model", "Google AI Studio 对话")
    )
    return HTML_TEMPLATE.format(
        title=title,
        header=header_html,
        chat_messages=chat_html,
        message_count=len(chunks),
        total_tokens=f"{total_tokens:,}",
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="将 Google AI Studio 聊天记录 JSON 转换为 HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n  python3 chat2html.py sample.json          # → sample.html\n"
               "  python3 chat2html.py chat.json -o out.html # → out.html",
    )
    parser.add_argument(
        "json_file",
        type=str,
        help="聊天记录 JSON 文件路径",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="输出 HTML 文件路径（默认：与输入同名的 .html 文件）",
    )
    args = parser.parse_args()

    # --- 读取 JSON ---
    input_path = Path(args.json_file)
    if not input_path.is_file():
        print(f"错误：文件不存在 —— {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误：JSON 解析失败 —— {e}", file=sys.stderr)
        sys.exit(1)

    # --- 确定输出路径 ---
    output_path = Path(args.output) if args.output else input_path.with_suffix(".html")

    # --- 转换 ---
    try:
        html_output = convert_json_to_html(data)
    except Exception as e:
        print(f"错误：转换失败 —— {e}", file=sys.stderr)
        sys.exit(1)

    # --- 写入 ---
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"✅ 转换完成：{input_path} → {output_path}")
    print(f"   {len(data.get('chunkedPrompt', {}).get('chunks', []))} 条消息")


if __name__ == "__main__":
    main()
