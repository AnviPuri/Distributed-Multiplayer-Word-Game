import game.word


class Game:
    def __init__(self):
        self.current_word = None

    def choose_word(self):
        self.current_word = game.word.choose_random_word()
        print(f"Word of the game is: {self.current_word}")

    def get_game_result(self, guessed_word, player_current_score):
        print("Get Result for the word played.")
        print(f"Current Score of Player: {player_current_score}")
        if self.current_word == guessed_word:
            print("Correct word guessed by player!")
            result = {
                "result_output": "CORRECT_GUESS"
            }
            return result
        else:
            return self.calculate_player_score(guessed_word, player_current_score)

    def calculate_player_score(self, guessed_word, player_current_score):
        i = 0
        any_correct_guess = False
        word_interpretation = ""
        result = {}
        for letter in self.current_word:
            if letter == guessed_word[i]:
                word_interpretation += letter
                player_current_score += 1
                any_correct_guess = True
            else:
                word_interpretation += "*"
            i += 1
        if not any_correct_guess:
            word_interpretation = None
        print(f"Word interpretation is {word_interpretation}")
        print(f"Updated score of player is  {player_current_score}")
        result["result_output"] = "INCORRECT_GUESS"
        result["last_word_interpretation"] = word_interpretation
        result["updated_score"] = player_current_score
        return result
