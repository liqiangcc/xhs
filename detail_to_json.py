import re
import json
import sys
import os

def extract_and_save_json(html_path):
    file_name = os.path.basename(html_path)
    base_name = os.path.splitext(file_name)[0]
    
    json_dir = "note_json"
    json_path = os.path.join(json_dir, f"{base_name}.json")

    if not os.path.exists(html_path):
        print(f"❌ 找不到源文件: {html_path}")
        sys.exit(-1)

    try:
        os.makedirs(json_dir, exist_ok=True)

        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 1. 提取数据
        pattern = r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})(?=;|<|/script)'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            print(f"⚠️  {file_name}: 未发现目标 JSON 数据。")
            sys.exit(-1) # 找不到数据，返回 -1

        json_str = match.group(1)

        # 2. 容错预清理
        json_str = json_str.replace(':undefined', ':null')
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # 过滤不可见控制字符再尝试
            json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
            try:
                data = json.loads(json_str)
            except:
                print(f"❌ {file_name}: JSON 格式严重损坏，无法解析。")
                sys.exit(-1) # 解析失败，返回 -1

        # 3. 写入文件
        with open(json_path, 'w', encoding='utf-8') as f_out:
            json.dump(data, f_out, ensure_ascii=False, indent=4)
        
        print(f"✅ 已提取: {json_path}")
        sys.exit(0) # 成功，返回 0

    except Exception as e:
        print(f"❌ 处理 {file_name} 时发生未知错误: {e}")
        sys.exit(-1) # 异常，返回 -1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用指南: python3 detail_to_json.py <html路径>")
        sys.exit(-1)
    else:
        extract_and_save_json(sys.argv[1])
