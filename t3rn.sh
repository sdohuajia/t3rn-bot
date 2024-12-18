#!/bin/bash

# 脚本保存路径
SCRIPT_PATH="$HOME/t3rn.sh"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 定义仓库地址和目录名称
REPO_URL="https://github.com/sdohuajia/t3rn-bot.git"
DIR_NAME="t3rn-bot"
PYTHON_FILE="keys_and_addresses.py"
DATA_BRIDGE_FILE="data_bridge.py"
BOT_FILE="bot.py"
VENV_DIR="t3rn-env"  # 虚拟环境目录

# 检查是否安装了 git
if ! command -v git &> /dev/null; then
    echo "Git 未安装，请先安装 Git。"
    exit 1
fi

# 检查是否安装了 python3-pip 和 python3-venv
if ! command -v pip3 &> /dev/null; then
    echo "pip 未安装，正在安装 python3-pip..."
    sudo apt update
    sudo apt install -y python3-pip
fi

if ! command -v python3 -m venv &> /dev/null; then
    echo "python3-venv 未安装，正在安装 python3-venv..."
    sudo apt update
    sudo apt install -y python3-venv
fi

# 拉取仓库
if [ -d "$DIR_NAME" ]; then
    echo "目录 $DIR_NAME 已存在，拉取最新更新..."
    cd "$DIR_NAME" || exit
    git pull origin main
else
    echo "正在克隆仓库 $REPO_URL..."
    git clone "$REPO_URL"
    cd "$DIR_NAME" || exit
fi

echo "已进入目录 $DIR_NAME"

# 创建虚拟环境并激活
echo "正在创建虚拟环境..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# 升级 pip
echo "正在升级 pip..."
pip install --upgrade pip

# 安装依赖
echo "正在安装依赖 web3 和 colorama..."
pip install web3 colorama

# 提醒用户私钥安全
echo "警告：请务必确保您的私钥安全！"
echo "私钥应当保存在安全的位置，切勿公开分享或泄漏给他人。"
echo "如果您的私钥被泄漏，可能导致您的资产丧失！"
echo "请输入您的私钥，确保安全操作。"

# 让用户输入私钥和标签
echo "请输入您的私钥（多个私钥以空格分隔）："
read -r private_keys_input

echo "请输入您的标签（多个标签以空格分隔，与私钥顺序一致）："
read -r labels_input

# 检查输入是否一致
IFS=' ' read -r -a private_keys <<< "$private_keys_input"
IFS=' ' read -r -a labels <<< "$labels_input"

if [ "${#private_keys[@]}" -ne "${#labels[@]}" ]; then
    echo "私钥和标签数量不一致，请重新运行脚本并确保它们匹配！"
    exit 1
fi

# 写入 keys_and_addresses.py 文件
echo "正在写入 $PYTHON_FILE 文件..."
cat > $PYTHON_FILE <<EOL
# 此文件由脚本生成

private_keys = [
$(printf "    '%s',\n" "${private_keys[@]}")
]

labels = [
$(printf "    '%s',\n" "${labels[@]}")
]
EOL

echo "$PYTHON_FILE 文件已生成。"

# 提醒用户私钥安全
echo "脚本执行完成！所有依赖已安装，私钥和标签已保存到 $PYTHON_FILE 中。"
echo "请务必妥善保管此文件，避免泄露您的私钥和标签信息！"

# 获取额外的用户输入："ARB - OP SEPOLIA" 和 "OP - ARB"
echo "请输入 'ARB - OP SEPOLIA' 的值："
read -r arb_op_sepolia_value

echo "请输入 'OP - ARB' 的值："
read -r op_arb_value

# 写入 data_bridge.py 文件
echo "正在写入 $DATA_BRIDGE_FILE 文件..."
cat > $DATA_BRIDGE_FILE <<EOL
# 此文件由脚本生成

data_bridge = {
    # Data bridge Arbitrum Sepolia
    "ARB - OP SEPOLIA": "$arb_op_sepolia_value",

    # Data bridge OP Sepolia
    "OP - ARB": "$op_arb_value",
}
EOL

echo "$DATA_BRIDGE_FILE 文件已生成。"

# 提醒用户运行 bot.py
echo "配置完成，正在运行 bot.py..."

# 运行 bot.py
python3 $BOT_FILE
