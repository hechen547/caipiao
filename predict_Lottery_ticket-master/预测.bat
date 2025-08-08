@echo off
:: 核心修复命令：将当前窗口的编码格式切换为 UTF-8
chcp 65001 > nul

echo.
echo =======================================================
echo ==          欢迎使用彩票号码 AI 预测工具             ==
echo =======================================================
echo.
echo 正在查找并启动 Anaconda 环境，请稍候...
echo.

:: 您的 Anaconda 安装路径
set ANACONDA_PATH=H:\python

:: --- 以下代码无需修改 ---
call "%ANACONDA_PATH%\Scripts\activate.bat" lottery_env

:: 检查环境是否成功激活
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo !!! 错误：无法激活 lottery_env 环境！!!!
    echo.
    echo 请检查：
    echo 1. 上方的 ANACONDA_PATH 路径是否填写正确？
    echo 2. 您是否已经成功创建了名为 lottery_env 的环境？
    echo.
    pause
    exit
)

echo.
echo 环境已成功激活，正在为您预测【双色球】...
echo.

python run_predict.py --name ssq

echo.
echo -------------------------------------------------------
echo.
echo 预测完成！请查看上面的结果。
echo.
echo 按任意键退出此窗口。
pause >nul