def get_fix_suggestion(vulnerability: dict) -> str:
    """Simulate AI fix advice based on CVE information."""
    comp = vulnerability.get("component")
    curr_v = vulnerability.get("version")
    fix_v = vulnerability.get("fix_versions", [])
    cve = vulnerability.get("cve_id")
    sev = vulnerability.get("severity", "UNKNOWN")
    
    if fix_v:
        target_v = fix_v[0]
        advice = f"### 🛡️ AI 修复建议 (针对 {cve})\n\n"
        advice += f"**风险评估**: {sev} 级别漏洞。检测到组件 `{comp}` 版本 `{curr_v}` 存在已知风险。\n\n"
        advice += f"**操作指令**:\n"
        advice += f"```bash\npip install --upgrade {comp}>={target_v}\n```\n"
        advice += f"**建议原因**: 官方已在 `{target_v}` 版本中修复此问题。建议立即升级以消除依赖链风险。"
    else:
        advice = f"### ⚠️ AI 风险警告 (针对 {cve})\n\n"
        advice += f"**风险评估**: 目前 `{comp}` 尚未发布针对此漏洞的正式修复版本。\n\n"
        advice += f"**操作指令**: 建议检查业务是否使用了受影响的代码逻辑，或考虑替换为同类安全组件（如 `httpx` 替代 `requests` 如果是协议层漏洞）。"
    
    return advice
