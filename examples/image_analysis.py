import os
import sys
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 使用OpenRouter API进行图像分析示例
def analyze_image_with_openrouter():
    # 初始化OpenRouter客户端
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv('OPENROUTER_API_KEY'),
    )

    # 调用API进行图像分析
    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "https://github.com/browser-use/macOS-use",  # 项目URL
            "X-Title": "macOS-use",  # 项目名称
        },
        model="openrouter/quasar-alpha",  # 选择支持视觉功能的模型
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这张图片中有什么内容？请详细描述。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
                        }
                    }
                ]
            }
        ]
    )
    
    # 打印分析结果
    print("图像分析结果:")
    print(completion.choices[0].message.content)

if __name__ == "__main__":
    if not os.getenv('OPENROUTER_API_KEY'):
        print("错误: 请在.env文件中设置OPENROUTER_API_KEY环境变量")
        sys.exit(1)
    
    analyze_image_with_openrouter() 