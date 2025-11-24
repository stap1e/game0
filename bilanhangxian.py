import cv2
import numpy as np
import time
import os
import random

# ===========================
# 1. 配置与常量定义
# ===========================

# 最大运行次数
MAX_RUN_TIMES = 20

# 图片模板路径 (请确保这些图片存在于 assets 文件夹或当前目录下)
TEMPLATE_PATHS = {
    "sweep_button": "assets/sweep_button.png",  # 扫荡/出击按钮
    "confirm_ok": "assets/confirm_ok.png",      # 结算页面的确定/再次前往
}

# 模拟固定入口坐标 (假设是日常任务的屏幕坐标)
# 注意：不同设备分辨率不同，建议通过截图测量
DAILY_TASK_ENTRY_POS = (1000, 600) 

# 截图保存的临时路径
SCREENSHOT_PATH = "temp_screen.png"

# ===========================
# 2. 底层交互层 (硬件抽象)
# ===========================

def capture_screen():
    """
    获取当前屏幕截图。
    这里演示使用 adb 命令获取，如果使用 uiautomator2，可用 d.screenshot(opencv=True)
    """
    # 方法 A: 使用 ADB 命令 (通用，但较慢)
    os.system(f"adb shell screencap -p /sdcard/screen.png")
    os.system(f"adb pull /sdcard/screen.png {SCREENSHOT_PATH}")
    
    # 读取图片
    image = cv2.imread(SCREENSHOT_PATH)
    
    # 容错：如果读取失败，返回空
    if image is None:
        print("[Error] 截图获取失败")
        return None
    return image

def simulate_click(x, y):
    """
    模拟点击屏幕指定坐标。
    """
    # 加入一点随机偏移，防止被游戏检测为机械脚本
    offset_x = random.randint(-5, 5)
    offset_y = random.randint(-5, 5)
    final_x, final_y = x + offset_x, y + offset_y
    
    print(f"[Action] 点击坐标: ({final_x}, {final_y})")
    
    # 方法 A: 使用 ADB Shell (慢)
    # os.system(f"adb shell input tap {final_x} {final_y}")
    
    # 方法 B: 如果对接 uiautomator2 (推荐)
    # d.click(final_x, final_y)

def simulate_back():
    """
    模拟安卓返回键
    """
    print("[Action] 按下返回键")
    # os.system("adb shell input keyevent 4")

# ===========================
# 3. 图像识别核心逻辑
# ===========================

def find_image_pos(screen_img, template_path, confidence=0.8):
    """
    在屏幕截图中寻找模板图片。
    返回: (center_x, center_y) 或 None
    """
    if screen_img is None:
        return None

    # 读取模板图片
    template = cv2.imread(template_path)
    if template is None:
        print(f"[Warning] 模板文件丢失: {template_path}")
        return None

    # 获取模板尺寸
    h, w = template.shape[:2]

    # 模板匹配
    try:
        result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    except Exception as e:
        print(f"[Error] OpenCV 匹配错误: {e}")
        return None

    # 判断相似度是否达标
    if max_val >= confidence:
        # 计算中心点
        top_left = max_loc
        center_x = int(top_left[0] + w / 2)
        center_y = int(top_left[1] + h / 2)
        print(f"[Detect] 发现目标 {template_path} (置信度: {max_val:.2f})")
        return (center_x, center_y)
    else:
        # print(f"[Detect] 未发现目标 {template_path} (最高置信度: {max_val:.2f})")
        return None

def find_and_click(template_name, confidence=0.8):
    """
    组合函数：截图 -> 找图 -> 点击
    """
    path = TEMPLATE_PATHS.get(template_name)
    if not path:
        return False

    screen = capture_screen()
    pos = find_image_pos(screen, path, confidence)
    
    if pos:
        simulate_click(pos[0], pos[1])
        return True
    return False

# ===========================
# 4. 业务逻辑主循环
# ===========================

def main_sweep_loop():
    print(f"=== 脚本启动: 计划执行 {MAX_RUN_TIMES} 次扫荡 ===")
    
    for i in range(1, MAX_RUN_TIMES + 1):
        print(f"\n>>> 开始第 [{i}/{MAX_RUN_TIMES}] 次循环")
        
        try:
            # ---------------------------
            # b. 进入任务 (固定坐标点击)
            # ---------------------------
            print("1. 尝试进入关卡/任务入口...")
            simulate_click(DAILY_TASK_ENTRY_POS[0], DAILY_TASK_ENTRY_POS[1])
            time.sleep(3) # 等待UI加载

            # ---------------------------
            # c. 执行扫荡 (图像识别点击)
            # ---------------------------
            print("2. 寻找扫荡/出击按钮...")
            # 尝试找5次，每次间隔1秒，防止UI延迟
            clicked_sweep = False
            for _ in range(5):
                if find_and_click("sweep_button", confidence=0.85):
                    clicked_sweep = True
                    break
                time.sleep(1)
            
            if not clicked_sweep:
                print("[Warning] 未找到扫荡按钮，跳过本次循环或尝试恢复...")
                # 可以选择 continue 或 return
                continue
                
            time.sleep(2) # 等待战斗或动画开始

            # ---------------------------
            # d. 处理结果 (循环等待结算)
            # ---------------------------
            print("3. 等待结算确认 (超时时间: 60秒)...")
            finished = False
            start_wait = time.time()
            
            while True:
                # 超时检测 (比如游戏卡死)
                if time.time() - start_wait > 60:
                    print("[Error] 等待结算超时！")
                    break
                
                # 检测是否出现“确定”或“点击继续”
                if find_and_click("confirm_ok", confidence=0.8):
                    print("   -> 结算完成")
                    finished = True
                    break
                
                print("   ...战斗/扫荡中...")
                time.sleep(3) # 每3秒检查一次

            if not finished:
                print("[Error] 流程异常，强制退出当前循环")
                # 此处可以增加报警逻辑

            # ---------------------------
            # e. 返回主页 (容错机制)
            # ---------------------------
            print("4. 返回主界面...")
            time.sleep(2)
            simulate_back()
            time.sleep(1.5)
            simulate_back() # 按两次确保退出多级菜单
            
            # 每一个大循环结束后的冷却
            time.sleep(2)

        except Exception as e:
            print(f"[Critical Error] 循环发生未捕获异常: {e}")
            break

    print("\n=== 任务全部结束 ===")

# ===========================
# 入口
# ===========================

if __name__ == "__main__":
    # 检查 assets 文件夹是否存在，防止报错
    if not os.path.exists("assets"):
        os.makedirs("assets")
        print("请将 'sweep_button.png' 和 'confirm_ok.png' 放入 assets 文件夹中。")
    
    # 启动主程序
    main_sweep_loop()