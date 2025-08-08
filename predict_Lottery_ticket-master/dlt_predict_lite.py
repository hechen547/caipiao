#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import csv
import argparse
from typing import Dict, Any, List

from config import name_path, data_file_name

MODEL_DIR = os.path.join("model", "dlt", "lite")
MODEL_PATH = os.path.join(MODEL_DIR, "lite_model.json")


def ensure_dirs():
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)


def load_dlt_rows() -> List[Dict[str, str]]:
    csv_path = os.path.join(name_path["dlt"]["path"], data_file_name)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"未找到本地数据文件: {csv_path}")
    # try common chinese encodings
    encodings = ["utf-8", "gbk", "gb2312"]
    last_err = None
    for enc in encodings:
        try:
            with open(csv_path, "r", encoding=enc) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            return rows
        except Exception as e:
            last_err = e
            continue
    raise last_err


def compute_frequencies(rows: List[Dict[str, str]]) -> Dict[str, Dict[int, int]]:
    red_cols = [f"红球_{i}" for i in range(1, 6)]
    blue_cols = [f"蓝球_{i}" for i in range(1, 3)]

    red_counts: Dict[int, int] = {}
    for col in red_cols:
        for row in rows:
            if col in row and row[col]:
                try:
                    val = int(row[col])
                except Exception:
                    continue
                red_counts[val] = red_counts.get(val, 0) + 1

    blue_counts: Dict[int, int] = {}
    for col in blue_cols:
        for row in rows:
            if col in row and row[col]:
                try:
                    val = int(row[col])
                except Exception:
                    continue
                blue_counts[val] = blue_counts.get(val, 0) + 1

    return {"red": red_counts, "blue": blue_counts}


def pick_top_k(counts: Dict[int, int], k: int) -> List[int]:
    return [n for n, _ in sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:k]]


def train() -> None:
    ensure_dirs()
    rows = load_dlt_rows()
    freqs = compute_frequencies(rows)
    with open(MODEL_PATH, "w", encoding="utf-8") as f:
        json.dump(freqs, f, ensure_ascii=False)
    print(f"[lite] 训练完成，已保存：{MODEL_PATH}")


def predict() -> Dict[str, Any]:
    if not os.path.exists(MODEL_PATH):
        train()
    with open(MODEL_PATH, "r", encoding="utf-8") as f:
        freqs = json.load(f)
    red_top5 = pick_top_k({int(k): int(v) for k, v in freqs.get("red", {}).items()}, 5)
    blue_top2 = pick_top_k({int(k): int(v) for k, v in freqs.get("blue", {}).items()}, 2)
    # 若数据不足，填充最小的未出现号码，保证数量
    def fill_missing(seq: List[int], need: int, max_num: int) -> List[int]:
        s = set(seq)
        for n in range(1, max_num + 1):
            if len(seq) >= need:
                break
            if n not in s:
                seq.append(n)
        return seq[:need]
    red_top5 = fill_missing(red_top5, 5, 35)
    blue_top2 = fill_missing(blue_top2, 2, 12)

    result = {**{f"红球_{i}": red_top5[i - 1] for i in range(1, 6)},
              **{f"蓝球_{i}": blue_top2[i - 1] for i in range(1, 3)}}
    print("预测结果：{}".format(result))
    return result


message = "DLT Lite Trainer/ Predictor"

def main():
    parser = argparse.ArgumentParser(description=message)
    parser.add_argument("--mode", choices=["train", "predict"], default="predict")
    args = parser.parse_args()
    if args.mode == "train":
        train()
    else:
        predict()


if __name__ == "__main__":
    main()