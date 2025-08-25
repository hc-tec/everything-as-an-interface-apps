
import asyncio
import json

from client_sdk.rpc_client import EAIRPCClient
import os
from utils.file_utils import read_json_with_project_root, write_json_with_project_root, PROJECT_ROOT

data_dir = PROJECT_ROOT / "data"
notes_brief_rela_path = "data/favorite_notes_brief.json"
notes_details_abs_file = data_dir / "favorite_notes_details.json"
notes_failed_abs_file = data_dir / "favorite_notes_details_failed.json"
notes_details_rela_file = "data/favorite_notes_details.json"
notes_failed_rela_file = "data/favorite_notes_details_failed.json"

def init_file():
    # 笔记数据由我们自己维护，初始哈笔记数据为一个对象
    if not os.path.exists(notes_details_abs_file):
        write_json_with_project_root(notes_details_rela_file, {})
    if not os.path.exists(notes_failed_abs_file):
        write_json_with_project_root(notes_failed_rela_file, {})

init_file()

async def get_details(client, brief_notes_results):
    if not brief_notes_results["success"]:
        print(f"[get_favorite_notes_brief_from_xhs]执行失败：{brief_notes_results['error']}")
        return

    # 只需要对增量笔记获取详情
    brief_data = brief_notes_results.copy()
    brief_data.pop("added")
    brief_data.pop("updated")
    brief_data["data"] = []
    for item in ["added", "updated"]:
        data = brief_notes_results[item]
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
        cookie_ids=["28ba44f1-bb67-41ab-86f0-a3d049d902aa"],
        close_page_when_task_finished=True,
    )

    if not details_notes_res["success"]:
        print(f"[get_notes_details_from_xhs]执行失败：{details_notes_res['error']}")
        return

    print(f"[get_notes_details_from_xhs]执行成功，耗时：{details_notes_res.get("exec_elapsed_ms", "null")}ms")

    # 获取到现有的笔记详情数据
    details_data = read_json_with_project_root(notes_details_rela_file)

    # 将新获取到的笔记详情数据添加进去
    data = details_data.get("data", [])
    if details_notes_res["count"] > 0:
        data.extend(details_notes_res["data"])
    details_data["data"] = data
    details_data["count"] = len(data)
    write_json_with_project_root(notes_details_rela_file, details_data)

    if details_notes_res["failed_notes"]["count"] == 0:
        print("All brief notes collected successfully!")
        return False

    # 笔记详情获取失败的也写入到文件中
    write_json_with_project_root(notes_failed_rela_file, {})

    return True

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


        brief_notes_results = read_json_with_project_root(notes_brief_rela_path)
        has_failed = await get_details(client, brief_notes_results)

        while has_failed:
            failed_notes_results = read_json_with_project_root(notes_failed_rela_file)
            has_failed = await get_details(client, failed_notes_results)

    except Exception as e:
        print(f"❌ 错误: {e}")

    finally:
        # 停止客户端
        await client.stop()
        print("\n✅ 小红书收藏笔记获取与处理")


if __name__ == "__main__":
    print("🚀 小红书收藏笔记获取与处理")
    asyncio.run(main())
