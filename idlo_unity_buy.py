import requests
import json
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from .idlo_unity_api import (
    get_goods_list,
    get_sku_basic_info,
    cal_order_info,
    create_order,
)

keywords = []  # 需要搜索的关键词列表 生日
birthday_range = (-4, 5)  # 以生日为中心，向前和向后各查询4个sku_id
exclude_sku_ids = []
category = []
buyed_sku_list = []  # 已经购买的sku_id
is_debug = False


def _query_sku(sku_id):
    """单个sku_id查询任务并筛选符合条件的sku_id"""
    if sku_id in buyed_sku_list:
        print(f"sku_id: {sku_id}已购买过，跳过查询")
        return None
    try:
        print(f"正在查询sku_id: {sku_id}的详情...")
        info = get_sku_basic_info(sku_id)
        if is_debug == True:
            print(f"查询到的sku_id: {sku_id}的基本信息: {info}")
        if info and "sku_name" in info:
            sku_name = info.get("sku_name", "")
            if any(keyword in sku_name for keyword in keywords):
                if len(category) == 0 or any(cat in sku_name for cat in category):
                    print(f"sku_id: {sku_id}_{sku_name}符合条件，添加到购买列表")
                    return sku_id

        else:
            print(f"sku_id: {sku_id}的详情信息不完整，无法判断是否符合条件")

    except Exception as e:
        print(f"查询sku_id: {sku_id}时发生异常: {e}")
    return None


def buy_sku(sku_id):
    """执行购买操作的函数，参数是符合条件的sku_id"""
    try:
        print(f"正在尝试购买sku_id: {sku_id}...")
        # 这里需要调用实际的购买接口，以下是一个示例调用
        order_info = cal_order_info(sku_id)
        if order_info:
            print(f"成功下单sku_id: {sku_id}")
        else:
            print(f"下单失败sku_id: {sku_id}")
        if is_debug:
            print(f"订单信息详情:{order_info}")
        address_info = order_info.get("member_address", {}) if order_info else {}
        if not address_info:
            address = ""
        else:
            address = address_info.get("full_address", "") + address_info.get(
                "address", ""
            )
        shop_goods_info = order_info.get("shop_goods_list", {}) if order_info else {}
        site_id_map = {}
        for item in shop_goods_info.keys():
            site_id_map[item] = ""
        # shop_goods_info.keys()[0] if shop_goods_info else "115"
        print(f"提取到的地址: {address}, site_id_str: {site_id_map}")
        create_order_info = create_order(sku_id, address, site_id_map)
        if create_order_info.get("code", 0) != 0:
            print(f"购买sku_id: {sku_id}失败，返回信息: {create_order_info}")
        return create_order_info
    except Exception as e:
        print(f"购买sku_id: {sku_id}时发生异常: {e}")
        traceback.print_exc()


def main():
    good_list = get_goods_list()
    if is_debug:
        print("获取到的商品列表：")
        print(good_list)
    need_sku = []
    buy_sku_id = []
    for good in good_list:
        sku_name = good.get("goods_name", "")
        if any(keyword in sku_name for keyword in keywords):  # 发现keywords在商品名称里
            need_sku.append(
                good.get("sku_id", 0)
            )  # 将对应的sku_id添加到需要查询详情的列表中
    print("需要查询详情的sku_id列表：", need_sku)

    # 构建所有需要查询的sku_id
    all_sku_ids = []
    for sku_id in need_sku:
        for offset in range(*birthday_range):  # range(-4, 5):
            current_sku_id = sku_id + offset
            if (
                current_sku_id > 0
                and current_sku_id not in exclude_sku_ids
                and current_sku_id not in buyed_sku_list
            ):  # 确保sku_id是正数且不在排除列表中
                all_sku_ids.append(current_sku_id)

    # 使用线程池并发查询
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_query_sku, sku_id): sku_id for sku_id in all_sku_ids
        }
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                buy_sku_id.append(result)
            time.sleep(0.2)  # 轻微延迟，避免请求过快被封禁
    # 去重
    buy_sku_id = list(set(buy_sku_id))
    print("符合最终条件的sku_id列表：", buy_sku_id)
    # 开始下单（并发执行）
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(buy_sku, sku_id): sku_id for sku_id in buy_sku_id}
        for future in as_completed(futures):
            sku_id = futures[future]
            res = future.result()
            print(f"购买结果 sku_id={sku_id}: {res}")
            if res:
                buyed_sku_list.append(sku_id)


if __name__ == "__main__":
    # 读取命令行参数
    print("仅可用于学习，不得用于任何商业用途！")
    print(
        "keywords和type会放在一起，只要满足其中一个就会被选中，category则是单独筛选条件，不选没事，选了必须满足category里至少一个才行"
    )
    print("开始解析命令行参数...")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug", default=False, action="store_true", help="启用调试模式，输出更多日志"
    )
    parser.add_argument(
        "--exclude_sku_ids", nargs="*", default=[], help="排除的sku_id列表"
    )
    parser.add_argument(
        "--keywords",
        nargs="*",
        default=["美玥"],
        help="需要抢购的成员的关键词列表,默认是['美玥']",
    )
    parser.add_argument(
        "--type",
        default="生日",
        help="抢购类型,商品大类,如'生日','宿题'等,默认是'生日'",
    )
    parser.add_argument(
        "--category",
        default="",
        help="抢购类别,内部细分类,可选如'三寸','五寸'等,默认所有",
    )

    args = parser.parse_args()
    is_debug = args.debug
    exclude_sku_ids = [int(sku_id) for sku_id in args.exclude_sku_ids]
    keywords.extend(args.keywords)
    keywords.append(args.type)
    if args.category:
        category.append(args.category)

    # x = buy_sku(3209)
    # print(x)
    # exit(0)
    while True:
        try:
            print(f"排除的sku_id列表: {exclude_sku_ids}")
            print(f"关键词列表: {keywords}")
            print(f"类别列表: {category}")
            print(f"已购买的sku_id列表: {buyed_sku_list}")
            print(f"调试模式: {'启用' if is_debug else '禁用'}")
            main()
        except Exception as e:
            print(f"执行main()时发生异常: {e}")
        time.sleep(3)  # 每3秒执行一次

    # 3208, 3209, 3204, 3205
    # x = get_goods_detail(3209)  # 这里的sku_id是一个示例值，需要替换成实际的sku_id
    # print(x)
