#!/bin/bash
# VLLM部署脚本 - 支持工具调用功能
# 更新版本：添加了工具调用相关参数

echo "🚀 部署Qwen3-32B VLLM服务器（支持工具调用）..."

# 停止并删除现有容器
echo "🔄 停止现有容器..."
docker stop coder 2>/dev/null || true
docker rm coder 2>/dev/null || true

# 启动新容器
echo "🔧 启动VLLM容器..."
docker run -d \
  --runtime=nvidia \
  --gpus=all \
  --name coder \
  -v /home/llm/model/qwen/Qwen3-32B-AWQ:/model/Qwen3-32B-AWQ \
  -p 8000:8000 \
  --cpuset-cpus 0-55 \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  --restart always \
  --ipc=host \
  vllm/vllm-openai:v0.8.5 \
  --model /model/Qwen3-32B-AWQ \
  --served-model-name coder \
  --tensor-parallel-size 4 \
  --dtype half \
  --quantization awq \
  --max-model-len 32768 \
  --max-num-batched-tokens 4096 \
  --gpu-memory-utilization 0.93 \
  --block-size 32 \
  --enable-chunked-prefill \
  --swap-space 16 \
  --tokenizer-pool-size 56 \
  --disable-custom-all-reduce \
  --enable-auto-tool-choice \
  --tool-call-parser hermes

echo "✅ VLLM容器启动完成"
echo "🔗 服务地址: http://10.49.121.127:8000"
echo "📋 模型名称: coder"
echo "🛠️  工具调用: 已启用"

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
if curl -s http://10.49.121.127:8000/v1/models > /dev/null; then
    echo "✅ VLLM服务启动成功!"
    echo "📋 可用模型:"
    curl -s http://10.49.121.127:8000/v1/models | jq '.data[].id' 2>/dev/null || echo "   - coder"
else
    echo "❌ VLLM服务启动失败，请检查日志:"
    echo "   docker logs coder"
fi