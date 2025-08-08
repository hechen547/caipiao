# -*- coding:utf-8 -*-
"""
Author: BigCat
"""
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup
from loguru import logger
from config import os, name_path, data_file_name

parser = argparse.ArgumentParser()
parser.add_argument('--name', default="ssq", type=str, help="选择爬取数据: 双色球/大乐透")
args = parser.parse_args()


def get_url(name):
    """
    :param name: 玩法名称
    :return:
    """
    url = "https://datachart.500.com/{}/history/".format(name)
    path = "newinc/history.php?start={}&end="
    return url, path


def get_current_number(name):
    """ 获取最新一期数字
    :return: int
    """
    url, _ = get_url(name)
    try:
        r = requests.get("{}{}".format(url, "history.shtml"), verify=False, timeout=10)
        r.encoding = "gb2312"
        soup = BeautifulSoup(r.text, "lxml")
        current_num = soup.find("div", class_="wrap_datachart").find("input", id="end")["value"]
        return current_num
    except Exception:
        # Fallback: read last issue number from local CSV if available
        local_csv = os.path.join(os.getcwd(), name_path[name]["path"], data_file_name)
        if os.path.exists(local_csv):
            try:
                df = pd.read_csv(local_csv)
                if "期数" in df.columns and len(df) > 0:
                    return str(int(df.iloc[-1]["期数"]))
            except Exception:
                pass
        raise


def spider(name, start, end, mode):
    """ 爬取历史数据
    :param name 玩法
    :param start 开始一期
    :param end 最近一期
    :param mode 模式，train：训练模式，predict：预测模式（训练模式会保持文件）
    :return:
    """
    url, path = get_url(name)
    try:
        url = "{}{}{}".format(url, path.format(start), end)
        r = requests.get(url=url, verify=False, timeout=10)
        r.encoding = "gb2312"
        soup = BeautifulSoup(r.text, "lxml")
        trs = soup.find("tbody", attrs={"id": "tdata"}).find_all("tr")
        data = []
        for tr in trs:
            item = dict()
            if name == "ssq":
                item[u"期数"] = tr.find_all("td")[0].get_text().strip()
                for i in range(6):
                    item[u"红球_{}".format(i+1)] = tr.find_all("td")[i+1].get_text().strip()
                item[u"蓝球"] = tr.find_all("td")[7].get_text().strip()
                data.append(item)
            elif name == "dlt":
                item[u"期数"] = tr.find_all("td")[0].get_text().strip()
                for i in range(5):
                    item[u"红球_{}".format(i+1)] = tr.find_all("td")[i+1].get_text().strip()
                for j in range(2):
                    item[u"蓝球_{}".format(j+1)] = tr.find_all("td")[6+j].get_text().strip()
                data.append(item)
            else:
                logger.warning("抱歉，没有找到数据源！")
        df = pd.DataFrame(data)
    except Exception:
        # Fallback: use local CSV if available
        local_csv = os.path.join(os.getcwd(), name_path[name]["path"], data_file_name)
        if os.path.exists(local_csv):
            logger.warning("网络抓取失败，回退使用本地数据：{}".format(local_csv))
            df = pd.read_csv(local_csv)
        else:
            raise

    if mode == "train":
        # 保存最新的抓取或本地数据
        if not os.path.exists(name_path[name]["path"]):
            os.makedirs(name_path[name]["path"])
        df.to_csv("{}{}".format(name_path[name]["path"], data_file_name), index=False, encoding="utf-8")
        return df
    elif mode == "predict":
        return df


def run(name):
    """
    :param name: 玩法名称
    :return:
    """
    current_number = get_current_number(name)
    logger.info("【{}】最新一期期号：{}".format(name_path[name]["name"], current_number))
    logger.info("正在获取【{}】数据。。。".format(name_path[name]["name"]))
    if not os.path.exists(name_path[name]["path"]):
        os.makedirs(name_path[name]["path"])
    data = spider(name, 1, current_number, "train")
    if "data" in os.listdir(os.getcwd()):
        logger.info("【{}】数据准备就绪，共{}期, 下一步可训练模型...".format(name_path[name]["name"], len(data)))
    else:
        logger.error("数据文件不存在！")


if __name__ == "__main__":
    if not args.name:
        raise Exception("玩法名称不能为空！")
    else:
        run(name=args.name)
