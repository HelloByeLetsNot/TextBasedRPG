import json
import random
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
import threading
from PIL import Image, ImageTk

def load_json(file_name):
    try:
        with open(file_name, 'r') as file:
            data = json.load(file)
            if not data:
                raise ValueError(f"The file {file_name} is empty or contains invalid JSON.")
            return data
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error loading {file_name}: {e}")
        return []

locations = load_json('locations.json')
items = load_json('items.json')
npcs = load_json('npcs.json')
shops = load_json('shops.json')
leaderboard = load_json('leaderboard.json')

player = {"name": "", "location": {}, "inventory": [], "hp": 100, "attack": 1, "defense": 1, "gold": 100, "kills": 0}
current_shop = current_npc = None

def explore():
    global current_npc
    if player["location"].get("is_town", False):
        if random.random() < player["location"].get("encounter_rate", 0):
            current_npc = encounter_npc()
        elif random.random() < player["location"].get("drop_rate", 0):
            find_item()
        else:
            find_merchant()
    else:
        if random.random() < player["location"].get("encounter_rate", 0):
            current_npc = encounter_npc()
        if random.random() < player["location"].get("drop_rate", 0):
            find_item()
    update_hp_bars()

def travel(direction):
    player["location"] = random.choice(locations) if locations else {}
    update_status(f"You traveled {direction} and arrived at {player['location'].get('name', 'unknown place')}. {player['location'].get('description', '')}")

def encounter_npc():
    npc = random.choice(npcs) if npcs else {}
    update_status(f"You encountered a {npc.get('name', 'mysterious entity')}! {npc.get('dialogue', '')}")
    return npc

def find_item():
    item = random.choice(items) if items else {}
    player["inventory"].append(item)
    update_status(f"You found a {item.get('name', 'mysterious item')}!")

def find_merchant():
    global current_shop
    current_shop = random.choice(shops) if shops else {}
    update_status(f"You found a merchant in {current_shop.get('name', 'unknown place')}! {current_shop.get('description', '')} {current_shop.get('dialogue', '')}")
    update_status("Items for sale:")
    for item in current_shop.get("items", []):
        update_status(f"{item['name']}: {item['price']} gold")

def battle():
    global current_npc
    if current_npc:
        update_status("Battle starts!")
        while player["hp"] > 0 and current_npc.get("hp", 0) > 0:
            attack_roll = random.randint(1, 20) + player["attack"]
            defense_roll = random.randint(1, 20) + current_npc.get("defense", 0)
            if attack_roll > defense_roll:
                damage = attack_roll - defense_roll
                current_npc["hp"] -= damage
                update_status(f"You dealt {damage} damage to {current_npc['name']}.")
            else:
                damage = defense_roll - attack_roll
                player["hp"] -= damage
                update_status(f"{current_npc['name']} dealt {damage} damage to you.")
            update_hp_bars()
            if player["hp"] <= 0:
                update_status("You have been defeated!")
                update_leaderboard()
                new_game_prompt()
                return
            elif current_npc["hp"] <= 0:
                update_status(f"You defeated {current_npc['name']}!")
                player["kills"] += 1
                drop_items(current_npc.get("drops", []))
                current_npc = None
                update_hp_bars()
                return
    else:
        update_status("No NPC to attack.")

def drop_items(drops):
    for drop in drops:
        item = next((item for item in items if item["name"] == drop), {})
        player["inventory"].append(item)
        update_status(f"You received a {item.get('name', 'mysterious item')} from the defeated enemy.")

def equip_item(item_name):
    for item in player["inventory"]:
        if item["name"].lower() == item_name.lower():
            if item["type"] == "weapon":
                player["attack"] += item["stats"]["attack"]
            elif item["type"] == "armor":
                player["defense"] += item["stats"]["defense"]
            update_status(f"You equipped {item['name']}.")
            return
    update_status("Item not found in inventory.")

def use_item(item_name):
    for item in player["inventory"]:
        if item["name"].lower() == item_name.lower() and item["type"] == "consumable":
            if "hp_restore" in item["effect"]:
                player["hp"] += item["effect"]["hp_restore"]
                player["inventory"].remove(item)
                update_status(f"You used {item['name']} and restored {item['effect']['hp_restore']} HP.")
            return
    update_status("Item not found or not usable.")

def visit_shop(shop_name):
    for shop in shops:
        if shop["name"].lower() == shop_name.lower():
            global current_shop
            current_shop = shop
            update_status(f"You entered {shop['name']}. {shop['description']} {shop['dialogue']}")
            update_status("Items for sale:")
            for item in shop["items"]:
                update_status(f"{item['name']}: {item['price']} gold")
            return shop
    update_status("Shop not found.")
    return None

def buy_item(shop, item_name):
    for item in shop["items"]:
        if item["name"].lower() == item_name.lower():
            if player["gold"] >= item["price"]:
                player["gold"] -= item["price"]
                player["inventory"].append(next((i for i in items if i["name"] == item["name"]), {}))
                update_status(f"You bought {item['name']} for {item['price']} gold.")
                return
            else:
                update_status("You don't have enough gold.")
                return
    update_status("Item not found in shop.")

def sell_item(item_name):
    for item in player["inventory"]:
        if item["name"].lower() == item_name.lower():
            sale_price = next((i["price"] for shop in shops for i in shop["items"] if i["name"] == item["name"]), 0) // 2
            player["gold"] += sale_price
            player["inventory"].remove(item)
            update_status(f"You sold {item['name']} for {sale_price} gold.")
            return
    update_status("Item not found in inventory.")

def update_status(message):
    status_label.config(state=tk.NORMAL)
    status_label.insert(tk.END, message + "\n")
    status_label.config(state=tk.DISABLED)
    status_label.yview(tk.END)

