#!/usr/bin/env python3

import time
import random
import json
import os
import threading
import schedule
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
PRIVATE_KEYS_FILE = "private_keys.json"
WALLETS_FILE = "wallets.json"
NFT_CONTRACT_ADDRESS = "0xDf954b362dCAB3b2b5AF49D79BE221fEC21489Cc"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear_screen()
    print(HEADER)
    print(f"{Fore.YELLOW}StratoVM Wallet Creator and Token Sender{Style.RESET_ALL}")
    print("=" * 60)

def get_or_create_private_keys():
    if os.path.exists(PRIVATE_KEYS_FILE):
        with open(PRIVATE_KEYS_FILE, "r") as f:
            return json.load(f)
    else:
        private_keys = []
        while True:
            key = input(f"{Fore.GREEN}Enter a private key (or press Enter to finish): {Style.RESET_ALL}").strip()
            if not key:
                break
            private_keys.append(key)
        with open(PRIVATE_KEYS_FILE, "w") as f:
            json.dump(private_keys, f)
        return private_keys

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

def automatic_transactions(web3, from_account):
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

def process_single_key(private_key, operation):
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not web3.is_connected():
        print(f"{Fore.RED}Failed to connect to the StratoVM network. Please check your internet connection and try again.{Style.RESET_ALL}")
        return

    from_account = Account.from_key(private_key)
    
    if operation == "transactions":
        automatic_transactions(web3, from_account)
    elif operation == "mint":
        mint_daily_nft(web3, from_account)

def auto_mint_job(private_keys):
    for key in private_keys:
        process_single_key(key, "mint")

def schedule_auto_mint(private_keys):
    schedule.every(25).hours.do(auto_mint_job, private_keys)
    
    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)

    thread = threading.Thread(target=run_schedule)
    thread.start()

def main_menu():
    private_keys = get_or_create_private_keys()
    auto_mint_enabled = False

    while True:
        print_header()
        print(f"{Fore.YELLOW}Main Menu:{Style.RESET_ALL}")
        print("1. Automatic Transactions")
        print("2. Mint Daily NFT")
        print("3. Daily Auto-Mint NFT")
        print("4. Exit")
        
        choice = input(f"{Fore.GREEN}Choose an option (1-4): {Style.RESET_ALL}")
        
        if choice in ['1', '2']:
            operation = "transactions" if choice == '1' else "mint"
            for key in private_keys:
                process_single_key(key, operation)
        elif choice == '3':
            auto_mint_enabled = not auto_mint_enabled
            if auto_mint_enabled:
                schedule_auto_mint(private_keys)
                print(f"{Fore.GREEN}Auto-Mint NFT enabled. It will run every 25 hours.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Auto-Mint NFT disabled.{Style.RESET_ALL}")
        elif choice == '4':
            print(f"{Fore.YELLOW}Thank you for using our service! Goodbye!{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}Invalid choice. Please choose 1, 2, 3, or 4.{Style.RESET_ALL}")
        
        if choice in ['1', '2']:
            delete_keys = get_yes_no_input("Do you want to delete the private keys file for security? (yes/no): ")
            if delete_keys:
                if os.path.exists(PRIVATE_KEYS_FILE):
                    print(f"{Fore.RED}Warning: If you delete the private keys, you won't be able to claim the Daily NFT automatically.{Style.RESET_ALL}")
                    confirm_delete = get_yes_no_input("Are you sure you want to delete the private keys? (yes/no): ")
                    if confirm_delete:
                        os.remove(PRIVATE_KEYS_FILE)
                        print(f"{Fore.YELLOW}Private keys file has been deleted.{Style.RESET_ALL}")
                        private_keys = []
                    else:
                        print(f"{Fore.GREEN}Private keys file has been kept.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Private keys file not found.{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}Private keys file has been kept.{Style.RESET_ALL}")
        
        input(f"{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")

if __name__ == "__main__":
    main_menu()
