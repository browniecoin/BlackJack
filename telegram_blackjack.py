from telegram import Update
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, CallbackContext, CallbackQueryHandler
import random
import requests
import hashlib
import uuid  # Import the uuid module
import json
from web3 import Web3
from eth_utils import is_address
import re
from telegram import ParseMode
import urllib.parse
import base64
from telegram import InputFile
from PIL import Image
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

contract_address = "0x"
private_key = "replace with payout wallet private key here"
from_address = "0x"
token_name = "BROWNIE"
botfather_token = "replace with token"
card_folder = "cards"
decks_foler = "decks"


def gen_image(player_hand,dealer_hand):
    card_images = []
    for card in player_hand:
        img_file_name = f"{card_folder}/{card['suit']}.{card['rank']}.png"
        try:
            card_image = Image.open(img_file_name)
            card_images.append(card_image)
        except Exception as e:
            print(f"Error opening image: {str(e)}")
    for card in dealer_hand:
        img_file_name = f"{card_folder}/{card['suit']}.{card['rank']}.png"
        try:
            card_image = Image.open(img_file_name)
            card_images.append(card_image)
        except Exception as e:
            print(f"Error opening image: {str(e)}")
    max_width = max([card.width for card in card_images])
    larger_hand = max(len(player_hand), len(dealer_hand))
    total_width = max_width * larger_hand
    max_height = max([card.height for card in card_images]) + 200
    combined_image = Image.new('RGB', (total_width, max_height * 2), (255, 255, 255))
    #combined_image = Image.new('RGB', (total_width, max_height * 2))  # Multiply max_height by 2 for two rows
    x_offset = 0
    y_offset = 200  # For the first row (player_hand)
    combined_image.paste(Image.open("player_card.png"), (0, 0))

    for card_image in card_images[:len(player_hand)]:
        combined_image.paste(card_image, (x_offset, y_offset))
        x_offset += card_image.width
    x_offset = 0 # Update the y_offset for the second row (dealer_hand)
    y_offset = max_height + 200 # For the second row (dealer_hand)

    combined_image.paste(Image.open("dealer_card.png"), (0, max_height))

    for card_image in card_images[len(player_hand):]:
        combined_image.paste(card_image, (x_offset, y_offset))
        x_offset += card_image.width
    output_buffer = BytesIO()
    combined_image.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    return output_buffer

def is_valid_single_character(text):
    # Ensure the string is a single character
    if len(text) != 1:
        return False

    # Convert the character to uppercase
    text = text.upper()

    # Check if it's a valid character
    if ('0' <= text <= '9') or ('A' <= text <= 'F'):
        return True
    else:
        return False

def calculate_hand_value(hand):
    value = 0
    num_aces = 0

    for card in hand:
        card_rank = card['rank']
        if card_rank in ['Jack', 'Queen', 'King']:
            value += 10
        elif card_rank == 'Ace':
            value += 11
            num_aces += 1
        else:
            value += int(card_rank)

    while num_aces > 0 and value > 21:
        value -= 10
        num_aces -= 1

    return value

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}!',
        reply_markup=None,
    )
