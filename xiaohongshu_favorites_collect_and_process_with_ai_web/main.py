
import asyncio
import json

from client_sdk.rpc_client import EAIRPCClient
import os
from pathlib import Path

def get_current_dir():
    try:
        # 如果在脚本中运行，有 __file__
        return Path(__file__).resolve().parent
    except NameError:
        # 如果在交互环境（如 Jupyter 或 REPL），__file__ 不存在
        return Path(os.getcwd()).resolve()

current_dir = get_current_dir()



# 最好用绝对路径，相对路径指的是服务端目录的相对路径，而不是当前客户端的
data_dir = get_current_dir() / "data"
favorite_notes_brief_storage_file = data_dir / "favorite_notes_brief.json"
favorite_notes_details_storage_file = data_dir / "favorite_notes_details.json"
favorite_notes_details_failed_file = data_dir / "favorite_notes_details_failed.json"


def init_file():
    # 笔记数据由我们自己维护，初始哈笔记数据为一个对象
    if not os.path.exists(favorite_notes_brief_storage_file):
        with open(favorite_notes_brief_storage_file, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    if not os.path.exists(favorite_notes_details_storage_file):
        with open(favorite_notes_details_storage_file, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    if not os.path.exists(favorite_notes_details_failed_file):
        with open(favorite_notes_details_failed_file, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

init_file()

async def main():
    # 创建客户端
    client = EAIRPCClient(
        base_url="http://127.0.0.1:8008",  # 服务程序ip+port
        api_key="testkey",  # 与服务程序约定好的API密钥
        webhook_host="127.0.0.1",  # webhook订阅服务，当服务程序成功获取到client所需要的订阅数据时，就会通过webhook调用向此请求发送订阅数据
        webhook_port=0,
    )

    try:
        # 启动客户端
        await client.start()
        print("✅ RPC客户端已启动")


        # chat_result = await client.chat_with_yuanbao(
        #     ask_question="你好，我是小星星",
        #     cookie_ids=["819969a2-9e59-46f5-b0ca-df2116d9c2a0"],
        #     close_page_when_task_finished=True,
        #     conversation_id="f0e31758-0368-4acf-a5bc-94f70d06f930"
        # )
        # print(f"AI回复: {chat_result.get("data")[0].get('last_model_message', 'N/A')}")



        with open(favorite_notes_brief_storage_file, "r", encoding="utf-8") as f:
            favorite_notes_brief = json.load(f)

        # 返回值是 全量笔记/新添加/有更新 的笔记数据，删除暂时没有做
        # storage_file会保存完整数据（包含之前数据以及上面两者）
        brief_notes_res = await client.get_favorite_notes_brief_from_xhs(
            storage_data=json.dumps(favorite_notes_brief),
            max_items=10,
            max_seconds=10**9,
            max_new_items=10,
            cookie_ids=["28ba44f1-bb67-41ab-86f0-a3d049d902aa"]
        )
        if not brief_notes_res["success"]:
            print(f"[get_favorite_notes_brief_from_xhs]执行失败：{brief_notes_res['error']}")
            return

        print(f"[get_favorite_notes_brief_from_xhs]执行成功，耗时：{brief_notes_res.get("exec_elapsed_ms", "null")}ms")

        # 全量笔记保存到本地
        with open(favorite_notes_brief_storage_file, "w", encoding="utf-8") as f:
            json.dump(brief_notes_res, f, ensure_ascii=False, indent=4)

        # 只需要对增量笔记获取详情
        brief_data = brief_notes_res.copy()
        brief_data.pop("added")
        brief_data.pop("updated")
        brief_data["data"] = []
        for item in ["added", "updated"]:
            data = brief_notes_res[item]
            brief_data["data"].extend(data["data"])

        # 返回值中包含笔记详情数据以及获取失败的笔记数据
        details_notes_res = await client.get_notes_details_from_xhs(
            brief_data=json.dumps(brief_data),
            max_items=10,
            max_seconds=10 ** 9,
            max_new_items=10,
            max_idle_rounds=999,
            wait_time_sec=10,  # 两次笔记详情获取时间间隔10s
            rpc_timeout_sec=9999,
            cookie_ids=["28ba44f1-bb67-41ab-86f0-a3d049d902aa"]
        )

        if not details_notes_res["success"]:
            print(f"[get_notes_details_from_xhs]执行失败：{details_notes_res['error']}")
            return

        print(f"[get_notes_details_from_xhs]执行成功，耗时：{details_notes_res.get("exec_elapsed_ms", "null")}ms")

        # 获取到现有的笔记详情数据
        with open(favorite_notes_details_storage_file, "r", encoding="utf-8") as f:
            details_data = json.load(f)

        # 将新获取到的笔记详情数据添加进去
        data = details_data.get("data", [])
        if details_notes_res["count"] > 0:
            data.extend(details_notes_res["data"])
        details_data["data"] = data
        details_data["count"] = len(data)
        with open(favorite_notes_details_storage_file, "w", encoding="utf-8") as f:
            json.dump(details_data, f, ensure_ascii=False, indent=4)

        # 笔记详情获取失败的也写入到文件中
        with open(favorite_notes_details_failed_file, "w", encoding="utf-8") as f:
            json.dump(details_notes_res["failed_notes"], f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"❌ 错误: {e}")

    finally:
        # 停止客户端
        await client.stop()
        print("\n✅ 小红书收藏笔记获取与处理")


if __name__ == "__main__":
    print("🚀 小红书收藏笔记获取与处理")
    asyncio.run(main())
