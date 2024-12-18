# -*- coding: utf-8 -*-

from web3 import Web3
from eth_account import Account
import time
import sys
import os

# 数据桥接配置
from data_bridge import data_bridge
from keys_and_addresses import private_keys, my_addresses, labels
from network_config import networks

# 文本居中函数
def center_text(text):
    terminal_width = os.get_terminal_size().columns
    lines = text.splitlines()
    centered_lines = [line.center(terminal_width) for line in lines]
    return "\n".join(centered_lines)

# 清理终端函数
def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

description = """
自动桥接机器人  https://bridge.t1rn.io/
操你麻痹Rambeboy,偷私钥🐶
"""

# 每个链的颜色和符号
chain_symbols = {
    'Arbitrum Sepolia': '\033[34m',   
    'OP Sepolia': '\033[91m',         
}

# 颜色定义
green_color = '\033[92m'
reset_color = '\033[0m'
menu_color = '\033[95m'  # 菜单文本颜色

# 每个网络的区块浏览器URL
explorer_urls = {
    'Arbitrum Sepolia': 'https://sepolia.arbiscan.io/tx/',
    'OP Sepolia': 'https://sepolia-optimism.etherscan.io/tx/',
    'BRN': 'https://brn.explorer.caldera.xyz/tx/'
}

# 获取BRN余额的函数
def get_brn_balance(web3, my_address):
    balance = web3.eth.get_balance(my_address)
    return web3.from_wei(balance, 'ether')

# 创建和发送交易的函数
def send_bridge_transaction(web3, account, my_address, data, network_name):
    nonce = web3.eth.get_transaction_count(my_address, 'pending')
    value_in_ether = 0.1
    value_in_wei = web3.to_wei(value_in_ether, 'ether')

    try:
        gas_estimate = web3.eth.estimate_gas({
            'to': networks[network_name]['contract_address'],
            'from': my_address,
            'data': data,
            'value': value_in_wei
        })
        gas_limit = gas_estimate + 50000  # 增加安全边际
    except Exception as e:
        print(f"估计gas错误: {e}")
        return None

    base_fee = web3.eth.get_block('latest')['baseFeePerGas']
    priority_fee = web3.to_wei(5, 'gwei')
    max_fee = base_fee + priority_fee

    transaction = {
        'nonce': nonce,
        'to': networks[network_name]['contract_address'],
        'value': value_in_wei,
        'gas': gas_limit,
        'maxFeePerGas': max_fee,
        'maxPriorityFeePerGas': priority_fee,
        'chainId': networks[network_name]['chain_id'],
        'data': data
    }

    try:
        signed_txn = web3.eth.account.sign_transaction(transaction, account.key)
    except Exception as e:
        print(f"签名交易错误: {e}")
        return None

    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        # 获取最新余额
        balance = web3.eth.get_balance(my_address)
        formatted_balance = web3.from_wei(balance, 'ether')

        # 获取区块浏览器链接
        explorer_link = f"{explorer_urls[network_name]}{web3.to_hex(tx_hash)}"

        # 显示交易信息
        print(f"{green_color}📤 发送地址: {account.address}")
        print(f"⛽ 使用Gas: {tx_receipt['gasUsed']}")
        print(f"🗳️  区块号: {tx_receipt['blockNumber']}")
        print(f"💰 ETH余额: {formatted_balance} ETH")
        brn_balance = get_brn_balance(Web3(Web3.HTTPProvider('https://brn.rpc.caldera.xyz/http')), my_address)
        print(f"🔵 BRN余额: {brn_balance} BRN")
        print(f"🔗 区块浏览器链接: {explorer_link}\n{reset_color}")

        return web3.to_hex(tx_hash), value_in_ether
    except Exception as e:
        print(f"发送交易错误: {e}")
        return None, None

# 在特定网络上处理交易的函数
def process_network_transactions(network_name, bridges, chain_data, successful_txs):
    web3 = Web3(Web3.HTTPProvider(chain_data['rpc_url']))
    if not web3.is_connected():
        raise Exception(f"无法连接到网络 {network_name}")

    for bridge in bridges:
        for i, private_key in enumerate(private_keys):
            account = Account.from_key(private_key)
            data = data_bridge[bridge]
            result = send_bridge_transaction(web3, account, my_addresses[i], data, network_name)
            if result:
                tx_hash, value_sent = result
                successful_txs += 1

                # 检查 value_sent 是否有效再格式化
                if value_sent is not None:
                    print(f"{chain_symbols[network_name]}🚀 成功交易总数: {successful_txs} | {labels[i]} | 桥接: {bridge} | 桥接金额: {value_sent:.5f} ETH ✅{reset_color}\n")
                else:
                    print(f"{chain_symbols[network_name]}🚀 成功交易总数: {successful_txs} | {labels[i]} | 桥接: {bridge} ✅{reset_color}\n")

                print(f"{'='*150}")
                print("\n")
            time.sleep(7)

    return successful_txs

# 显示链选择菜单的函数
def display_menu():
    print(f"{menu_color}选择要运行交易的链:{reset_color}")
    print("")
    print(f"{chain_symbols['Arbitrum Sepolia']}1. ARB -> OP Sepolia{reset_color}")
    print(f"{chain_symbols['OP Sepolia']}2. OP -> ARB Sepolia{reset_color}")
    print(f"{menu_color}3. 运行所有链{reset_color}")
    print("")
    choice = input("输入选择 (1-3): ")
    return choice

def main():
    print("\033[92m" + center_text(description) + "\033[0m")
    print("\n\n")

    successful_txs = 0

    while True:
        # 显示菜单并获取用户选择
        choice = display_menu()
        clear_terminal()  # 在显示新交易前清理终端
        print("\033[92m" + center_text(description) + "\033[0m")
        print("\n\n")

        try:
            if choice == '1':
                while True:
                    successful_txs = process_network_transactions('Arbitrum Sepolia', ["ARB - OP SEPOLIA"], networks['Arbitrum Sepolia'], successful_txs)
            elif choice == '2':
                while True:
                    successful_txs = process_network_transactions('OP Sepolia', ["OP - ARB"], networks['OP Sepolia'], successful_txs)
            elif choice == '3':
                while True:
                    successful_txs = process_network_transactions('Arbitrum Sepolia', ["ARB - OP SEPOLIA"], networks['Arbitrum Sepolia'], successful_txs)
                    successful_txs = process_network_transactions('OP Sepolia', ["OP - ARB"], networks['OP Sepolia'], successful_txs)
            else:
                print("无效选择。请再试一次。")

        except KeyboardInterrupt:
            print("\n脚本被用户终止。 ✋")
            print(f"成功交易总数: {successful_txs} 🎉")
            sys.exit(0)
        except Exception as e:
            print(f"发生错误: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()