# Define a function to handle the button click
def handle_button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = update.effective_user.id
    # Check the callback data
    if query.data == 'button_clicked_100':
        with open(f"{decks_foler}/bet_{user_id}.txt", "w") as file:
            file.write("100")
        deal_cards(update, context)
    elif query.data == 'button_clicked_200':
        with open(f"{decks_foler}/bet_{user_id}.txt", "w") as file:
            file.write("200")
        deal_cards(update, context)
    elif query.data == 'button_clicked_500':
        with open(f"{decks_foler}/bet_{user_id}.txt", "w") as file:
            file.write("500")
        deal_cards(update, context)
    elif query.data == 'button_clicked_1000':
        with open(f"{decks_foler}/bet_{user_id}.txt", "w") as file:
            file.write("1000")
        deal_cards(update, context)
    elif query.data == 'button_clicked_5000':
        with open(f"{decks_foler}/bet_{user_id}.txt", "w") as file:
            file.write("5000")
        deal_cards(update, context)
    elif query.data == 'button_clicked_10000':
        with open(f"{decks_foler}/bet_{user_id}.txt", "w") as file:
            file.write("10000")
        deal_cards(update, context)
    elif query.data == 'button_clicked_hit':
        # Send a response when the button is clicked
        # Load the deck, player hand, and dealer hand from files

        score_file_name = f"{decks_foler}/score_{user_id}.txt"
        deck_file_name = f"{decks_foler}/deck_{user_id}.txt"
        player_hand_file_name = f"{decks_foler}/player_hand_{user_id}.txt"
        dealer_hand_file_name = f"{decks_foler}/dealer_hand_{user_id}.txt"


        bet_amount = 1  # Default bet amount
        try:
            with open(f"{decks_foler}/bet_{user_id}.txt", "r") as file:
                bet_amount = int(file.read().strip())
                if bet_amount == 0:
                    query.message.reply_text("Deal Again Bet is finished")
                    return # Read the content of the file and remove leading/trailing spaces
        except FileNotFoundError:
            # Handle the case when the file doesn't exist
            pass

        try:
            with open(deck_file_name, 'r') as file:
                deck_json = file.read()
                deck = json.loads(deck_json)
        except FileNotFoundError:
            # Handle the case when the file doesn't exist or other exceptions
            deck = []

        try:
            with open(player_hand_file_name, 'r') as file:
                player_hand_json = file.read()
                player_hand = json.loads(player_hand_json)
        except FileNotFoundError:
            # Handle the case when the file doesn't exist or other exceptions
            player_hand = []

        try:
            with open(dealer_hand_file_name, 'r') as file:
                dealer_hand_json = file.read()
                dealer_hand = json.loads(dealer_hand_json)
        except FileNotFoundError:
            # Handle the case when the file doesn't exist or other exceptions
            dealer_hand = []

        # Deal another card to the player
        if len(deck) > 0:
            new_card = deck.pop()
            player_hand.append(new_card)

            # Update the player's hand file with the new card
            player_hand_json = json.dumps(player_hand)
            with open(player_hand_file_name, 'w') as file:
                file.write(player_hand_json)

            # Update the deck file without the dealt card
            deck_json = json.dumps(deck)
            with open(deck_file_name, 'w') as file:
                file.write(deck_json)

        # Calculate the updated values of the player's and dealer's hands
        player_value = calculate_hand_value(player_hand)

        # Construct a message with the updated player's hand
        message = "Player's Hand:\n"
        for card in player_hand:
            message += f"{card['rank']} of {card['suit']}\n"

        message += f"Player's Hand Value: {player_value}\n\nDealer's Hand:\n"

        # Display only the last card in the dealer's hand
        last_card = dealer_hand[-1]
        message += f"{last_card['rank']} of {last_card['suit']}\n"

        dealer_hand.pop(0)  # Remove the first card from the dealer's hand.
        dealer_value = calculate_hand_value(dealer_hand)

        message += f"Dealer's Hand Value: {dealer_value}\n"
        is_bust = False
        # Send the message as a reply
        if player_value > 21 :
            try:
                with open(score_file_name, "r") as file:
                    current_score = int(file.read())
            except FileNotFoundError:
                # If the file doesn't exist, initialize the score to 0
                current_score = 0
            current_score -= bet_amount
            with open(score_file_name, "w") as file:
                file.write(str(current_score))
            message += f"Player Bust Game Over \nPayout Total {current_score} {token_name}\n"
            is_bust = True
            with open(f"{decks_foler}/bet_{user_id}.txt", "w") as file:
                file.write("0")

        query.message.reply_photo(photo=InputFile(gen_image(player_hand, dealer_hand), filename="combined_cards.png"))
        query.message.reply_text(message)
        if not is_bust :
            button = InlineKeyboardButton(text="HIT", callback_data='button_clicked_hit')
            button2 = InlineKeyboardButton(text="STAY", callback_data='button_clicked_stay')
            keyboard = [[button, button2]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send the message with the clickable button
            query.message.reply_text("Please click the button below:", reply_markup=reply_markup)

    elif query.data == 'button_clicked_stay':
        # Send a response when the button is clicked
        #query.message.reply_text("You clicked the button! Stay")
        score_file_name = f"{decks_foler}/score_{user_id}.txt"
        deck_file_name = f"{decks_foler}/deck_{user_id}.txt"
        player_hand_file_name = f"{decks_foler}/player_hand_{user_id}.txt"
        dealer_hand_file_name = f"{decks_foler}/dealer_hand_{user_id}.txt"

        bet_amount = 1  # Default bet amount

        try:
            with open(f"{decks_foler}/bet_{user_id}.txt", "r") as file:

                bet_amount = int(file.read().strip())  # Read the content of the file and remove leading/trailing spaces

                if bet_amount == 0 :
                    query.message.reply_text("Deal Again Bet is finished")
                    return

        except FileNotFoundError:
            # Handle the case when the file doesn't exist
            print("Finished Stay Request pass")
            pass

        print("Finished Stay Request")
        try:
            with open(deck_file_name, 'r') as file:
                deck_json = file.read()
                deck = json.loads(deck_json)
        except FileNotFoundError:
            # Handle the case when the file doesn't exist or other exceptions
            deck = []

        try:
            with open(player_hand_file_name, 'r') as file:
                player_hand_json = file.read()
                player_hand = json.loads(player_hand_json)
        except FileNotFoundError:
            # Handle the case when the file doesn't exist or other exceptions
            player_hand = []

        try:
            with open(dealer_hand_file_name, 'r') as file:
                dealer_hand_json = file.read()
                dealer_hand = json.loads(dealer_hand_json)
        except FileNotFoundError:
            # Handle the case when the file doesn't exist or other exceptions
            dealer_hand = []

        while calculate_hand_value(dealer_hand) < 17:
            if len(deck) > 0:
                new_card = deck.pop()
                dealer_hand.append(new_card)

                # Update the dealer's hand file with the new card
                dealer_hand_json = json.dumps(dealer_hand)
                with open(dealer_hand_file_name, 'w') as file:
                    file.write(dealer_hand_json)

                # Update the deck file without the dealt card
                deck_json = json.dumps(deck)
                with open(deck_file_name, 'w') as file:
                    file.write(deck_json)

        # Calculate the updated values of the player's and dealer's hands
        player_value = calculate_hand_value(player_hand)
        dealer_value = calculate_hand_value(dealer_hand)

        # Construct a message with the final hands
        message = "Player's Hand:\n"
        for card in player_hand:
            message += f"{card['rank']} of {card['suit']}\n"

        message += f"Player's Hand Value: {player_value}\n\nDealer's Hand:\n"
        for card in dealer_hand:
            message += f"{card['rank']} of {card['suit']}\n"

        message += f"Dealer's Hand Value: {dealer_value}\n"

        # Determine the winner
        if player_value > 21:
            message += "Player Bust. Dealer Wins!\n"
        elif dealer_value > 21 or player_value > dealer_value:
            try:
                with open(score_file_name, "r") as file:
                    current_score = int(file.read())
            except FileNotFoundError:
                # If the file doesn't exist, initialize the score to 0
                current_score = 0
            current_score += bet_amount
            with open(score_file_name, "w") as file:
                file.write(str(current_score))
            message += f"Player Wins! \nPayout Total {current_score} {token_name}\n"

        elif player_value == dealer_value:
            message += "It's a Tie!\n"
        else:
            try:
                with open(score_file_name, "r") as file:
                    current_score = int(file.read())
            except FileNotFoundError:
                # If the file doesn't exist, initialize the score to 0
                current_score = 0
            current_score -= bet_amount

            with open(score_file_name, "w") as file:
                file.write(str(current_score))
            message += f"Dealer Wins! \nPayout Total {current_score} {token_name}\n"

        with open(f"{decks_foler}/bet_{user_id}.txt", "w") as file:
            file.write("0")
        print("Finished Stay Request")
        query.message.reply_photo(photo=InputFile(gen_image(player_hand, dealer_hand), filename="combined_cards.png"))
        query.message.reply_text(message)

def handle_text(update: Update, context: CallbackContext) -> None:
    # Get the text of the message
    text = update.message.text

    # Check if the message contains "CA" (case-insensitive)

    if "HELP" == text.upper():
        message = f"DEAL 500\n [Start new game with the bet amount of 500, change the value to change bet ammount, max bet is 1,000,000]\n"
        message += f"SET WALLET 0xsampleaddress\n [Set wallet addres to cash out winnings to wallet address]\n"
        message += f"CASH OUT\n [Cash out winnings to wallet address]\n"
        update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    if "---CASH OUT" == text.upper():
        user_id = update.effective_user.id
        message = ""
        current_score = 0
        score_file_name = f"{decks_foler}/score_{user_id}.txt"
        try:
            with open(score_file_name, "r") as file:
                current_score = int(file.read())
        except FileNotFoundError:
            # If the file doesn't exist, initialize the score to 0
            current_score = 0

        if current_score > 1000:
            #Transfer function
            url = f"https://browniecoins.org/home/get_wallet/?tg_id={update.effective_user.id}"
            print(url)
            response = requests.get(url)
            to_address = response.text.strip()
            ethereum_rpc_url = "https://mainnet.infura.io/v3/2d268dafebd547468e00356bd161a545"
            web3 = Web3(Web3.HTTPProvider(ethereum_rpc_url))


            # ADD LOGIC TO MOVE ERC20 token
            # Define the ABI for the ERC20 token contract
            contract_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "type": "function",
                },
                {
                    "constant": False,
                    "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
                    "name": "transfer",
                    "outputs": [{"name": "", "type": "bool"}],
                    "type": "function",
                }
            ]



            # Create a contract instance
            contract = web3.eth.contract(address=contract_address, abi=contract_abi)

            # Check the balance of the sender address
            from_balance = contract.functions.balanceOf(from_address).call()

            # Define the recipient address
            print(from_balance)
            to_address = response.text.strip()  # This should be the recipient's address
            print(to_address)
            # Define the amount of tokens to transfer (in the smallest unit, e.g., Wei)
            amount_to_transfer = current_score  # Replace with the actual amount
            print(amount_to_transfer)
            # Ensure you have enough balance to perform the transfer
            if from_balance >= amount_to_transfer:
                current_gas_price = web3.eth.gas_price
                new_amount_to_transfer= web3.to_wei(amount_to_transfer, 'ether')
                transaction = contract.functions.transfer(to_address, new_amount_to_transfer).build_transaction({
                    'chainId': 1,  # Mainnet
                    'gas': 50000,  # You may need to adjust the gas limit
                    'gasPrice': current_gas_price,  # Adjust the gas price as needed
                    'nonce': web3.eth.get_transaction_count(from_address),
                })
                signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
                transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
                message += f"{token_name} out {current_score} {token_name}.\n"
                with open(score_file_name, "w") as file:
                    file.write(str(0))

        else:
            message += f"Can't {token_name} out {current_score} {token_name}. Min amount is 1,000, Oh, ya.\n"

        update.message.reply_text(message)



    if "MY WALLET" in text.upper() or text.upper() == "-W":
        url = f"https://browniecoins.org/home/get_wallet/?tg_id={update.effective_user.id}"
        print(url)
        response = requests.get(url)

        ethereum_rpc_url = "https://mainnet.infura.io/v3/2d268dafebd547468e00356bd161a545"
        web3 = Web3(Web3.HTTPProvider(ethereum_rpc_url))
        contract_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function",
            }
        ]
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)
        wallet_address = response.text.strip()
        if not is_address(wallet_address):
            print("Invalid Ethereum address")
            update.message.reply_text(f"Payout Wallet {response.text} Invalid Ethereum address")
        else:
            balance = contract.functions.balanceOf(wallet_address).call()
            balance_in_wei = balance
            balance_in_eth = int(balance / 1e18)
            formatted_balance = "{:,}".format(balance_in_eth)
            print(f"Balance of {wallet_address}: {balance} ETH")
            update.message.reply_text(f"Payout Wallet {response.text} Balance {formatted_balance} {token_name}")

    if "MY PAY WALLET" in text.upper() or text.upper() == "-WP":
        url = f"https://browniecoins.org/home/get_wallet_pay/?tg_id={update.effective_user.id}"
        print(url)
        response = requests.get(url)
        ethereum_rpc_url = "https://mainnet.infura.io/v3/2d268dafebd547468e00356bd161a545"
        web3 = Web3(Web3.HTTPProvider(ethereum_rpc_url))
        contract_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function",
            }
        ]
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)
        wallet_address = response.text.strip()
        if not is_address(wallet_address):
            print("Invalid Ethereum address")
            update.message.reply_text(f"Fund Wallet {response.text} Invalid Ethereum address")
        else:
            balance = contract.functions.balanceOf(wallet_address).call()
            balance_in_wei = balance
            balance_in_eth = balance / 1e18
            print(f"Balance of {wallet_address}: {balance_in_eth} ETH")
            update.message.reply_text(f"Fund Wallet {response.text} Balance {balance_in_eth} {token_name}")


    if "SET WALLET" in text.upper() or text.upper() == "-S":
        words = text.split()
        wallet_id = words[-1]
        url = f"https://browniecoins.org/home/add_wallet/?tg_id={update.effective_user.id}&wallet_id={wallet_id}"
        response = requests.get(url)
        update.message.reply_text(f"Wallet {response.text}")

    if text.upper() == "P":
        last_digit = text[-1]
        url = f"https://browniecoins.org/home/get_magic_key_prize/?tg_id={update.effective_user.id}"
        response = requests.get(url)
        formatted_response = "{:,}".format(int(response.text))
        update.message.reply_text(f"The prize total {formatted_response}")

    if len(text) == 1 and (('0' <= text.upper() <= '9') or ('A' <= text.upper() <= 'F')):
        last_digit = text
        url = f"https://browniecoins.org/home/add_magic_key/?tg_id={update.effective_user.id}&magic_key_guess={last_digit}"
        response = requests.get(url)
        update.message.reply_text(f"Guess {response.text}")

    if text.upper() == "K":
        url = "https://api.browniecoins.org/getLastblockhash.jsp"
        response = requests.get(url)
        if response.status_code == 200:
            response_text = response.text
            response_text = response_text.strip()
            last_digit = response_text[-1]
            #update.message.reply_text(f"{update.effective_user.id} Current Magic Key {last_digit}")
            update.message.reply_text(f"Current Magic Key {last_digit}")
            print("Last Digit:", last_digit)
        else:
            print("Failed to retrieve data. Status code:", response.status_code)

    if "-M-EME" in text.upper():
        random_number = str(random.randint(1, 616))
        update.message.reply_text(f"https://browniecoins.org/images/meme/{random_number}.gif")

