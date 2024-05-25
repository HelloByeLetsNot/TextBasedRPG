import json
import random
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk

class RPGGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Text-Based RPG")
        self.create_widgets()
        self.load_data()
        self.start_game()

    def create_widgets(self):
        self.output_frame = ttk.Frame(self.master)
        self.output_frame.pack(padx=10, pady=10, fill='both', expand=True)

        self.output = tk.Text(self.output_frame, wrap='word', state='disabled', bg='#2c3e50', fg='#e0e0e0')
        self.output.pack(padx=10, pady=10, fill='both', expand=True)

        self.input_frame = ttk.Frame(self.master)
        self.input_frame.pack(padx=10, pady=10, fill='x')

        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(self.input_frame, textvariable=self.input_var)
        self.input_entry.pack(side='left', padx=5, pady=5, fill='x', expand=True)
        self.input_entry.bind('<Return>', self.handle_input)

        self.enter_button = ttk.Button(self.input_frame, text="Enter", command=self.handle_input)
        self.enter_button.pack(side='right', padx=5, pady=5)

        self.leaderboard_frame = ttk.Frame(self.master)
        self.leaderboard_frame.pack(padx=10, pady=10, fill='x')

        self.leaderboard_label = ttk.Label(self.leaderboard_frame, text="Leaderboard")
        self.leaderboard_label.pack(padx=10, pady=5)

        self.leaderboard = tk.Text(self.leaderboard_frame, wrap='word', state='disabled', bg='#2c3e50', fg='#e0e0e0', height=10)
        self.leaderboard.pack(padx=10, pady=5, fill='x')

    def load_data(self):
        with open('locations.json') as f:
            self.areas = json.load(f)
        with open('npcs.json') as f:
            self.npcs = json.load(f)
        self.player_hp = 100
        self.player_gold = 10
        self.player_inventory = []
        self.navigation_count = 0
        self.current_area = 'forest'
        self.current_npc = None
        self.username = 'Player'
        self.player_xp = 0
        self.player_level = 1

        try:
            with open('leaderboard.json') as f:
                self.leaderboard_data = json.load(f)
        except FileNotFoundError:
            self.leaderboard_data = []

    def start_game(self):
        self.output_message(f"Welcome to the game, {self.username}! You start in a forest. {self.areas[self.current_area]['description']}")
        self.update_leaderboard()

    def output_message(self, message):
        self.output.config(state='normal')
        self.output.insert(tk.END, message + "\n")
        self.output.config(state='disabled')
        self.output.see(tk.END)

    def handle_input(self, event=None):
        command = self.input_var.get()
        self.input_var.set("")
        self.process_command(command)

    def process_command(self, command):
        parts = command.split(' ')
        main_command = parts[0].toLowerCase()
        argument = ' '.join(parts[1:])

        if main_command == 'go':
            self.move(argument)
        elif main_command == 'explore':
            self.explore()
        elif main_command == 'attack':
            self.attack(argument)
        elif main_command == 'trade':
            self.trade(argument)
        elif main_command == 'buy':
            self.buy(argument)
        elif main_command == 'sell':
            self.sell(argument)
        elif main_command == 'leave':
            self.leave()
        elif main_command == 'help':
            self.show_help()
        elif main_command == 'end':
            self.end_game()
        elif main_command == 'inventory':
            self.show_inventory()
        else:
            pass  # Do nothing for unknown commands

    def move(self, direction):
        if not self.areas[self.current_area].get('exits') or not self.areas[self.current_area]['exits'].get(direction):
            self.output_message("You can't go that way.")
            return
        self.current_area = self.areas[self.current_area]['exits'][direction]
        self.navigation_count += 1
        self.output_message(f"You move {direction} to the {self.current_area}. {self.areas[self.current_area]['description']}")
        self.explore()

    def explore(self):
        if random.random() < 0.4:
            npcs_in_area = self.areas[self.current_area]['npcs']
            npc_name = random.choice(npcs_in_area)
            self.current_npc = self.npcs[npc_name]
            self.output_message(f"You encounter a {self.current_npc['name']}. {self.current_npc['responses'][0]}")
        else:
            self.output_message("You find nothing of interest.")

    def attack(self, target):
        if not self.current_npc:
            self.output_message("There is no one to attack.")
            return

        player_roll = random.randint(1, 20)
        npc_roll = random.randint(1, 20)

        self.output_message(f"You roll a {player_roll} to attack.")
        self.output_message(f"{self.current_npc['name']} rolls a {npc_roll} to defend.")

        if player_roll == 1:
            self.player_hp -= 1
            self.output_message("You fumble and hurt yourself!")
        elif player_roll == 20:
            self.current_npc['health'] -= 10
            self.output_message(f"Critical hit! You deal 10 damage to the {self.current_npc['name']}.")
        elif player_roll > npc_roll:
            self.current_npc['health'] -= (player_roll - npc_roll)
            self.output_message(f"You hit the {self.current_npc['name']} for {player_roll - npc_roll} damage.")
        else:
            self.output_message("You miss.")

        if self.current_npc['health'] <= 0:
            self.output_message(f"You have defeated the {self.current_npc['name']}.")
            self.add_item_to_inventory('gold', 5)
            self.player_xp += 10
            self.output_message(f"You find 5 gold on the {self.current_npc['name']} and gain 10 XP.")
            self.current_npc = None
            self.check_level_up()
        else:
            self.npc_attack()

    def npc_attack(self):
        npc_roll = random.randint(1, 20)
        player_roll = random.randint(1, 20)

        self.output_message(f"{self.current_npc['name']} rolls a {npc_roll} to attack.")
        self.output_message(f"You roll a {player_roll} to defend.")

        if npc_roll == 1:
            self.current_npc['health'] -= 1
            self.output_message(f"{self.current_npc['name']} fumbles and hurts itself!")
        elif npc_roll == 20:
            self.player_hp -= 10
            self.output_message(f"Critical hit! The {self.current_npc['name']} deals 10 damage to you.")
        elif npc_roll > player_roll:
            self.player_hp -= (npc_roll - player_roll)
            self.output_message(f"The {self.current_npc['name']} hits you for {npc_roll - player_roll} damage.")
        else:
            self.output_message(f"The {self.current_npc['name']} misses.")

        if self.player_hp <= 0:
            self.end_game()

    def add_item_to_inventory(self, name, quantity):
        for item in self.player_inventory:
            if item['name'] == name:
                item['quantity'] += quantity
                return
        self.player_inventory.append({'name': name, 'quantity': quantity})

    def trade(self, npc_name):
        if npc_name.lower() != 'merchant' or not self.current_npc or self.current_npc['name'].lower() != 'merchant':
            self.output_message("There is no merchant to trade with.")
            return
        self.output_message("The merchant offers the following items:")
        for item in self.current_npc['items']:
            self.output_message(f"{item}: {self.current_npc['items'][item]['price']} gold")

    def buy(self, item_name):
        if not self.current_npc or self.current_npc['name'].lower() != 'merchant':
            self.output_message("There is no merchant to buy from.")
            return
        item = self.current_npc['items'].get(item_name)
        if not item:
            self.output_message("The merchant does not have that item.")
            return
        if self.player_gold < item['price']:
            self.output_message("You do not have enough gold to buy that.")
            return
        self.player_gold -= item['price']
        self.add_item_to_inventory(item_name, 1)
        self.output_message(f"You buy a {item_name}.")

    def sell(self, item_name):
        for item in self.player_inventory:
            if item['name'].lower() == item_name.lower():
                if item['quantity'] > 1:
                    item['quantity']-= 1
                else:
                    self.player_inventory.remove(item)
                self.player_gold += item['price']
                self.output_message(f"You sell a {item_name}.")
                return
        self.output_message("You do not have that item.")

    def leave(self):
        if not self.current_npc or self.current_npc['name'].lower() != 'merchant':
            self.output_message("There is no one to leave.")
            return
        self.current_npc = None
        self.output_message("You leave the merchant's stall.")

    def show_help(self):
        self.output_message("""
            Commands:
            - go [direction]: Move in a specified direction (north, south, east, west)
            - explore: Explore the current area for NPCs or other interactions
            - attack [npc]: Attack a specific NPC
            - attack: Attack the current NPC
            - trade merchant: Trade with the merchant NPC
            - buy [item]: Buy an item from the merchant
            - sell [item]: Sell an item to the merchant
            - leave: Leave the merchant's stall
            - help: List the description of things you can do and that can happen
            - end: End your game session and save your score
            - inventory: Show your current inventory
        """)

    def update_inventory(self):
        inventory_items = ', '.join(f"{item['name']} ({item['quantity']})" for item in self.player_inventory)
        self.output_message(f"Inventory: {inventory_items or 'Your inventory is empty.'}")

    def check_level_up(self):
        if self.player_xp >= self.player_level * 100:
            self.player_level += 1
            self.player_xp = 0
            self.output_message(f"You leveled up! You are now level {self.player_level}.")

    def update_leaderboard(self):
        self.leaderboard.config(state='normal')
        self.leaderboard.delete(1.0, tk.END)
        for entry in self.leaderboard_data:
            self.leaderboard.insert(tk.END, f"{entry['username']}: {entry['score']} points\n")
        self.leaderboard.config(state='disabled')

    def end_game(self):
        score = self.calculate_score()
        self.save_to_leaderboard(self.username, score)
        self.output_message(f"Game over! Your score: {score}")
        self.output_message("You have died and lost all your progress. This is permadeath.")
        self.player_hp = 100
        self.player_gold = 10
        self.player_inventory = []
        self.player_xp = 0
        self.player_level = 1
        self.navigation_count = 0
        self.current_area = 'forest'
        self.current_npc = None
        self.update_leaderboard()

    def calculate_score(self):
        return self.navigation_count + sum(item['quantity'] for item in self.player_inventory) + self.player_gold + self.player_xp

    def save_to_leaderboard(self, username, score):
        new_entry = {'username': username, 'score': score}
        self.leaderboard_data.append(new_entry)
        self.leaderboard_data = sorted(self.leaderboard_data, key=lambda x: x['score'], reverse=True)[:10]
        with open('leaderboard.json', 'w') as f:
            json.dump(self.leaderboard_data, f, indent=4)
        self.update_leaderboard()

if __name__ == "__main__":
    root = ThemedTk(theme="equilux")
    app = RPGGame(root)
    root.mainloop()