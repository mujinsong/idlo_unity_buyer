import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from pathlib import Path


def load_setting() -> dict:
    """从同目录下的 setting.json 读取接口配置。"""
    setting_path = Path(__file__).with_name("setting.json")
    try:
        with open(setting_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        raise ValueError("setting.json 内容必须是 JSON 对象")
    except FileNotFoundError:
        print("未找到 setting.json，请确认文件已放在同目录下。")
        return {}
    except json.JSONDecodeError as exc:
        print(f"读取 setting.json 失败：JSON 格式错误 ({exc})")
        return {}
    except Exception as exc:
        print(f"读取 setting.json 失败：{exc}")
        return {}


_setting = load_setting()

access_token = _setting.get("access_token", "")
meid = _setting.get("meid", "")
app_type = _setting.get("app_type", "android")
os = _setting.get("os", "android_15")
device_brand = _setting.get("device_brand", "")
v = _setting.get("v", "android_105")
channel = _setting.get("channel", "common")
network_status = _setting.get("network_status", "wifi")
app_type_name = _setting.get("app_type_name", "安卓")

header = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept-Encoding": "gzip",
    "User-Agent": "okhttp/4.2.2",
}


def get_goods_list():
    url = "http://shop.idolunity.com/bxapi/Goodssku/getRecommandGoodsLists"

    body = {
        "is_platform_recommand": 0,
        "is_recommand": 1,
        "site_id": 115,  # todo:存疑点，可能需要改
        "page": 1,
        "page_size": 10,
    }
    response = requests.post(url, data=body, headers=header)
    if response.status_code == 200:
        data = response.json()
        # print("请求get_goods_list成功！返回数据如下：")
        # print(data)
        return data.get("data", {}).get("list", [])  # 返回商品列表
    else:
        print(f"请求get_goods_list失败，状态码: {response.status_code}")
        print(response.text)
        return []  # 请求失败时返回空列表


def get_goods_detail(sku_id: int):
    url = "http://shop.idolunity.com/bxapi/Goodssku/getGoodsDetail"
    body = {
        "access_token": access_token,
        "meid": meid,
        "app_type": app_type,
        "os": os,
        "device_brand": device_brand,
        "v": v,
        "channel": channel,
        "network_status": network_status,
        "app_type_name": app_type_name,
        "sku_id": sku_id,  # todo：这里需要替换成实际的sku_id，可以从get_goods_list接口的返回数据中获取到
    }
    response = requests.post(url, data=body, headers=header)
    if response.status_code == 200:
        data = response.json()
        print("请求成功！返回数据如下：")
        # print(data)
        return data.get("data", {})  # 返回商品详情

    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(response.text)
        return {}  # 请求失败时返回空字典


def get_sku_basic_info(sku_id: int):
    """获取sku_id的基本信息，如商品名称等"""
    url = "http://shop.idolunity.com/bxapi/Goodssku/getGoodSkuBasicInfo"

    body = {
        "access_token": access_token,
        "meid": meid,
        "app_type": app_type,
        "os": os,
        "device_brand": device_brand,
        "v": v,
        "channel": channel,
        "network_status": network_status,
        "app_type_name": app_type_name,
        "sku_id": sku_id,
    }
    response = requests.post(url, data=body, headers=header)
    if response.status_code == 200:
        data = response.json()
        return data.get("data", {})  # 返回商品基本信息
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(response.text)
        return {}  # 请求失败时返回空字典


def get_wait_pay_order_info(sku_id: int):
    url = "http://shop.idolunity.com/bxapi/Ordercreate/getWaitPayOrderInfo"

    body = {
        "access_token": access_token,
        "meid": meid,
        "app_type": app_type,
        "os": os,
        "device_brand": device_brand,
        "v": v,
        "coupon": {},
        "channel": channel,
        "network_status": network_status,
        "app_type_name": app_type_name,
        "num": 1,
        "sku_id": sku_id,
    }
    response = requests.post(url, data=body, headers=header)
    if response.status_code == 200:
        data = response.json()
        return data.get("data", {})  # 返回待支付订单信息
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(response.text)
        return {}  # 请求失败时返回空字典


def cal_order_info(sku_id: int):
    url = "http://shop.idolunity.com/bxapi/Ordercreate/calOrderData"
    body = {
        "access_token": access_token,
        "meid": meid,
        "app_type": app_type,
        "os": os,
        "device_brand": device_brand,
        "v": v,
        "channel": channel,
        "network_status": network_status,
        "app_type_name": app_type_name,
        "num": 1,
        "sku_id": sku_id,
    }
    response = requests.post(url, data=body, headers=header)
    if response.status_code == 200:
        data = response.json()
        return data.get("data", {})  # 返回订单信息
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(response.text)
        return {}  # 请求失败时返回空字典


def create_order(sku_id: int, member_address: str, buyer_message: dict[str, str]):
    url = "http://shop.idolunity.com/bxapi/Ordercreate/create"
    body = {
        "access_token": access_token,
        "meid": meid,
        "app_type": app_type,
        "os": os,
        "device_brand": device_brand,
        "v": v,
        "channel": channel,
        "network_status": network_status,
        "app_type_name": app_type_name,
        "member_address": member_address,
        "buyer_message": buyer_message,
        "num": 1,
        "sku_id": sku_id,
        # 订单创建接口需要的其他参数，如地址信息、支付方式等，这里需要根据实际情况进行补充
    }
    response = requests.post(url, data=body, headers=header)
    if response.status_code == 200:
        data = response.json()
        # print(f"订单创建结果: {data}")
        if data.get("code") != 0:
            return data  # 订单创建失败时返回错误信息
        return data.get("data", {})  # 返回订单创建结果
    else:
        print(f"请求失败，状态码: {response.status_code}")
        # print(response.text)
        return {}  # 请求失败时返回空字典


if __name__ == "__main__":
    pass
