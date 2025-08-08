#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import threading
import subprocess
import shlex
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

# Project root
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
PYTHON = shlex.quote(sys.executable)


def run_cmd(args, on_line=None, on_done=None):
    """Run a command and stream output to callbacks."""
    try:
        proc = subprocess.Popen(
            args,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            bufsize=1,
            universal_newlines=True,
        )
        for line in iter(proc.stdout.readline, ""):
            if on_line:
                on_line(line.rstrip("\n"))
        proc.stdout.close()
        returncode = proc.wait()
        if on_done:
            on_done(returncode)
    except Exception as e:
        if on_line:
            on_line(f"[ERROR] {e}")
        if on_done:
            on_done(1)


def format_ts():
    return datetime.datetime.now().strftime("%H:%M:%S")


class DltGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("大乐透预测 - 桌面版")
        self.geometry("820x560")
        self.minsize(820, 560)
        self._build_widgets()
        self._set_state_idle()

    def _build_widgets(self):
        # Controls frame
        ctrl = ttk.Frame(self)
        ctrl.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Options
        self.var_refresh = tk.BooleanVar(value=False)
        self.var_force_train = tk.BooleanVar(value=False)
        self.var_predict_only = tk.BooleanVar(value=False)
        self.var_split = tk.StringVar(value="0.8")

        ttk.Checkbutton(ctrl, text="刷新数据", variable=self.var_refresh).grid(row=0, column=0, padx=6)
        ttk.Checkbutton(ctrl, text="强制重训", variable=self.var_force_train).grid(row=0, column=1, padx=6)
        ttk.Checkbutton(ctrl, text="只预测", variable=self.var_predict_only).grid(row=0, column=2, padx=6)

        ttk.Label(ctrl, text="训练集比例").grid(row=0, column=3, padx=(18, 6))
        self.ent_split = ttk.Entry(ctrl, width=6, textvariable=self.var_split)
        self.ent_split.grid(row=0, column=4, padx=6)

        # Buttons
        self.btn_fetch = ttk.Button(ctrl, text="抓取数据", command=self.on_fetch)
        self.btn_train = ttk.Button(ctrl, text="训练", command=self.on_train)
        self.btn_predict = ttk.Button(ctrl, text="预测", command=self.on_predict)
        self.btn_oneclick = ttk.Button(ctrl, text="一键运行", command=self.on_oneclick)
        self.btn_fetch.grid(row=1, column=0, padx=6, pady=10, sticky=tk.W+tk.E)
        self.btn_train.grid(row=1, column=1, padx=6, pady=10, sticky=tk.W+tk.E)
        self.btn_predict.grid(row=1, column=2, padx=6, pady=10, sticky=tk.W+tk.E)
        self.btn_oneclick.grid(row=1, column=3, columnspan=2, padx=6, pady=10, sticky=tk.W+tk.E)

        ctrl.grid_columnconfigure(4, weight=1)

        # Log panel
        self.log = ScrolledText(self, wrap=tk.WORD, height=26)
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.log.tag_config("ts", foreground="#888888")
        self.log.tag_config("info", foreground="#222222")
        self.log.tag_config("warn", foreground="#b58900")
        self.log.tag_config("error", foreground="#dc322f")

    def _append_log(self, text, tag="info"):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, f"[{format_ts()}] ", ("ts",))
        self.log.insert(tk.END, text + "\n", (tag,))
        self.log.configure(state=tk.DISABLED)
        self.log.see(tk.END)
        self.update_idletasks()

    def _set_state_busy(self):
        for b in (self.btn_fetch, self.btn_train, self.btn_predict, self.btn_oneclick):
            b.configure(state=tk.DISABLED)
        self.ent_split.configure(state=tk.DISABLED)

    def _set_state_idle(self):
        for b in (self.btn_fetch, self.btn_train, self.btn_predict, self.btn_oneclick):
            b.configure(state=tk.NORMAL)
        self.ent_split.configure(state=tk.NORMAL)

    def _validate_split(self):
        try:
            val = float(self.var_split.get())
            if 0.5 <= val < 1.0:
                return val
        except Exception:
            pass
        messagebox.showwarning("参数错误", "训练集比例需为0.5~1.0之间的小数，例如 0.8")
        return None

    def _run_async(self, target, *args):
        self._set_state_busy()
        threading.Thread(target=self._wrap_run, args=(target, *args), daemon=True).start()

    def _wrap_run(self, target, *args):
        try:
            target(*args)
        finally:
            self.after(0, self._set_state_idle)

    # Actions
    def on_fetch(self):
        self._run_async(self._do_fetch)

    def _do_fetch(self):
        self._append_log("开始抓取大乐透历史数据...")
        cmd = [PYTHON, os.path.join(PROJECT_ROOT, "get_data.py"), "--name", "dlt"]
        def on_line(line):
            self._append_log(line)
        def on_done(code):
            if code == 0:
                self._append_log("抓取完成", tag="info")
            else:
                self._append_log(f"抓取失败，退出码 {code}", tag="error")
        run_cmd(cmd, on_line, on_done)

    def on_train(self):
        split = self._validate_split()
        if split is None:
            return
        self._run_async(self._do_train, split)

    def _do_train(self, split):
        self._append_log("开始训练大乐透模型...")
        cmd = [PYTHON, os.path.join(PROJECT_ROOT, "run_train_model.py"), "--name", "dlt", "--train_test_split", str(split)]
        def on_line(line):
            self._append_log(line)
        def on_done(code):
            if code == 0:
                self._append_log("训练完成", tag="info")
            else:
                self._append_log(f"训练失败，退出码 {code}", tag="error")
        run_cmd(cmd, on_line, on_done)

    def on_predict(self):
        self._run_async(self._do_predict)

    def _do_predict(self):
        self._append_log("开始运行预测...")
        cmd = [PYTHON, os.path.join(PROJECT_ROOT, "run_predict.py"), "--name", "dlt"]
        def on_line(line):
            self._append_log(line)
        def on_done(code):
            if code == 0:
                self._append_log("预测完成", tag="info")
            else:
                self._append_log(f"预测失败，退出码 {code}", tag="error")
        run_cmd(cmd, on_line, on_done)

    def on_oneclick(self):
        split = self._validate_split()
        if split is None:
            return
        refresh = self.var_refresh.get()
        force = self.var_force_train.get()
        predict_only = self.var_predict_only.get()
        self._run_async(self._do_oneclick, refresh, force, predict_only, split)

    def _do_oneclick(self, refresh, force, predict_only, split):
        self._append_log("开始一键运行...")
        # Compose command
        cmd = [PYTHON, os.path.join(PROJECT_ROOT, "dlt_predict_app.py")]
        if refresh:
            cmd.append("--refresh-data")
        if force:
            cmd.append("--force-train")
        if predict_only:
            cmd.append("--predict-only")
        cmd.extend(["--train-test-split", str(split)])

        def on_line(line):
            self._append_log(line)
        def on_done(code):
            if code == 0:
                self._append_log("一键运行完成", tag="info")
            else:
                self._append_log(f"一键运行失败，退出码 {code}", tag="error")
        run_cmd(cmd, on_line, on_done)


def main():
    app = DltGUI()
    app.mainloop()


if __name__ == "__main__":
    main()