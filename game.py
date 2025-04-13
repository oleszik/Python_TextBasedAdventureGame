import json
import os
import string
from typing import List

MENU = """*** Welcome to the Journey to Mount Qaf ***\n\n1. Start a new game (START)\n2. Load your progress (LOAD)\n3. Quit the game (QUIT)"""

CREATION = """Good luck on your journey, {username}!
Your character: {name}, {species}, {gender}
Your inventory: {snack}, {weapon}, {tool}
Difficulty: {difficulty}
Number of lives: {lives}
---------------------------"""

HELP = """Type the number of the option you want to choose.
Commands you can use:
/i => Shows inventory.
/q => Exits the game.
/c => Shows the character traits.
/h => Shows help.
/s => Save the game."""

INVENTORY = "Inventory: {inventory}"
CHARACTER = "Your character: {name}, {species}, {gender}.\nLives remaining: {lives}"


def input_exact(correct: List[str], output='') -> str:
    inp = input(output).lower().strip()
    while inp not in correct:
        print("Unknown input! Please enter a valid one.")
        inp = input().lower().strip()
    return inp


class Player:
    def __init__(self, username, data):
        self.username = username
        self.data = data

    @classmethod
    def create_character(cls, username):
        print("Create your character:")
        char = []
        for i in ['name', 'species', 'gender']:
            char.append(input(f"\t{string.capwords(i)}: ").strip())

        print("Pack your bag for the journey:")
        items = []
        for i in ['Snack', 'Weapon', 'Tool']:
            print(f"{i}: ", end='')
            items.append(input().strip())

        print("Choose your difficulty:")
        print("\t1. Easy\n\t2. Medium\n\t3. Hard")
        diff = input_exact(['1', '2', '3', 'easy', 'medium', 'hard'], '> ')
        difficulty = 'easy' if diff in ['1', 'easy'] else 'medium' if diff in ['2', 'medium'] else 'hard'
        lives = 5 if difficulty == 'easy' else 3 if difficulty == 'medium' else 1

        return cls(username, {
            "character": {"name": char[0], "species": char[1], "gender": char[2]},
            "inventory": {"snack": items[0], "weapon": items[1], "tool": items[2], "content": items.copy()},
            "progress": {"level": 'level1', "scene": 'scene1'},
            "lives": lives,
            "difficulty": difficulty
        })

    def show_inventory(self):
        print(INVENTORY.format(inventory=", ".join(self.data['inventory']['content'])))

    def show_character(self):
        print(CHARACTER.format(
            name=self.data['character']['name'],
            species=self.data['character']['species'],
            gender=self.data['character']['gender'],
            lives=self.data['lives'])
        )

    def save_game(self):
        save_data = {
            "character": self.data["character"],
            "inventory": {
                "snack_name": self.data["inventory"]["snack"],
                "weapon_name": self.data["inventory"]["weapon"],
                "tool_name": self.data["inventory"]["tool"],
                "content": self.data["inventory"]["content"]
            },
            "progress": self.data["progress"],
            "lives": self.data["lives"],
            "difficulty": self.data["difficulty"]
        }

        os.makedirs("data/saves", exist_ok=True)
        save_path = f"data/saves/{self.username}.json"
        with open(save_path, "w") as f:
            json.dump(save_data, f, indent=2)
        print("Game saved!")

    def __str__(self):
        return CREATION.format(
            username=self.username,
            name=self.data['character']['name'],
            species=self.data['character']['species'],
            gender=self.data['character']['gender'],
            snack=self.data['inventory']['snack'],
            weapon=self.data['inventory']['weapon'],
            tool=self.data['inventory']['tool'],
            difficulty=self.data['difficulty'],
            lives=self.data['lives'])


def substitute_story(story, inventory):
    story_str = json.dumps(story)
    story_str = story_str.replace('{tool}', inventory['tool'])
    story_str = story_str.replace('{weapon}', inventory['weapon'])
    story_str = story_str.replace('{snack}', inventory['snack'])
    return json.loads(story_str)


