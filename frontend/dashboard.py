import base64
import html
import tempfile
import time
import textwrap
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

BACKEND = "http://localhost:8888"
ASSET_DIR = Path(__file__).resolve().parent / "assets"

st.set_page_config(
    page_title="SBOM 核心控制台",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CRED_USER = "moBS"
_CRED_PASS = "dfahjeaiwf23878@#"


def asset_data_uri(filename: str) -> str:
    path = ASSET_DIR / filename
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def inject_styles() -> None:
    grid_uri = asset_data_uri("control-grid.svg")
    radar_uri = asset_data_uri("status-radar.svg")
    style = '\n    <style>\n        :root {\n            --bg-base: #0b111a;\n            --bg-panel: rgba(14, 23, 35, 0.82);\n            --bg-panel-strong: rgba(18, 28, 43, 0.96);\n            --line-soft: rgba(56, 94, 132, 0.34);\n            --line-strong: rgba(88, 166, 255, 0.48);\n            --accent-blue: #58a6ff;\n            --accent-cyan: #53d7ff;\n            --accent-red: #f85149;\n            --accent-green: #7ee787;\n            --accent-amber: #d29922;\n            --accent-gold: #f2bc62;\n            --text-main: #d6e3f3;\n            --text-dim: #8fa5bf;\n            --shadow-soft: 0 22px 44px rgba(0, 0, 0, 0.32);\n            --shadow-glow: 0 0 0 1px rgba(88, 166, 255, 0.08), 0 18px 40px rgba(2, 12, 24, 0.45);\n            --shell-radius: 28px;\n            --panel-radius: 22px;\n        }\n\n        @keyframes shellDrift {\n            0% { transform: translate3d(0, 0, 0) scale(1); opacity: 0.8; }\n            50% { transform: translate3d(12px, -10px, 0) scale(1.02); opacity: 1; }\n            100% { transform: translate3d(0, 0, 0) scale(1); opacity: 0.8; }\n        }\n\n        @keyframes sweepGlow {\n            0% { transform: translateX(-120%); opacity: 0; }\n            20% { opacity: 0.2; }\n            60% { opacity: 0.42; }\n            100% { transform: translateX(160%); opacity: 0; }\n        }\n\n        @keyframes beaconPulse {\n            0% { box-shadow: 0 0 0 0 rgba(126, 231, 135, 0.45); opacity: 0.92; }\n            70% { box-shadow: 0 0 0 10px rgba(126, 231, 135, 0); opacity: 1; }\n            100% { box-shadow: 0 0 0 0 rgba(126, 231, 135, 0); opacity: 0.92; }\n        }\n\n        @keyframes buttonBreath {\n            0% { box-shadow: 0 0 0 0 rgba(248, 81, 73, 0.22); }\n            50% { box-shadow: 0 0 0 8px rgba(248, 81, 73, 0.02); }\n            100% { box-shadow: 0 0 0 0 rgba(248, 81, 73, 0.22); }\n        }\n\n        @keyframes haloFloat {\n            0% { transform: rotate(0deg) scale(1); }\n            50% { transform: rotate(8deg) scale(1.02); }\n            100% { transform: rotate(0deg) scale(1); }\n        }\n\n        @keyframes radarSweep {\n            0% { transform: rotate(-8deg); opacity: 0.15; }\n            50% { transform: rotate(14deg); opacity: 0.42; }\n            100% { transform: rotate(34deg); opacity: 0.1; }\n        }\n\n        @keyframes orbitPulse {\n            0% { transform: scale(0.82); opacity: 0.12; }\n            55% { transform: scale(1.04); opacity: 0.28; }\n            100% { transform: scale(1.18); opacity: 0; }\n        }\n\n        html, body, [class*="css"] {\n            font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;\n        }\n\n        .stApp {\n            color: var(--text-main);\n            background:\n                radial-gradient(circle at 28% 14%, rgba(83, 215, 255, 0.08), transparent 18%),\n                radial-gradient(circle at 12% 20%, rgba(88, 166, 255, 0.12), transparent 28%),\n                radial-gradient(circle at 74% 20%, rgba(242, 188, 98, 0.08), transparent 18%),\n                radial-gradient(circle at 82% 12%, rgba(248, 81, 73, 0.12), transparent 22%),\n                linear-gradient(135deg, rgba(9, 17, 27, 0.96), rgba(8, 13, 20, 0.98)),\n                url("__GRID__");\n            background-size: auto, auto, auto, auto, auto, 420px 420px;\n            background-attachment: fixed;\n        }\n\n        .stApp::before,\n        .stApp::after {\n            content: "";\n            position: fixed;\n            inset: auto;\n            width: 28rem;\n            height: 28rem;\n            border-radius: 999px;\n            filter: blur(50px);\n            z-index: 0;\n            pointer-events: none;\n            animation: shellDrift 12s ease-in-out infinite;\n        }\n\n        .stApp::before {\n            top: 7rem;\n            right: -10rem;\n            background: radial-gradient(circle, rgba(88, 166, 255, 0.2), transparent 68%);\n        }\n\n        .stApp::after {\n            bottom: -12rem;\n            left: -8rem;\n            background: radial-gradient(circle, rgba(248, 81, 73, 0.16), transparent 70%);\n            animation-delay: -6s;\n        }\n\n        .main .block-container {\n            position: relative;\n            z-index: 1;\n            max-width: 1480px;\n            padding-top: 1.8rem;\n            padding-bottom: 2.5rem;\n        }\n\n        [data-testid="stSidebar"] {\n            background:\n                linear-gradient(180deg, rgba(8, 15, 24, 0.98), rgba(10, 18, 29, 0.94)),\n                url("__GRID__");\n            border-right: 1px solid var(--line-soft);\n        }\n\n        [data-testid="stSidebar"] > div:first-child {\n            background: transparent;\n        }\n\n        [data-testid="stSidebar"] .block-container {\n            padding-top: 1.6rem;\n        }\n\n        [data-testid="stSidebar"] .stMarkdown p,\n        [data-testid="stSidebar"] label,\n        [data-testid="stSidebar"] .stTextInput label,\n        [data-testid="stSidebar"] .stSelectbox label {\n            color: var(--text-dim) !important;\n        }\n\n        [data-testid="stTextInputRootElement"] > div,\n        .stSelectbox > div > div,\n        .stTextInput > div > div {\n            background: rgba(6, 14, 23, 0.88) !important;\n            border: 1px solid rgba(88, 166, 255, 0.18) !important;\n            border-radius: 16px !important;\n            box-shadow: inset 0 0 0 1px rgba(88, 166, 255, 0.04);\n        }\n\n        [data-testid="stTextInputRootElement"] input,\n        .stSelectbox input {\n            color: var(--text-main) !important;\n        }\n\n        [data-testid="stSidebar"] [data-testid="stButton"] button {\n            min-height: 3.2rem;\n            border-radius: 16px;\n            border: 1px solid rgba(248, 81, 73, 0.42);\n            background: linear-gradient(135deg, rgba(248, 81, 73, 0.96), rgba(181, 46, 49, 0.96));\n            color: #fff;\n            font-weight: 700;\n            letter-spacing: 0.02em;\n            box-shadow: 0 16px 30px rgba(120, 13, 16, 0.3);\n            animation: buttonBreath 3.2s ease-in-out infinite;\n            transition: transform 0.18s ease, box-shadow 0.18s ease;\n        }\n\n        [data-testid="stSidebar"] [data-testid="stButton"] button:hover {\n            transform: translateY(-1px);\n            box-shadow: 0 18px 36px rgba(120, 13, 16, 0.42);\n        }\n\n        .command-center-shell,\n        .report-shell,\n        .section-shell,\n        .login-hero {\n            position: relative;\n            overflow: hidden;\n            border-radius: var(--shell-radius);\n            background:\n                linear-gradient(180deg, rgba(14, 23, 35, 0.96), rgba(10, 17, 26, 0.9)),\n                radial-gradient(circle at top right, rgba(88, 166, 255, 0.08), transparent 28%);\n            border: 1px solid rgba(76, 122, 170, 0.22);\n            box-shadow: var(--shadow-soft);\n        }\n\n        .soft-shell {\n            backdrop-filter: blur(14px);\n            box-shadow:\n                0 26px 52px rgba(0, 0, 0, 0.28),\n                inset 0 1px 0 rgba(255, 255, 255, 0.02);\n        }\n\n        .soft-shell-muted {\n            border-color: rgba(76, 122, 170, 0.14);\n            box-shadow:\n                0 22px 46px rgba(0, 0, 0, 0.24),\n                inset 0 1px 0 rgba(255, 255, 255, 0.015);\n        }\n\n        .command-center-shell::after,\n        .report-shell::after,\n        .section-shell::after {\n            content: "";\n            position: absolute;\n            inset: 12px;\n            border-radius: 22px;\n            border: 1px solid rgba(88, 166, 255, 0.06);\n            pointer-events: none;\n        }\n\n        .soft-shell::after {\n            box-shadow: inset 0 0 26px rgba(83, 215, 255, 0.03);\n        }\n\n        .soft-shell-muted::after {\n            inset: 16px;\n            border-radius: 24px;\n            border-color: rgba(88, 166, 255, 0.035);\n            box-shadow: inset 0 0 22px rgba(83, 215, 255, 0.018);\n        }\n\n        .command-center-shell::before,\n        .report-shell::before,\n        .section-shell::before,\n        .login-hero::before,\n        .metric-card::before {\n            content: "";\n            position: absolute;\n            top: 0;\n            left: -30%;\n            width: 30%;\n            height: 100%;\n            background: linear-gradient(90deg, transparent, rgba(88, 166, 255, 0.24), transparent);\n            transform: skewX(-24deg);\n            animation: sweepGlow 9s linear infinite;\n            pointer-events: none;\n        }\n\n        .soft-shell::before {\n            opacity: 0.7;\n            filter: blur(0.6px);\n        }\n\n        .soft-shell-muted::before {\n            opacity: 0.42;\n            filter: blur(1px);\n        }\n\n        .command-center-shell {\n            padding: 1.7rem 1.8rem;\n            margin-bottom: 1rem;\n        }\n\n        .command-center-shell--main {\n            padding-bottom: 1.25rem;\n        }\n\n        .hud-shell-corners,\n        .panel-corners {\n            pointer-events: none;\n            position: absolute;\n            inset: 0;\n            z-index: 1;\n        }\n\n        .hud-shell-corners span,\n        .panel-corners span {\n            position: absolute;\n            width: 28px;\n            height: 28px;\n            opacity: 0.75;\n        }\n\n        .soft-corners span {\n            width: 24px;\n            height: 24px;\n            opacity: 0.52;\n            filter: blur(0.2px);\n        }\n\n        .soft-shell-muted .soft-corners span {\n            opacity: 0.3;\n            filter: blur(0.45px);\n        }\n\n        .hud-shell-corners span::before,\n        .hud-shell-corners span::after,\n        .panel-corners span::before,\n        .panel-corners span::after {\n            content: "";\n            position: absolute;\n            background: linear-gradient(90deg, rgba(88, 166, 255, 0.82), rgba(88, 166, 255, 0));\n            box-shadow: 0 0 10px rgba(88, 166, 255, 0.2);\n        }\n\n        .soft-corners span::before,\n        .soft-corners span::after {\n            box-shadow: 0 0 16px rgba(83, 215, 255, 0.12);\n        }\n\n        .hud-shell-corners .corner-tl,\n        .panel-corners .corner-tl { top: 10px; left: 10px; }\n        .hud-shell-corners .corner-tr,\n        .panel-corners .corner-tr { top: 10px; right: 10px; transform: scaleX(-1); }\n        .hud-shell-corners .corner-bl,\n        .panel-corners .corner-bl { bottom: 10px; left: 10px; transform: scaleY(-1); }\n        .hud-shell-corners .corner-br,\n        .panel-corners .corner-br { bottom: 10px; right: 10px; transform: scale(-1); }\n\n        .soft-shell-muted .corner-tl { top: 16px; left: 16px; }\n        .soft-shell-muted .corner-tr { top: 16px; right: 16px; }\n        .soft-shell-muted .corner-bl { bottom: 16px; left: 16px; }\n        .soft-shell-muted .corner-br { bottom: 16px; right: 16px; }\n\n        .hud-shell-corners span::before,\n        .panel-corners span::before {\n            width: 22px;\n            height: 2px;\n            top: 0;\n            left: 0;\n        }\n\n        .soft-corners span::before {\n            width: 16px;\n            height: 1px;\n            border-radius: 999px;\n            background: linear-gradient(90deg, rgba(83, 215, 255, 0.58), rgba(83, 215, 255, 0));\n        }\n\n        .hud-shell-corners span::after,\n        .panel-corners span::after {\n            width: 2px;\n            height: 22px;\n            top: 0;\n            left: 0;\n            background: linear-gradient(180deg, rgba(88, 166, 255, 0.82), rgba(88, 166, 255, 0));\n        }\n\n        .soft-corners span::after {\n            width: 1px;\n            height: 16px;\n            border-radius: 999px;\n            background: linear-gradient(180deg, rgba(83, 215, 255, 0.58), rgba(83, 215, 255, 0));\n        }\n\n        .signal-rail {\n            display: grid;\n            grid-template-columns: repeat(4, minmax(0, 1fr));\n            gap: 0.45rem;\n            margin-top: 0.9rem;\n        }\n\n        .signal-rail span {\n            display: block;\n            height: 5px;\n            border-radius: 999px;\n            background: linear-gradient(90deg, rgba(88, 166, 255, 0.06), rgba(88, 166, 255, 0.88), rgba(88, 166, 255, 0.14));\n            box-shadow: 0 0 14px rgba(88, 166, 255, 0.18);\n        }\n\n        .signal-rail span:nth-child(2n) {\n            background: linear-gradient(90deg, rgba(83, 215, 255, 0.06), rgba(83, 215, 255, 0.82), rgba(88, 166, 255, 0.16));\n            box-shadow: 0 0 14px rgba(83, 215, 255, 0.16);\n        }\n\n        .signal-rail span:nth-child(3n) {\n            background: linear-gradient(90deg, rgba(242, 188, 98, 0.04), rgba(242, 188, 98, 0.58), rgba(88, 166, 255, 0.12));\n            box-shadow: 0 0 14px rgba(242, 188, 98, 0.1);\n        }\n\n        .signal-rail.warm-signal span {\n            background: linear-gradient(90deg, rgba(242, 188, 98, 0.06), rgba(242, 188, 98, 0.72), rgba(88, 166, 255, 0.12));\n            box-shadow: 0 0 14px rgba(242, 188, 98, 0.14);\n        }\n\n        .signal-rail.warm-signal span:nth-child(2n) {\n            background: linear-gradient(90deg, rgba(248, 81, 73, 0.05), rgba(242, 188, 98, 0.62), rgba(83, 215, 255, 0.1));\n            box-shadow: 0 0 16px rgba(242, 188, 98, 0.16);\n        }\n\n        .shell-grid {\n            display: grid;\n            grid-template-columns: minmax(0, 1.7fr) minmax(300px, 0.95fr);\n            gap: 1.2rem;\n            align-items: stretch;\n        }\n\n        .hero-kicker {\n            display: inline-flex;\n            align-items: center;\n            gap: 0.5rem;\n            margin-bottom: 0.75rem;\n            color: var(--accent-blue);\n            font-size: 0.82rem;\n            letter-spacing: 0.18em;\n            text-transform: uppercase;\n        }\n\n        .hero-title {\n            margin: 0;\n            font-size: clamp(2rem, 4vw, 3.2rem);\n            font-weight: 800;\n            letter-spacing: -0.03em;\n        }\n\n        .hero-subtitle {\n            margin: 0.75rem 0 1.1rem;\n            max-width: 46rem;\n            line-height: 1.75;\n            color: var(--text-dim);\n            font-size: 0.98rem;\n        }\n\n        .hero-chip-row {\n            display: flex;\n            flex-wrap: wrap;\n            gap: 0.75rem;\n        }\n\n        .hero-data-rack {\n            display: grid;\n            grid-template-columns: repeat(3, minmax(0, 1fr));\n            gap: 0.8rem;\n            margin-top: 1rem;\n        }\n\n        .hero-data-rack .rack-cell {\n            position: relative;\n            padding: 0.85rem 0.95rem;\n            border-radius: 20px;\n            border: 1px solid rgba(88, 166, 255, 0.1);\n            background: linear-gradient(180deg, rgba(7, 13, 21, 0.84), rgba(10, 17, 26, 0.78));\n        }\n\n        .hero-data-rack .rack-cell::after {\n            content: "";\n            position: absolute;\n            right: 12px;\n            bottom: 12px;\n            width: 34px;\n            height: 34px;\n            border: 1px solid rgba(88, 166, 255, 0.08);\n            border-radius: 999px;\n            opacity: 0.28;\n        }\n\n        .hero-data-rack small {\n            display: block;\n            color: var(--text-dim);\n            letter-spacing: 0.12em;\n            margin-bottom: 0.3rem;\n        }\n\n        .hero-data-rack strong {\n            color: var(--text-main);\n            font-size: 0.96rem;\n        }\n\n        .status-chip {\n            display: inline-flex;\n            align-items: center;\n            gap: 0.45rem;\n            padding: 0.45rem 0.85rem;\n            border-radius: 999px;\n            border: 1px solid rgba(88, 166, 255, 0.14);\n            background: linear-gradient(180deg, rgba(7, 14, 22, 0.72), rgba(10, 17, 27, 0.56));\n            color: var(--text-main);\n            font-size: 0.84rem;\n        }\n\n        .status-chip--cyan {\n            border-color: rgba(83, 215, 255, 0.2);\n            box-shadow: inset 0 0 0 1px rgba(83, 215, 255, 0.04), 0 0 18px rgba(83, 215, 255, 0.08);\n        }\n\n        .status-chip--amber {\n            border-color: rgba(242, 188, 98, 0.22);\n            background: linear-gradient(180deg, rgba(29, 22, 10, 0.5), rgba(14, 13, 16, 0.54));\n            box-shadow: inset 0 0 0 1px rgba(242, 188, 98, 0.04), 0 0 18px rgba(242, 188, 98, 0.08);\n        }\n\n        .status-beacon {\n            width: 0.65rem;\n            height: 0.65rem;\n            border-radius: 999px;\n            background: var(--accent-green);\n            animation: beaconPulse 2.2s ease-out infinite;\n        }\n\n        .hero-side {\n            position: relative;\n            min-height: 100%;\n            padding: 1.25rem 1.3rem;\n            border-radius: 24px;\n            background:\n                linear-gradient(180deg, rgba(12, 19, 29, 0.98), rgba(6, 12, 20, 0.92)),\n                radial-gradient(circle at 22% 82%, rgba(242, 188, 98, 0.06), transparent 28%),\n                radial-gradient(circle at top right, rgba(88, 166, 255, 0.08), transparent 30%);\n            border: 1px solid rgba(88, 166, 255, 0.12);\n            box-shadow: var(--shadow-glow);\n        }\n\n        .resource-ring {\n            position: absolute;\n            inset: 0;\n            pointer-events: none;\n            opacity: 0.78;\n        }\n\n        .resource-ring::before {\n            content: "";\n            position: absolute;\n            width: 12.5rem;\n            height: 12.5rem;\n            top: -2.6rem;\n            right: -2.4rem;\n            background: url("__RADAR__") center/contain no-repeat;\n            opacity: 0.82;\n            animation: haloFloat 8s ease-in-out infinite;\n        }\n\n        .radar-sweep {\n            position: absolute;\n            inset: 0;\n            pointer-events: none;\n            overflow: hidden;\n            z-index: 1;\n        }\n\n        .radar-sweep::before {\n            content: "";\n            position: absolute;\n            width: 220px;\n            height: 220px;\n            right: 18px;\n            top: 8px;\n            border-radius: 999px;\n            background: conic-gradient(from 220deg, rgba(88, 166, 255, 0), rgba(88, 166, 255, 0.04), rgba(126, 231, 135, 0.3), rgba(88, 166, 255, 0.02), rgba(88, 166, 255, 0));\n            filter: blur(0.2px);\n            transform-origin: 50% 50%;\n            animation: radarSweep 6s linear infinite;\n        }\n\n        .pulse-orbit {\n            position: absolute;\n            right: 76px;\n            top: 72px;\n            width: 34px;\n            height: 34px;\n            border-radius: 999px;\n            background: rgba(88, 166, 255, 0.12);\n            border: 1px solid rgba(88, 166, 255, 0.18);\n            z-index: 2;\n            pointer-events: none;\n        }\n\n        .pulse-orbit::before,\n        .pulse-orbit::after {\n            content: "";\n            position: absolute;\n            inset: -12px;\n            border-radius: 999px;\n            border: 1px solid rgba(88, 166, 255, 0.22);\n            animation: orbitPulse 3.1s ease-out infinite;\n        }\n\n        .pulse-orbit::after {\n            animation-delay: 1.35s;\n        }\n\n        .target-lock {\n            position: absolute;\n            inset: auto 14px 14px auto;\n            width: 46px;\n            height: 46px;\n            border-radius: 999px;\n            border: 1px solid rgba(248, 81, 73, 0.14);\n            background: radial-gradient(circle, rgba(248, 81, 73, 0.12), rgba(248, 81, 73, 0.02) 52%, transparent 74%);\n            pointer-events: none;\n            z-index: 2;\n        }\n\n        .target-lock.soft-lock {\n            box-shadow:\n                0 0 0 1px rgba(248, 81, 73, 0.04),\n                0 0 24px rgba(248, 81, 73, 0.08);\n            filter: saturate(0.92);\n        }\n\n        .target-lock::before,\n        .target-lock::after {\n            content: "";\n            position: absolute;\n            background: rgba(248, 81, 73, 0.66);\n        }\n\n        .target-lock::before {\n            width: 24px;\n            height: 1px;\n            top: 22px;\n            left: 11px;\n        }\n\n        .target-lock::after {\n            width: 1px;\n            height: 24px;\n            top: 11px;\n            left: 22px;\n        }\n\n        .target-lock.soft-lock::before {\n            width: 18px;\n            height: 1px;\n            top: 22px;\n            left: 14px;\n            border-radius: 999px;\n            background: linear-gradient(90deg, rgba(248, 81, 73, 0.18), rgba(248, 81, 73, 0.54), rgba(248, 81, 73, 0.18));\n        }\n\n        .target-lock.soft-lock::after {\n            width: 1px;\n            height: 18px;\n            top: 14px;\n            left: 22px;\n            border-radius: 999px;\n            background: linear-gradient(180deg, rgba(248, 81, 73, 0.18), rgba(248, 81, 73, 0.54), rgba(248, 81, 73, 0.18));\n        }\n\n        .side-label {\n            color: var(--accent-cyan);\n            font-size: 0.8rem;\n            text-transform: uppercase;\n            letter-spacing: 0.18em;\n            margin-bottom: 0.75rem;\n        }\n\n        .side-stat {\n            display: flex;\n            justify-content: space-between;\n            gap: 1rem;\n            padding: 0.85rem 0;\n            border-bottom: 1px solid rgba(88, 166, 255, 0.1);\n            font-size: 0.92rem;\n        }\n\n        .side-stat:last-child {\n            border-bottom: none;\n        }\n\n        .side-stat strong {\n            color: var(--text-main);\n            text-align: right;\n        }\n\n        .side-stat:nth-of-type(2) strong {\n            color: var(--accent-cyan);\n        }\n\n        .side-stat:nth-of-type(4) strong {\n            color: var(--accent-gold);\n        }\n\n        .sidebar-shell {\n            margin-bottom: 1rem;\n            padding: 1rem 1rem 0.8rem;\n            border-radius: 18px;\n            background: linear-gradient(180deg, rgba(13, 22, 33, 0.92), rgba(8, 15, 24, 0.86));\n            border: 1px solid rgba(88, 166, 255, 0.14);\n            box-shadow: var(--shadow-glow);\n        }\n\n        .sidebar-shell::after {\n            content: "";\n            display: block;\n            margin-top: 0.8rem;\n            height: 1px;\n            background: linear-gradient(90deg, rgba(88, 166, 255, 0), rgba(88, 166, 255, 0.58), rgba(88, 166, 255, 0));\n        }\n\n        .sidebar-shell h3 {\n            margin: 0 0 0.45rem;\n            font-size: 1.05rem;\n        }\n\n        .sidebar-shell p {\n            margin: 0;\n            color: var(--text-dim);\n            line-height: 1.65;\n            font-size: 0.86rem;\n        }\n\n        .phase-track {\n            margin: 0.8rem 0 0.7rem;\n            padding: 0.85rem 0.95rem;\n            border-radius: 16px;\n            background: rgba(7, 12, 20, 0.84);\n            border: 1px solid rgba(88, 166, 255, 0.14);\n            font-size: 0.85rem;\n            color: var(--text-main);\n        }\n\n        .terminal-window {\n            position: relative;\n            margin-top: 0.55rem;\n            border-radius: 16px;\n            border: 1px solid rgba(88, 166, 255, 0.16);\n            background: linear-gradient(180deg, rgba(1, 6, 12, 0.98), rgba(5, 12, 18, 0.94));\n            padding: 1rem;\n            font-family: "Cascadia Code", Consolas, monospace;\n            color: #7ee787;\n            font-size: 0.8rem;\n            max-height: 180px;\n            overflow-y: auto;\n            box-shadow: inset 0 0 0 1px rgba(88, 166, 255, 0.05);\n        }\n\n        .report-shell,\n        .section-shell {\n            padding: 1.1rem 1.25rem;\n            margin: 0.65rem 0 1rem;\n        }\n\n        .report-shell--hud,\n        .section-shell--hud {\n            background:\n                linear-gradient(180deg, rgba(15, 24, 36, 0.96), rgba(9, 15, 24, 0.92)),\n                linear-gradient(90deg, rgba(88, 166, 255, 0.05), transparent 18%, transparent 82%, rgba(248, 81, 73, 0.05));\n        }\n\n        .shell-label {\n            color: var(--accent-cyan);\n            font-size: 0.79rem;\n            text-transform: uppercase;\n            letter-spacing: 0.18em;\n            margin-bottom: 0.4rem;\n            text-shadow: 0 0 12px rgba(83, 215, 255, 0.12);\n        }\n\n        .shell-title {\n            margin: 0;\n            font-size: 1.25rem;\n            font-weight: 700;\n        }\n\n        .shell-copy {\n            margin: 0.4rem 0 0;\n            line-height: 1.7;\n            color: var(--text-dim);\n            font-size: 0.9rem;\n        }\n\n        .report-meta-grid {\n            display: grid;\n            grid-template-columns: repeat(4, minmax(0, 1fr));\n            gap: 0.85rem;\n            margin-top: 1rem;\n        }\n\n        .meta-cell {\n            padding: 0.9rem 0.95rem;\n            border-radius: 20px;\n            background: rgba(6, 12, 20, 0.8);\n            border: 1px solid rgba(88, 166, 255, 0.1);\n        }\n\n        .meta-cell small {\n            display: block;\n            margin-bottom: 0.35rem;\n            color: var(--text-dim);\n            letter-spacing: 0.08em;\n        }\n\n        .meta-cell strong {\n            color: var(--text-main);\n            font-size: 0.96rem;\n            word-break: break-word;\n        }\n\n        .metric-card {\n            position: relative;\n            overflow: hidden;\n            min-height: 148px;\n            border-radius: 24px;\n            padding: 1.15rem 1.1rem 1rem;\n            background:\n                linear-gradient(180deg, rgba(14, 22, 34, 0.96), rgba(9, 15, 24, 0.92)),\n                radial-gradient(circle at 18% 14%, rgba(83, 215, 255, 0.04), transparent 22%),\n                radial-gradient(circle at top right, rgba(88, 166, 255, 0.08), transparent 24%);\n            border: 1px solid rgba(88, 166, 255, 0.13);\n            box-shadow: var(--shadow-glow);\n            transition: transform 0.18s ease, border-color 0.18s ease;\n        }\n\n        .metric-card:nth-child(2n) {\n            border-color: rgba(83, 215, 255, 0.16);\n        }\n\n        .metric-card:nth-child(3n) {\n            background:\n                linear-gradient(180deg, rgba(18, 20, 30, 0.96), rgba(10, 15, 24, 0.92)),\n                radial-gradient(circle at 85% 14%, rgba(242, 188, 98, 0.06), transparent 18%),\n                radial-gradient(circle at top right, rgba(88, 166, 255, 0.08), transparent 24%);\n        }\n\n        .metric-card:hover {\n            transform: translateY(-2px);\n            border-color: rgba(88, 166, 255, 0.24);\n        }\n\n        .metric-card::after {\n            content: "";\n            position: absolute;\n            top: 0;\n            left: 0;\n            width: 100%;\n            height: 2px;\n            background: linear-gradient(90deg, rgba(88, 166, 255, 0), rgba(88, 166, 255, 0.68), rgba(88, 166, 255, 0));\n        }\n\n        .metric-card::before {\n            z-index: 0;\n        }\n\n        .metric-card .metric-value-row {\n            display: flex;\n            align-items: flex-start;\n            justify-content: space-between;\n            gap: 0.75rem;\n            position: relative;\n            z-index: 2;\n        }\n\n        .metric-card .metric-badge {\n            padding: 0.28rem 0.42rem;\n            border-radius: 999px;\n            border: 1px solid rgba(88, 166, 255, 0.16);\n            color: var(--accent-cyan);\n            font-size: 0.72rem;\n            letter-spacing: 0.08em;\n            background: rgba(6, 12, 20, 0.74);\n        }\n\n        .metric-card .metric-foot {\n            position: relative;\n            z-index: 2;\n            margin-top: 0.5rem;\n        }\n\n        .metric-card .target-lock {\n            inset: auto 12px 12px auto;\n            width: 38px;\n            height: 38px;\n            border-color: rgba(88, 166, 255, 0.14);\n            background: radial-gradient(circle, rgba(88, 166, 255, 0.14), transparent 68%);\n        }\n\n        .metric-card .target-lock::before,\n        .metric-card .target-lock::after {\n            background: rgba(83, 215, 255, 0.72);\n        }\n\n        .metric-card--danger::after {\n            background: linear-gradient(90deg, rgba(248, 81, 73, 0), rgba(248, 81, 73, 1), rgba(248, 81, 73, 0));\n        }\n\n        .metric-card small {\n            display: block;\n            color: var(--text-dim);\n            letter-spacing: 0.18em;\n            text-transform: uppercase;\n            font-size: 0.76rem;\n        }\n\n        .metric-card h3 {\n            margin: 0.75rem 0 0.4rem;\n            font-size: 2.15rem;\n            line-height: 1;\n            color: var(--text-main);\n        }\n\n        .metric-card--danger h3 {\n            color: var(--accent-red);\n        }\n\n        .metric-card p {\n            margin: 0;\n            color: var(--text-dim);\n            line-height: 1.6;\n            font-size: 0.86rem;\n        }\n\n        .tab-intro {\n            margin-bottom: 0.9rem;\n        }\n\n        .hud-tab-frame {\n            position: relative;\n            margin-top: 0.4rem;\n            padding: 0.35rem 0.4rem 0;\n            border-radius: 28px;\n            background: linear-gradient(180deg, rgba(10, 17, 26, 0.7), rgba(10, 17, 26, 0.18));\n            border: 1px solid rgba(88, 166, 255, 0.08);\n        }\n\n        [data-testid="stTabs"] {\n            margin-top: 0.85rem;\n        }\n\n        [data-testid="stTabs"] [role="tablist"] {\n            gap: 0.7rem;\n            padding: 0.2rem 0.2rem 0.6rem;\n        }\n\n        [data-testid="stTabs"] [role="tab"] {\n            border-radius: 999px;\n            padding: 0.55rem 0.95rem;\n            background: rgba(9, 15, 24, 0.76);\n            border: 1px solid rgba(88, 166, 255, 0.12);\n            color: var(--text-dim);\n        }\n\n        [data-testid="stTabs"] [aria-selected="true"] {\n            background: linear-gradient(180deg, rgba(17, 28, 41, 0.98), rgba(12, 20, 32, 0.94));\n            color: var(--text-main);\n            border-color: rgba(248, 81, 73, 0.28);\n            box-shadow: 0 10px 22px rgba(2, 9, 16, 0.35);\n        }\n\n        [data-testid="stTabs"] [role="tab"]:hover {\n            color: var(--text-main);\n            border-color: rgba(88, 166, 255, 0.22);\n        }\n\n        [data-testid="stDataFrame"],\n        [data-testid="stExpander"],\n        .stAlert {\n            border-radius: 18px !important;\n        }\n\n        [data-testid="stDataFrame"] {\n            border: 1px solid rgba(88, 166, 255, 0.12);\n            background: rgba(6, 12, 20, 0.72);\n            box-shadow: inset 0 0 0 1px rgba(88, 166, 255, 0.04);\n        }\n\n        [data-testid="stExpander"] {\n            border: 1px solid rgba(88, 166, 255, 0.11) !important;\n            background: linear-gradient(180deg, rgba(13, 20, 31, 0.96), rgba(8, 14, 22, 0.88)) !important;\n            overflow: hidden;\n        }\n\n        [data-testid="stExpander"] summary {\n            background: rgba(8, 14, 22, 0.62);\n        }\n\n        [data-testid="stExpander"] summary p {\n            color: var(--text-main);\n        }\n\n        .policy-gate {\n            padding: 1.15rem;\n            border-radius: 22px;\n            min-height: 100%;\n            background: linear-gradient(180deg, rgba(11, 18, 28, 0.94), rgba(7, 13, 21, 0.88));\n            border: 1px solid rgba(88, 166, 255, 0.1);\n        }\n\n        .policy-gate--pass {\n            border-color: rgba(126, 231, 135, 0.24);\n        }\n\n        .policy-gate--fail {\n            border-color: rgba(248, 81, 73, 0.24);\n        }\n\n        .policy-gate h2 {\n            margin: 0 0 0.25rem;\n            font-size: 2rem;\n        }\n\n        .policy-gate p {\n            margin: 0.25rem 0;\n            color: var(--text-dim);\n        }\n\n        .reason-list {\n            margin-top: 0.9rem;\n            display: grid;\n            gap: 0.45rem;\n            font-size: 0.88rem;\n            color: var(--text-main);\n        }\n\n        .empty-panel {\n            position: relative;\n            padding: 1.35rem;\n            border-radius: 22px;\n            border: 1px dashed rgba(88, 166, 255, 0.12);\n            background: rgba(7, 13, 21, 0.7);\n            color: var(--text-dim);\n            line-height: 1.8;\n        }\n\n        .login-layout-shell {\n            margin: 0 auto 0.65rem;\n        }\n\n        .login-hero {\n            padding: 1.55rem 1.55rem 1.25rem;\n            text-align: center;\n            min-height: 100%;\n        }\n\n        .login-hero h1 {\n            margin: 0;\n            font-size: clamp(1.9rem, 3.2vw, 2.8rem);\n        }\n\n        .login-hero p {\n            margin: 0.7rem auto 0;\n            max-width: 34rem;\n            color: var(--text-dim);\n            line-height: 1.72;\n        }\n\n        .login-form-shell {\n            padding-top: 0.35rem;\n        }\n\n        .login-form-note {\n            margin-bottom: 0.7rem;\n            padding: 0.9rem 1rem;\n            border-radius: 20px;\n            background: rgba(8, 15, 24, 0.76);\n            border: 1px solid rgba(88, 166, 255, 0.1);\n            color: var(--text-dim);\n            line-height: 1.65;\n        }\n\n        [data-testid="stForm"] {\n            padding: 1.1rem 1.2rem;\n            border-radius: 20px;\n            border: 1px solid rgba(88, 166, 255, 0.14);\n            background: linear-gradient(180deg, rgba(12, 19, 29, 0.96), rgba(7, 14, 21, 0.88));\n            box-shadow: var(--shadow-glow);\n        }\n\n        footer, #MainMenu {\n            visibility: hidden;\n        }\n\n        @media (max-width: 1100px) {\n            .shell-grid,\n            .report-meta-grid {\n                grid-template-columns: 1fr;\n            }\n        }\n\n        @media (max-width: 980px) {\n            .login-hero {\n                margin-bottom: 0.85rem;\n            }\n        }\n    </style>\n    '.replace("__GRID__", grid_uri).replace("__RADAR__", radar_uri)
    st.markdown(style, unsafe_allow_html=True)


def inject_motion_styles() -> None:
    st.markdown(
        """
        <style>
            @keyframes vectorFlow {
                0% { background-position: 0% 50%; }
                100% { background-position: 140% 50%; }
            }

            @keyframes vectorBlink {
                0% { opacity: 0.38; transform: scaleX(0.9); }
                50% { opacity: 1; transform: scaleX(1); }
                100% { opacity: 0.38; transform: scaleX(0.9); }
            }

            @keyframes meshDrift {
                0% { stroke-dashoffset: 0; opacity: 0.4; }
                50% { opacity: 0.7; }
                100% { stroke-dashoffset: -32; opacity: 0.4; }
            }

            @keyframes meshPulse {
                0% { opacity: 0.72; transform: scale(0.96); }
                50% { opacity: 1; transform: scale(1.06); }
                100% { opacity: 0.72; transform: scale(0.96); }
            }

            @keyframes trendFlow {
                0% { background-position: 0 0; opacity: 0.72; }
                50% { opacity: 1; }
                100% { background-position: 180% 0; opacity: 0.72; }
            }

            @keyframes telemetryShift {
                0% { background-position: 0 0; opacity: 0.46; }
                50% { opacity: 0.92; }
                100% { background-position: 160% 0; opacity: 0.46; }
            }

            .hero-asset-board {
                position: relative;
                min-height: 254px;
                padding-top: 6.8rem;
                z-index: 2;
            }

            .hero-asset-board::after {
                content: "";
                position: absolute;
                left: 1rem;
                right: 1rem;
                bottom: 1.1rem;
                height: 48px;
                border-radius: 18px;
                background: linear-gradient(90deg, rgba(88, 166, 255, 0.02), rgba(83, 215, 255, 0.14), rgba(242, 188, 98, 0.12), rgba(88, 166, 255, 0.02));
                mask-image: linear-gradient(90deg, transparent, #000 10%, #000 90%, transparent);
                pointer-events: none;
                opacity: 0.8;
            }

            .asset-mesh {
                position: absolute;
                inset: 0;
                pointer-events: none;
                mask-image: radial-gradient(circle at 48% 42%, #000 0, #000 62%, transparent 100%);
            }

            .asset-mesh::before {
                content: "";
                position: absolute;
                left: 72px;
                top: 78px;
                width: 220px;
                height: 110px;
                border-radius: 999px;
                background: radial-gradient(circle, rgba(83, 215, 255, 0.18), rgba(242, 188, 98, 0.08) 52%, transparent 76%);
                filter: blur(18px);
                opacity: 0.8;
            }

            .mesh-link {
                position: absolute;
                height: 3px;
                border-radius: 999px;
                background: linear-gradient(90deg, rgba(88, 166, 255, 0.05), rgba(83, 215, 255, 0.72), rgba(242, 188, 98, 0.2), rgba(88, 166, 255, 0.04));
                transform-origin: left center;
                animation: meshDrift 9s linear infinite;
                box-shadow: 0 0 18px rgba(83, 215, 255, 0.12);
                opacity: 0.8;
            }

            .mesh-link--one {
                left: 58px;
                top: 74px;
                width: 144px;
                transform: rotate(18deg);
            }

            .mesh-link--two {
                left: 168px;
                top: 132px;
                width: 126px;
                transform: rotate(23deg);
            }

            .mesh-link--three {
                left: 114px;
                top: 170px;
                width: 86px;
                transform: rotate(-34deg);
            }

            .mesh-node {
                position: absolute;
                width: 14px;
                height: 14px;
                border-radius: 999px;
                box-shadow: 0 0 22px rgba(88, 166, 255, 0.18);
                animation: meshPulse 3.2s ease-in-out infinite;
            }

            .mesh-node::after {
                content: "";
                position: absolute;
                inset: -9px;
                border-radius: 999px;
                border: 1px solid rgba(88, 166, 255, 0.16);
                opacity: 0.5;
            }

            .mesh-node--asset {
                background: radial-gradient(circle, rgba(131, 221, 255, 0.98), rgba(83, 215, 255, 0.42));
            }

            .mesh-node--risk {
                width: 20px;
                height: 20px;
                background: radial-gradient(circle, rgba(242, 188, 98, 0.98), rgba(242, 188, 98, 0.5));
                box-shadow: 0 0 26px rgba(242, 188, 98, 0.24);
            }

            .mesh-node--policy {
                background: radial-gradient(circle, rgba(126, 231, 135, 0.98), rgba(126, 231, 135, 0.42));
                box-shadow: 0 0 22px rgba(126, 231, 135, 0.22);
            }

            .mesh-node--one { left: 54px; top: 64px; }
            .mesh-node--two { left: 138px; top: 176px; }
            .mesh-node--three { left: 236px; top: 118px; }
            .mesh-node--four { left: 298px; top: 180px; }

            .metric-card__signal {
                position: relative;
            }

            .metric-card--warm {
                border-color: rgba(242, 188, 98, 0.18);
                box-shadow: 0 24px 44px rgba(0, 0, 0, 0.28), 0 0 0 1px rgba(242, 188, 98, 0.05);
            }

            .trend-strip {
                position: relative;
                z-index: 2;
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.38rem;
                margin-top: 0.72rem;
            }

            .trend-strip__lane {
                display: block;
                height: 8px;
                border-radius: 999px;
                background: linear-gradient(90deg, rgba(88, 166, 255, 0.06), rgba(83, 215, 255, 0.92), rgba(88, 166, 255, 0.14));
                background-size: 180% 100%;
                animation: trendFlow 3.4s linear infinite;
            }

            .trend-strip--warm .trend-strip__lane {
                background: linear-gradient(90deg, rgba(242, 188, 98, 0.06), rgba(242, 188, 98, 0.88), rgba(248, 81, 73, 0.2));
            }

            .policy-gate--warm {
                box-shadow: inset 0 0 0 1px rgba(242, 188, 98, 0.06), 0 0 26px rgba(242, 188, 98, 0.08);
                background: linear-gradient(180deg, rgba(20, 20, 24, 0.94), rgba(9, 14, 22, 0.9));
            }

            .login-hero--signal::after {
                content: "";
                position: absolute;
                inset: auto 18px 18px 18px;
                height: 46px;
                border-radius: 18px;
                background: linear-gradient(90deg, rgba(88, 166, 255, 0.05), rgba(83, 215, 255, 0.16), rgba(242, 188, 98, 0.08));
                mask-image: linear-gradient(90deg, transparent, #000 12%, #000 88%, transparent);
                pointer-events: none;
            }

            .report-sync-shell {
                position: relative;
            }

            .report-sync-shell::before {
                animation-duration: 6.6s;
            }

            .report-shell--active {
                border-color: rgba(83, 215, 255, 0.14);
                box-shadow: 0 24px 48px rgba(0, 0, 0, 0.28), 0 0 0 1px rgba(83, 215, 255, 0.04), 0 0 32px rgba(242, 188, 98, 0.05);
            }

            .hud-shell-corners span,
            .panel-corners span {
                width: 24px;
                height: 24px;
                opacity: 0.54;
            }

            .soft-corners span {
                width: 18px;
                height: 18px;
                opacity: 0.38;
                filter: blur(0.35px);
            }

            .soft-shell-muted .soft-corners span {
                opacity: 0.22;
                filter: blur(0.55px);
            }

            .soft-corners span::before,
            .soft-corners span::after {
                box-shadow: 0 0 14px rgba(83, 215, 255, 0.09);
            }

            .hud-shell-corners span::before,
            .panel-corners span::before {
                width: 18px;
                height: 1px;
            }

            .soft-corners span::before {
                width: 12px;
                background: linear-gradient(90deg, rgba(83, 215, 255, 0.42), rgba(83, 215, 255, 0));
            }

            .hud-shell-corners span::after,
            .panel-corners span::after {
                width: 1px;
                height: 18px;
                background: linear-gradient(180deg, rgba(88, 166, 255, 0.6), rgba(88, 166, 255, 0));
            }

            .soft-corners span::after {
                height: 12px;
                background: linear-gradient(180deg, rgba(83, 215, 255, 0.42), rgba(83, 215, 255, 0));
            }

            .hero-side {
                padding: 1.3rem 1.25rem 1.15rem;
                border-radius: 28px;
                background:
                    radial-gradient(circle at 80% 18%, rgba(83, 215, 255, 0.12), transparent 26%),
                    radial-gradient(circle at 24% 82%, rgba(242, 188, 98, 0.12), transparent 30%),
                    linear-gradient(180deg, rgba(11, 19, 30, 0.98), rgba(6, 12, 20, 0.94));
                border-color: rgba(88, 166, 255, 0.1);
                box-shadow: 0 26px 54px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.03);
            }

            .resource-ring {
                opacity: 0.76;
            }

            .resource-ring::before {
                width: 11.2rem;
                height: 11.2rem;
                top: -1.9rem;
                right: -1.8rem;
                opacity: 0.54;
            }

            .resource-ring::after {
                content: "";
                position: absolute;
                right: 2.2rem;
                top: 3.1rem;
                width: 7.2rem;
                height: 7.2rem;
                border-radius: 999px;
                background: radial-gradient(circle, rgba(242, 188, 98, 0.18), rgba(83, 215, 255, 0.08) 46%, transparent 74%);
                filter: blur(18px);
                opacity: 0.72;
            }

            .radar-sweep::before {
                width: 248px;
                height: 248px;
                right: 6px;
                top: 2px;
                background: conic-gradient(from 226deg, rgba(88, 166, 255, 0), rgba(88, 166, 255, 0.02), rgba(83, 215, 255, 0.16), rgba(126, 231, 135, 0.18), rgba(242, 188, 98, 0.08), rgba(88, 166, 255, 0));
                filter: blur(1.2px);
                animation-duration: 7.4s;
            }

            .radar-sweep::after {
                content: "";
                position: absolute;
                left: 2rem;
                right: 2rem;
                top: 8.8rem;
                height: 1px;
                background: linear-gradient(90deg, rgba(88, 166, 255, 0), rgba(83, 215, 255, 0.48), rgba(242, 188, 98, 0.42), rgba(88, 166, 255, 0));
                opacity: 0.58;
            }

            .pulse-orbit {
                right: 70px;
                top: 84px;
                width: 24px;
                height: 24px;
                background: rgba(83, 215, 255, 0.16);
                border-color: rgba(83, 215, 255, 0.16);
                box-shadow: 0 0 18px rgba(83, 215, 255, 0.16);
            }

            .target-lock {
                inset: auto 16px 16px auto;
                width: 42px;
                height: 42px;
                border-color: rgba(242, 188, 98, 0.16);
                background: radial-gradient(circle, rgba(242, 188, 98, 0.16), rgba(248, 81, 73, 0.04) 54%, transparent 76%);
            }

            .target-lock.soft-lock {
                box-shadow: 0 0 0 1px rgba(242, 188, 98, 0.04), 0 0 24px rgba(242, 188, 98, 0.08);
                filter: saturate(0.88);
            }

            .target-lock::before,
            .target-lock::after {
                background: rgba(242, 188, 98, 0.62);
            }

            .target-lock::before {
                width: 18px;
                top: 20px;
                left: 12px;
            }

            .target-lock::after {
                height: 18px;
                top: 12px;
                left: 20px;
            }

            .target-lock.soft-lock::before {
                width: 14px;
                top: 20px;
                left: 14px;
                background: linear-gradient(90deg, rgba(242, 188, 98, 0.14), rgba(242, 188, 98, 0.58), rgba(242, 188, 98, 0.14));
            }

            .target-lock.soft-lock::after {
                height: 14px;
                top: 14px;
                left: 20px;
                background: linear-gradient(180deg, rgba(242, 188, 98, 0.14), rgba(242, 188, 98, 0.58), rgba(242, 188, 98, 0.14));
            }

            .side-label {
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                padding: 0.38rem 0.78rem;
                border-radius: 999px;
                font-size: 0.76rem;
                letter-spacing: 0.16em;
                margin-bottom: 0.75rem;
                background: linear-gradient(180deg, rgba(8, 15, 24, 0.72), rgba(10, 16, 26, 0.54));
                border: 1px solid rgba(83, 215, 255, 0.12);
                box-shadow: inset 0 0 0 1px rgba(83, 215, 255, 0.03);
            }

            .side-stat {
                display: grid;
                grid-template-columns: minmax(0, 0.82fr) minmax(0, 1.18fr);
                align-items: center;
                gap: 0.9rem;
                padding: 0.9rem 0.92rem;
                margin-top: 0.52rem;
                border-radius: 18px;
                background: linear-gradient(180deg, rgba(8, 14, 22, 0.82), rgba(10, 16, 25, 0.72));
                border: 1px solid rgba(88, 166, 255, 0.08);
                box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.015);
            }

            .side-stat span {
                color: var(--text-dim);
                letter-spacing: 0.08em;
                text-transform: uppercase;
                font-size: 0.72rem;
            }

            .side-stat strong {
                line-height: 1.45;
            }

            .telemetry-band {
                position: relative;
                z-index: 2;
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 0.34rem;
                margin: 0.2rem 0 0.95rem;
                padding: 0.45rem 0.5rem;
                border-radius: 16px;
                background: rgba(7, 13, 21, 0.46);
                border: 1px solid rgba(88, 166, 255, 0.08);
            }

            .telemetry-band__bar {
                display: block;
                height: 6px;
                border-radius: 999px;
                background: linear-gradient(90deg, rgba(88, 166, 255, 0.04), rgba(83, 215, 255, 0.88), rgba(88, 166, 255, 0.08));
                background-size: 180% 100%;
                animation: telemetryShift 4.4s linear infinite;
                box-shadow: 0 0 12px rgba(83, 215, 255, 0.1);
            }

            .telemetry-band__bar:nth-child(2n) {
                animation-delay: -1.1s;
            }

            .telemetry-band__bar:nth-child(3n) {
                animation-delay: -2.2s;
            }

            .telemetry-band--warm .telemetry-band__bar {
                background: linear-gradient(90deg, rgba(242, 188, 98, 0.05), rgba(242, 188, 98, 0.88), rgba(248, 81, 73, 0.14));
                box-shadow: 0 0 14px rgba(242, 188, 98, 0.12);
            }

            .scan-vector-matrix {
                margin: 0.85rem 0 0.72rem;
                padding: 0.95rem 0.95rem 0.9rem;
                border-radius: 20px;
                background:
                    linear-gradient(180deg, rgba(7, 12, 20, 0.92), rgba(9, 16, 24, 0.84)),
                    radial-gradient(circle at top right, rgba(83, 215, 255, 0.06), transparent 24%);
                border: 1px solid rgba(88, 166, 255, 0.16);
                box-shadow:
                    inset 0 0 0 1px rgba(88, 166, 255, 0.03),
                    0 18px 34px rgba(1, 7, 13, 0.34);
            }

            .scan-vector-head {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 0.8rem;
                margin-bottom: 0.75rem;
                font-size: 0.76rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                color: var(--accent-cyan);
            }

            .scan-vector-head strong {
                color: var(--text-main);
                font-size: 0.72rem;
                letter-spacing: 0.08em;
            }

            .scan-vector-grid {
                display: grid;
                gap: 0.65rem;
            }

            .scan-vector-card {
                position: relative;
                overflow: hidden;
                padding: 0.82rem 0.88rem 0.85rem;
                border-radius: 18px;
                background:
                    linear-gradient(180deg, rgba(10, 18, 28, 0.96), rgba(6, 11, 18, 0.88)),
                    radial-gradient(circle at 85% 22%, rgba(242, 188, 98, 0.06), transparent 20%);
                border: 1px solid rgba(88, 166, 255, 0.12);
            }

            .scan-vector-card::before {
                content: "";
                position: absolute;
                inset: 0;
                background: linear-gradient(90deg, transparent, rgba(83, 215, 255, 0.08), transparent);
                transform: translateX(-120%);
                pointer-events: none;
            }

            .scan-vector-card--active::before {
                animation: sweepGlow 2.8s linear infinite;
            }

            .scan-vector-card--done {
                border-color: rgba(126, 231, 135, 0.2);
                box-shadow: inset 0 0 0 1px rgba(126, 231, 135, 0.03);
            }

            .scan-vector-card--active {
                border-color: rgba(83, 215, 255, 0.24);
                box-shadow:
                    inset 0 0 0 1px rgba(83, 215, 255, 0.05),
                    0 0 26px rgba(83, 215, 255, 0.08);
            }

            .scan-vector-top {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 0.7rem;
                margin-bottom: 0.48rem;
            }

            .scan-vector-title {
                display: block;
                color: var(--text-main);
                font-size: 0.87rem;
                font-weight: 700;
                line-height: 1.25;
            }

            .scan-vector-copy {
                display: block;
                margin-top: 0.18rem;
                color: var(--text-dim);
                font-size: 0.75rem;
                line-height: 1.45;
            }

            .scan-vector-state {
                display: inline-flex;
                align-items: center;
                gap: 0.32rem;
                padding: 0.22rem 0.5rem;
                border-radius: 999px;
                background: rgba(88, 166, 255, 0.08);
                border: 1px solid rgba(88, 166, 255, 0.12);
                color: var(--accent-cyan);
                font-size: 0.7rem;
                white-space: nowrap;
            }

            .scan-vector-card--done .scan-vector-state {
                color: var(--accent-green);
                border-color: rgba(126, 231, 135, 0.18);
                background: rgba(126, 231, 135, 0.08);
            }

            .scan-vector-card--pending .scan-vector-state {
                color: var(--text-dim);
                border-color: rgba(88, 166, 255, 0.08);
                background: rgba(88, 166, 255, 0.04);
            }

            .scan-vector-bar {
                position: relative;
                height: 0.46rem;
                border-radius: 999px;
                overflow: hidden;
                background: linear-gradient(90deg, rgba(88, 166, 255, 0.08), rgba(15, 24, 36, 0.86));
                border: 1px solid rgba(88, 166, 255, 0.06);
            }

            .scan-vector-fill {
                position: absolute;
                inset: 0 auto 0 0;
                border-radius: inherit;
                background:
                    linear-gradient(90deg, rgba(83, 215, 255, 0.56), rgba(88, 166, 255, 0.96), rgba(242, 188, 98, 0.76));
                background-size: 200% 100%;
                box-shadow: 0 0 18px rgba(83, 215, 255, 0.18);
            }

            .scan-vector-card--active .scan-vector-fill {
                animation: vectorFlow 1.9s linear infinite;
            }

            .scan-vector-card--done .scan-vector-fill {
                background: linear-gradient(90deg, rgba(126, 231, 135, 0.72), rgba(83, 215, 255, 0.8), rgba(242, 188, 98, 0.76));
            }

            .scan-vector-foot {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 0.7rem;
                margin-top: 0.4rem;
                color: var(--text-dim);
                font-size: 0.72rem;
            }

            .scan-vector-pulse {
                display: inline-flex;
                align-items: center;
                gap: 0.2rem;
            }

            .scan-vector-pulse span {
                width: 0.22rem;
                height: 0.22rem;
                border-radius: 999px;
                background: rgba(83, 215, 255, 0.72);
                animation: vectorBlink 1.4s ease-in-out infinite;
            }

            .scan-vector-pulse span:nth-child(2) {
                animation-delay: 0.18s;
            }

            .scan-vector-pulse span:nth-child(3) {
                animation-delay: 0.36s;
            }

            .scan-vector-card--done .scan-vector-pulse span {
                background: rgba(126, 231, 135, 0.76);
            }

            .scan-vector-card--pending .scan-vector-pulse span {
                background: rgba(143, 165, 191, 0.4);
            }

            .scan-vector-card--failed {
                border-color: rgba(248, 81, 73, 0.24);
                box-shadow: inset 0 0 0 1px rgba(248, 81, 73, 0.04);
            }

            .scan-vector-card--failed .scan-vector-state {
                color: var(--accent-red);
                border-color: rgba(248, 81, 73, 0.2);
                background: rgba(248, 81, 73, 0.08);
            }

            .scan-vector-card--failed .scan-vector-fill {
                background: linear-gradient(90deg, rgba(248, 81, 73, 0.78), rgba(242, 188, 98, 0.72));
                box-shadow: 0 0 18px rgba(248, 81, 73, 0.14);
            }

            .scan-vector-card--failed .scan-vector-pulse span {
                background: rgba(248, 81, 73, 0.76);
            }

            .scan-vector-card--skipped {
                border-color: rgba(242, 188, 98, 0.18);
                box-shadow: inset 0 0 0 1px rgba(242, 188, 98, 0.03);
            }

            .scan-vector-card--skipped .scan-vector-state {
                color: var(--accent-gold);
                border-color: rgba(242, 188, 98, 0.18);
                background: rgba(242, 188, 98, 0.08);
            }

            .scan-vector-card--skipped .scan-vector-fill {
                background: linear-gradient(90deg, rgba(242, 188, 98, 0.72), rgba(88, 166, 255, 0.58));
                box-shadow: 0 0 16px rgba(242, 188, 98, 0.12);
            }

            .scan-vector-card--skipped .scan-vector-pulse span {
                background: rgba(242, 188, 98, 0.72);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hud_corners() -> str:
    return "<div class='hud-shell-corners soft-corners'><span class='corner-tl'></span><span class='corner-tr'></span><span class='corner-bl'></span><span class='corner-br'></span></div>"


def panel_corners() -> str:
    return "<div class='panel-corners soft-corners'><span class='corner-tl'></span><span class='corner-tr'></span><span class='corner-bl'></span><span class='corner-br'></span></div>"


def signal_rail(count: int = 4, tone: str = "") -> str:
    tone_class = f" {tone}" if tone else ""
    return f"<div class='signal-rail{tone_class}'>" + "".join("<span></span>" for _ in range(count)) + "</div>"


def hero_asset_mesh() -> str:
    return """
    <div class="hero-asset-board">
        <div class="asset-mesh" aria-hidden="true">
            <span class="mesh-link mesh-link--one"></span>
            <span class="mesh-link mesh-link--two"></span>
            <span class="mesh-link mesh-link--three"></span>
            <span class="mesh-node mesh-node--asset mesh-node--one"></span>
            <span class="mesh-node mesh-node--asset mesh-node--two"></span>
            <span class="mesh-node mesh-node--risk mesh-node--three"></span>
            <span class="mesh-node mesh-node--policy mesh-node--four"></span>
        </div>
    </div>
    """


def telemetry_band(tone: str = "cool") -> str:
    warm_class = " telemetry-band--warm" if tone == "warm" else ""
    return (
        f"<div class='telemetry-band{warm_class}' aria-hidden='true'>"
        "<span class='telemetry-band__bar'></span>"
        "<span class='telemetry-band__bar'></span>"
        "<span class='telemetry-band__bar'></span>"
        "<span class='telemetry-band__bar'></span>"
        "</div>"
    )


SCAN_VECTOR_META = {
    "SBOM": ("SBOM 资产提取", "解析依赖清单与组件资产拓扑"),
    "SAST": ("SAST 源码审计", "扫描规则命中与高危代码路径"),
    "CVE": ("CVE 风险匹配", "关联漏洞情报与版本暴露面"),
    "REPORT": ("REPORT 汇总结论", "聚合门禁策略与最终报告"),
}

SCAN_STATE_LABELS = {
    "pending": "待机",
    "running": "扫描中",
    "completed": "已完成",
    "failed": "失败",
    "skipped": "跳过",
}

SCAN_STATUS_TO_CLASS = {
    "pending": "scan-vector-card scan-vector-card--pending",
    "running": "scan-vector-card scan-vector-card--active",
    "completed": "scan-vector-card scan-vector-card--done",
    "failed": "scan-vector-card scan-vector-card--failed",
    "skipped": "scan-vector-card scan-vector-card--skipped",
}


def idle_scan_job(target: str = "") -> dict:
    stages = []
    for key in ("SBOM", "SAST", "CVE", "REPORT"):
        label, copy_text = SCAN_VECTOR_META[key]
        stages.append(
            {
                "key": key,
                "label": label,
                "status": "pending",
                "percent": 8,
                "message": copy_text,
            }
        )

    return {
        "job_id": "",
        "target": target,
        "status": "idle",
        "phase": "IDLE",
        "percent": 0,
        "message": "等待新的扫描任务。",
        "logs": [f"REQ: {target}"] if target else ["SYSTEM: Ready for the next scan request."],
        "stages": stages,
    }


def render_scan_job_log(logs: list[str]) -> str:
    lines = logs[-8:] if logs else ["SYSTEM: Waiting for scan signal."]
    html_log = "".join(
        [
            "<div><span style='color:#8FA5BF'>[{}]</span> {}</div>".format(
                time.strftime("%H:%M:%S"),
                html.escape(line),
            )
            for line in lines
        ]
    )
    return f"<div class='terminal-window'>{html_log}</div>"


def scan_vector_matrix(scan_job: dict | None = None) -> str:
    scan_job = scan_job or idle_scan_job()
    stages = scan_job.get("stages") or idle_scan_job().get("stages", [])
    cards = []

    for stage in stages:
        key = stage.get("key", "UNKNOWN")
        title, default_copy = SCAN_VECTOR_META.get(
            key,
            (stage.get("label", key), stage.get("message", "")),
        )
        status = stage.get("status", "pending")
        state = SCAN_STATE_LABELS.get(status, "待机")
        percent = int(stage.get("percent", 0))
        copy_text = stage.get("message") or default_copy
        card_class = SCAN_STATUS_TO_CLASS.get(status, "scan-vector-card scan-vector-card--pending")

        cards.append(
            textwrap.dedent(
                f"""
                <div class="{card_class}">
                    <div class="scan-vector-top">
                        <div>
                            <span class="scan-vector-title">{html.escape(title)}</span>
                            <span class="scan-vector-copy">{html.escape(copy_text)}</span>
                        </div>
                        <span class="scan-vector-state">{html.escape(state)}</span>
                    </div>
                    <div class="scan-vector-bar">
                        <span class="scan-vector-fill" style="width: {percent}%"></span>
                    </div>
                    <div class="scan-vector-foot">
                        <span>{html.escape(key)} · {percent}%</span>
                        <span class="scan-vector-pulse"><span></span><span></span><span></span></span>
                    </div>
                </div>
                """
            ).strip()
        )

    phase_label = html.escape(str(scan_job.get("phase", "IDLE")))
    phase_percent = int(scan_job.get("percent", 0))
    return (
        "<div class='scan-vector-matrix'>"
        f"<div class='scan-vector-head'><span>SCAN VECTOR MATRIX</span><strong>{phase_label} {phase_percent}%</strong></div>"
        "<div class='scan-vector-grid'>"
        + "".join(cards)
        + "</div></div>"
    )


def trend_strip(tone: str = "cool") -> str:
    tone_class = " trend-strip--warm" if tone == "warm" else ""
    return (
        f"<div class='trend-strip{tone_class}'>"
        "<span class='trend-strip__lane'></span>"
        "<span class='trend-strip__lane'></span>"
        "<span class='trend-strip__lane'></span>"
        "</div>"
    )


def render_metric_card(label: str, value: str | int, detail: str, tone: str = "default") -> str:
    tone_class = " metric-card--danger metric-card--warm" if tone == "danger" else ""
    trend_tone = "warm" if tone == "danger" else "cool"
    return (
        f"<div class='metric-card metric-card__signal{tone_class}'>"
        f"{panel_corners()}"
        "<div class='target-lock soft-lock'></div><small>"
        f"{html.escape(label)}"
        "</small><div class='metric-value-row'><h3>"
        f"{html.escape(str(value))}"
        "</h3><span class='metric-badge'>SYNC</span></div>"
        f"{trend_strip(trend_tone)}"
        "<p class='metric-foot'>"
        f"{html.escape(detail)}"
        "</p></div>"
    )


def panel_intro(label: str, title: str, copy: str) -> None:
    st.markdown(
        (
            "<div class='section-shell section-shell--hud tab-intro soft-shell'>"
            f"{panel_corners()}"
            "<div class='shell-label'>"
            f"{html.escape(label)}"
            "</div><h3 class='shell-title'>"
            f"{html.escape(title)}"
            "</h3><p class='shell-copy'>"
            f"{html.escape(copy)}"
            "</p>"
            f"{signal_rail(4)}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def api_get(path: str):
    try:
        response = requests.get(f"{BACKEND}{path}", timeout=10)
        return response.json() if response.status_code == 200 else None
    except requests.RequestException:
        return None


def api_post(path: str, body: dict):
    return requests.post(f"{BACKEND}{path}", json=body, timeout=600)


def render_login() -> None:
    st.markdown("<div class='login-layout-shell'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.08, 0.92], gap="large")
    with left:
        st.markdown(
            """
            <div class="login-hero login-hero--signal soft-shell">
                <div class="hero-kicker"><span class="status-beacon"></span>SECURE ACCESS CONTROL</div>
                <h1>🛡️ SBOM 核心控制台</h1>
                <p>
                    进入供应链安全指挥台，集中查看 SBOM 资产、漏洞暴露、源码告警与历史扫描记录。
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <div class="login-form-shell">
                <div class="login-form-note">使用现有控制台账号登录，进入后将直接打开新的安全指挥台首页。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            st.markdown("#### 身份验证")
            user = st.text_input("用户名")
            pwd = st.text_input("密码", type="password")
            submitted = st.form_submit_button("进入控制台", use_container_width=True)
            if submitted:
                if user == _CRED_USER and pwd == _CRED_PASS:
                    st.session_state.logged_in = True
                    st.rerun()
                st.error("凭证无效，请重试。")
    st.stop()


inject_styles()
inject_motion_styles()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    render_login()

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-shell">
            <h3>🛠️ 扫描中控台</h3>
            <p>输入待检测路径或镜像目标，触发一次新的供应链安全巡检，页面会自动刷新最新结果。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    scan_target = st.text_input("探测目标", placeholder="/home/ubuntu/vuln-target")

    if st.button("启动扫描", use_container_width=True, type="primary"):
        if scan_target:
            progress = st.empty()
            log_area = st.empty()
            scan_job = idle_scan_job(scan_target)
            progress.markdown(scan_vector_matrix(scan_job), unsafe_allow_html=True)
            log_area.markdown(render_scan_job_log(scan_job.get("logs", [])), unsafe_allow_html=True)

            try:
                response = api_post("/api/scan-jobs", {"path": scan_target})
                if response.status_code != 200:
                    st.error("ERR: {}".format(response.json().get("detail", response.text[:200])))
                else:
                    scan_job = response.json()
                    while True:
                        progress.markdown(scan_vector_matrix(scan_job), unsafe_allow_html=True)
                        log_area.markdown(
                            render_scan_job_log(scan_job.get("logs", [])),
                            unsafe_allow_html=True,
                        )

                        if scan_job.get("status") == "completed":
                            st.success("扫描完成，面板正在刷新。")
                            time.sleep(0.5)
                            st.rerun()

                        if scan_job.get("status") == "failed":
                            st.error("ERR: {}".format(scan_job.get("error") or scan_job.get("message", "Unknown error")))
                            break

                        time.sleep(0.65)
                        job_id = scan_job.get("job_id")
                        latest_job = api_get(f"/api/scan-jobs/{job_id}") if job_id else None
                        if latest_job is None:
                            st.error("ERR: 无法获取实时扫描状态。")
                            break
                        scan_job = latest_job
            except Exception as exc:  # pragma: no cover
                st.error(str(exc))

history_data = api_get("/api/history")
history = history_data.get("reports", []) if history_data else []
health_data = api_get("/health") or {}

latest_report = history[0] if history else {}
backend_version = health_data.get("version", "unknown")
latest_target = latest_report.get("target", "等待新的扫描任务")
latest_scan_time = latest_report.get("scanned_at", "暂无记录")

st.markdown(
    textwrap.dedent(
        f"""
    <div class="command-center-shell command-center-shell--main report-shell--hud soft-shell soft-shell-muted">
        {hud_corners()}
        <div class="shell-grid">
            <div>
                <div class="hero-kicker"><span class="status-beacon"></span>COMMAND CENTER ONLINE</div>
                <h1 class="hero-title">SBOM 核心控制台</h1>
                <p class="hero-subtitle">
                    面向供应链扫描、漏洞聚合、源码安全告警与实验历史追踪的统一安全指挥台。
                </p>
                <div class="hero-chip-row">
                    <span class="status-chip"><span class="status-beacon"></span>LIVE</span>
                    <span class="status-chip status-chip--cyan">HISTORY {len(history)}</span>
                    <span class="status-chip status-chip--amber">BACKEND v{html.escape(str(backend_version))}</span>
                </div>
                {signal_rail(4, "warm-signal")}
                <div class="hero-data-rack">
                    <div class="rack-cell">{panel_corners()}<small>SCAN STATUS</small><strong>{html.escape(str(health_data.get("status", "unknown")).upper())}</strong></div>
                    <div class="rack-cell">{panel_corners()}<small>FOCUS TARGET</small><strong>{html.escape(str(latest_target))}</strong></div>
                    <div class="rack-cell">{panel_corners()}<small>REPORT CLOCK</small><strong>{html.escape(str(latest_scan_time))}</strong></div>
                </div>
            </div>
            <div class="hero-side soft-shell report-shell--active report-sync-shell">
                {panel_corners()}
                <div class="radar-sweep"></div>
                <div class="pulse-orbit"></div>
                <div class="target-lock soft-lock"></div>
                <div class="resource-ring"></div>
{hero_asset_mesh().strip()}
{telemetry_band("warm")}
<div class="side-label">运行态概览</div>
<div class="side-stat"><span>最新目标</span><strong>{html.escape(str(latest_target))}</strong></div>
<div class="side-stat"><span>最近扫描</span><strong>{html.escape(str(latest_scan_time))}</strong></div>
<div class="side-stat"><span>报告总数</span><strong>{len(history)}</strong></div>
<div class="side-stat"><span>后端状态</span><strong>{html.escape(str(health_data.get("status", "unknown")).upper())}</strong></div>
{signal_rail(3, "warm-signal")}
            </div>
        </div>
    </div>
    """,
    ).strip(),
    unsafe_allow_html=True,
)

if not history:
    st.markdown(
        f"""
        <div class="section-shell section-shell--hud soft-shell">
            {panel_corners()}
            <div class="shell-label">No Reports Yet</div>
            <h3 class="shell-title">当前还没有可展示的扫描报告</h3>
            <p class="shell-copy">先在左侧中控台输入目标并启动扫描，完成后这里会自动切换到最新结果。</p>
            {signal_rail(4)}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

report_labels = ["{}  |  {}".format(item["report_id"], item["target"]) for item in history]

if "selected_idx" not in st.session_state:
    st.session_state.selected_idx = 0

st.markdown(
    f"""
    <div class="report-shell report-shell--hud report-sync-shell soft-shell soft-shell-muted">
        {hud_corners()}
        <div class="shell-label">Report Switchboard</div>
        <h3 class="shell-title">全局报告切换</h3>
        <p class="shell-copy">切换报告编号后，下方所有指标、漏洞、源码审计和历史表格都会同步刷新。</p>
        {signal_rail(4)}
    </div>
    """,
    unsafe_allow_html=True,
)

selected_idx = st.selectbox(
    "当前报告",
    range(len(report_labels)),
    format_func=lambda idx: report_labels[idx],
    index=st.session_state.selected_idx,
    key="report_selector",
)
st.session_state.selected_idx = selected_idx
chosen_id = history[selected_idx]["report_id"]

report = api_get(f"/api/history/{chosen_id}")
if not report:
    st.error(f"无法加载报告: {chosen_id}")
    st.stop()

scan_info = report.get("scan_info", {})
vuln_summary = report.get("vulnerabilities", {}).get("summary", {})
vuln_details = report.get("vulnerabilities", {}).get("details", [])
static_findings = report.get("static_analysis", [])
policy = report.get("policy", {})

files_scanned = scan_info.get("files_scanned", 0)
component_count = scan_info.get("component_count", 0)
vuln_count = vuln_summary.get("total", 0)
sast_count = len(static_findings)

st.markdown(
    f"""
    <div class="report-shell command-center-shell report-shell--hud report-shell--active report-sync-shell soft-shell soft-shell-muted">
        {hud_corners()}
        <div class="shell-label">Selected Report</div>
        <h3 class="shell-title">{html.escape(chosen_id)}</h3>
        <p class="shell-copy">当前页面聚焦于 <strong>{html.escape(str(report.get("target", "-")))}</strong> 的扫描结果。</p>
        {signal_rail(4)}
        <div class="report-meta-grid">
            <div class="meta-cell">{panel_corners()}<small>TARGET</small><strong>{html.escape(str(report.get("target", "-")))}</strong></div>
            <div class="meta-cell">{panel_corners()}<small>SCANNED_AT</small><strong>{html.escape(str(report.get("scanned_at", "-")))}</strong></div>
            <div class="meta-cell">{panel_corners()}<small>DURATION</small><strong>{html.escape(str(report.get("duration_seconds", "-")))} s</strong></div>
            <div class="meta-cell">{panel_corners()}<small>POLICY</small><strong>{html.escape(str(policy.get("status", "UNKNOWN")))}</strong></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(render_metric_card("FILES_SCANNED", files_scanned, "扫描覆盖的文件数量"), unsafe_allow_html=True)
with c2:
    st.markdown(render_metric_card("COMPONENTS", component_count, "SBOM 提取出的依赖组件资产"), unsafe_allow_html=True)
with c3:
    st.markdown(render_metric_card("CVE_COUNT", vuln_count, "依赖链中命中的已知漏洞总数", tone="danger"), unsafe_allow_html=True)
with c4:
    st.markdown(render_metric_card("SAST_HITS", sast_count, "静态代码审计发现的问题条目"), unsafe_allow_html=True)

st.markdown(f"<div class='hud-tab-frame'>{hud_corners()}</div>", unsafe_allow_html=True)
tab_sbom, tab_cve, tab_sast, tab_graph, tab_hist = st.tabs(
    [
        "1.资产透视(SBOM)",
        "2.风险匹配(CVE)",
        "3.源码审计(SAST)",
        "4.依赖拓扑(Graph)",
        "5.实验记录(History)",
    ]
)

with tab_sbom:
    panel_intro("Asset View", "组件资产与策略门禁", "查看组件资产结构、目标信息与策略门禁结论。")
    col_l, col_r = st.columns([1.8, 1])
    with col_l:
        if vuln_details:
            df = pd.DataFrame(vuln_details)[["component", "version", "severity"]].drop_duplicates()
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.markdown(
                f"<div class='empty-panel'>{panel_corners()}Syft 未提取到带版本号的组件，请确认目标目录包含可识别的依赖清单。</div>",
                unsafe_allow_html=True,
            )
    with col_r:
        status = policy.get("status", "UNKNOWN")
        color = "#7EE787" if status == "PASS" else "#F85149"
        gate_class = "policy-gate policy-gate--pass report-sync-shell" if status == "PASS" else "policy-gate policy-gate--fail policy-gate--warm report-sync-shell"
        reasons = policy.get("reasons", []) or ["未触发显式阻断原因。"]
        reasons_html = "".join([f"<div>• {html.escape(reason)}</div>" for reason in reasons])
        st.markdown(
            f"""
            <div class="{gate_class}">
                {panel_corners()}
                <div class="shell-label">Policy Gate</div>
                <h2 style="color:{color}">{html.escape(status)}</h2>
                <p>综合依赖漏洞与源码审计结论后的本次门禁结果。</p>
                {signal_rail(3)}
                <div class="reason-list">{reasons_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with tab_cve:
    panel_intro("Threat Profile", "漏洞画像与修复建议", "按组件与严重级别浏览漏洞命中详情。")
    if not vuln_details:
        st.markdown(
            f"<div class='empty-panel'>{panel_corners()}当前报告未发现可展示的依赖漏洞命中。</div>",
            unsafe_allow_html=True,
        )
    else:
        for vuln in vuln_details:
            expander_title = "[{}] {} | {} @ {}".format(
                vuln.get("severity", "?"),
                vuln.get("cve_id", "UNKNOWN"),
                vuln.get("component", "unknown"),
                vuln.get("version", "-"),
            )
            with st.expander(expander_title):
                st.markdown("**DESC**: {}".format(vuln.get("description", "N/A")))
                st.markdown(
                    "**CVSS**: `{}` | **VECTOR**: `{}` | **SOURCE**: `{}`".format(
                        vuln.get("cvss_score", "N/A"),
                        vuln.get("cvss_vector", "N/A"),
                        vuln.get("source", "N/A"),
                    )
                )
                fix_versions = ", ".join(vuln.get("fix_versions") or ["NONE"])
                st.markdown(f"**FIX**: `{fix_versions}`")
                if vuln.get("ai_fix"):
                    st.info(vuln["ai_fix"])

with tab_sast:
    panel_intro("Source Audit", "源码告警与风险位置", "聚焦 Semgrep 返回的代码告警与风险位置。")
    if not static_findings:
        st.markdown(
            f"<div class='empty-panel'>{panel_corners()}当前报告没有新的 SAST 告警命中。</div>",
            unsafe_allow_html=True,
        )
    else:
        for finding in static_findings:
            title = "{} | {}:{} | {}".format(
                finding.get("severity", "?"),
                finding.get("file", "unknown"),
                finding.get("line", "?"),
                finding.get("rule_id", "unknown"),
            )
            with st.expander(title):
                st.code(finding.get("content", ""), language="python")
                st.markdown("**MSG**: {}".format(finding.get("message", "N/A")))
                if finding.get("ai_fix"):
                    st.info(finding["ai_fix"])

with tab_graph:
    panel_intro("Dependency Graph", "高风险依赖拓扑", "轻量展示主要组件关系，优先高亮风险依赖点。")
    net = Network(height="480px", width="100%", bgcolor="transparent", font_color="#C9D1D9", directed=True)
    net.add_node("root", label="TARGET", color="#58A6FF", size=22)
    seen = set()
    for vuln in vuln_details[:50]:
        name = vuln.get("component", "unknown")
        if name in seen:
            continue
        seen.add(name)
        severity = vuln.get("severity", "LOW")
        if severity in ("CRITICAL", "HIGH"):
            node_color = "#F85149"
        elif severity == "MEDIUM":
            node_color = "#D29922"
        else:
            node_color = "#30363D"
        net.add_node(name, label=name, color=node_color, size=14)
        net.add_edge("root", name, color="#21262D", width=0.5)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        components.html(Path(tmp.name).read_text(encoding="utf-8"), height=520)

with tab_hist:
    panel_intro("History Matrix", "实验记录与全局追踪", "查看所有历史报告的目标、时间、漏洞规模与门禁结果。")
    if history:
        df_history = pd.DataFrame(history)
        column_order = [
            "report_id",
            "target",
            "scanned_at",
            "policy_status",
            "files_scanned",
            "component_count",
            "total_vulns",
            "critical",
            "high",
        ]
        existing = [column for column in column_order if column in df_history.columns]
        st.dataframe(df_history[existing], use_container_width=True, hide_index=True)
