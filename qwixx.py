import random


# https://www.thegameroom.nl/dobbelspellen/qwixx/

WHITE_DICE = 2
DICE_PER_COLOR = 1

FAILED_THROW_PENALTY = -5
MIN_CROSSES_BEFORE_CLOSING = 5

PLAYERS_MIN = 2
PLAYERS_MAX = 5

# end conditions
MAX_FAILED_THROWS = 4
MAX_COLORS_CLOSED = 2
MAX_THROWS = 0  # not a real rule

ASCENDING_COLORS = ["red", "yellow"]
DESCENDING_COLORS = ["green", "blue"]
ALL_COLORS = ASCENDING_COLORS.copy()
ALL_COLORS.extend(DESCENDING_COLORS)

COLOR_NUMBERS = {}
for _ in ASCENDING_COLORS:
    COLOR_NUMBERS[_] = list(range(2, 13))

for _ in DESCENDING_COLORS:
    COLOR_NUMBERS[_] = list(range(12, 1, -1))


def create_player_card():
    card = {}
    for color in ALL_COLORS:
        card[color] = {}

    for color in ASCENDING_COLORS:
        for number in range(2, 13):
            card[color][number] = False

    for color in DESCENDING_COLORS:
        for number in range(12, 1, -1):
            card[color][number] = False

    card["failed_throws"] = 0

    return card


def calculate_points(card):  # works
    points = 0
    for color in ALL_COLORS:
        color_crosses = 0
        for number in card[color].keys():
            if card[color][number]:  # is crossed
                color_crosses += 1

                if number == COLOR_NUMBERS[color][-1]:  # locking bonus
                    color_crosses += 1

        while color_crosses > 0:
            points += color_crosses
            color_crosses -= 1

    return points + card["failed_throws"] * FAILED_THROW_PENALTY


def dice_throw():
    return random.randint(1, 6)


class Player:
    def __init__(self, host_game, player_number):
        self.game = host_game
        self.number = player_number

        self.card = create_player_card()

    def __repr__(self):
        lines = [f"Player #{self.number}: {calculate_points(self.card)} points"]
        for key in self.card.keys():
            if key == "failed_throws":
                lines.append(f"{key}: {self.card[key]}")

            else:  # key is a color
                number_row_formatted = []
                for number in self.card[key].keys():
                    if self.card[key][number]:
                        number_formatted = f"/{str(number)}/"
                        number_row_formatted.append(number_formatted)
                    else:
                        number_row_formatted.append(f" {number} ")

                add_line = f"{key}: ".zfill(8).replace("0", " ")
                add_line += " ".join(number_row_formatted)
                lines.append(add_line)

        return "\n".join(lines)

    def try_to_cross(self, color, cross_number):
        print(f"- Player {self.number} trying to cross {color} {cross_number}...")
        if color in game.closed_colors:
            print(f"-- {color} is already closed")
            return False

        color_crosses = 0
        furthest_crossed_number = 0
        for number in COLOR_NUMBERS[color]:
            if self.card[color][number]:
                color_crosses += 1
                furthest_crossed_number = number

        print(f"-- Crosses = {color_crosses}, furthest = {furthest_crossed_number}")

        can_cross = False
        if cross_number == COLOR_NUMBERS[color][-1]:
            if not color_crosses >= MIN_CROSSES_BEFORE_CLOSING:
                print(f"-- Not enough crosses to close ({color_crosses} < {MIN_CROSSES_BEFORE_CLOSING})")

        elif color in ASCENDING_COLORS:
            if not furthest_crossed_number:
                # nothing crossed yet
                can_cross = True

            elif cross_number > furthest_crossed_number:
                # allowed to cross after furthest cross
                can_cross = True

        elif color in DESCENDING_COLORS:
            if not furthest_crossed_number:
                # nothing crossed yet
                can_cross = True

            elif cross_number < furthest_crossed_number:
                # allowed to cross after furthest cross
                can_cross = True

        if can_cross:
            self.card[color][cross_number] = True
            print(f"Player {self.number} crossed {color} {cross_number}")
            if cross_number == COLOR_NUMBERS[color][-1]:
                self.game.append_closed_color(color)
        else:
            print(f"-- Unable to cross")
        return can_cross

    def failed_throw(self):
        self.card["failed_throws"] += 1


