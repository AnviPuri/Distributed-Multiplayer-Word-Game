class ClientDetail:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        # have to change this to true at some point
        self.can_play_the_round = False
        self.client_score = 0
        self.last_played_word = None
        self.last_word_interpretation = None
        self.has_guessed_word = False

    def setCanPlayTheRound(self, can_play_the_round):
        self.can_play_the_round = can_play_the_round

    def setClientScore(self, can_play_the_round):
        self.can_play_the_round = can_play_the_round

    def setLastPlayedWord(self, last_played_word):
        self.last_played_word = last_played_word

    def setLastWordInterpretation(self, last_word_interpretation):
        self.last_word_interpretation = last_word_interpretation

    def setHasGuessedWord(self, has_guessed_word):
        self.has_guessed_word = has_guessed_word
