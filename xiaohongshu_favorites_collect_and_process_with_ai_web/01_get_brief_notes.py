
import asyncio
import json
import os

from client_sdk.params import TaskParams, ServiceParams, SyncParams
from client_sdk.rpc_client import EAIRPCClient
from utils.file_utils import read_json_with_project_root, write_json_with_project_root, PROJECT_ROOT

data_dir = PROJECT_ROOT / "data"
storage_abs_path = data_dir / "favorite_notes_brief.json"
storage_rela_path = "data/favorite_notes_brief.json"

def init_file():
    # 笔记数据由我们自己维护，初始哈笔记数据为一个对象
    if not os.path.exists(storage_abs_path):
        write_json_with_project_root(storage_rela_path, {})

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

        notes = read_json_with_project_root(storage_rela_path)

        # 返回值是 全量笔记/新添加/有更新 的笔记数据，删除暂时没有做
        # storage_file会保存完整数据（包含之前数据以及上面两者）
        results = await client.get_favorite_notes_brief_from_xhs(
            storage_data=json.dumps(notes),
            task_params=TaskParams(
                cookie_ids=["28ba44f1-bb67-41ab-86f0-a3d049d902aa"],
                close_page_when_task_finished=True,
            ),
            service_params=ServiceParams(
                max_items=20,
                max_seconds=20 ** 9,
            ),
            sync_params=SyncParams(
                max_new_items=20,
            )
        )
        if not results["success"]:
            print(f"[get_favorite_notes_brief_from_xhs]执行失败：{results['error']}")
            return

        print(f"[get_favorite_notes_brief_from_xhs]执行成功，耗时：{results.get('exec_elapsed_ms', 'null')}ms")

        write_json_with_project_root(storage_rela_path, results)

    except Exception as e:
        print(f"❌ 错误: {e}")

    finally:
        # 停止客户端
        await client.stop()
        print("\n✅ 小红书收藏笔记获取与处理")


if __name__ == "__main__":
    print("🚀 小红书收藏笔记获取与处理")
    asyncio.run(main())
