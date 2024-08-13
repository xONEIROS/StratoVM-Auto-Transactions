#!/usr/bin/env python3

import time
import random
import json
import os
from web3 import Web3
from eth_account import Account
from colorama import init, Fore, Style
from tqdm import tqdm


init(autoreset=True)


HEADER = f"""{Fore.CYAN}
  ______              ______                       __                               
 /      \            /      \                     /  |                              
/$$$$$$  | __    __ /$$$$$$  | _______    ______  $$/   ______    ______    _______ 
$$$  \$$ |/  \  /  |$$ |  $$ |/       \  /      \ /  | /      \  /      \  /       |
$$$$  $$ |$$  \/$$/ $$ |  $$ |$$$$$$$  |/$$$$$$  |$$ |/$$$$$$  |/$$$$$$  |/$$$$$$$/ 
$$ $$ $$ | $$  $$<  $$ |  $$ |$$ |  $$ |$$    $$ |$$ |$$ |  $$/ $$ |  $$ |$$      \ 
$$ \$$$$ | /$$$$  \ $$ \__$$ |$$ |  $$ |$$$$$$$$/ $$ |$$ |      $$ \__$$ | $$$$$$  |
$$   $$$/ /$$/ $$  |$$    $$/ $$ |  $$ |$$       |$$ |$$ |      $$    $$/ /     $$/ 
 $$$$$$/  $$/   $$/  $$$$$$/  $$/   $$/  $$$$$$$/ $$/ $$/        $$$$$$/  $$$$$$$/  
{Style.RESET_ALL}"""


RPC_URL = "https://rpc.stratovm.io"
CHAIN_ID = 93747
PRIVATE_KEY_FILE = "private_key.txt"
WALLETS_FILE = "wallets.json"
NFT_CONTRACT_ADDRESS = "0xDf954b362dCAB3b2b5AF49D79BE221fEC21489Cc"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear_screen()
    print(HEADER)
    print(f"{Fore.YELLOW}StratoVM Wallet Creator and Token Sender{Style.RESET_ALL}")
    print("=" * 60)

def get_or_create_private_key():
    if os.path.exists(PRIVATE_KEY_FILE):
        with open(PRIVATE_KEY_FILE, "r") as f:
            return f.read().strip()
    else:
        private_key = input(f"{Fore.GREEN}Enter your private key to connect to the network: {Style.RESET_ALL}").strip()
        with open(PRIVATE_KEY_FILE, "w") as f:
            f.write(private_key)
        return private_key

def get_wallet_count():
    while True:
        try:
            count = int(input(f"{Fore.GREEN}Enter the number of wallets to create: {Style.RESET_ALL}"))
            if count > 0:
                return count
            print(f"{Fore.RED}Please enter a positive number.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")

def create_wallets(count):
    return [Account.create() for _ in range(count)]

def save_wallets(wallets):
    wallet_data = [{"address": w.address, "private_key": w._private_key.hex()} for w in wallets]
    with open(WALLETS_FILE, "w") as f:
        json.dump(wallet_data, f, indent=2)

def load_wallets():
    if os.path.exists(WALLETS_FILE):
        with open(WALLETS_FILE, "r") as f:
            wallet_data = json.load(f)
        return [Account.from_key(w["private_key"]) for w in wallet_data]
    return []