def update_hp_bars():
    player_hp_var.set(f"HP: {player['hp']}")
    if current_npc:
        npc_hp_var.set(f"{current_npc['name']} HP: {current_npc['hp']}")
    else:
        npc_hp_var.set("")

def handle_command(event=None):
    command = command_entry.get().strip().lower()
    command_entry.delete(0, tk.END)
    threading.Thread(target=process_command, args=(command,)).start()

def process_command(command):
    if player["name"] == "":
        player["name"] = command
        start_game()
    else:
        if command == "explore":
            explore()
        elif command.startswith("travel"):
            direction = command.split()[1]
            travel(direction)
        elif command == "inventory":
            update_status("Your inventory:")
            for item in player["inventory"]:
                update_status(f"- {item['name']}: {item['description']}")
        elif command.startswith("equip"):
            item_name = command.split(" ", 1)[1]
            equip_item(item_name)
        elif command.startswith("use"):
            item_name = command.split(" ", 1)[1]
            use_item(item_name)
        elif command.startswith("shop"):
            shop_name = command.split(" ", 1)[1]
            visit_shop(shop_name)
        elif command.startswith("buy") and current_shop:
            item_name = command.split(" ", 1)[1]
            buy_item(current_shop, item_name)
        elif command.startswith("sell"):
            item_name = command.split(" ", 1)[1]
            sell_item(item_name)
        else:
            update_status("Unknown command. Please try again.")

def start_game():
    update_status(f"Welcome, {player['name']}!")
    player["location"] = random.choice(locations) if locations else {}
    update_status(f"Starting at {player['location'].get('name', 'an unknown place')}.")
    update_status(player["location"].get('description', ''))
    update_hp_bars()

def new_game_prompt():
    global player
    player = {"name": "", "location": {}, "inventory": [], "hp": 100, "attack": 1, "defense": 1, "gold": 100, "kills": 0}
    update_status("Please enter your name to start the game:")

def update_leaderboard():
    leaderboard.append({"name": player["name"], "kills": player["kills"]})
    leaderboard.sort(key=lambda x: x["kills"], reverse=True)
    with open('leaderboard.json', 'w') as file:
        json.dump(leaderboard, file, indent=4)
    leaderboard_var.set("\n".join([f"{entry['name']}: {entry['kills']} kills" for entry in leaderboard]))
    if leaderboard_window:
        update_leaderboard_popup()

def update_leaderboard_popup():
    leaderboard_text.delete(1.0, tk.END)
    leaderboard_text.insert(tk.END, "\n".join([f"{entry['name']}: {entry['kills']} kills" for entry in leaderboard]))

def leaderboard_popup():
    global leaderboard_window, leaderboard_text
    leaderboard_window = tk.Toplevel(root)
    leaderboard_window.title("Leaderboard")
    leaderboard_text = tk.Text(leaderboard_window, wrap="word", state=tk.NORMAL, height=20, width=40)
    leaderboard_text.pack(padx=10, pady=10)
    update_leaderboard_popup()

def commands_popup():
    commands_window = tk.Toplevel(root)
    commands_window.title("Commands")
    commands_text = tk.Text(commands_window, wrap="word", state=tk.NORMAL, height=20, width=40)
    commands_text.pack(padx=10, pady=10)
    commands_text.insert(tk.END, "Available commands:\n")
    commands_text.insert(tk.END, "explore - Explore the current location\n")
    commands_text.insert(tk.END, "travel <direction> - Travel in a direction (north, south, east, west)\n")
    commands_text.insert(tk.END, "inventory - Show your inventory\n")
    commands_text.insert(tk.END, "equip <item> - Equip an item from your inventory\n")
    commands_text.insert(tk.END, "use <item> - Use an item from your inventory\n")
    commands_text.insert(tk.END, "shop <name> - Visit a shop\n")
    commands_text.insert(tk.END, "buy <item> - Buy an item from the current shop\n")
    commands_text.insert(tk.END, "sell <item> - Sell an item from your inventory\n")
    commands_text.config(state=tk.DISABLED)

root = ThemedTk(theme="smog")
root.title("Text-Based RPG")

# Set the background image
background_image = Image.open("background.png")
bg_photo = ImageTk.PhotoImage(background_image)

background_label = tk.Label(root, image=bg_photo)
background_label.place(relwidth=1, relheight=1)

main_frame = ttk.Frame(root, padding="10")
main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

status_label = tk.Text(main_frame, wrap="word", height=20, width=60)
status_label.grid(row=0, column=0, columnspan=2)

button_frame = ttk.Frame(main_frame)
button_frame.grid(row=1, column=0, columnspan=2, pady=10)

leaderboard_button = ttk.Button(button_frame, text="Leaderboard", command=leaderboard_popup)
leaderboard_button.grid(row=0, column=0, padx=5)

commands_button = ttk.Button(button_frame, text="Commands", command=commands_popup)
commands_button.grid(row=0, column=1, padx=5)

command_entry = ttk.Entry(main_frame, width=50)
command_entry.grid(row=2, column=0, pady=5)

command_entry.bind("<Return>", handle_command)

command_button = ttk.Button(main_frame, text="Enter", command=handle_command)
command_button.grid(row=2, column=1, pady=5)

player_hp_var = tk.StringVar()
player_hp_label = ttk.Label(main_frame, textvariable=player_hp_var)
player_hp_label.grid(row=3, column=0, pady=5)

npc_hp_var = tk.StringVar()
npc_hp_label = ttk.Label(main_frame, textvariable=npc_hp_var)
npc_hp_label.grid(row=3, column=1, pady=5)

leaderboard_var = tk.StringVar()
leaderboard_window = None

update_leaderboard()
update_hp_bars()

new_game_prompt()

root.mainloop()