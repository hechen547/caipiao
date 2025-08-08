#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import subprocess
import shlex
import re
import ast
from typing import Dict, Any

# Reuse config constants without importing heavy frameworks
try:
    from config import model_args, model_path
except Exception:
    # Fallback if import path differs
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import model_args, model_path


def absolute(path: str) -> str:
    return os.path.abspath(path)


def file_exists(path: str) -> bool:
    return os.path.exists(path) and os.path.isfile(path)


def ensure_data_for_dlt(project_root: str) -> None:
    script = absolute(os.path.join(project_root, "get_data.py"))
    cmd = f"{shlex.quote(sys.executable)} {shlex.quote(script)} --name dlt"
    subprocess.run(cmd, shell=True, check=True, cwd=project_root)


def models_present_for_dlt(project_root: str) -> bool:
    red_meta = os.path.join(project_root, "model", "dlt", "red_ball_model", "red_ball_model.ckpt.meta")
    blue_meta = os.path.join(project_root, "model", "dlt", "blue_ball_model", "blue_ball_model.ckpt.meta")
    return file_exists(red_meta) and file_exists(blue_meta)


def train_models_for_dlt(project_root: str, train_test_split: float) -> None:
    script = absolute(os.path.join(project_root, "run_train_model.py"))
    cmd = (
        f"{shlex.quote(sys.executable)} {shlex.quote(script)} --name dlt "
        f"--train_test_split {train_test_split}"
    )
    subprocess.run(cmd, shell=True, check=True, cwd=project_root)


def run_prediction_for_dlt(project_root: str) -> str:
    script = absolute(os.path.join(project_root, "run_predict.py"))
    cmd = f"{shlex.quote(sys.executable)} {shlex.quote(script)} --name dlt"
    proc = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=project_root)
    return proc.stdout.decode("utf-8", errors="ignore")


def extract_prediction_from_output(output: str) -> Dict[str, Any]:
    # Expect a line like: 预测结果：{'红球_1': 1, '红球_2': 2, ..., '蓝球_2': 12}
    m = re.search(r"预测结果：(\{.*?\})", output, re.S)
    if not m:
        return {}
    text = m.group(1)
    try:
        return ast.literal_eval(text)
    except Exception:
        return {}


def format_dlt_prediction(pred: Dict[str, Any]) -> str:
    if not pred:
        return "未能解析预测结果，请检查依赖与模型是否正确安装/训练。"
    red = [pred.get(f"红球_{i}") for i in range(1, 6)]
    blue = [pred.get(f"蓝球_{i}") for i in range(1, 3)]
    red = [x for x in red if isinstance(x, int)]
    blue = [x for x in blue if isinstance(x, int)]
    red_sorted = " ".join(f"{n:02d}" for n in sorted(red)) if red else "--"
    blue_sorted = " ".join(f"{n:02d}" for n in sorted(blue)) if blue else "--"
    return (
        "\n===== 大乐透预测结果 =====\n"
        f"红球(5): {red_sorted}\n"
        f"蓝球(2): {blue_sorted}\n"
    )


def main():
    parser = argparse.ArgumentParser(description="DLT Predictor (one-click)")
    parser.add_argument("--refresh-data", action="store_true", help="重新抓取数据（训练前执行）")
    parser.add_argument("--force-train", action="store_true", help="无论是否已有模型，强制重新训练")
    parser.add_argument("--predict-only", action="store_true", help="只进行预测（要求已有模型）")
    parser.add_argument("--train-test-split", type=float, default=0.8, help="训练集比例，默认0.8")
    args = parser.parse_args()

    project_root = absolute(os.path.dirname(__file__))

    if args.refresh_data and not args.predict_only:
        print("[1/3] 正在抓取大乐透历史数据...")
        ensure_data_for_dlt(project_root)

    need_train = args.force_train or (not models_present_for_dlt(project_root))

    if need_train and args.predict_only:
        print("未发现已训练模型，且指定了只预测。请先训练或去掉 --predict-only。")
        sys.exit(2)

    if need_train:
        if not args.refresh_data:
            print("[1/3] 未发现模型，先抓取大乐透历史数据...")
            ensure_data_for_dlt(project_root)
        print("[2/3] 正在训练大乐透模型...（可能耗时较久）")
        train_models_for_dlt(project_root, args.train_test_split)
    else:
        print("已发现已训练模型，跳过训练。")

    print("[3/3] 正在运行预测...")
    output = run_prediction_for_dlt(project_root)
    pred = extract_prediction_from_output(output)
    print(format_dlt_prediction(pred))


if __name__ == "__main__":
    main()