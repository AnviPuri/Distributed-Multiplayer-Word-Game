import game.word


# start the game as soon as we have more than 1 client
# the game will have 5 rounds. In case the word is guessed before those 5 rounds, the game ends and winner is declared
# in every round fifo ordering is done
# the clients are asked one by one to guess the word and their result is calculated amd sent back to the client
# at any point if the correct word is guessed , the game ends and the result is shared with all clients
# each client also has canplaythisround value which tells if it will be a part of this round

# once the game ends, a new game is started

# get word given by player and calculate score based on word - played_word, current_word
# for every correct letter and placement - +1
# we also maintain the correct letters and their placement in the word that were chosen correct by the players
class Game:
    def __init__(self):
        self.current_word = None

    def choose_word(self):
        self.current_word = game.word.choose_random_word()
        print(f"Word of the game is: {self.current_word}")

    def get_game_result(self, guessed_word, player_current_score):
        # to add a check that the played word has to be a 5 letter word on client side itself
        # can add to server side later

        # to return updated score of the player
        # along with correctly chosen letters
        # only the plater will be displayed the word not the other players
        # in case correct word chosen game is ended and all clients are conveyed the result
        # so for client to save their score, last_played_word, last_word_interpretation - word_interpretation will contain a string with correctly played letters else None in case of no correct guess
        # if correct guess return a dictionary with result_output = correct_guess/incorrect_guess
        # in case of incorrect guess return last_word_interpretation and updated score
        print("Get Result for the word played.")
        print(f"Word played: {guessed_word}")
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
                print("Correct letter chosen")
                word_interpretation += letter
                player_current_score += 1
                any_correct_guess = True
            else:
                print("Wrong letter chosen")
                word_interpretation += "*"
        if not any_correct_guess:
            word_interpretation = None
        print(f"Word interpretation is {word_interpretation}")
        print(f"Updated score of player is  {player_current_score}")
        result["result_output"] = "INCORRECT_GUESS"
        result["last_word_interpretation"] = word_interpretation
        result["updated_score"] = player_current_score
        return result
