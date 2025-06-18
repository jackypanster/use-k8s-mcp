#!/usr/bin/env python3
"""
LLM配置测试脚本
用于验证不同提供商的配置是否正确
"""

import os
import sys
from dotenv import load_dotenv
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from llm_config import (
    create_llm,
    get_model_info,
    print_model_status
)


def test_provider_detection():
    """测试模型配置检测"""
    print("🔍 测试模型配置检测...")
    info = get_model_info()
    provider = info.get('provider', 'Unknown')
    print(f"   当前提供商: {provider}")

    if 'OpenRouter' not in provider:
        print(f"❌ 错误: 不支持的提供商 {provider}")
        return False

    print("✅ 模型配置检测正常")
    return True


def test_provider_info():
    """测试模型信息获取"""
    print("\n📋 测试模型信息...")
    try:
        info = get_model_info()
        print(f"   提供商: {info.get('provider', 'Unknown')}")
        print(f"   服务地址: {info.get('base_url', 'N/A')}")
        print(f"   模型: {info.get('model', 'N/A')}")
        print(f"   输入上下文: {info.get('input_context', 'N/A')}")
        print(f"   输出能力: {info.get('output_tokens', 'N/A')}")

        print("✅ 模型信息获取正常")
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_llm_creation():
    """测试LLM实例创建"""
    print("\n🤖 测试LLM实例创建...")

    try:
        print(f"   测试环境配置LLM创建...")
        llm = create_llm()

        # 验证基本属性
        assert hasattr(llm, 'model_name'), "缺少model_name属性"
        assert hasattr(llm, 'temperature'), "缺少temperature属性"
        assert hasattr(llm, 'max_tokens'), "缺少max_tokens属性"
        assert hasattr(llm, 'openai_api_base'), "缺少openai_api_base属性"

        print(f"     ✅ 环境配置LLM: {llm.model_name}")
        print(f"     ✅ 温度设置: {llm.temperature}")
        print(f"     ✅ 最大输出: {llm.max_tokens:,} tokens")
        print(f"     ✅ API地址: {llm.openai_api_base}")

        # 测试参数覆盖
        print(f"   测试参数覆盖...")
        llm_override = create_llm(max_tokens=16384, temperature=0.1)
        assert llm_override.max_tokens == 16384, f"参数覆盖失败: {llm_override.max_tokens}"
        assert llm_override.temperature == 0.1, f"温度覆盖失败: {llm_override.temperature}"
        print(f"     ✅ 参数覆盖: max_tokens={llm_override.max_tokens}, temperature={llm_override.temperature}")

        print("✅ LLM创建测试成功")
        return True

    except Exception as e:
        print(f"❌ LLM创建测试失败: {e}")
        return False


def test_k8s_llm_creation():
    """测试Kubernetes专用LLM创建"""
    print("\n⚙️  测试Kubernetes专用LLM创建...")
    
    k8s_environments = [
        ("production", "生产环境"),
        ("development", "开发环境"), 
        ("analysis", "分析环境")
    ]
    
    success_count = 0
    
    for env, description in k8s_environments:
        try:
            print(f"   测试K8s {description} ({env})...")
            llm = create_llm()
            
            # 验证K8s特定配置
            assert llm.temperature <= 0.1, f"温度过高: {llm.temperature}"
            assert llm.max_tokens >= 3000, f"最大token过少: {llm.max_tokens}"
            assert llm.stop, "缺少安全停止序列"
            
            print(f"     ✅ K8s {description}: 温度={llm.temperature}, Token={llm.max_tokens}")
            success_count += 1
            
        except Exception as e:
            print(f"     ❌ K8s {description}: {e}")
    
    print(f"\n📊 K8s LLM创建测试结果: {success_count}/{len(k8s_environments)} 成功")
    return success_count == len(k8s_environments)


def test_environment_variables():
    """测试环境变量配置"""
    print("\n🔧 测试环境变量配置...")

    missing_vars = []

    # 检查必需的环境变量
    required_vars = [
        "OPENROUTER_API_KEY",
        "OPENROUTER_BASE_URL",
        "LLM_MODEL_NAME"
    ]

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"   ✅ {var}: 已设置")

    # 检查可选的环境变量
    optional_vars = [
        "LLM_MAX_INPUT_CONTEXT",
        "LLM_MAX_OUTPUT_TOKENS",
        "LLM_REQUEST_TIMEOUT",
        "LLM_TEMPERATURE",
        "LLM_TOP_P",
        "LLM_MAX_RETRIES",
        "LLM_SEED"
    ]

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"   ⚙️  {var}: {value}")
        else:
            print(f"   📝 {var}: 使用默认值")

    if missing_vars:
        print(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        print("   请检查 .env 文件配置")
        return False

    print("✅ 环境变量配置正常")
    return True


def main():
    """主测试函数"""
    print("🧪 LLM配置测试开始")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    
    # 显示当前状态
    print_model_status()
    print("=" * 60)
    
    # 运行测试
    tests = [
        test_provider_detection,
        test_environment_variables,
        test_provider_info,
        test_llm_creation,
        test_k8s_llm_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 失败: {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())
