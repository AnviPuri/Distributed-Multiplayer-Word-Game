class ClientDetail:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.can_play_the_round = False
        self.client_score = 0
        self.last_played_word = None
        self.last_word_interpretation = None
        self.has_guessed_word = False

    def reset_client_state(self):
        self.client_score = 0
        self.last_played_word = None
        self.last_word_interpretation = None
        self.has_guessed_word = False

    def set_can_play_round(self, can_play_the_round):
        self.can_play_the_round = can_play_the_round

    def set_client_score(self, client_score):
        self.client_score = client_score

    def set_last_played_word(self, last_played_word):
        self.last_played_word = last_played_word

    def set_last_word_interpretation(self, last_word_interpretation):
        self.last_word_interpretation = last_word_interpretation

    def set_has_guessed_word(self, has_guessed_word):
        self.has_guessed_word = has_guessed_word
