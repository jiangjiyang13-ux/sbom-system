from pathlib import Path
import unittest


class DashboardRenderTests(unittest.TestCase):
    def test_dashboard_includes_new_command_center_shell(self):
        source = Path("/home/ubuntu/sbom-system/frontend/dashboard.py").read_text(encoding="utf-8")
        self.assertIn("command-center-shell", source)
        self.assertIn("status-beacon", source)
        self.assertIn("resource-ring", source)

    def test_login_layout_uses_compact_shell(self):
        source = Path("/home/ubuntu/sbom-system/frontend/dashboard.py").read_text(encoding="utf-8")
        self.assertIn("login-layout-shell", source)
        self.assertNotIn("min-height: 86vh", source)
        self.assertNotIn("这一页现在收敛成首屏可见的紧凑入口", source)
        self.assertNotIn("login-feature-list", source)

    def test_dashboard_uses_hud_shell_markers(self):
        source = Path("/home/ubuntu/sbom-system/frontend/dashboard.py").read_text(encoding="utf-8")
        self.assertIn("hud-shell-corners", source)
        self.assertIn("signal-rail", source)
        self.assertIn("panel-corners", source)
        self.assertNotIn('.format(hud_corners=', source)

    def test_dashboard_uses_radar_console_markers(self):
        source = Path("/home/ubuntu/sbom-system/frontend/dashboard.py").read_text(encoding="utf-8")
        self.assertIn("radar-sweep", source)
        self.assertIn("target-lock", source)
        self.assertIn("pulse-orbit", source)

    def test_dashboard_uses_enriched_accent_markers(self):
        source = Path("/home/ubuntu/sbom-system/frontend/dashboard.py").read_text(encoding="utf-8")
        self.assertIn("accent-cyan", source)
        self.assertIn("accent-gold", source)
        self.assertIn("status-chip--amber", source)
        self.assertIn("warm-signal", source)

    def test_dashboard_uses_softened_ui_markers(self):
        source = Path("/home/ubuntu/sbom-system/frontend/dashboard.py").read_text(encoding="utf-8")
        self.assertIn("soft-shell", source)
        self.assertIn("soft-corners", source)
        self.assertIn("soft-lock", source)
        self.assertIn("soft-shell-muted", source)

    def test_dashboard_restores_human_readable_copy(self):
        source = Path("/home/ubuntu/sbom-system/frontend/dashboard.py").read_text(encoding="utf-8")
        self.assertNotIn("???", source)
        self.assertIn("SBOM 核心控制台", source)
        self.assertIn("身份验证", source)
        self.assertIn("用户名", source)
        self.assertIn("密码", source)
        self.assertIn("进入控制台", source)


if __name__ == "__main__":
    unittest.main()