class Game:
    def __init__(self, n_players=0):
        if not n_players:
            n_players = random.randint(PLAYERS_MIN, PLAYERS_MAX)

        print(f"Starting game with {n_players} players")

        self.players = [Player(self, player_number) for
                        player_number in range(1, n_players + 1)]
        self.next_players_throw = random.randint(1, n_players)
        print(f"Next player's throw: {self.next_players_throw}")
        self.throws = 0
        self.closed_colors = []

    def is_over(self):
        if MAX_THROWS and self.throws == MAX_THROWS:
            print(f"Game over, max throws reached ({MAX_THROWS})")
            return True

        if len(self.closed_colors) == MAX_COLORS_CLOSED:
            print(f"Game over, max colors closed ({MAX_COLORS_CLOSED})")
            return True

        for player in self.players:
            for color in ALL_COLORS:
                if color in self.closed_colors:
                    continue

                if player.card[color][COLOR_NUMBERS[color][-1]]:  # closed color
                    self.closed_colors.append(color)

                    if len(self.closed_colors) == MAX_COLORS_CLOSED:
                        print("Game over, closed colors:", self.closed_colors)
                        return True

                    continue

            failed_throws = player.card["failed_throws"]
            if failed_throws >= MAX_FAILED_THROWS:
                print(f"Game over, player {player.number} has {failed_throws} failed throws")
                return True

        return False

    def do_next_throw(self):
        self.throws += 1

        print(f"THROW {self.throws}: player {self.next_players_throw} is throwing")

        throw_result = {}
        for color in ALL_COLORS:
            throw_result[color] = 0
        throw_result["white"] = []

        for _ in range(WHITE_DICE):
            throw_result["white"].append(dice_throw())

        for color in ALL_COLORS:
            for _ in range(DICE_PER_COLOR):
                throw_result[color] = dice_throw()

        print(f"Player {self.next_players_throw} threw: {throw_result}")

        for player in self.players:
            # all players can use both white dice
            total_white = sum(throw_result["white"])
            try_colored_die_order = ALL_COLORS.copy()
            random.shuffle(try_colored_die_order)

            crossed_white = False
            for i in range(len(try_colored_die_order)):
                if player.try_to_cross(try_colored_die_order[i], total_white):
                    crossed_white = True
                    break

            # player whose turn it is can use 1 white & 1 colored
            if player.number == self.next_players_throw:
                try_white_die_order = throw_result["white"].copy()
                random.shuffle(try_white_die_order)
                random.shuffle(try_colored_die_order)
                crossed_mixed_colors = False
                for i in range(len(try_white_die_order)):
                    for j in range(len(try_colored_die_order)):
                        color = try_colored_die_order[j]
                        cross_number = throw_result["white"][i] + \
                            throw_result[color]
                        
                        if player.try_to_cross(color, cross_number):
                            crossed_mixed_colors = True
                            break

                    if crossed_mixed_colors:
                        break

                if not (crossed_white or crossed_mixed_colors):
                    print(f"Player {player.number} failed a throw!")
                    player.failed_throw()

        self.next_players_throw += 1
        if self.next_players_throw > len(self.players):
            self.next_players_throw = 1

    def append_closed_color(self, color):
        self.closed_colors.append(color)
        print(f"Color {color} is closed")

    def dump_winners(self):
        winners = []
        highest_points = 0

        for player in self.players:
            points = calculate_points(player.card)
            if points >= highest_points:
                highest_points = points
                winners.append(player.number)

        print(f"Winners: {winners} with {highest_points} points")

    def dump_player_cards(self):
        print(f"{'/' * 10} PLAYER CARDS:")
        for player in self.players:
            print(player)


if __name__ == "__main__":
    game = Game()

    while not game.is_over():
        game.do_next_throw()

    game.dump_winners()
    game.dump_player_cards()