def play_game(player):
    with open('data/story.json') as f:
        story = substitute_story(json.load(f), player.data['inventory'])

    while True:
        level_id = player.data['progress']['level']
        scene_id = player.data['progress']['scene']
        level = story[level_id]
        scene = level['scenes'][scene_id]

        if scene_id == 'scene1' and level_id == 'level2':
            print("------ Level 2 ------")

        print()
        print(scene['text'])
        print("What will you do? Type the number of the option or type '/h' to show help.\n")
        for i, option in enumerate(scene['options'], 1):
            print(f"{i}. {option['option_text']}")
        choice = input('> ').strip().lower()

        if choice == '/h':
            print(HELP)
        elif choice == '/i':
            player.show_inventory()
        elif choice == '/c':
            player.show_character()
        elif choice == '/s':
            player.save_game()
        elif choice == '/q':
            print("Thanks for playing!")
            exit()
        elif choice.isdigit() and 1 <= int(choice) <= len(scene['options']):
            option = scene['options'][int(choice) - 1]
            print()
            print(option['result_text'])

            # Track if the player died
            death = False

            for action in option['actions']:
                if action.startswith('+'):
                    item = action[1:]
                    if item not in player.data['inventory']['content']:
                        player.data['inventory']['content'].append(item)
                    print(f"------ Item added: {item} ------")
                elif action.startswith('-'):
                    item = action[1:]
                    if item in player.data['inventory']['content']:
                        player.data['inventory']['content'].remove(item)
                    print(f"------ Item removed: {item} ------")
                elif action == 'hit':
                    player.data['lives'] -= 1
                    if player.data['lives'] <= 0:
                        print("------ You died ------")
                        player.data['lives'] = 5 if player.data['difficulty'] == 'easy' else 3 if player.data['difficulty'] == 'medium' else 1
                        player.data['progress']['scene'] = 'scene1'
                        death = True
                        break
                    else:
                        print(f"------ Lives remaining: {player.data['lives']} ------")
                elif action == 'heal':
                    player.data['lives'] += 1
                    print(f"------ Lives remaining: {player.data['lives']} ------")

            if death:
                continue  # Restart loop to reprint scene1 of the same level

            if option['next'] == 'end':
                current_level = player.data['progress']['level']
                next_level_num = int(current_level.replace("level", "")) + 1
                next_level = f"level{next_level_num}"
                player.data['progress']['level'] = next_level
                player.data['progress']['scene'] = 'scene1'
                print(f"------ Level {next_level_num} ------")
                continue

            # Normal scene transition
            player.data['progress']['scene'] = option['next']

        else:
            print("Unknown input! Please enter a valid one.")



def load_game():
    saves_path = "data/saves"
    if not os.path.exists(saves_path) or not os.listdir(saves_path):
        print("No saved data found")
        return

    print("Choose username (/b - back):\n")
    usernames = [f[:-5] for f in os.listdir(saves_path) if f.endswith(".json")]
    for name in usernames:
        print(name)
    while True:
        choice = input("> ").strip()
        if choice.lower() == "/b":
            return
        elif choice in usernames:
            print("Loading your progress...")
            with open(f"{saves_path}/{choice}.json") as f:
                data = json.load(f)
            level_number = data["progress"]["level"].replace("level", "")
            print(f"Level {level_number}")

            # Rebuild inventory format
            inventory = {
                "snack": data["inventory"]["snack_name"],
                "weapon": data["inventory"]["weapon_name"],
                "tool": data["inventory"]["tool_name"],
                "content": data["inventory"]["content"]
            }
            data["inventory"] = inventory
            player = Player(choice, data)
            play_game(player)
            return
        else:
            print("Unknown input! Please enter a valid one.")


def main():
    while True:
        print(MENU)
        choice = input('> ').strip().lower()
        if choice in ['1', 'start']:
            username = input("Starting a new game...\nEnter a username ('/b' to go back): ").strip()
            if username.lower() == '/b':
                continue
            player = Player.create_character(username)
            print(player)
            play_game(player)
        elif choice in ['2', 'load']:
            load_game()
        elif choice in ['3', 'quit']:
            print("Goodbye")
            break
        else:
            print("Unknown input! Please enter a valid one.")


if __name__ == '__main__':
    main()
