import asyncio
import sys
import os
from mlx_use.mac.tree import MacUITreeBuilder
import Cocoa

# 添加项目根目录到路径，确保能正确导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    # 1. 打开应用
    app_name = "iPhone Mirroring"  # iPhone镜像应用
    formatted_app_name = app_name  # 保持原名称，因为这可能不是Apple的应用
    workspace = Cocoa.NSWorkspace.sharedWorkspace()
    
    print(f'\n启动 {app_name} 应用...')
    success = workspace.launchApplication_(app_name)
    
    if not success:
        print(f'❌ 无法启动 {app_name} 应用')
        return
    
    # 2. 给应用一些启动时间
    await asyncio.sleep(2)  # 增加等待时间，确保应用完全启动
    
    # 3. 获取应用PID
    pid = None
    for app in workspace.runningApplications():
        if app.bundleIdentifier() and app_name.lower() in app.localizedName().lower():
            pid = app.processIdentifier()
            print(f"找到应用: {app.localizedName()}")
            print(f"Bundle ID: {app.bundleIdentifier()}")
            print(f"PID: {pid}")
            break
    
    if not pid:
        print(f"❌ 无法找到应用: {app_name}")
        return
    
    # 4. 激活应用窗口
    for app in workspace.runningApplications():
        if app.processIdentifier() == pid:
            app.activateWithOptions_(Cocoa.NSApplicationActivateIgnoringOtherApps)
            break
    
    await asyncio.sleep(1)  # 给应用激活一些时间
    
    # 5. 构建UI树
    try:
        tree_builder = MacUITreeBuilder()
        root = await tree_builder.build_tree(pid)
        
        # 6. 输出UI元素
        if root:
            print(f"\n✅ 成功构建 {app_name} 的UI树!")
            print(f"根节点子元素数量: {len(root.children)}")
            
            # 打印整个UI树结构
            def print_tree(node, indent=0):
                print('  ' * indent + repr(node))
                for child in node.children:
                    print_tree(child, indent + 1)
            
            print(f"\n{app_name} 的完整UI树结构:")
            print_tree(root)
            
            print("\n可交互元素:")
            print(root.get_clickable_elements_string())
            
            print("\n详细UI树:")
            print(root.get_detailed_string())
        else:
            print(f"❌ 无法获取 {app_name} 的UI树")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'tree_builder' in locals():
            tree_builder.cleanup()

if __name__ == "__main__":
    asyncio.run(main())