def send_tokens(web3, from_account, to_address, amount, nonce):
    gas_price = web3.eth.gas_price
    gas_price_with_premium = int(gas_price * 1.1) 

    tx = {
        'nonce': nonce,
        'to': to_address,
        'value': web3.to_wei(amount, 'ether'),
        'gas': 21000,
        'gasPrice': gas_price_with_premium,
        'chainId': CHAIN_ID
    }
    signed_tx = web3.eth.account.sign_transaction(tx, from_account._private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return web3.to_hex(tx_hash)

def get_user_input_float(prompt, default):
    user_input = input(f"{Fore.GREEN}{prompt} {Style.RESET_ALL}").strip()
    if user_input == "":
        return default
    try:
        return float(user_input)
    except ValueError:
        print(f"{Fore.RED}Invalid input. Using default value.{Style.RESET_ALL}")
        return default

def get_user_input_int(prompt, default):
    user_input = input(f"{Fore.GREEN}{prompt} {Style.RESET_ALL}").strip()
    if user_input == "":
        return default
    try:
        return int(user_input)
    except ValueError:
        print(f"{Fore.RED}Invalid input. Using default value.{Style.RESET_ALL}")
        return default

def get_yes_no_input(prompt):
    while True:
        user_input = input(f"{Fore.GREEN}{prompt} {Style.RESET_ALL}").strip().lower()
        if user_input in ['yes', 'y']:
            return True
        elif user_input in ['no', 'n']:
            return False
        else:
            print(f"{Fore.RED}Invalid input. Please enter 'yes' or 'no' (or 'y' or 'n').{Style.RESET_ALL}")

def automatic_transactions():
    print_header()
    time.sleep(2)  

    private_key = get_or_create_private_key()
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not web3.is_connected():
        print(f"{Fore.RED}Failed to connect to the StratoVM network. Please check your internet connection and try again.{Style.RESET_ALL}")
        return

    from_account = Account.from_key(private_key)

    existing_wallets = load_wallets()
    if existing_wallets:
        print(f"{Fore.YELLOW}Found {len(existing_wallets)} existing wallets.{Style.RESET_ALL}")
        create_new = get_yes_no_input("Do you want to create new wallets? (yes/no): ")
        if create_new:
            wallet_count = get_wallet_count()
            wallets = create_wallets(wallet_count)
            save_wallets(wallets)
        else:
            wallets = existing_wallets
    else:
        wallet_count = get_wallet_count()
        wallets = create_wallets(wallet_count)
        save_wallets(wallets)

    min_amount = get_user_input_float("Enter minimum amount to send (default 0.000000123): ", 0.000000123)
    max_amount = get_user_input_float("Enter maximum amount to send (default 0.000000987): ", 0.000000987)
    min_delay = get_user_input_int("Enter minimum delay between transactions in seconds (default 9): ", 9)
    max_delay = get_user_input_int("Enter maximum delay between transactions in seconds (default 300): ", 300)

    print(f"\n{Fore.CYAN}Preparing to send tokens...{Style.RESET_ALL}")
    nonce = web3.eth.get_transaction_count(from_account.address)

    for i, wallet in enumerate(tqdm(wallets, desc="Sending Tokens", unit="wallet"), 1):
        amount = random.uniform(min_amount, max_amount)
        try:
            tx_hash = send_tokens(web3, from_account, wallet.address, amount, nonce)
            print(f"\n{Fore.GREEN}Wallet {i}:{Style.RESET_ALL}")
            print(f"  Address: {Fore.YELLOW}{wallet.address}{Style.RESET_ALL}")
            print(f"  Amount Sent: {Fore.CYAN}{amount:.12f} SVM{Style.RESET_ALL}")
            print(f"  Transaction Hash: {Fore.MAGENTA}{tx_hash}{Style.RESET_ALL}")
            nonce += 1  
            delay = random.randint(min_delay, max_delay)
            for _ in tqdm(range(delay), desc="Waiting", unit="s", leave=False):
                time.sleep(1)
        except Exception as e:
            print(f"{Fore.RED}Error sending tokens to wallet {i}: {str(e)}{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}Operation completed successfully!{Style.RESET_ALL}")


    delete_key = get_yes_no_input("Do you want to delete the private key file for security? (yes/no): ")
    if delete_key:
        if os.path.exists(PRIVATE_KEY_FILE):
            os.remove(PRIVATE_KEY_FILE)
            print(f"{Fore.YELLOW}Private key file has been deleted.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Private key file not found.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Private key file has been kept.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Join our Telegram channel: {Fore.BLUE}https://t.me/xOneiros{Style.RESET_ALL}")

def mint_daily_nft(web3, from_account):

    abi = json.loads('[{"inputs":[],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"}]')
    
    contract = web3.eth.contract(address=NFT_CONTRACT_ADDRESS, abi=abi)
    
    nonce = web3.eth.get_transaction_count(from_account.address)
    
    try:

        estimated_gas = contract.functions.mint().estimate_gas({'from': from_account.address})
        

        safe_gas = int(estimated_gas * 1.2)  
        

        tx = contract.functions.mint().build_transaction({
            'chainId': CHAIN_ID,
            'gas': safe_gas,
            'gasPrice': web3.eth.gas_price,
            'nonce': nonce,
            'value': 0x0,  
        })
        

        signed_tx = web3.eth.account.sign_transaction(tx, from_account._private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        
        if tx_receipt['status'] == 1:
            print(f"{Fore.GREEN}NFT minted successfully!{Style.RESET_ALL}")
            print(f"Transaction hash: {Fore.YELLOW}{tx_hash.hex()}{Style.RESET_ALL}")
            print(f"Gas used: {Fore.CYAN}{tx_receipt['gasUsed']}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to mint NFT. Transaction failed.{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"{Fore.RED}Error minting NFT: {str(e)}{Style.RESET_ALL}")

def main_menu():
    while True:
        print_header()
        print(f"{Fore.YELLOW}Main Menu:{Style.RESET_ALL}")
        print("1. Automatic Transactions")
        print("2. Mint Daily NFT")
        print("3. Exit")
        
        choice = input(f"{Fore.GREEN}Choose an option (1-3): {Style.RESET_ALL}")
        
        if choice == '1':
            automatic_transactions()
        elif choice == '2':
            private_key = get_or_create_private_key()
            web3 = Web3(Web3.HTTPProvider(RPC_URL))
            if not web3.is_connected():
                print(f"{Fore.RED}Failed to connect to the StratoVM network. Please check your internet connection and try again.{Style.RESET_ALL}")
                continue
            from_account = Account.from_key(private_key)
            mint_daily_nft(web3, from_account)
        elif choice == '3':
            print(f"{Fore.YELLOW}Thank you for using our service! Goodbye!{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}Invalid choice. Please choose 1, 2, or 3.{Style.RESET_ALL}")
        
        input(f"{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")

if __name__ == "__main__":
    main_menu()
