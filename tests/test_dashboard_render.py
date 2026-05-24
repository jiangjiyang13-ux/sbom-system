from pathlib import Path
import unittest


SOURCE = (Path(__file__).resolve().parents[1] / "frontend" / "dashboard.py").read_text(encoding="utf-8")


class DashboardRenderTests(unittest.TestCase):
    def test_dashboard_includes_new_command_center_shell(self):
        self.assertIn("command-center-shell", SOURCE)
        self.assertIn("status-beacon", SOURCE)
        self.assertIn("resource-ring", SOURCE)

    def test_login_layout_uses_compact_shell(self):
        self.assertIn("login-layout-shell", SOURCE)
        self.assertNotIn("min-height: 86vh", SOURCE)
        self.assertNotIn("login-feature-list", SOURCE)

    def test_dashboard_uses_hud_shell_markers(self):
        self.assertIn("hud-shell-corners", SOURCE)
        self.assertIn("signal-rail", SOURCE)
        self.assertIn("panel-corners", SOURCE)
        self.assertNotIn('.format(hud_corners=', SOURCE)

    def test_dashboard_uses_radar_console_markers(self):
        self.assertIn("radar-sweep", SOURCE)
        self.assertIn("target-lock", SOURCE)
        self.assertIn("pulse-orbit", SOURCE)

    def test_dashboard_uses_enriched_accent_markers(self):
        self.assertIn("accent-cyan", SOURCE)
        self.assertIn("accent-gold", SOURCE)
        self.assertIn("status-chip--amber", SOURCE)
        self.assertIn("warm-signal", SOURCE)

    def test_dashboard_uses_softened_ui_markers(self):
        self.assertIn("soft-shell", SOURCE)
        self.assertIn("soft-corners", SOURCE)
        self.assertIn("soft-lock", SOURCE)
        self.assertIn("soft-shell-muted", SOURCE)

    def test_dashboard_uses_asset_mesh_markers(self):
        self.assertIn("asset-mesh", SOURCE)
        self.assertIn("mesh-node", SOURCE)
        self.assertIn("mesh-link", SOURCE)
        self.assertIn("hero-asset-board", SOURCE)
        self.assertIn("telemetry-band", SOURCE)

    def test_dashboard_uses_metric_trend_markers(self):
        self.assertIn("trend-strip", SOURCE)
        self.assertIn("trend-strip__lane", SOURCE)
        self.assertIn("metric-card__signal", SOURCE)
        self.assertIn("metric-card--warm", SOURCE)

    def test_dashboard_uses_report_sync_markers(self):
        self.assertIn("report-sync-shell", SOURCE)
        self.assertIn("report-shell--active", SOURCE)
        self.assertIn("policy-gate--warm", SOURCE)
        self.assertIn("login-hero--signal", SOURCE)

    def test_dashboard_dedents_command_center_markup(self):
        self.assertIn("textwrap.dedent(", SOURCE)
        self.assertIn('{telemetry_band("warm")}', SOURCE)

    def test_dashboard_replaces_phase_track_with_scan_vectors(self):
        self.assertIn("scan-vector-matrix", SOURCE)
        self.assertIn("scan-vector-card", SOURCE)
        self.assertIn("scan-vector-fill", SOURCE)
        self.assertIn("scan-vector-state", SOURCE)
        self.assertNotIn("PHASE</strong>", SOURCE)

    def test_dashboard_dedents_scan_vector_markup(self):
        section = SOURCE.split("def scan_vector_matrix", 1)[1].split("def trend_strip", 1)[0]
        self.assertIn("textwrap.dedent(", section)
        self.assertIn(".strip()", section)

    def test_dashboard_uses_real_scan_job_markers(self):
        self.assertIn('"/api/scan-jobs"', SOURCE)
        self.assertIn('f"/api/scan-jobs/{job_id}"', SOURCE)
        self.assertIn("def idle_scan_job", SOURCE)
        self.assertIn("def render_scan_job_log", SOURCE)

    def test_dashboard_removes_old_hero_subtitle_sentence(self):
        self.assertNotIn("保留现有深色主基调", SOURCE)

    def test_dashboard_restores_human_readable_copy(self):
        self.assertNotIn("???", SOURCE)
        self.assertIn("SBOM", SOURCE)
        self.assertIn("LOGIN", SOURCE.upper())


if __name__ == "__main__":
    unittest.main()
