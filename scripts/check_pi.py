from web3 import Web3
import json

def main():
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
    with open('./build/contracts/PiContr.json') as f:
        contract_json = json.load(f)
        abi = contract_json['abi']

    pi_contract_address = contract_json['networks']['5777']['address']
    contract = w3.eth.contract(address=pi_contract_address, abi=abi)

    print(f"Pi Contract: {contract.address}")


    print("Функции в ABI:")
    for f in abi:
        if f.get("type") == "function":
            print(" -", f["name"])

    with open('./build/contracts/MyToken.json') as f:
        token_contract_json = json.load(f)
        token_abi = token_contract_json['abi']
    token_address = token_contract_json['networks']['5777']['address']
    token_contract = w3.eth.contract(address=token_address, abi=token_abi)

    print(f"Token Contract: {token_contract.address}")
    print(f"Token contract address in PiContr: {contract.functions.token().call()}")

    with open('pi.txt', 'r') as file:
        pi = file.read().replace('\n', '')

    while True:
        user_choose = input("\n\n\n\nВведите y для проверки, иначе будет производится покупка(exit для выхода): ").strip().upper()
        if user_choose == "Y":
            print("Выбран режим ПРОВЕРКИ")
            (sequence, seq_ent) = append_data(pi)

            if sequence is None or seq_ent is None:
                print("Failed, retrying")
                continue

            seq_ent = int(seq_ent)
            
            bought_sq = str(f"{sequence}-{seq_ent}")

            print(f"Последовательность найдена в числе π!")

            res = contract.functions.checkSequence(sequence, bought_sq, seq_ent).call()

            if res[0] == "0x0000000000000000000000000000000000000000" and res[1] == 0:
                print("Данная последовательность никому не принадлежит")
            else:
                print(f"Данная последовательность принадлежит {res[0]} начиная с индекса {res[1]} и значением: {res[2]}")

            continue
        
        elif user_choose == "EXIT":
            break

        print("Выбран режим ПОКУПКИ")
        temp_acc = input("Введите аддресс аккаунта, который собирается покупать (default: 1 acc): ").strip();
        if not temp_acc:
            temp_acc = "1"
        if not temp_acc.startswith("0x") and temp_acc.isdigit():
            try:
                account = w3.eth.accounts[int(temp_acc)]
            except Exception as e:
                print(e)
                continue
        elif not temp_acc.startswith("0x"):
            print("Invalid account")
            continue
        else:
            account = temp_acc

        try:
            print("Working on account: ", account)
            balance = token_contract.functions.balanceOf(account).call()
            print(f"Token balance: {balance} for {account}")
        except:
            print("Unknown address, retry")
            continue

        (sequence, seq_ent) = append_data(pi)

        if sequence is None or seq_ent is None:
            print("Failed, retrying")
            continue

        seq_ent = int(seq_ent)
        
        bought_sq = str(f"{sequence}-{seq_ent}")

        print(f"Последовательность найдена в числе π!")

        token_price = contract.functions.price().call()
        print("Token price:", token_price)

        try:
            print("Approving tokens for the purchase...")
            approve_tx = token_contract.functions.approve(pi_contract_address, token_price).transact({
                'from': account
            })
            approve_receipt = w3.eth.wait_for_transaction_receipt(approve_tx)
            print("Approval successful. Tx hash:", approve_receipt.transactionHash.hex())
        except Exception as e:
            print("Ошибка во время approve:", e)
            continue

        try:
            print("Покупка последовательности, отправка транзакции buySequence...")
            tx_hash = contract.functions.buySequence(sequence, bought_sq, seq_ent).transact({
                'from': account
            })
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            print("Ошибка во время покупки:", e)
            continue

        print("Покупка завершена!")
        print("Tx hash:", receipt.transactionHash.hex())

        info = contract.functions.getSequenceInfo(bought_sq).call()
        print("Владелец:", info[0])
        print("Индекс в π start:", info[1])
        print("Индекс в π end:", info[2])
        print("Tx Hash (локальный):", info[3].hex())
        print("Sequence:", info[4])


def append_data(pi):
    sequence = input("Введите последовательность, которую хотите купить: ").strip()

    if not(sequence != '' and sequence.isdigit() and int(sequence) > 0):
        print("Not a digit or empty")
        return None, None

    seq_occ = find_seq_in_pi(pi, sequence)

    if len(seq_occ) == 0:
        print("This sequence not in a 1M pi symbols")
        return None, None
    else:
        print(f"Found next entries {seq_occ}")

    seq_num = input("Введите номер вхождения, который хотите купить: ").strip()

    if not(seq_num != '' and seq_num.isdigit()):
        print("Not a digit or empty")
        return None, None
    
    if int(seq_num) not in seq_occ:
        print("Entry don't exists")
        return None, None
    
    return sequence, seq_num

def find_seq_in_pi(pi_str, s):
    indices = []
    index = pi_str.find(s)
    while index != -1:
        indices.append(index + 2)
        index = pi_str.find(s, index + 1)
    return indices

if __name__ == "__main__":
    main()
