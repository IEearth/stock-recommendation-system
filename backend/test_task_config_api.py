#!/usr/bin/env python
"""
测试任务配置 API 功能
"""
import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000/api"


async def test_api():
    """测试 API 功能"""
    print("🧪 开始测试任务配置 API...\n")

    async with aiohttp.ClientSession() as session:
        try:
            # 1. 获取所有任务配置
            print("1️⃣  获取所有任务配置...")
            async with session.get(f"{BASE_URL}/task-configs") as resp:
                data = await resp.json()
                print(f"   ✅ 成功获取 {data['total']} 个任务配置")
                for config in data['configs']:
                    print(f"      - {config['task_name']}: {config['task_type']} (启用: {config['is_enabled']})")

            # 2. 获取单个任务配置
            print("\n2️⃣  获取单个任务配置 (health_check)...")
            async with session.get(f"{BASE_URL}/task-configs/health_check") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ 成功获取任务配置: {data['task_name']}")
                else:
                    print(f"   ❌ 获取失败: {resp.status}")

            # 3. 切换任务状态
            print("\n3️⃣  切换任务状态...")
            async with session.post(f"{BASE_URL}/task-configs/health_check/toggle") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ 状态切换成功: {data['message']}")
                else:
                    print(f"   ❌ 切换失败: {resp.status}")

            # 4. 创建新任务配置
            print("\n4️⃣  创建新任务配置...")
            new_config = {
                "task_name": "test_task",
                "task_type": "data_fetch",
                "is_enabled": False,
                "interval_seconds": 300,
                "description": "测试任务"
            }
            async with session.post(
                f"{BASE_URL}/task-configs",
                json=new_config
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ 创建成功: {data['message']}")
                else:
                    text = await resp.text()
                    print(f"   ❌ 创建失败: {resp.status} - {text}")

            # 5. 更新任务配置
            print("\n5️⃣  更新任务配置...")
            update_config = {
                "description": "测试任务（已更新）",
                "interval_seconds": 600
            }
            async with session.put(
                f"{BASE_URL}/task-configs/test_task",
                json=update_config
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ 更新成功: {data['message']}")
                else:
                    text = await resp.text()
                    print(f"   ❌ 更新失败: {resp.status} - {text}")

            # 6. 删除测试任务
            print("\n6️⃣  删除测试任务...")
            async with session.delete(f"{BASE}/task-configs/test_task") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ 删除成功: {data['message']}")
                else:
                    text = await resp.text()
                    print(f"   ⚠️  删除失败: {resp.status} - {text}")

            print("\n✅ 所有测试完成！")

        except aiohttp.ClientError as e:
            print(f"❌ 连接失败: {e}")
            print("💡 请确保后端服务正在运行: python3 main.py")


if __name__ == "__main__":
    asyncio.run(test_api())