def deal_cards(update: Update, context: CallbackContext):

    user_id = update.effective_user.id
    query = update.callback_query

    bet_amount = 1  # Default bet amount
    try:
        with open(f"{decks_foler}/bet_{user_id}.txt", "r") as file:
            bet_amount = int(file.read().strip())  # Read the content of the file and remove leading/trailing spaces
    except FileNotFoundError:
        # Handle the case when the file doesn't exist
        print("Finished Stay Request pass")
        pass

    # Your deck creation code (from the previous answer)
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    ranks = ['Ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King']

    deck = [{'id': str(uuid.uuid4()), 'rank': rank, 'suit': suit} for suit in suits for rank in ranks]

    # Shuffle the deck
    random.shuffle(deck)

    # Deal two cards to the player and two cards to the dealer
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]

    player_hand_json = json.dumps(player_hand)
    player_hand_file_name = f"{decks_foler}/player_hand_{user_id}.txt"
    with open(player_hand_file_name, 'w') as file:
        file.write(player_hand_json)

    dealer_hand_json = json.dumps(dealer_hand)
    dealer_hand_file_name = f"{decks_foler}/dealer_hand_{user_id}.txt"
    with open(dealer_hand_file_name, 'w') as file:
        file.write(dealer_hand_json)

    deck_json = json.dumps(deck)
    file_name = f"{decks_foler}/deck_{user_id}.txt"
    with open(file_name, 'w') as file:
        file.write(deck_json)

    # Function to calculate the value of a hand

    # Calculate the values of the player's and dealer's hands
    player_value = calculate_hand_value(player_hand)

    # Printing the shuffled deck
    shuffled_deck_text = "\n".join([f"{card['rank']} of {card['suit']}" for card in deck])

    # Construct a message with the shuffled deck and initial hands
    #message = f"Shuffled Deck Hash:\n{hashlib.sha256(shuffled_deck_text.encode()).hexdigest()}\n\nPlayer's Hand:\n"
    message = f"Player's Hand:\n"

    for card in player_hand:
        message += f"{card['rank']} of {card['suit']}\n"

    message += f"Player's Hand Value: {player_value}\n\nDealer's Hand:\n"

    # Display only the last card in the dealer's hand
    last_card = dealer_hand[-1]
    message += f"{last_card['rank']} of {last_card['suit']}\n"

    dealer_hand.pop(0)  # Remove the first card from the dealer's hand.
    dealer_value = calculate_hand_value(dealer_hand)

    message += f"Dealer's Hand Value: {dealer_value}\n Bet Amount {bet_amount} {token_name}"


    # Send the message as a reply
    query.message.reply_photo(photo=InputFile(gen_image(player_hand, dealer_hand), filename="combined_cards.png"))
    query.message.reply_text(message)
    button = InlineKeyboardButton(text="HIT", callback_data='button_clicked_hit')
    button2 = InlineKeyboardButton(text="STAY", callback_data='button_clicked_stay')
    keyboard = [[button, button2]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with the clickable button
    query.message.reply_text("Please click the button below:", reply_markup=reply_markup)

def deal(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    button100 = InlineKeyboardButton(text="100", callback_data='button_clicked_100')
    button200 = InlineKeyboardButton(text="200", callback_data='button_clicked_200')
    button500 = InlineKeyboardButton(text="500", callback_data='button_clicked_500')
    button1000 = InlineKeyboardButton(text="1000", callback_data='button_clicked_1000')
    button5000 = InlineKeyboardButton(text="5000", callback_data='button_clicked_5000')
    button10000 = InlineKeyboardButton(text="10000", callback_data='button_clicked_10000')
    keyboard = [[button100, button200, button500, button1000, button5000, button10000]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with the clickable button
    update.message.reply_text("Select Play Amount:", reply_markup=reply_markup)


def handle_deal_command(update: Update, context: CallbackContext):
    # Your logic for handling the /example command
    deal(update, context)

def handle_cashout_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    message = ""
    current_score = 0
    score_file_name = f"{decks_foler}/score_{user_id}.txt"
    try:
        with open(score_file_name, "r") as file:
            current_score = int(file.read())
    except FileNotFoundError:
        # If the file doesn't exist, initialize the score to 0
        current_score = 0

    if current_score > 1000:
        #Transfer function
        url = f"https://browniecoins.org/home/get_wallet/?tg_id={update.effective_user.id}"
        print(url)
        response = requests.get(url)
        to_address = response.text.strip()
        ethereum_rpc_url = "https://mainnet.infura.io/v3/2d268dafebd547468e00356bd161a545"
        web3 = Web3(Web3.HTTPProvider(ethereum_rpc_url))


        # ADD LOGIC TO MOVE ERC20 token
        # Define the ABI for the ERC20 token contract
        contract_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function",
            },
            {
                "constant": False,
                "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function",
            }
        ]



        # Create a contract instance
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)

        # Check the balance of the sender address
        from_balance = contract.functions.balanceOf(from_address).call()

        # Define the recipient address
        print(from_balance)
        to_address = response.text.strip()  # This should be the recipient's address
        print(to_address)
        # Define the amount of tokens to transfer (in the smallest unit, e.g., Wei)
        amount_to_transfer = current_score  # Replace with the actual amount
        print(amount_to_transfer)
        # Ensure you have enough balance to perform the transfer
        print(from_balance)
        if from_balance >= amount_to_transfer:
            print(from_balance)
            current_gas_price = web3.eth.gas_price
            new_amount_to_transfer= web3.to_wei(amount_to_transfer, 'ether')
            transaction = contract.functions.transfer(to_address, new_amount_to_transfer).build_transaction({
                'chainId': 1,  # Mainnet
                'gas': 50000,  # You may need to adjust the gas limit
                'gasPrice': current_gas_price,  # Adjust the gas price as needed
                'nonce': web3.eth.get_transaction_count(from_address),
            })
            signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
            transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            message += f"{token_name} out {current_score} {token_name}. Oh, you are big boy now.\n"
            with open(score_file_name, "w") as file:
                file.write(str(0))
        else:
            message += f"Can't Cash Out {amount_to_transfer} {token_name}, Bank Wallet Balance is {from_balance} {token_name}"
    else:
        message += f"Can't {token_name} out {current_score} {token_name}. Min amount is 1,000, Oh, ya.\n"


    update.message.reply_text(message)

def main() -> None:
    # Initialize the bot with your API token
    updater = Updater(botfather_token, use_context=True)

    dp = updater.dispatcher

    # Add a command handler for the /start command
    dp.add_handler(CommandHandler("start", start))

    # Add a message handler to respond to text messages containing "hello"
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    dp.add_handler(CallbackQueryHandler(handle_button))
    # Start the bot

    # Add a command handler for the /example command
    dp.add_handler(CommandHandler("deal", handle_deal_command))

    # Add a command handler for the /example command
    dp.add_handler(CommandHandler("cashout", handle_cashout_command))


    updater.start_polling()

    # Run the bot until you manually stop it
    updater.idle()

if __name__ == '__main__':
    main()
